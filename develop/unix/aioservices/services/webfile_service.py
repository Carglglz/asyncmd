import os
from microdot_asyncio_serv import Microdot, send_file
from aioclass import Service
import aioctl
import ssl as _ssl


def serve_path(path):
    html_links = ""
    for nm in os.listdir(f"./{path}"):
        if not path.endswith("/"):
            if os.stat(f"{path}/{nm}")[0] & 0x4000:
                html_links += f'<li><a href="{path}/{nm}/">{nm}/</a></li>\n'
            else:
                html_links += f'<li><a href="{path}/{nm}">{nm}</a></li>\n'
        else:
            if os.stat(f"{path}/{nm}")[0] & 0x4000:
                html_links += f'<li><a href="{nm}/">{nm}/</a></li>\n'
            else:
                html_links += f'<li><a href="{nm}">{nm}</a></li>\n'
    html_tmp = f"""
<!DOCTYPE HTML>
<html lang="en">
    <head>
        <meta charset="utf-8">
        <title>Directory listing for {path}</title>
    </head>
    <body>
        <h1>Directory listing for {path}</h1>
        <hr>
        <ul>
        {html_links}
        </ul>
        <hr>
    </body>
</html>
"""

    return (
        html_tmp,
        200,
        {"Content-Type": "text/html"},
    )


class WebFileService(Service):
    def __init__(self, name):
        super().__init__(name)
        self.info = "Microdot Async File Webserver v1.0"
        self.type = "runtime.service"  # continuous running, other types are
        self.enabled = True
        self.docs = "https://github.com/Carglglz/asyncmd/blob/main/README.md"
        self.args = []
        self.kwargs = {
            "host": "0.0.0.0",
            "port": 4444,
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
            return serve_path(".")

        @self.app.route("/<path:path>")
        async def fileserv(request, path):
            if ".." in path:
                # directory traversal is not allowed
                return "Not found", 404
            if os.stat(path)[0] & 0x4000:
                return serve_path(path)
            return send_file(path)

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
        port=4444,
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
            # self.sslctx.verify_mode = _ssl.CERT_REQUIRED
            self.sslctx.load_cert_chain(cert, keyfile=key)
            # self.sslctx.load_verify_locations(cert)
        await self.app.start_server(host=host, port=port, debug=debug, ssl=self.sslctx)
        # if this consumes Cancelled Error but still want to run on_stop
        # callback raise Cancelled Error or run on_stop here
        self.on_stop()


service = WebFileService("webfile")
