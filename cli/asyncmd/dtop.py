import re
import math
import ssl
import time
from datetime import timedelta
import datetime
import curses
import asyncio_mqtt as aiomqtt
import json
import asyncio
from . import __version__ as version
from functools import wraps


def convert_size(size_bytes):  # convert from bytes to other units
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1000)))
    p = math.pow(1000, i)
    s = round(size_bytes / p, 2)
    return "%s %s" % (s, size_name[i])


def handle(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except curses.error:
            pass

    return decorated


class Pointer:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.tabspace = 4
        # direction: X [down], Y [right]

    def tab(self, tabs=None):
        self.y = self.y + (tabs if tabs else self.tabspace)

    def reverttab(self, tabs=None):
        self.y = self.y - (tabs if tabs else self.tabspace)

    def newline(self):
        self.x = self.x + 1


class DeviceTOP:
    # one task handle screen update --> draw
    # second task handle data collection (mqtt) --> mqtt subscribe
    # self.data_buffer = {hostname:{data}}
    # main --> create tasks and gather
    def __init__(self, args):
        self.args = args
        self._data_buffer = {}
        self._close_flag = False

        self._status_colors = {
            "running": 5,
            "error": 6,
            "stopped": 7,
            "scheduled": 8,
            "done": 2,
        }

    def bottom_status_bar(self):
        local_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S %Z")
        bottom_statusbar_str = f"asyncmd {version} | Local time {local_time}"
        return bottom_statusbar_str

    @handle
    def printline(self, stdscr, string, ptr, maxc):
        stdscr.addnstr(ptr.x, ptr.y, string, maxc)
        ptr.newline()

    @handle
    def printline_colors(self, stdscr, string, ptr, maxc):
        stdscr.move(ptr.x, ptr.y)
        pattern = r"({0:s})".format(
            "|".join(
                r"\b{0:s}\b".format(word.upper()) for word in self._status_colors.keys()
            )
        )
        s = re.split(pattern, string)
        for s in s:
            stdscr.addstr(s, curses.color_pair(self._status_colors.get(s.lower(), 0)))
        ptr.newline()

    @handle
    def init(self, stdscr):
        stdscr.idcok(False)
        stdscr.idlok(False)
        stdscr.scrollok(True)
        stdscr.nodelay(True)
        stdscr.keypad(True)
        curses.curs_set(0)
        curses.noecho()
        curses.start_color()
        curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_GREEN)
        curses.init_pair(4, curses.COLOR_BLACK, curses.COLOR_CYAN)
        curses.init_pair(5, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(6, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(7, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(8, curses.COLOR_CYAN, curses.COLOR_BLACK)

    @handle
    def print_bottom_status_bar(self, stdscr, width, height):
        bottom_statusbar_str = self.bottom_status_bar()
        stdscr.attron(curses.color_pair(4))
        stdscr.addnstr(height - 1, 0, bottom_statusbar_str, width)
        stdscr.addnstr(
            height - 1,
            len(bottom_statusbar_str),
            " " * (width - len(bottom_statusbar_str)),
            width,
        )
        stdscr.attroff(curses.color_pair(4))

    @handle
    def print_node_info(self, stdscr, ptr, data, maxc):
        stdscr.attron(curses.color_pair(1))
        ptr.newline()
        for item in data:
            if item:
                self.printline(stdscr, item, ptr, maxc)
        ptr.newline()
        stdscr.attroff(curses.color_pair(1))

    @handle
    def print_vm_info(self, stdscr, ptr, vm_status_list, status_bar_item_length, maxc):
        stdscr.attron(curses.color_pair(2))
        for item in vm_status_list:
            if item:
                item_str = item
                self.printline_colors(stdscr, item_str, ptr, maxc)
        stdscr.attroff(curses.color_pair(2))

    @handle
    def print_upper_status_bar(self, stdscr, width, status_bar_str, node_info_len):
        stdscr.attron(curses.color_pair(3))
        stdscr.addnstr(node_info_len, 0, status_bar_str, width)
        stdscr.addnstr(
            node_info_len,
            len(status_bar_str),
            " " * (width - len(status_bar_str)),
            width,
        )
        stdscr.attroff(curses.color_pair(3))

    def get_sep(self, col, headlist, info, tmf):
        if col in ["hostname", "DEVICE"]:
            max_s = len(info["hostname"]) + 4

        elif col == "SERVICE":
            max_s = max([len(k) for k in info.keys() if k != "hostname"]) + 4

        else:
            if col in ["DONE", "done"]:
                col = "done_at"
            max_s = (
                max(
                    [
                        len(self.get_val(col, info, serv, tmf))
                        for serv in info
                        if serv != "hostname"
                    ]
                )
                + 4
            )

        return max_s

    def _fmt_dict(self, val):
        if isinstance(val, dict):
            return " | ".join([f"{k}={self._fmt_dict(v)}" for k, v in val.items()])
        else:
            return str(val)

    def get_val(self, col, info, serv, tmf):
        val = info[serv].get(col.lower(), "")
        if col in ["SINCE", "DONE_AT"]:
            if val is not None:
                val += 946684800  # EPOCH DELTA
                if tmf == "ISO":
                    return time.strftime("%Y-%m-%d  %H:%M:%S", time.localtime(val))
                else:
                    return (
                        str(timedelta(seconds=time.time() - val)).split(".")[0] + " ago"
                    )

            else:
                return str(val)
        if col == "STATUS":
            return str(val).upper()

        if col == "STATS":
            if val and serv != "aiomqtt.service":
                return self._fmt_dict(val)
            else:
                return ""
        return str(val)

    def get_node_info(self, _all_info):
        # 1st line
        # Mem [                           %65.4] | Tasks: , Services: , CTasks:
        # Disk[                           %70.0] | Recv:  , Send:
        # Firmware
        # Machine, platform...
        info = _all_info["aiomqtt.service"]["stats"]
        nod_info = []
        _mem_pc = (info["mused"] / info["mtotal"]) * 100
        _mem_ = f"[{convert_size(info['mused'])}/{convert_size(info['mtotal'])}]"
        _len_str = len(f"Mem [{'|'*int(_mem_pc):100}{_mem_pc:.1f}%]{_mem_:23}")

        _mem_tasks = (
            f"Mem [{'|'*int(_mem_pc):100}{_mem_pc:.1f}%]{_mem_:23}|"
            f" Tasks: {info['tasks']}, Services: {info['services']}"
            f", CTasks: {info['ctasks']}"
        )
        _disk_pc = (info["fsused"] / info["fstotal"]) * 100
        _disk_ = f"[{convert_size(info['fsused'])}/{convert_size(info['fstotal'])}]"
        _disk_msg = (
            f"Disk[{'|'*int(_disk_pc):100}{_disk_pc:.1f}%]{_disk_:23}|"
            f" Recv: {info['nrecv']}, Send: {info['npub']}"
        )
        fmw_str = f"Firmware: {info['firmware']}"
        _uptime = self.get_val("SINCE", _all_info, "watcher.service", "DELTA").replace(
            "ago", ""
        )
        _fmw = f"{fmw_str:{_len_str}s}|" f" Uptime: {_uptime}"
        _mach = f"Machine: {info['machine']}"
        nod_info.append(_mem_tasks)
        nod_info.append(_disk_msg)
        nod_info.append(_fmw)
        nod_info.append(_mach)
        nod_info.append(" ")
        return nod_info

    async def data_feed(self):
        tls_params = None
        if self.args.cafile:
            tls_params = aiomqtt.TLSParameters(
                ca_certs=self.args.cafile,
                certfile=self.args.cert,
                keyfile=self.args.key,
                cert_reqs=ssl.CERT_REQUIRED,
                tls_version=ssl.PROTOCOL_TLS,
                ciphers=None,
            )

            # stdscr.nodelay(True)
        async with aiomqtt.Client(
            hostname=self.args.ht, port=self.args.p, logger=None, tls_params=tls_params
        ) as client:
            async with client.messages() as messages:
                await client.subscribe("device/+/status")
                async for message in messages:
                    devname = str(message.topic).split("/")[1]

                    _servs = json.loads(message.payload.decode())
                    self._data_buffer[devname] = _servs
                    if self._close_flag:
                        return

    async def draw(self, stdscr, update_interval):
        self.init(stdscr)
        k = 0
        node_idx = 0
        TM_FORMAT = "DELTA"

        stdscr.nodelay(True)

        while True:
            k = stdscr.getch()
            nodes = list(self._data_buffer.keys())
            if not nodes:
                await asyncio.sleep(0.1)
                continue
            # set --> add from topic
            # n, p filter by topic
            # also all
            nodes_cnt = len(nodes)
            if k == ord("q"):
                self._close_flag = True
                break
            elif k == ord("n"):
                node_idx = nodes_cnt - 1 if node_idx + 1 >= nodes_cnt else node_idx + 1
            elif k == ord("p"):
                node_idx = 0 if node_idx - 1 < 0 else node_idx - 1
            if k == ord("s"):
                if TM_FORMAT == "ISO":
                    TM_FORMAT = "DELTA"
                else:
                    TM_FORMAT = "ISO"

            # add key for
            node = nodes[node_idx]
            node_info_str = [f"Device: {node}"]
            data = self._data_buffer[node]
            node_info_str += self.get_node_info(data)
            _HL = ["DEVICE", "SERVICE", "STATUS", "SINCE", "DONE_AT", "RESULT", "STATS"]
            _max_hn = self.get_sep("hostname", _HL, data, TM_FORMAT)

            _max_sep = {k: self.get_sep(k, _HL, data, TM_FORMAT) for k in _HL}

            vm_status_list = [
                f" {data['hostname']:{_max_hn}s}"
                f"{serv:{_max_sep['SERVICE']}s}"
                + "".join(
                    [
                        f"{self.get_val(hdr, data, serv, TM_FORMAT):{_max_sep[hdr]}s}"
                        for hdr in ["STATUS", "SINCE", "DONE_AT", "RESULT", "STATS"]
                    ]
                )
                for serv in data.keys()
                if serv != "hostname"
            ]  # --> services row
            status_bar_item_length = 3
            status_bar_str = "".join(
                [f" {'DEVICE':{_max_sep['DEVICE']}s}"]
                + [
                    f"{stat:{_max_sep[stat]}s}"
                    for stat in [
                        "SERVICE",
                        "STATUS",
                        "SINCE",
                        "DONE_AT",
                        "RESULT",
                        "STATS",
                    ]
                ]
            )  # --> static : # DEVICE # SERVICE
            # STATUS # SINCE # DONE, # RESULT, # STATS
            ptr = Pointer()
            height, width = stdscr.getmaxyx()
            stdscr.erase()

            self.print_node_info(stdscr, ptr, node_info_str, width)
            self.print_vm_info(
                stdscr, ptr, vm_status_list, status_bar_item_length, width
            )
            self.print_bottom_status_bar(stdscr, width, height)
            self.print_upper_status_bar(
                stdscr, width, status_bar_str, len(node_info_str)
            )
            stdscr.noutrefresh()
            curses.doupdate()
            stdscr.timeout(update_interval)
            await asyncio.sleep(0.1)
        curses.endwin()

    async def run(self, stdscr, upint):
        self._feed_task = asyncio.create_task(self.data_feed())
        self._draw_task = asyncio.create_task(self.draw(stdscr, upint))
        self._tasks_set = {self._feed_task, self._draw_task}
        await asyncio.gather(*self._tasks_set)

    def start(self, stdscr, upint):
        return asyncio.run(self.run(stdscr, upint))
