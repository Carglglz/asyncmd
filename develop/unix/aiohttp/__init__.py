import asyncio
import json as _json
from .aiohttp_ws import (
    _WSRequestContextManager,
    ClientWebSocketResponse,
    WebSocketClient,
)


class ClientResponse:
    def __init__(self, reader):
        self.content = reader

    def read(self, sz=-1):
        return self.content.read(sz)

    def text(self, sz=-1):
        return self.read(sz=sz)

    async def json(self):
        return _json.loads(await self.read())

    def __repr__(self):
        return "<ClientResponse %d %s>" % (self.status, self.headers)


class ChunkedClientResponse(ClientResponse):
    def __init__(self, reader):
        self.content = reader
        self.chunk_size = 0

    async def read(self, sz=4 * 1024 * 1024):
        if self.chunk_size == 0:
            l = await self.content.readline()
            l = l.split(b";", 1)[0]
            self.chunk_size = int(l, 16)
            if self.chunk_size == 0:
                # End of message
                sep = await self.content.read(2)
                assert sep == b"\r\n"
                return b""
        data = await self.content.read(min(sz, self.chunk_size))
        self.chunk_size -= len(data)
        if self.chunk_size == 0:
            sep = await self.content.read(2)
            assert sep == b"\r\n"
        return data

    def __repr__(self):
        return "<ChunkedClientResponse %d %s>" % (self.status, self.headers)


class _RequestContextManager:
    def __init__(self, client, request_co):
        self.reqco = request_co
        self.client = client

    async def __aenter__(self):
        return await self.reqco

    async def __aexit__(self, *args):
        await self.client._reader.aclose()
        return await asyncio.sleep(0)


class ClientSession:
    def __init__(self, base_url=""):
        self._reader = None
        self._base_url = base_url

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return await asyncio.sleep(0)

    def request(self, method, url, data=None, json=None, ssl=None):
        return _RequestContextManager(
            self,
            self._request(method, self._base_url + url, data=data, json=json, ssl=ssl),
        )

    async def _request(self, method, url, data=None, json=None, ssl=None):
        redir_cnt = 0
        redir_url = None
        while redir_cnt < 2:
            reader = await self.request_raw(method, url, data, json, ssl)
            headers = []
            sline = await reader.readline()
            sline = sline.split(None, 2)
            status = int(sline[1])
            chunked = False
            while True:
                line = await reader.readline()
                if not line or line == b"\r\n":
                    break
                headers.append(line)
                if line.startswith(b"Transfer-Encoding:"):
                    if b"chunked" in line:
                        chunked = True
                elif line.startswith(b"Location:"):
                    url = line.rstrip().split(None, 1)[1].decode("latin-1")

            if 301 <= status <= 303:
                redir_cnt += 1
                await reader.aclose()
                continue
            break

        if chunked:
            resp = ChunkedClientResponse(reader)
        else:
            resp = ClientResponse(reader)
        resp.status = status
        resp.headers = headers
        try:
            resp.headers = {
                val.split(":", 1)[0]: val.split(":", 1)[-1].strip()
                for val in [hed.decode().strip() for hed in headers]
            }
        except Exception:
            pass
        self._reader = reader
        return resp

    async def request_raw(self, method, url, data=None, json=None, ssl=None):
        if json and isinstance(json, dict):
            data = _json.dumps(json)
        if data is not None and method == "GET":
            method = "POST"
        try:
            proto, dummy, host, path = url.split("/", 3)
        except ValueError:
            proto, dummy, host = url.split("/", 2)
            path = ""

        if proto == "http:":
            port = 80
        elif proto == "https:":
            port = 443
            if ssl is None:
                ssl = True
        else:
            raise ValueError("Unsupported protocol: " + proto)

        if ":" in host:
            host, port = host.split(":", 1)
            port = int(port)

        reader, writer = await asyncio.open_connection(host, port, ssl=ssl)

        # Use protocol 1.0, because 1.1 always allows to use chunked transfer-encoding
        # But explicitly set Connection: close, even though this should be default for 1.0,
        # because some servers misbehave w/o it.
        if not data:
            query = (
                "%s /%s HTTP/1.0\r\nHost: %s\r\nConnection: close\r\nUser-Agent: compat\r\n\r\n"
                % (
                    method,
                    path,
                    host,
                )
            )
        else:
            query = (
                """%s /%s HTTP/1.0\r\nHost: %s\r\n%sContent-Length: %s\r\n\r\n%s\r\nConnection: close\r\nUser-Agent: compat\r\n\r\n"""
                % (
                    method,
                    path,
                    host,
                    "Content-Type: application/json\r\n" if json else "",
                    str(len(str(data))),
                    data,
                )
            )

        await writer.awrite(query.encode("latin-1"))
        #    yield from writer.aclose()
        return reader

    def get(self, url, ssl=None):
        return _RequestContextManager(self, self._request("GET", self._base_url + url, ssl=ssl))

    def post(self, url, data=None, json=None, ssl=None):
        return _RequestContextManager(
            self,
            self._request("POST", self._base_url + url, data=data, json=json, ssl=ssl),
        )

    def put(self, url, data=None, json=None, ssl=None):
        return _RequestContextManager(
            self,
            self._request("PUT", self._base_url + url, data=data, json=json, ssl=ssl),
        )

    def patch(self, url, data=None, json=None, ssl=None):
        return _RequestContextManager(
            self,
            self._request("PATCH", self._base_url + url, data=data, json=json, ssl=ssl),
        )

    def delete(self, url, ssl=None):
        return _RequestContextManager(
            self,
            self._request("DELETE", self._base_url + url, ssl=ssl),
        )

    def head(self, url, ssl=None):
        return _RequestContextManager(
            self,
            self._request("HEAD", self._base_url + url, ssl=ssl),
        )

    def options(self, url, ssl=None):
        return _RequestContextManager(
            self,
            self._request("OPTIONS", self._base_url + url, ssl=ssl),
        )

    def ws_connect(self, url, ssl=None):
        return _WSRequestContextManager(self, self._ws_connect(url, ssl=ssl))

    async def _ws_connect(self, url, ssl=None):
        ws_client = WebSocketClient(None)
        await ws_client.connect(url, ssl=ssl)
        self._reader = ws_client.reader
        return ClientWebSocketResponse(ws_client)
