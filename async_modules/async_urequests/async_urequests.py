import uasyncio as asyncio


class Response:
    def __init__(self, f):
        self.raw = f
        self.encoding = "utf-8"
        self._cached = None

    async def close(self):
        if self.raw:
            self.raw.close()
            await self.raw.wait_closed()
            self.raw = None
        self._cached = None

    @property
    async def content(self):
        if self._cached is None:
            try:
                self._cached = await self.raw.read()
            finally:
                self.raw.close()
                await self.raw.wait_closed()
                self.raw = None
        return self._cached

    @property
    async def text(self):
        return str(await self.content, self.encoding)

    async def json(self):
        import ujson

        return ujson.loads(await self.content)


async def request(
    method,
    url,
    data=None,
    json=None,
    headers={},
    stream=None,
    auth=None,
    hostname=None,
    timeout=None,
    parse_headers=True,
):
    redirect = None  # redirection url, None means no redirection
    chunked_data = (
        data and getattr(data, "__iter__", None) and not getattr(data, "__len__", None)
    )

    if auth is not None:
        import ubinascii

        username, password = auth
        formated = b"{}:{}".format(username, password)
        formated = str(ubinascii.b2a_base64(formated)[:-1], "ascii")
        headers["Authorization"] = "Basic {}".format(formated)

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

    # ai = usocket.getaddrinfo(host, port, 0, usocket.SOCK_STREAM)
    # ai = ai[0]
    # print(proto, host, port)
    resp_d = None
    if parse_headers is not False:
        resp_d = {}

    # s = usocket.socket(ai[0], usocket.SOCK_STREAM, ai[2])

    # if timeout is not None:
    #     # Note: settimeout is not supported on all platforms, will raise
    #     # an AttributeError if not available.
    #     s.settimeout(timeout)

    try:
        # s.connect(ai[-1])
        # host ai[-1][0]
        sslctx = None
        if not hostname:
            hostname = host
        if proto == "https:":
            import ssl

            sslctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            sslctx.check_hostname = False
            sslctx.verify_mode = ssl.CERT_NONE

        reader, writer = await asyncio.open_connection(host, port, ssl=sslctx)
        writer.write(b"%s /%s HTTP/1.0\r\n" % (method, path))
        await writer.drain()
        if "Host" not in headers:
            writer.write(b"Host: %s\r\n" % host)
            await writer.drain()
        # Iterate over keys to avoid tuple alloc
        for k in headers:
            writer.write(k)
            writer.write(b": ")
            writer.write(headers[k])
            writer.write(b"\r\n")
            await writer.drain()
        if json is not None:
            assert data is None
            import ujson

            data = ujson.dumps(json)
            writer.write(b"Content-Type: application/json\r\n")
            await writer.drain()
        if data:
            if chunked_data:
                writer.write(b"Transfer-Encoding: chunked\r\n")
            else:
                writer.write(b"Content-Length: %d\r\n" % len(data))

            await writer.drain()
        writer.write(b"Connection: close\r\n\r\n")
        await writer.drain()
        if data:
            if chunked_data:
                for chunk in data:
                    writer.write(b"%x\r\n" % len(chunk))
                    writer.write(chunk)
                    writer.write(b"\r\n")
                    await writer.drain()
                writer.write("0\r\n\r\n")
                await writer.drain()
            else:
                writer.write(data)
                await writer.drain()

        l = await reader.readline()
        # print(l)
        l = l.split(None, 2)
        if len(l) < 2:
            # Invalid response
            raise ValueError("HTTP error: BadStatusLine:\n%s" % l)
        status = int(l[1])
        reason = ""
        if len(l) > 2:
            reason = l[2].rstrip()
        while True:
            l = await reader.readline()
            if not l or l == b"\r\n":
                break
            # print(l)
            if l.startswith(b"Transfer-Encoding:"):
                if b"chunked" in l:
                    raise ValueError("Unsupported " + str(l, "utf-8"))
            elif l.startswith(b"Location:") and not 200 <= status <= 299:
                if status in [301, 302, 303, 307, 308]:
                    redirect = str(l[10:-2], "utf-8")
                else:
                    raise NotImplementedError("Redirect %d not yet supported" % status)
            if parse_headers is False:
                pass
            elif parse_headers is True:
                l = str(l, "utf-8")
                k, v = l.split(":", 1)
                resp_d[k] = v.strip()
            else:
                parse_headers(l, resp_d)
    except OSError:
        writer.close()
        await writer.wait_closed()
        raise

    if redirect:
        writer.close()
        await writer.wait_closed()
        if status in [301, 302, 303]:
            return await request("GET", redirect, None, None, headers, stream)
        else:
            return await request(method, redirect, data, json, headers, stream)
    else:
        resp = Response(reader)
        resp.status_code = status
        resp.reason = reason
        if resp_d is not None:
            resp.headers = resp_d
            return resp


async def head(url, **kw):
    return await request("HEAD", url, **kw)


async def get(url, **kw):
    return await request("GET", url, **kw)


async def post(url, **kw):
    return await request("POST", url, **kw)


async def put(url, **kw):
    return await request("PUT", url, **kw)


async def patch(url, **kw):
    return await request("PATCH", url, **kw)


def delete(url, **kw):
    return await request("DELETE", url, **kw)
