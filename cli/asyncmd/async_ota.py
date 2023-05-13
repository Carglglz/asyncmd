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
    index, wheel, nb_of_total, speed, time_e, loop_l, percentage, ett, size_bar=bar_size
):
    l_bloc = bloc_progress[loop_l]
    if index == size_bar:
        l_bloc = "█"
    sys.stdout.write("\033[K")
    print(
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


class AOTAServer:
    """
    Async OTA Server Class
    """

    def __init__(
        self,
        client,
        port,
        topic,
        firmware,
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
            # self.context.load_verify_locations(cadata=self.cadata)

        self.update_sha(firmware)

    def update_sha(self, firmware):
        self._fw_file = firmware
        with open(firmware, "rb") as fwr:
            self.firmware = fwr.read()
        self.sz = len(self.firmware)
        hf = hashlib.sha256(self.firmware)
        if self.sz % BLOCKLEN != 0:
            self._n_blocks = (self.sz // BLOCKLEN) + 1

            hf.update(b"\xff" * ((self._n_blocks * BLOCKLEN) - self.sz))
        else:
            self._n_blocks = self.sz // BLOCKLEN
        self.check_sha = hexlify(hf.digest()).decode()

    def find_localip(self):
        ip_soc = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        ip_soc.connect(("8.8.8.8", 1))
        local_ip = ip_soc.getsockname()[0]
        ip_soc.close()
        return local_ip

    def get_pos_pgb(self):
        n = 1
        while n in self._busy_pos:
            n += 1
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
            with logging_redirect_tqdm():
                self.log.info(f"Connection received from {addr} @ {dport}")
                self._conn_addr.add(addr)
                if self._use_tls:
                    self.log.info("Connection TLS enabled...")
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
                else:
                    self.log.info("OTA Firmware Update Failed.")
                await asyncio.sleep(5)
                if addr in self._conn_addr:
                    self._conn_addr.remove(addr)
                if devname in self._conn_devs:
                    self._conn_devs.remove(devname)

                self.log.info(f"Device @ {addr} disconnected")

        # END ####

        self.log.info(f"Starting async server on {self.host}:{self.port}...")

        self.log.info("OTA Server listening...")
        if self._use_tls:
            self.log.info("OTA TLS enabled...")
        await self.client.publish(
            self._topic,
            payload=json.dumps(
                {
                    "host": self.host,
                    "port": self.port,
                    "sha": self.check_sha,
                    "blocks": self._n_blocks,
                    "bg": self._bg,
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
        sz = len(self.firmware)
        if not self._bg:
            tqdm.write(f"{self._fw_file}  [{sz / 1000:.2f} kB]")
        cnt = 0
        data = await reader.read(2)
        assert data == b"OK"
        _pb_index = self.get_pos_pgb()

        with open(self._fw_file, "rb") as fmwf:
            with tqdm(
                desc=addr,
                total=sz,
                unit="B",
                unit_scale=True,
                unit_divisor=1000,
                position=_pb_index,
                leave=False,
            ) as pgb:
                f = CallbackIOWrapper(pgb.update, fmwf, "read")
                self.buff = f.read(BLOCKLEN)
                while True:
                    try:
                        if self.buff != b"":
                            cnt += len(self.buff)
                            if len(self.buff) < BLOCKLEN:  # fill last block
                                for i in range(BLOCKLEN - len(self.buff)):
                                    self.buff += b"\xff"  # erased flash is ff
                            writer.write(self.buff)
                            await writer.drain()
                            self.buff = f.read(BLOCKLEN)
                        else:
                            break

                    except Exception:
                        # print(e)
                        await asyncio.sleep(0.02)
                        pass
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
