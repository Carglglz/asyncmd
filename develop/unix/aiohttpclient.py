import asyncio
import json as _json
import socket


class ClientResponse:
    def __init__(self, reader):
        self.content = reader

    def read(self, sz=-1):
        return (yield from self.content.read(sz))

    def text(self, sz=-1):
        return self.read(sz=sz)

    def json(self):
        return _json.loads(await self.read())

    def __repr__(self):
        return "<ClientResponse %d %s>" % (self.status, self.headers)


class ChunkedClientResponse(ClientResponse):
    def __init__(self, reader):
        self.content = reader
        self.chunk_size = 0

    def read(self, sz=4 * 1024 * 1024):
        if self.chunk_size == 0:
            l = yield from self.content.readline()
            # print("chunk line:", l)
            l = l.split(b";", 1)[0]
            self.chunk_size = int(l, 16)
            # print("chunk size:", self.chunk_size)
            if self.chunk_size == 0:
                # End of message
                sep = yield from self.content.read(2)
                assert sep == b"\r\n"
                return b""
        data = yield from self.content.read(min(sz, self.chunk_size))
        self.chunk_size -= len(data)
        if self.chunk_size == 0:
            sep = yield from self.content.read(2)
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
        while redir_cnt < 2:
            reader = yield from self.request_raw(method, url, data, json, ssl)
            headers = []
            sline = yield from reader.readline()
            sline = sline.split(None, 2)
            status = int(sline[1])
            chunked = False
            while True:
                line = yield from reader.readline()
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
                yield from reader.aclose()
                continue
            break

        if chunked:
            resp = ChunkedClientResponse(reader)
        else:
            resp = ClientResponse(reader)
        resp.status = status
        resp.headers = headers
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

        ai = socket.getaddrinfo(host, port, socket.AF_INET, socket.SOCK_STREAM)
        _host = ai[0][-1]
        if isinstance(_host, tuple):
            _host = _host[0]
        else:
            _host = socket.inet_ntop(socket.AF_INET, _host[4:])
        if not isinstance(ssl, dict):
            ssl = {"ssl": ssl, "server_hostname": host}

        # print(_host, host, port)

        reader, writer = yield from asyncio.open_connection(_host, port, **ssl)
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

        yield from writer.awrite(query.encode("latin-1"))
        #    yield from writer.aclose()
        return reader

    def get(self, url, ssl=None):
        return _RequestContextManager(
            self, self._request("GET", self._base_url + url, ssl=ssl)
        )

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


def request_raw(method, url):
    try:
        proto, dummy, host, path = url.split("/", 3)
    except ValueError:
        proto, dummy, host = url.split("/", 2)
        path = ""

    if proto == "http:":
        port = 80
    elif proto == "https:":
        port = 443
    else:
        raise ValueError("Unsupported protocol: " + proto)

    if ":" in host:
        host, port = host.split(":", 1)
        port = int(port)

    reader, writer = yield from asyncio.open_connection(
        host, port, ssl=proto == "https:"
    )
    # Use protocol 1.0, because 1.1 always allows to use chunked transfer-encoding
    # But explicitly set Connection: close, even though this should be default for 1.0,
    # because some servers misbehave w/o it.
    query = (
        "%s /%s HTTP/1.0\r\nHost: %s\r\nConnection: close\r\nUser-Agent: compat\r\n\r\n"
        % (
            method,
            path,
            host,
        )
    )
    yield from writer.awrite(query.encode("latin-1"))
    #    yield from writer.aclose()
    return reader


def request(method, url):
    redir_cnt = 0
    while redir_cnt < 2:
        reader = yield from request_raw(method, url)
        headers = []
        sline = yield from reader.readline()
        sline = sline.split(None, 2)
        status = int(sline[1])
        chunked = False
        while True:
            line = yield from reader.readline()
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
            yield from reader.aclose()
            continue
        break

    if chunked:
        resp = ChunkedClientResponse(reader)
    else:
        resp = ClientResponse(reader)
    resp.status = status
    resp.headers = headers
    return resp
