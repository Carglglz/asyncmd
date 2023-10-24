# µPing (MicroPing) for MicroPython
# copyright (c) 2018 Shawwwn <shawwwn1@gmail.com>
# License: MIT

# Internet Checksum Algorithm
# Author: Olav Morken
# https://github.com/olavmrk/python-ping/blob/master/ping.py
# @data: bytes

# ping statistics, loop mode and KeyboardInterrupt handler, + esp8266 compatible
# & async ping
# copyright (c) 2020-2023 Carglglz
# License: MIT
import asyncio
from asyncio.stream import Stream
from asyncio import core
import sys


def checksum(data):
    if len(data) & 0x1:  # Odd number of bytes
        data += b"\0"
    cs = 0
    for pos in range(0, len(data), 2):
        b1 = data[pos]
        b2 = data[pos + 1]
        cs += (b1 << 8) + b2
    while cs >= 0x10000:
        cs = (cs & 0xFFFF) + (cs >> 16)
    cs = ~cs & 0xFFFF
    return cs


def stddev(data):
    N = len(data)
    avg = sum(data) / N
    num = sum([(x - avg) ** 2 for x in data])
    den = N - 1
    stddev = (num / den) ** 0.5
    return stddev


async def ping(
    host,
    count=4,
    timeout=5000,
    interval=10,
    quiet=False,
    size=64,
    rx_size=84,
    rtn=True,
    rtn_dict=False,
    loop=False,
    int_loop=800,
    debug=False,
    raise_exc=True,
):
    import time
    import uctypes
    import socket
    import struct
    import random
    from sys import platform
    import gc
    from array import array
    from errno import EINPROGRESS

    # prepare packet
    assert size >= 16, "pkt size too small"
    pkt = b"Q" * size
    pkt_desc = {
        "type": uctypes.UINT8 | 0,
        "code": uctypes.UINT8 | 1,
        "checksum": uctypes.UINT16 | 2,
        "id": uctypes.UINT16 | 4,
        "seq": uctypes.INT16 | 6,
        "timestamp": uctypes.UINT64 | 8,
    }  # packet header descriptor
    h = uctypes.struct(uctypes.addressof(pkt), pkt_desc, uctypes.BIG_ENDIAN)
    h.type = 8  # ICMP_ECHO_REQUEST
    h.code = 0
    h.checksum = 0
    if platform == "esp8266":
        h.id = random.getrandbits(16)
    else:
        h.id = random.randint(0, 65535)
    h.seq = 1
    time_data = array("f", (0 for _ in range(0)))

    # init socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, 1)
    sock.setblocking(False)
    sock.settimeout(timeout / 1000)

    ai = socket.getaddrinfo(host, 1, socket.AF_INET, socket.SOCK_DGRAM)
    addr = _host = ai[0][-1]
    if isinstance(_host, tuple):
        _host = _host[0]
    else:
        _host = socket.inet_ntop(socket.AF_INET, _host[4:])
    # addr = socket.getaddrinfo(host, 1)[0][-1][0]  # ip address
    # print(addr)
    ss = Stream(sock)

    try:
        sock.connect(addr)
    except OSError as er:
        if er.errno != EINPROGRESS:
            raise er
    yield core._io_queue.queue_write(sock)
    reader = writer = ss
    not quiet and print("PING %s (%s): %u data bytes" % (host, _host, len(pkt)))
    try:
        seqs = list(range(1, count + 1))  # [1,2,...,count]
        c = 1
        t = 0
        n_trans = 0
        n_recv = 0
        finish = False
        while t < timeout:
            if t == interval and c <= count:
                # send packet
                h.checksum = 0
                h.seq = c
                h.timestamp = time.ticks_us()
                h.checksum = checksum(pkt)
                writer.write(pkt)
                wr_size = len(pkt)
                if wr_size == size:
                    n_trans += 1
                    t = 0  # reset timeout
                else:
                    seqs.remove(c)
                    if loop:
                        count += 1
                        seqs.append(count)
                c += 1
                await writer.drain()

            # recv packet
            while 1:
                resp = []
                try:
                    resp = await asyncio.wait_for(reader.read(rx_size), interval / 1000)

                except asyncio.TimeoutError:
                    pass
                # print("recv packet", resp)
                if resp:
                    resp_mv = memoryview(resp)
                    h2 = uctypes.struct(
                        uctypes.addressof(resp_mv[20:]),
                        pkt_desc,
                        uctypes.BIG_ENDIAN,
                    )
                    # TODO: validate checksum (optional)
                    seq = h2.seq
                    # 0: ICMP_ECHO_REPLY
                    if h2.type == 0 and h2.id == h.id and (seq in seqs):
                        t_elapsed = (time.ticks_us() - h2.timestamp) / 1000
                        ttl = struct.unpack("!B", resp_mv[8:9])[0]  # time-to-live
                        n_recv += 1
                        not quiet and print(
                            "{} bytes from {}: icmp_seq={} ttl={} time={:.3f} ms".format(
                                len(resp), _host, seq, ttl, t_elapsed
                            )
                        )
                        time_data.append(t_elapsed)
                        seqs.remove(seq)
                        if loop:
                            count += 1
                            seqs.append(count)
                            await asyncio.sleep_ms(int_loop)
                        if len(seqs) == 0:
                            finish = True
                            break
                else:
                    break

            if finish:
                if not loop:
                    break

            await asyncio.sleep_ms(1)
            t += 1
        sock.close()
        if not quiet:
            print("--- {} ping statistics ---".format(host))
            print(
                "{} packets transmitted, {} packets received, {:.1f}% packet loss".format(
                    n_trans, n_recv, (1 - (n_recv / n_trans)) * 100
                )
            )
            print(
                "round-trip min/avg/max/stddev = {:.2f}/{:.2f}/{:.2f}/{:.2f} ms".format(
                    min(time_data),
                    sum(time_data) / len(time_data),
                    max(time_data),
                    stddev(time_data),
                )
            )
        gc.collect()
        if rtn:
            if rtn_dict:
                return {
                    "ntx": n_trans,
                    "nrx": n_recv,
                    "loss": (1 - (n_recv / n_trans)) * 100,
                    "min": min(time_data),
                    "avg": sum(time_data) / len(time_data),
                    "max": max(time_data),
                    "stddev": stddev(time_data),
                }
            return (n_trans, n_recv)
    except Exception as e:
        if debug:
            sys.print_exception(e)
        if raise_exc:
            raise e
