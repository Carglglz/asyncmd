from aioclass import Service
import aioctl
import uasyncio as asyncio
import aiostats
import re
import json


class JSONAPIService(Service):
    def __init__(self, name):
        super().__init__(name)
        self.version = "1.0"
        self.info = f"Stats JSON API  v{self.version}"
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

    def pre_route(self, writer):
        async def _func(writer):
            await self.send_stats(writer)

        return _func

    # b'/': pre_route('/www/page.htm'),
    # b'/static/jquery.js': pre_route('/www/jquery-3.5.1.min.js')}

    def route(self, location, writer):
        self.routes[location] = self.pre_route(writer)

    async def send_stats(self, writer):
        _stats = json.dumps(aiostats.stats("*.service")).encode("utf-8")
        writer.write(b"HTTP/1.1 200 OK\r\n")
        writer.write(b"Content-Type: application/json\r\n")
        writer.write(f"Content-Length: {len(_stats)}\r\n".encode("utf-8"))
        writer.write(b"\r\n")
        await writer.drain()
        writer.write(_stats)
        await writer.drain()
        writer.close()
        await writer.wait_closed()

    async def handle_connection(self, reader, writer):
        req = await reader.readline()
        if self.log:
            self.log.info(f"[{self.name}.service] {req}")
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
            self.log.info(f"[{self.name}.service]route: {route_req.decode('utf-8')}")
        await self.send_stats(writer)
        self.n_msg += 1
        # test = route_req in self.routes
        # print("Route found?: {}".format(test))

        # if route_req in self.routes:
        #     await routes[route_req](writer)
        # else:
        #     writer.write(b"HTTP/1.0 404 Not Found\r\n")
        #     writer.write(b"\r\n")
        #     await writer.drain()
        #     writer.close()
        #     await writer.wait_closed()

    def show(self):
        return (
            "Stats",
            f"   Requests: {self.n_msg}",
        )

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
