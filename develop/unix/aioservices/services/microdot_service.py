import random
from microdot_asyncio_serv import Microdot, send_file
from aioclass import Service
import aioctl
import ssl as _ssl


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

htmldoc_sensor = """<!DOCTYPE HTML><html><head>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="stylesheet" href="https://use.fontawesome.com/releases/v5.7.2/css/all.css" integrity="sha384-fnmOCqbTlWIlj8LyTjo7mOUStjsKC4pOpQbqyi7RrhN7udi9RwhKkMHpvLbHG9Sr" crossorigin="anonymous">
  </head><body><h2>ESP32 Microdot WebServer</h2>
  <p><i class="fas fa-thermometer-half" style="color:#059e8a;"></i>
    <span class="ds-labels">Temperature</span>
    <span id="temperature">{}</span>
    <sup class="units">&deg;C</sup>
  </p></body></html>"""


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
        self.url = None
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

        @self.app.route("/shutdown")
        async def shutdown(request):
            await request.app.shutdown()
            return "The server is shutting down..."

        @self.app.route("/color")
        async def color(request):
            R = int(request.args.get("r", "0"))
            G = int(request.args.get("g", "0"))
            B = int(request.args.get("b", "0"))
            return (
                htmldoc_color.format(str((R, G, B))),
                200,
                {"Content-Type": "text/html"},
            )

        @self.app.route("/temp")
        async def temp(request):
            return (
                htmldoc_sensor.format(25 + (random.random() * random.choice([1, -1]))),
                200,
                {"Content-Type": "text/html"},
            )

        @self.app.route("/py")
        async def index_py(request):
            return send_file("static/index_pyscript.html")

        @self.app.route("/click")
        async def index_click(request):
            return send_file("static/index_pyscript_click.html")

        @self.app.route("/req")
        async def index_req(request):
            return send_file("static/index_pyscript_req.html")

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


service = MicrodotService("microdot")
