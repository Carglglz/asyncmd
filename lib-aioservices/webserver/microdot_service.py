import ssl
from microdot_asyncio_serv import Microdot, send_file
from async_base_animations import _loadnpxy
from aioclass import Service
import aioctl

anm = _loadnpxy(18, 71, timing=(400, 850, 850, 400))


@aioctl.aiotask
async def pulse(*args, **kwargs):
    log = kwargs.get("log")
    if log:
        kwargs.pop("log")
        log.info(f"[pulse] {args} {kwargs} pulse")
    await anm.pulse(*args, **kwargs)


htmldoc_color = """
<!DOCTYPE html>
<html>
    <head>
        <title>Microdot Example Page</title>
    </head>
    <body>
        <div>
            <h1>Microdot Example Page</h1>
            <p>Hello from Microdot colored {}!</p>
            <p><a href="/shutdown">Click to shutdown the server</a></p>
        </div>
    </body>
</html>
"""


class MicrodotService(Service):
    def __init__(self, name):
        super().__init__(name)
        self.info = "Microdot Async Webserver v1.0"
        self.type = "runtime.service"  # continuous running, other types are
        self.enabled = True
        self.docs = "https://github.com/Carglglz/asyncmd/blob/main/README.md"
        self.args = []
        self.kwargs = {
            "host": "0.0.0.0",
            "port": 4443,
            "debug": True,
            "on_stop": self.on_stop,
            "on_error": self.on_error,
        }
        self.anm = anm

        self.sslctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        self.sslctx.load_cert_chain(
            "SSL_certificate7c9ebd3d9df4.der", "SSL_key7c9ebd3d9df4.pem"
        )

        # init webserver app
        self.log = None
        self.app = Microdot()
        self.app.set_config(f"{self.name}.service", None, 0)

        @self.app.route("/")
        async def index(request):
            return send_file("static/index.html")

        @self.app.route("/favicon.ico")
        async def favicon(request):
            return send_file("static/favicon.ico")

        @self.app.route("/static/<path:path>")
        async def static(request, path):
            if ".." in path:
                # directory traversal is not allowed
                return "Not found", 404
            return send_file("static/" + path)

        @self.app.route("/webrepl")
        async def webreplserv(request):
            return send_file("./webrepl.html")

        @self.app.route("webrpl/<path:path>")
        async def webtermserv(request, path):
            if ".." in path:
                # directory traversal is not allowed
                return "Not found", 404
            return send_file("./webrpl/" + path)

        @self.app.route("/shutdown")
        async def shutdown(request):
            await request.app.shutdown()
            return "The server is shutting down..."

        @self.app.route("/color")
        async def color(request):
            R = int(request.args.get("r", "0"))
            G = int(request.args.get("g", "0"))
            B = int(request.args.get("b", "0"))
            if "pulse" in aioctl.group().tasks:
                aioctl.delete("pulse")
            aioctl.add(pulse, (R, G, B), 1, loops=2, log=request.app.log)
            return (
                htmldoc_color.format(str((R, G, B))),
                200,
                {"Content-Type": "text/html"},
            )

    def show(self):
        return "Stats", f"   Requests: {self.app.request_counter}"

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
    async def task(self, host="0.0.0.0", port=4443, debug=True, log=None):
        self.log = log
        self.app.log = log
        await self.app.start_server(host=host, port=port, debug=debug, ssl=self.sslctx)
        # if this consumes Cancelled Error but still want to run on_stop
        # callback raise Cancelled Error or run on_stop here
        self.on_stop()


service = MicrodotService("microdot")
