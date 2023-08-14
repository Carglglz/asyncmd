from microdot_asyncio_serv import Microdot, send_file
from microdot_asyncio_websocket import with_websocket
from aioclass import Service
import aioctl
import ssl as _ssl


class MicrodotService(Service):
    def __init__(self, name):
        super().__init__(name)
        self.info = "Microdot Async WebSocketserver v1.0"
        self.type = "runtime.service"  # continuous running, other types are
        self.enabled = True
        self.docs = "https://github.com/Carglglz/asyncmd/blob/main/README.md"
        self.args = []
        self.kwargs = {
            "host": "0.0.0.0",
            "port": 8042,
            "debug": True,
            "on_stop": self.on_stop,
            "on_error": self.on_error,
            "ssl": False,
            "key": None,
            "cert": None,
        }
        self.sslctx = None

        # init webserver app
        self.log = None
        self.app = Microdot()
        self.app.set_config(f"{self.name}.service", None, 0)

        @self.app.route("/")
        async def index(request):
            return send_file("static/index_ws.html")

        @self.app.route("/favicon.ico")
        async def favicon(request):
            return send_file("static/favicon.ico")

        @self.app.route("/static/<path:path>")
        async def static(request, path):
            if ".." in path:
                # directory traversal is not allowed
                return "Not found", 404
            return send_file("static/" + path)

        @self.app.route("/echo")
        @with_websocket
        async def echo(request, ws):
            while True:
                data = await ws.receive()
                await ws.send(data)

        @self.app.route("/shutdown")
        async def shutdown(request):
            await request.app.shutdown()
            return "The server is shutting down..."

    def show(self):
        return "Stats", f"   Requests: {self.app.request_counter}, URL: {self.url}"

    def stats(self):
        return {"requests": self.app.request_counter, "url": self.url}

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
        port=4443,
        debug=True,
        ssl=False,
        key=None,
        cert=None,
        log=None,
    ):
        self.log = log
        self.app.log = log
        proto = "http"
        if ssl:
            proto = "https"
        _host = "localhost"
        if host != "0.0.0.0":
            _host = host
        self.url = f"{proto}://{_host}:{port}"

        if ssl:
            self.sslctx = _ssl.SSLContext(_ssl.PROTOCOL_TLS_SERVER)
            self.sslctx.load_cert_chain(cert, keyfile=key)
        await self.app.start_server(host=host, port=port, debug=debug, ssl=self.sslctx)
        # if this consumes Cancelled Error but still want to run on_stop
        # callback raise Cancelled Error or run on_stop here
        self.on_stop()


service = MicrodotService("microdot_ws")
