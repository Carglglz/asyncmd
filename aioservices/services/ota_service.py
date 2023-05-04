import ssl as _ssl
from aioclass import Service
import aioctl
import uasyncio as asyncio
from esp32 import Partition
import hashlib
from micropython import const
import binascii
import gc
from machine import unique_id
import time
import sys


BLOCKLEN = const(4096)  # data bytes in a flash block


class OTAService(Service):
    def __init__(self, name):
        super().__init__(name)
        self.version = "1.0"
        self.info = f"Async OTA client v{self.version}"
        self.type = "runtime.service"  # continuous running, other types are
        self.enabled = True
        self.docs = "https://github.com/Carglglz/asyncmd/blob/main/README.md"
        self.part = Partition(Partition.RUNNING).get_next_update()
        self.sha = hashlib.sha256()
        self.block = 0
        self.buf = bytearray(BLOCKLEN)
        self._tmp_buf = b""
        self.buflen = 0
        self.read_size = 512
        self._key = f"SSL_key{binascii.hexlify(unique_id()).decode()}.der"
        self._cert = f"SSL_certificate{binascii.hexlify(unique_id()).decode()}.der"
        self._cadata = "ROOT_CA_cert.pem"
        self.sslctx = None
        self._start_ota = False
        self.check_sha = ""
        self._total_blocks = 0
        self._OK = False
        self._ota_complete = False
        self._bg = False
        self.host = ""
        self.port = 0
        self._t0 = 0
        self._tf = 0
        self.args = []
        self._progress = 0
        self.kwargs = {
            "tls": False,
            "hostname": None,
            "read_size": self.read_size,
            "on_stop": self.on_stop,
            "on_error": self.on_error,
        }

    def show(self):
        _progress = (
            f"   Firmware: {self.block*BLOCKLEN/1000}/"
            + f"{self._total_blocks*BLOCKLEN/1000} kB |"
            + f" {self._fmt_time()}\n"
        )
        _progress += f"    Progress: {int(self._progress*100)} % "
        _progress += f"| {'█' * (int(self._progress*80))}"

        return ("Stats", _progress)

    def on_stop(self, *args, **kwargs):  # same args and kwargs as self.task
        if self.log:
            self.log.info(f"[{self.name}.service] stopped")
        return

    def on_error(self, e, *args, **kwargs):
        if self.log:
            self.log.error(f"[{self.name}.service] Error callback {e}")
        return e

    def start_ota(self, host, port, check_sha, blocks=0, bg=False):
        self.host = host
        self.port = port
        self.check_sha = check_sha
        self._total_blocks = blocks
        self._start_ota = True
        self._bg = bg
        self._tmp_buf = bytearray(self.kwargs.get("read_size", self.read_size))

    async def do_ota(self):
        nb = 0
        idx = 0
        while True:
            try:
                self._tmp_buf = await self.cli_soc.read(self.read_size)
                nb = len(self._tmp_buf)
                if self._tmp_buf != b"":
                    self.buf[idx : idx + nb] = self._tmp_buf
                    idx += nb
                    if idx < BLOCKLEN:
                        if self.block < self._total_blocks:
                            while idx < BLOCKLEN:
                                if BLOCKLEN - idx < self.read_size:
                                    self._tmp_buf = await self.cli_soc.read(
                                        BLOCKLEN - idx
                                    )
                                else:
                                    self._tmp_buf = await self.cli_soc.read(
                                        self.read_size
                                    )

                                nb = len(self._tmp_buf)
                                if self._tmp_buf != b"":
                                    self.buf[idx : idx + nb] = self._tmp_buf
                                    idx += nb
                    self.buflen = idx
                    self.sha.update(self.buf)
                    if self.buflen == BLOCKLEN:
                        self.part.writeblocks(self.block, self.buf)
                    self.block += 1
                    idx = 0
                    self._progress = self.block / self._total_blocks
                    # print(f"{self._progress * 100:.1f} %", end="\r")
                    if self.log:
                        if int(self.block % (self._total_blocks / 4)) == 0:
                            try:
                                self.log.info(
                                    f"[{self.name}.service] OTA:"
                                    + f" {int(self._progress * 100)} %"
                                )
                            except Exception:
                                pass

                    if self.block == self._total_blocks:
                        self.a_writer.write(b"OK")
                        await self.a_writer.drain()
                        break
                    if self._bg:
                        await asyncio.sleep_ms(200)
                else:
                    print("END OF FILE")
                    break
            except Exception as e:
                if e == KeyboardInterrupt:
                    break
                else:
                    raise e
        self._ota_complete = True
        gc.collect()

    def check_ota(self):
        del self.buf
        calc_sha = binascii.hexlify(self.sha.digest()).decode()
        if calc_sha != self.check_sha:
            raise ValueError(
                "SHA mismatch calc:{} check={}".format(calc_sha, self.check_sha)
            )
        else:
            self._OK = True
        self.part.set_boot()
        return True

    def _fmt_time(self):
        mm = 0
        if not self._tf:
            if self._t0:
                ss = time.time() - self._t0
            else:
                ss = 0
        else:
            ss = self._tf - self._t0
        mm = ss // 60
        ss = ss % 60
        if mm < 10:
            mm = f"0{mm}"
        if ss < 10:
            ss = f"0{ss}"
        return f"{mm}:{ss}"

    @aioctl.aiotask
    async def task(self, tls=False, hostname=None, log=None, read_size=512):
        self.log = log

        while not self._start_ota:
            await asyncio.sleep(1)

        if tls:
            if not self.sslctx:
                self.sslctx = _ssl.SSLContext(_ssl.PROTOCOL_TLS_CLIENT)
                self.sslctx.load_verify_locations(cafile=self._cadata)
                self.sslctx.load_cert_chain(self._cert, self._key)
        if self.log:
            self.log.info(f"[{self.name}.service] Starting OTA firmware update...")
        self.cli_soc, self.a_writer = await asyncio.open_connection(
            self.host, self.port, ssl=self.sslctx, server_hostname=hostname
        )
        self.a_writer.write(b"OK")
        await self.a_writer.drain()
        self.read_size = read_size
        self._t0 = time.time()
        await self.do_ota()
        res = self.check_ota()
        assert res is True
        self._tf = time.time()
        if self.log:
            self.log.info(f"[{self.name}.service] OTA update [ \033[92mOK\x1b[0m ]")
        self._start_ota = False
        self.a_writer.close()
        await self.a_writer.wait_closed()
        self.sslctx = None
        return res


service = OTAService("ota")
