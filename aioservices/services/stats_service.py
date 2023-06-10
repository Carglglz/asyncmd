from aioclass import Service
import aioctl
import uasyncio as asyncio
import aiostats
import re
import json
import sys
import os
import gc
import io


class JSONAPIService(Service):
    def __init__(self, name):
        super().__init__(name)
        self.version = "1.0"
        self.info = f"Stats JSON API v{self.version}"
        self.type = "runtime.service"  # continuous running, other types are
        self.enabled = True
        self.docs = "https://github.com/Carglglz/asyncmd/blob/main/README.md"
        self.args = []
        self.kwargs = {
            "host": "0.0.0.0",
            "port": 8888,
            "ssl": False,
            "ssl_params": {},
            "debug": True,
            "on_stop": self.on_stop,
            "on_error": self.on_error,
        }
        self.n_msg = 0
        self.url_pat = re.compile(
            r"^(([^:/\\?#]+):)?"
            + r"(//([^/\\?#]*))?"  # scheme                # NOQA
            + r"([^\\?#]*)"  # user:pass@host:port   # NOQA
            + r"(\\?([^#]*))?"  # route                 # NOQA
            + r"(#(.*))?"  # query                 # NOQA
        )  # fragment              # NOQA
        self.routes = {}
        self._stat_buff = io.StringIO(4000)

    def _szfmt(self, filesize):
        _kB = 1000
        if filesize < _kB:
            sizestr = str(filesize) + " by"
        elif filesize < _kB**2:
            sizestr = "%0.1f kB" % (filesize / _kB)
        elif filesize < _kB**3:
            sizestr = "%0.1f MB" % (filesize / _kB**2)
        else:
            sizestr = "%0.1f GB" % (filesize / _kB**3)
        return sizestr

    def _df(self):
        size_info = os.statvfs(".")
        self._total_b = size_info[0] * size_info[2]
        self._used_b = (size_info[0] * size_info[2]) - (size_info[0] * size_info[3])
        self._free_b = size_info[0] * size_info[3]

    def _taskinfo(self):
        self._tasks_total = len(aioctl.tasks_match("*"))
        self._services_total = len(aioctl.tasks_match("*.service"))
        self._ctasks_total = len(aioctl.tasks_match("*.service.*"))

    def show(self):
        self._df()
        return (
            "Stats",
            (
                f"   Requests: {self.n_msg}"
                + f"\n    Fs(/): total: {self._szfmt(self._total_b)}, used:"
                + f" {self._szfmt(self._used_b)}, free: {self._szfmt(self._free_b)}"
                + f"\n    Mem: total: {self._szfmt(gc.mem_free() + gc.mem_alloc())}, "
                + f"used: {self._szfmt(gc.mem_alloc())}, "
                + f"free: {self._szfmt(gc.mem_free())}"
            ),
        )

    def stats(self):
        # fs,mem,tasks,firmware
        self._df()
        self._taskinfo()
        gc.collect()
        return {
            "fstotal": self._total_b,
            "fsfree": self._free_b,
            "fsused": self._used_b,
            "mtotal": gc.mem_free() + gc.mem_alloc(),
            "mfree": gc.mem_free(),
            "mused": gc.mem_alloc(),
            "tasks": self._tasks_total,
            "services": self._services_total,
            "ctasks": self._ctasks_total,
            "requests": self.n_msg,
            "firmware": sys.version,
            "machine": sys.implementation._machine,
            "platform": sys.platform,
        }

    def on_stop(self, *args, **kwargs):  # same args and kwargs as self.task
        # self.app awaits self.app.server.wait_closed which
        # consumes Cancelled error so this does not run
        if self.log:
            self.log.info(f"[{self.name}.service] stopped")
            # aioctl.add(self.app.shutdown)

        return

    def on_error(self, e, *args, **kwargs):
        if self.log:
            self.log.error(f"[{self.name}.service] Error callback {e}")
        return e

    async def send_stats(self, writer, debug=False):
        self._stat_buff.seek(0)

        json.dump(aiostats.stats("*.service", debug), self._stat_buff)
        len_b = self._stat_buff.tell()
        self._stat_buff.seek(0)
        writer.write(b"HTTP/1.1 200 OK\r\n")
        if self.log:
            self.log.info(f"[{self.name}.service] HTTP/1.1 200 OK")
        writer.write(b"Content-Type: application/json\r\n")
        writer.write(f"Content-Length: {len_b}\r\n".encode("utf-8"))
        writer.write(b"\r\n")
        await writer.drain()
        for i in range(0, len_b, 512):
            writer.write(self._stat_buff.read(512).encode("utf-8"))
        await writer.drain()
        writer.close()
        await writer.wait_closed()

    async def handle_connection(self, reader, writer):
        try:
            req = await reader.readline()
            if self.log:
                self.log.info(f"[{self.name}.service] {req.decode().strip()}")
            try:
                method, uri, proto = req.split(b" ")
                m = re.match(self.url_pat, uri)
                route_req = m.group(5)
            except Exception as e:
                if self.log:
                    self.log.warning(f"[{self.name}.service] Malformed request: {req}")
                    self.log.error(f"[{self.name}.service] {e}")
                writer.close()
                await writer.wait_closed()
                return

            while True:
                h = await reader.readline()
                if h == b"" or h == b"\r\n":
                    break
                if self.log:
                    self.log.debug(f"[{self.name}.service] {h}")

            if self.log:
                self.log.debug(
                    f"[{self.name}.service] route: {route_req.decode('utf-8')}"
                )

            await self.send_stats(writer, debug=route_req.decode("utf-8"))
            self.n_msg += 1
            gc.collect()
        except Exception as e:
            self.on_error(e)
            gc.collect()

    @aioctl.aiotask
    async def task(
        self,
        host="0.0.0.0",
        port=8888,
        ssl=False,
        ssl_params={},
        debug=True,
        log=None,
    ):
        self.log = log
        self.server = await asyncio.start_server(
            self.handle_connection, host, port, ssl=ssl
        )
        while True:
            try:
                await self.server.wait_closed()
                break
            except AttributeError:  # pragma: no cover
                # the task hasn't been initialized in the server object yet
                # wait a bit and try again
                await asyncio.sleep(0.1)

        # if ssl:
        #     if not self.sslctx:
        #         self.sslctx = _ssl.SSLContext(_ssl.PROTOCOL_TLS_CLIENT)
        #         self.sslctx.load_verify_locations(cafile=ssl_params["ca"])
        #         self.sslctx.load_cert_chain(ssl_params["cert"], ssl_params["key"])


service = JSONAPIService("stats")
