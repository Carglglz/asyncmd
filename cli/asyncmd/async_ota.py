import socket
import hashlib
from binascii import hexlify
import os
import sys
from datetime import timedelta
from tqdm.auto import tqdm
from tqdm.utils import CallbackIOWrapper
from tqdm.contrib.logging import logging_redirect_tqdm
import ssl
import getpass
import json
import asyncio
import time

BLOCKLEN = 4096

bloc_progress = ["▏", "▎", "▍", "▌", "▋", "▊", "▉"]

try:
    columns, rows = os.get_terminal_size(0)
except Exception:
    columns, rows = 80, 80

cnt_size = 65
if columns > cnt_size:
    bar_size = int((columns - cnt_size))
    pb = True
else:
    bar_size = 1
    pb = False


def do_pg_bar(
    fwrite,
    index,
    wheel,
    nb_of_total,
    speed,
    time_e,
    loop_l,
    percentage,
    ett,
    size_bar=bar_size,
):
    l_bloc = bloc_progress[loop_l]
    if index == size_bar:
        l_bloc = "█"
    fwrite("\033[K")
    fwrite(
        "▏{}▏{:>2}{:>5} % | {} | {:>5} kB/s | {}/{} s".format(
            "█" * index + l_bloc + " " * ((size_bar + 1) - len("█" * index + l_bloc)),
            wheel[index % 4],
            int((percentage) * 100),
            nb_of_total,
            speed,
            str(timedelta(seconds=time_e)).split(".")[0][2:],
            str(timedelta(seconds=ett)).split(".")[0][2:],
        ),
        end="\r",
    )
    sys.stdout.flush()


class cstqdm(tqdm):
    """Provides a `total_time` format parameter"""

    @property
    def format_dict(self):
        wheel = ["|", "/", "-", "\\"]
        d = super(cstqdm, self).format_dict
        # print(d)
        total = d.get("total")
        n = d.get("n")
        rate = d.get("rate")
        remaining = (total - n) / rate if rate and total else 0
        widx = wheel[int((n / total) * 100) % 4]
        eta_secs = d.get("elapsed", 0) + remaining
        d.update(eta_secs=self.format_interval(eta_secs) + " s", spin=widx)
        return d


class AOTAServer:
    """
    Async OTA Server Class
    """

    def __init__(
        self,
        client,
        port,
        topic,
        firmwares,
        logger,
        buff=BLOCKLEN,
        tls_params={},
        _async=True,
        _bg=False,
    ):
        try:
            self.host = self.find_localip()
            # print(self.host)
        except Exception as e:
            self.log.info(e)
        self.client = client
        self.port = port
        self.serv_soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serv_soc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.addr = None
        self.buff = bytearray(buff)
        self.conn = None
        self.addr_client = None
        self._use_tls = tls_params
        self.host_fwd = None
        self._async = _async
        self.log = logger
        self._topic = topic
        self._bg = _bg
        self.server = None
        self._conn_addr = set()
        self._conn_devs = set()
        self._busy_pos = set()
        self._device_register = {}
        self._sucess_updates = 0
        self._fail_updates = 0
        if tls_params:
            self.key = tls_params["key"]
            self.cert = tls_params["cert"]
            self.root = tls_params["cafile"]
            self.cadata = ""
            with open(self.root, "r") as root_ca:
                self.cadata += root_ca.read()
                self.cadata += "\n"

            self.context = ssl.create_default_context(
                ssl.Purpose.CLIENT_AUTH, cadata=self.cadata
            )
            self.context.set_ciphers("ECDHE-ECDSA-AES128-CCM8")
            my_p = tls_params["pph"]
            if not my_p:
                while True:
                    try:
                        my_p = getpass.getpass(
                            prompt="Enter passphrase for key "
                            f"'{os.path.basename(self.key)}':",
                            stream=None,
                        )
                        self.context.load_cert_chain(
                            keyfile=self.key, certfile=self.cert, password=my_p
                        )
                        break
                    except ssl.SSLError:
                        # self.log.info(e)
                        self.log.error("Passphrase incorrect, try again...")
            else:
                self.context.load_cert_chain(
                    keyfile=self.key, certfile=self.cert, password=my_p
                )
            self.context.verify_mode = ssl.CERT_REQUIRED

        self.check_sha = {}  # self.context.load_verify_locations(cadata=self.cadata)
        self._default_fwfile = firmwares[0]
        self._fw_files = {fwfile: {} for fwfile in firmwares}
        for fwfile in firmwares:
            if os.path.exists(fwfile):
                self.update_sha(fwfile)

    def update_sha(self, fwfile):
        # self._fw_file = firmware
        with open(fwfile, "rb") as fwr:
            firmware = fwr.read()
        self._fw_files[fwfile]["sz"] = sz = len(firmware)
        hf = hashlib.sha256(firmware)
        if sz % BLOCKLEN != 0:
            self._fw_files[fwfile]["n_blocks"] = _n_blocks = (sz // BLOCKLEN) + 1

            hf.update(b"\xff" * ((_n_blocks * BLOCKLEN) - sz))
        else:
            self._fw_files[fwfile]["n_blocks"] = _n_blocks = sz // BLOCKLEN
        self.check_sha[fwfile] = self._fw_files[fwfile]["sha"] = hexlify(
            hf.digest()
        ).decode()

    def find_localip(self):
        ip_soc = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        ip_soc.connect(("8.8.8.8", 1))
        local_ip = ip_soc.getsockname()[0]
        ip_soc.close()
        return local_ip

    def register_device(self, devname, sha_file):
        self._device_register[devname] = sha_file

    def get_devfile_from_ip(self, ip):
        for dev, sha_file in self._device_register.items():
            if ip == sha_file["ip"]:
                return sha_file["fwfile"]
        return self._default_fwfile

    def get_dev_from_ip(self, ip):
        for dev, sha_file in self._device_register.items():
            if ip == sha_file["ip"]:
                return dev
        return ip

    def get_pos_pgb(self):
        # space progress bars
        n = 1
        while n in self._busy_pos:
            n += 2
        self._busy_pos.add(n)
        return n

    async def start_ota_server(self):
        # SERVE OTA
        async def serve(reader, writer):
            if not hasattr(writer, "awrite"):  # pragma: no cover
                # CPython provides the awrite and aclose methods in 3.8+
                async def awrite(self, data):
                    self.write(data)
                    await self.drain()

                async def aclose(self):
                    self.close()
                    await self.wait_closed()

                from types import MethodType

                writer.awrite = MethodType(awrite, writer)
                writer.aclose = MethodType(aclose, writer)

            addr, dport = writer.get_extra_info("peername")
            _dev = self.get_dev_from_ip(addr)

            with logging_redirect_tqdm():
                self.log.info(f"Connection received from {_dev} @ {dport}")
                self._conn_addr.add(addr)
                if self._use_tls:
                    self.log.info("Connection TLS enabled...")
                await self.client.publish(
                    "device/otaserver/otasrv",
                    payload=json.dumps(
                        {
                            "hostname": "otaserver",
                            "ipaddr": addr,
                            "ota_msg": "started",
                            "n_conn": len(self._conn_addr),
                            "n_success": self._sucess_updates,
                            "n_failures": self._fail_updates,
                        }
                    ),
                )

                self.log.info("Starting OTA Firmware update...")
                await self.do_async_ota(addr, reader, writer)

                self.log.info("Checking Firmware...")
                ota_ok = False
                try:
                    async with self.client.messages() as messages:
                        sub_topic = self._topic
                        if "/all/" in self._topic:
                            sub_topic = self._topic.replace("all", "+")
                        await self.client.subscribe(f"{sub_topic}ok")
                        async for message in messages:
                            # resp from device --> message.topic --> send reset to
                            # message.topic
                            devname = str(message.topic).split("/")[1]
                            if devname not in self._conn_devs:
                                self.log.info(
                                    f"[{message.topic}] {message.payload.decode()}"
                                )
                                self._conn_devs.add(devname)
                                if message.payload.decode() == "OK":
                                    ota_ok = True
                                    break
                                else:
                                    ota_ok = False
                                    break

                except Exception as e:
                    self.log.error(e)
                if ota_ok:
                    self.log.info("OTA Firmware Updated Succesfully!")
                    await self.client.publish(f"device/{devname}/cmd", payload="reset")
                    self._sucess_updates += 1
                else:
                    self.log.info("OTA Firmware Update Failed.")
                    self._fail_updates += 1
                await asyncio.sleep(5)
                if addr in self._conn_addr:
                    self._conn_addr.remove(addr)
                if devname in self._conn_devs:
                    self._conn_devs.remove(devname)
                await self.client.publish(
                    f"device/{devname}/otasrv",
                    payload=json.dumps(
                        {
                            "hostname": devname,
                            "ipaddr": addr,
                            "ota_msg": str(ota_ok),
                            "n_conn": len(self._conn_addr),
                            "n_success": self._sucess_updates,
                            "n_failures": self._fail_updates,
                        }
                    ),
                )

                self.log.info(f"Device @ {_dev} disconnected")

        # END ####

        self.log.info(f"Starting async server on {self.host}:{self.port}...")

        self.log.info("OTA Server listening...")
        if self._use_tls:
            self.log.info("OTA TLS enabled...")
        await self.client.publish(
            self._topic,
            # payload="check"
            payload=json.dumps(  # TODO: Fix
                {
                    "host": self.host,
                    "port": self.port,
                    "sha": self.check_sha[self._default_fwfile],
                    "blocks": self._fw_files[self._default_fwfile]["n_blocks"],
                    "bg": self._bg,
                    "fwfile": self._default_fwfile,
                }
            ),
        )

        self.server = await asyncio.start_server(
            serve, self.host, self.port, ssl=self.context, reuse_port=True
        )

        while True:
            try:
                await self.server.wait_closed()
                break
            except AttributeError:  # pragma: no cover
                # the task hasn't been initialized in the server object yet
                # wait a bit and try again
                await asyncio.sleep(0.1)

    async def do_async_ota(self, addr, reader, writer):
        try:
            columns, rows = os.get_terminal_size(0)
        except Exception:
            columns, rows = 80, 80
        cnt_size = 65
        if columns > cnt_size:
            size_bar = int((columns - cnt_size))
        else:
            size_bar = 1
        wheel = ["|", "/", "-", "\\"]
        fwfile = self.get_devfile_from_ip(addr)
        _dev = self.get_dev_from_ip(addr)

        sz = self._fw_files[fwfile]["sz"]
        if not self._bg:
            tqdm.write(f"{os.path.relpath(fwfile)}  [{sz / 1000:.2f} kB]")
        cnt = 0
        data = await reader.read(2)
        assert data == b"OK"
        _pb_index = self.get_pos_pgb()
        buff = b""
        t_start = time.time()
        with open(fwfile, "rb") as fmwf:
            with cstqdm(
                desc=_dev,
                total=sz,
                unit="B",
                unit_scale=True,
                unit_divisor=1000,
                position=_pb_index,
                bar_format=(
                    "{desc} |{bar} {spin} {percentage:>5.0f} % | "
                    "{n_fmt:>6}/{total_fmt:6} | {rate_fmt:8} | "
                    "{elapsed}/{eta_secs}    "
                ),
                leave=False,
            ) as pgb:
                f = CallbackIOWrapper(pgb.update, fmwf, "read")
                buff = f.read(BLOCKLEN)
                while True:
                    try:
                        if buff != b"":
                            cnt += len(buff)
                            if len(buff) < BLOCKLEN:  # fill last block
                                for i in range(BLOCKLEN - len(buff)):
                                    buff += b"\xff"  # erased flash is ff
                            writer.write(buff)
                            await writer.drain()
                            buff = f.read(BLOCKLEN)
                            loop_index_f = (cnt / sz) * size_bar
                            loop_index = int(loop_index_f)
                            loop_index_l = int(round(loop_index_f - loop_index, 1) * 6)
                            nb_of_total = "{:.2f}/{:.2f} kB".format(
                                cnt / (1000), sz / (1000)
                            )
                            percentage = cnt / sz
                            t_elapsed = time.time() - t_start
                            t_speed = "{:^2.2f}".format((cnt / (1000)) / t_elapsed)
                            ett = sz / (cnt / t_elapsed)

                        else:
                            break

                    except Exception:
                        # print(e)
                        await asyncio.sleep(0.02)
                        pass

        tqdm.write("")
        tqdm.write(f"{os.path.basename(fwfile)} @ {_dev} [ \033[92mOK\x1b[0m ] ")
        do_pg_bar(
            tqdm.write,
            loop_index,
            wheel,
            nb_of_total,
            t_speed,
            t_elapsed,
            loop_index_l,
            percentage,
            ett,
            size_bar,
        )
        tqdm.write("\n")
        self._busy_pos.remove(_pb_index)
        if self._async:
            while True:
                data = await reader.read(2)
                assert data == b"OK"
                writer.close()
                try:
                    await writer.wait_closed()
                except Exception:
                    break
