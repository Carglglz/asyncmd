import sys
import signal
import shlex
import subprocess
import os
import re
import math
import ssl
import time
from datetime import timedelta
import datetime
import curses
import curses.ascii
import asyncio_mqtt as aiomqtt
import json
import asyncio
from . import __version__ as version
import asyncmd.cmd_parser as cmd_parser
import asyncmd.status as debug_st
import io
from functools import wraps
import yaml
import textwrap
from prompt_toolkit import PromptSession, shortcuts, patch_stdout
from prompt_toolkit.completion import (
    WordCompleter,
    FuzzyWordCompleter,
    NestedCompleter,
    PathCompleter,
    merge_completers,
)


_EPOCH_2000 = 946684800

_OFFLINE = 60


_RESET = "\x1b[0m"
_GREEN = "\x1b[32;1m"
_RED = "\x1b[31;1m"
_BLUE = "\x1b[36m"
_YELLOW = "\x1b[33;1m"
_WHITE = "\x1b[37;1m"


def parse_config_file(config_file):
    with open(config_file, "r") as tf:
        _conf = tf.read()
    return yaml.safe_load(_conf)


def convert_size(size_bytes):  # convert from bytes to other units
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1000)))
    p = math.pow(1000, i)
    s = round(size_bytes / p, 2)
    return "%s %s" % (s, size_name[i])


def node_match(patt, nodes):
    pattrn = re.compile(patt.replace(".", r"\.").replace("*", ".*") + "$")
    try:
        return [node for node in nodes if pattrn.match(node)]
    except Exception:
        return []
    return []


def service_match(service, line):
    pattern = r"\[[^\]]+\]"
    matches = re.findall(pattern, line)
    return any([service in match for match in matches])


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
    def __init__(self, args):
        self.args = args
        self._data_buffer = {"all": {}}
        self._conf_buffer = {}
        self._log_buffer = {}
        self._errlog_buffer = {}
        self._help_buffer = {}
        self._report_buffer = {}
        self._services_path = {}
        self._info_enabled = True
        self._close_flag = False
        self._client = None
        self._log_enabled = False
        self._log_mode = b"log"
        self._errlog_query = False
        self._filt_dev = None
        self._last_filt = None
        self._filt_nodes = []
        self._cmd_parser = cmd_parser.CmdParser()
        self._dev_cmd_parser = cmd_parser.CmdParser(cmd_parser.dev_parser)
        self._subparses = cmd_parser.SHELL_CMD_SUBPARSERS
        self._cmd_lib = cmd_parser.SHELL_CMD_DICT_PARSER
        self._cmd_resps = {}
        self._last_cmd = ""
        self._line_index = 0

        self._status_colors = {
            "running": 5,
            "error": 6,
            "stopped": 7,
            "scheduled": 8,
            "done": 2,
        }

        self._color_flags = {
            "\x1b[92m": 5,
            "\x1b[0m": 0,
            "\x1b[32;1m": 5,
            "\x1b[31;1m": 6,
            "\x1b[36m": 8,
            "\x1b[33;1m": 7,
            "\x1b[37;1m": 0,
            "\x1b[1m": curses.A_BOLD,
        }

    def bottom_status_bar(self, n=0):
        local_time = datetime.datetime.now().strftime("%H:%M:%S %Z")
        bottom_statusbar_str = (
            f"asyncmd {version} | {local_time}"
            " | KEYS: n/p: next/pevious device"
            ", c: fetch services.config"
            ", i: toggle device info"
            ", l: toggle device log"
            ", ESC: clear filters"
            f" | filter: {self._filt_dev}"
            f" | #devices: {n}"
            f" | line: {self._line_index}"
        )
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
        ## colored text codes

        for s in s:
            if s.lower() in self._status_colors:
                _s = s.lower() if s != "ERROR" else s
                stdscr.addstr(
                    _s,
                    curses.color_pair(self._status_colors.get(s.lower(), 0))
                    | curses.A_BOLD,
                )
            else:
                _pattern = r"(\x1b\[[0-9;]+m)"
                ws = re.split(_pattern, s)
                color_flag = 0

                for w in ws:
                    if isinstance(self._color_flags.get(w), int):
                        color_flag = self._color_flags.get(w)
                    else:
                        if color_flag != 0:
                            stdscr.addstr(
                                w,
                                curses.color_pair(color_flag) | curses.A_BOLD,
                            )
                        else:
                            stdscr.addstr(w, curses.color_pair(0))
                # stdscr.addstr(
                #     s, curses.color_pair(self._status_colors.get(s.lower(), 0))
                # )

        ptr.newline()

    @handle
    def printline_debug_colors(self, stdscr, string, ptr, maxc, base=0):
        stdscr.move(ptr.x, ptr.y)
        pattern = r"(\x1b\[[0-9;]+m)"
        s = re.split(pattern, string)
        color_flag = base
        bold_flag = False
        # stdscr.addstr(str(s))
        for w in s:
            if isinstance(self._color_flags.get(w), int):
                color_flag = self._color_flags.get(w)
                bold_flag = ";" in w
                if color_flag == curses.A_BOLD:
                    color_flag = base
                    bold_flag = True

            else:
                if color_flag != base:
                    if bold_flag:
                        _color_attr = curses.color_pair(color_flag) | curses.A_BOLD
                    else:
                        _color_attr = curses.color_pair(color_flag)
                    stdscr.addstr(w, _color_attr)
                else:
                    if bold_flag:
                        stdscr.addstr(w, curses.color_pair(base) | curses.A_BOLD)
                    else:
                        stdscr.addstr(w, curses.color_pair(base))
            # if self._color_flags.get(w) is not None:
            #     color_flag = self._color_flags.get(w)
            # else:
            #     if isinstance(color_flag, int):
            #         stdscr.addstr(
            #             w,
            #             curses.color_pair(color_flag) | curses.A_BOLD,
            #         )
            #     else:
            #         stdscr.addstr(w, curses.color_pair(base))

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
        curses.init_pair(9, curses.COLOR_BLACK, curses.COLOR_WHITE)

    @handle
    def print_bottom_status_bar(self, stdscr, n, width, height):
        bottom_statusbar_str = self.bottom_status_bar(n)
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
                self.printline_debug_colors(stdscr, item, ptr, maxc, base=1)
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
            platform = info["aiomqtt.service"].get("stats").get("platform")
            if val is not None:
                if platform in ["esp32"]:
                    val += _EPOCH_2000  # EPOCH DELTA # FIXME
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

    def get_node_info(self, _all_info, width):
        # 1st line
        # Mem [                           %65.4] | Tasks: , Services: , CTasks:
        # Disk[                           %70.0] | Recv:  , Send:
        # Firmware
        # Machine, platform...
        info = _all_info["aiomqtt.service"]["stats"]
        nod_info = []
        w = min(int(width / 3), 100)
        _mem_pc = (info["mused"] / info["mtotal"]) * 100
        _mem_b = (info["mused"] / info["mtotal"]) * w
        _mem_ = f"[{convert_size(info['mused'])}/{convert_size(info['mtotal'])}]"
        _len_str = len(f"Mem [{'|'*int(_mem_b):{w}s}{_mem_pc:.1f}%]{_mem_:23}")

        _mem_tasks = (
            f"Mem [{'|'*int(_mem_b):{w}s}{_mem_pc:.1f}%]{_mem_:23}|"
            f" Tasks: {info['tasks']}, Services: {info['services']}"
            f", CTasks: {info['ctasks']}"
        )
        _disk_pc = (info["fsused"] / info["fstotal"]) * 100
        _disk_b = (info["fsused"] / info["fstotal"]) * w
        _disk_ = f"[{convert_size(info['fsused'])}/{convert_size(info['fstotal'])}]"
        _disk_msg = (
            f"Disk[{'|'*int(_disk_b):{w}s}{_disk_pc:.1f}%]{_disk_:23}|"
            f" Recv: {info['nrecv']}, Pub: {info['npub']}"
        )
        fmw_str = f"Firmware: {info['firmware']}"
        _uptime = self.get_val("SINCE", _all_info, "watcher.service", "DELTA").replace(
            "ago", ""
        )
        _lt_seen = (
            str(timedelta(seconds=time.time() - info["lt_seen"])).split(".")[0] + " ago"
        )
        _fmw = f"{fmw_str:{_len_str}s}|" f" Uptime: {_uptime} Last: {_lt_seen}"
        _mach_str = f"Machine: {info['machine']}"
        _status_conn = f"{_WHITE}[{_RED} OFFLINE {_WHITE}]{_RESET}"
        if time.time() - info["lt_seen"] < _OFFLINE:
            _status_conn = f"{_WHITE}[{_GREEN} ONLINE {_WHITE}]{_RESET}"
        _mach = f"{_mach_str:{_len_str}s}|" f" Status: {_status_conn}"
        nod_info.append(_mem_tasks)
        nod_info.append(_disk_msg)
        nod_info.append(_fmw)
        nod_info.append(_mach)
        nod_info.append(" ")
        return nod_info

    def draw_section(self, stdscr, ptr, title, section_str, width, colored=False):
        ptr.newline()
        stdscr.attron(curses.color_pair(3))
        self.printline(stdscr, f" {title} {' ' * (width - 7)}", ptr, width)
        stdscr.attroff(curses.color_pair(3))
        ptr.newline()
        if not colored:
            for line in section_str.split("\n")[self._line_index :]:
                if line:
                    for _line in textwrap.wrap(line, width - 4):
                        self.printline(stdscr, f"{_line}", ptr, width)
                else:
                    self.printline(stdscr, " ", ptr, width)
        else:
            for line in section_str.split("\n")[self._line_index :]:
                if line:
                    for _line in textwrap.wrap(line, width - 4):
                        self.printline_debug_colors(stdscr, _line, ptr, width)
                else:
                    self.printline(stdscr, " ", ptr, width)

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

        async with aiomqtt.Client(
            hostname=self.args.ht, port=self.args.p, logger=None, tls_params=tls_params
        ) as client:
            self._client = client
            async with client.messages() as messages:
                await client.subscribe("device/+/status")
                await client.subscribe("device/+/config")
                await client.subscribe("device/+/log")
                await client.subscribe("device/+/resp")
                await client.subscribe("device/+/help")
                await client.subscribe("device/+/report/#")
                async for message in messages:
                    devname, *topic = str(message.topic).split("/")[1:]
                    if isinstance(topic, list):
                        if len(topic) == 1:
                            (topic,) = topic
                        else:
                            topic, _rp_service = topic
                    if topic == "status":
                        _servs = json.loads(message.payload.decode())
                        if "hostname" in _servs:
                            if not self._data_buffer.get(devname):
                                self._data_buffer[devname] = _servs
                            else:
                                for service, vals in {
                                    s: v for s, v in _servs.items() if s != "hostname"
                                }.items():
                                    if self._data_buffer[devname].get(service):
                                        self._data_buffer[devname][service].update(
                                            **vals
                                        )
                            self._data_buffer[devname]["aiomqtt.service"]["stats"][
                                "lt_seen"
                            ] = time.time()

                        else:
                            if devname not in self._cmd_resps:
                                self._cmd_resps[devname] = {}
                            if self._last_cmd:
                                self._cmd_resps[devname][self._last_cmd] = _servs
                    elif topic == "config":
                        _confs = json.loads(message.payload.decode())
                        self._conf_buffer[devname] = _confs

                    elif topic == "resp":
                        resp = json.loads(message.payload.decode())

                        if devname not in self._cmd_resps:
                            self._cmd_resps[devname] = {}
                        if self._last_cmd:
                            self._cmd_resps[devname][self._last_cmd] = resp
                    elif topic == "log":
                        if self._log_mode == b"log":
                            if not self._log_buffer.get(devname):
                                self._log_buffer[devname] = ""
                            self._log_buffer[devname] += message.payload.decode()
                        else:
                            if not self._errlog_buffer.get(devname):
                                self._errlog_buffer[devname] = ""
                            self._errlog_buffer[devname] += message.payload.decode()
                    elif topic == "help":
                        _help = json.loads(message.payload.decode())
                        if devname not in self._help_buffer:
                            self._help_buffer[devname] = _help
                        else:
                            self._help_buffer[devname].update(**_help)

                    elif topic == "report":
                        if devname not in self._report_buffer:
                            self._report_buffer[devname] = {}

                        if _rp_service not in self._report_buffer.get(devname):
                            self._report_buffer[devname][_rp_service] = ""

                        if f"{_rp_service};" in message.payload.decode():
                            self._report_buffer[devname][_rp_service] = ""

                        self._report_buffer[devname][
                            _rp_service
                        ] += message.payload.decode()

                    if self._close_flag:
                        return

    async def data_log(self):
        while True:
            if self._close_flag:
                return
            if self._client and self._log_enabled:
                if self._log_mode == b"log":
                    if not self._filt_dev:
                        await self._client.publish(
                            "device/all/logger", payload=self._log_mode
                        )
                    else:
                        for _nodm in self._filt_nodes:
                            await self._client.publish(
                                f"device/{_nodm}/logger", payload=self._log_mode
                            )
                else:
                    if not self._errlog_query:
                        if not self._filt_dev:
                            await self._client.publish(
                                "device/all/logger", payload=self._log_mode
                            )
                        else:
                            for _nodm in self._filt_nodes:
                                await self._client.publish(
                                    f"device/{_nodm}/logger", payload=self._log_mode
                                )

                        self._errlog_query = True
                if self._close_flag:
                    return

                await asyncio.sleep(9)
            await asyncio.sleep(1)

    async def draw(self, stdscr, update_interval):
        self.init(stdscr)
        k = 0
        node_idx = 0
        show_config = False
        cmd = False
        _cmd_buff = ""
        filt_dev = ""
        filt_log = ""
        filt_serv = ""
        command = ""
        rest_args = ""
        dev_args = ""
        help_command = ""
        command_sent = False
        refresh_devconfig = False
        TM_FMT = "DELTA"
        _HL = [
            "DEVICE",
            "SERVICE",
            "STATUS",
            "SINCE",
            "DONE_AT",
            "RESULT",
            "STATS",
        ]

        session_cmd = PromptSession()
        session_filt = PromptSession()
        session_help = PromptSession()
        session_dev = PromptSession()
        _cmdlw = None

        cmd_completer = WordCompleter(self._cmd_lib.keys())

        while True:
            k = stdscr.getch()
            nodes = list(self._data_buffer.keys())
            if not nodes or nodes == ["all"]:
                ptr = Pointer()
                height, width = stdscr.getmaxyx()
                self.printline(stdscr, "Fetching info...", ptr, width)
                await asyncio.sleep(0.1)
                continue

            cmd_inp = ""
            cmd_help = ""
            ptr = Pointer()
            height, width = stdscr.getmaxyx()
            stdscr.erase()
            nodes_cnt = len(nodes)
            if sys.platform != "linux":
                curses.resizeterm(*stdscr.getmaxyx())

            if k == ord("q"):
                self._close_flag = True
                break
            elif k == ord("n"):
                node_idx = nodes_cnt - 1 if node_idx + 1 >= nodes_cnt else node_idx + 1
            elif k == ord("p"):
                node_idx = 0 if node_idx - 1 < 0 else node_idx - 1
            elif k == ord("0"):
                node_idx = 0
            elif k == ord("s"):
                if TM_FMT == "ISO":
                    TM_FMT = "DELTA"
                else:
                    TM_FMT = "ISO"

            elif k == ord("i"):
                self._info_enabled = not self._info_enabled
            elif k == ord("c"):
                show_config = not show_config
                if show_config:
                    if self._client:
                        _msg = json.dumps({"config": {"get": "*"}})
                        # apply filter
                        if not self._filt_dev:
                            await self._client.publish(
                                "device/all/service", payload=_msg
                            )
                        else:
                            for _nodm in node_match(self._filt_dev, nodes):
                                await self._client.publish(
                                    f"device/{_nodm}/service", payload=_msg
                                )

                command = ""
                help_command = ""
            elif k == ord("l"):
                self._log_enabled = not self._log_enabled
                self._log_mode = b"log"
                if self._last_cmd != "debug":
                    command = ""
                help_command = ""

            elif k == ord("k"):
                # if self._line_index > 0:
                self._line_index -= 1
            elif k == curses.KEY_UP:
                self._line_index -= 1

            elif k == ord("j"):
                self._line_index += 1

            elif k == curses.KEY_DOWN:
                self._line_index += 1

            elif k == ord(" "):
                self._line_index += 20

            elif k == ord("{"):
                self._line_index -= 10

            elif k == ord("}"):
                self._line_index += 10

            elif k == ord("g"):
                self._line_index = 0

            elif k == ord("f"):
                filt_dev = self._last_filt

            elif k == ord("/"):
                curses.curs_set(1)
                _cmdlw = stdscr.derwin(height - 1, 0)
                autocomp_filt = set()
                autocomp_filt.update(nodes)
                dev_completer = FuzzyWordCompleter(autocomp_filt)

                filt_dev = await session_filt.prompt_async(
                    "/", completer=dev_completer, complete_while_typing=False
                )
                if filt_dev.startswith("s/"):
                    filt_serv = filt_dev.replace("s/", "")
                    filt_dev = self._last_filt
                elif filt_dev.startswith("l/"):
                    filt_log = filt_dev.replace("l/", "")
                    filt_dev = self._last_filt

                self._last_filt = filt_dev

                shortcuts.clear()
                _cmdlw.deleteln()
                _cmdlw.erase()
                _cmdlw.refresh()
                stdscr.erase()
                stdscr.refresh()

                curses.curs_set(0)
            elif k == ord("$"):
                curses.curs_set(1)
                _cmdlw = stdscr.derwin(height - 1, 0)
                autocomp_filt = set()
                for _dev in self._data_buffer:
                    for _serv in self._data_buffer[_dev]:
                        if _serv != "hostname":
                            autocomp_filt.add(_serv)
                dev_completer = FuzzyWordCompleter(autocomp_filt)

                filt_serv = await session_filt.prompt_async(
                    "$", completer=dev_completer, complete_while_typing=False
                )

                shortcuts.clear()
                _cmdlw.deleteln()
                _cmdlw.erase()
                _cmdlw.refresh()
                stdscr.erase()
                stdscr.refresh()

                curses.curs_set(0)
            elif k == ord("%"):
                curses.curs_set(1)
                _cmdlw = stdscr.derwin(height - 1, 0)
                autocomp_filt = set()
                for _dev in self._data_buffer:
                    for _serv in self._data_buffer[_dev]:
                        if _serv != "hostname":
                            autocomp_filt.add(f"{_serv}")
                dev_completer = FuzzyWordCompleter(autocomp_filt)

                filt_log = await session_filt.prompt_async(
                    "%", completer=dev_completer, complete_while_typing=False
                )

                shortcuts.clear()
                _cmdlw.deleteln()
                _cmdlw.erase()
                _cmdlw.refresh()
                stdscr.erase()
                stdscr.refresh()

                curses.curs_set(0)
            elif k == ord(":"):
                curses.curs_set(1)
                _cmdlw = stdscr.derwin(height - 1, 0)
                cmd_comp_dict = {kcmd: None for kcmd in self._cmd_lib.keys()}
                # add services to [start, stop, enable, disable, config]
                # add os.listdir() to wconf, e
                all_servs_active = set()
                all_servs = set()

                path_completer = PathCompleter(
                    expanduser=True,
                    file_filter=lambda file: file if file.endswith(".config") else None,
                )
                for _dev in self._data_buffer:
                    for _serv in self._data_buffer[_dev]:
                        if _serv != "hostname":
                            all_servs_active.add(_serv)

                for _dev in self._conf_buffer:
                    for _serv in self._conf_buffer[_dev]:
                        all_servs.add(f"{_serv}.service")

                for kcmd in [
                    "start",
                    "stop",
                    "stats",
                    "debug",
                    "report",
                    "traceback",
                    "enable",
                    "disable",
                    "config",
                ]:
                    cmd_comp_dict[kcmd] = all_servs_active

                for kcmd in ["enable", "disable"]:
                    cmd_comp_dict[kcmd] = all_servs

                for kcmd in ["wconf"]:
                    cmd_comp_dict[kcmd] = path_completer

                cmd_comp_dict["e"] = merge_completers(
                    (WordCompleter(list(all_servs_active)), path_completer)
                )

                cmd_comp_dict["config"] = merge_completers(
                    (WordCompleter(list(all_servs)), path_completer)
                )

                cmd_completer = NestedCompleter.from_nested_dict(cmd_comp_dict)
                with patch_stdout.patch_stdout():
                    cmd_inp = await session_cmd.prompt_async(
                        ":", completer=cmd_completer, complete_while_typing=False
                    )
                shortcuts.clear()
                _cmdlw.deleteln()
                _cmdlw.erase()
                _cmdlw.refresh()
                stdscr.erase()
                stdscr.refresh()
                curses.curs_set(0)
                if cmd_inp:
                    command = ""
                    help_command = ""
                    self._last_cmd = ""
                    self._line_index = 0
                    # show_config = False
                    # self._log_enabled = False

            elif k == ord("@"):
                curses.curs_set(1)
                _cmdlw = stdscr.derwin(height - 1, 0)
                # cmd_inp = ""
                _dev_cmds_comps = [
                    WordCompleter(list(_dcmd.keys()))
                    for _dev, _dcmd in self._help_buffer.items()
                ]

                _dev_cmds_comps += [WordCompleter(["help", "reset"])]
                dev_cmd_comp = merge_completers(
                    _dev_cmds_comps,
                    deduplicate=True,
                )

                with patch_stdout.patch_stdout():
                    cmd_inp = await session_dev.prompt_async(
                        "@", completer=dev_cmd_comp, complete_while_typing=False
                    )
                    if cmd_inp:
                        dev_args = None
                        if any(("--args" in cmd_inp, "--kwargs" in cmd_inp)):
                            cmd_inp, _, dev_args = self._dev_cmd_parser.sh_cmd(cmd_inp)
                        cmd_inp = f"@{cmd_inp}"
                shortcuts.clear()
                _cmdlw.deleteln()
                _cmdlw.erase()
                _cmdlw.refresh()
                stdscr.erase()
                stdscr.refresh()
                curses.curs_set(0)
                if cmd_inp:
                    command = ""
                    help_command = ""
                    self._last_cmd = ""
                    self._line_index = 0
                    # show_config = False
                    # self._log_enabled = False

            elif k == ord("?"):
                curses.curs_set(1)
                _cmdlw = stdscr.derwin(height - 1, 0)
                _help_completer = WordCompleter(list(self._cmd_lib.keys()))
                cmd_help = await session_help.prompt_async(
                    "?", completer=_help_completer, complete_while_typing=False
                )
                shortcuts.clear()
                _cmdlw.deleteln()
                _cmdlw.erase()
                _cmdlw.refresh()
                stdscr.erase()
                stdscr.refresh()
                curses.curs_set(0)
                if cmd_help:
                    command = ""
                    help_command = ""
                    self._line_index = 0

            elif k == curses.ascii.ESC:
                filt_dev = ""
                help_command = ""
                # self._log_enabled = False
                show_config = False
                if not filt_serv or self._last_cmd != "debug":
                    self._last_cmd = ""

                    command = ""
                self._line_index = 0
                filt_log = ""
                filt_serv = ""
                if self._log_mode != b"log":
                    self._log_enabled = False
                    self._log_mode = b"log"

            self._filt_dev = filt_dev
            node = nodes[node_idx]
            _nodes = [node]
            _max_seps = {k: [] for k in _HL}
            _max_hns = []
            _cmd_inp = cmd_inp
            if _nodes == ["all"]:
                _nodes = [nd for nd in list(self._data_buffer.keys()) if nd != "all"]
                _nodes.sort()
                if filt_dev:
                    _filt_nodes = node_match(filt_dev, _nodes)
                    self._filt_nodes = _filt_nodes
                    if _filt_nodes:
                        _nodes = _filt_nodes
                        _nodes.sort()
                        # Device cmds
                        if (cmd_inp and cmd_inp.startswith("@")) or cmd_inp == "reset":
                            if dev_args:
                                _cmd_inp = json.dumps(
                                    {
                                        "cmd": cmd_inp.replace("@", ""),
                                        "args": dev_args.args,
                                        "kwargs": dev_args.kwargs,
                                    }
                                )
                            for node in _nodes:
                                await self._client.publish(
                                    f"device/{node}/cmd",
                                    payload=_cmd_inp.replace("@", ""),
                                )
                else:
                    # all --> publish to all (faster instead of looping)

                    if (cmd_inp and cmd_inp.startswith("@")) or cmd_inp == "reset":
                        if dev_args:
                            _cmd_inp = json.dumps(
                                {
                                    "cmd": cmd_inp.replace("@", ""),
                                    "args": dev_args.args,
                                    "kwargs": dev_args.kwargs,
                                }
                            )
                        await self._client.publish(
                            "device/all/cmd", payload=_cmd_inp.replace("@", "")
                        )
            else:
                self._filt_dev = node
                self._filt_nodes = [node]
                if (cmd_inp and cmd_inp.startswith("@")) or cmd_inp == "reset":
                    if dev_args:
                        _cmd_inp = json.dumps(
                            {
                                "cmd": cmd_inp.replace("@", ""),
                                "args": dev_args.args,
                                "kwargs": dev_args.kwargs,
                            }
                        )
                    for node in _nodes:
                        await self._client.publish(
                            f"device/{node}/cmd", payload=_cmd_inp.replace("@", "")
                        )

            # Parse cmd line
            if not cmd_inp.startswith("@") or cmd_help:
                _cmd = cmd_inp or cmd_help
                if "-h" in _cmd or cmd_help:
                    _cmd = _cmd.replace("-h", "").strip()
                    help_command = f"HELP: {_cmd}"
                    if not _cmd:
                        rest_args = self._cmd_parser.parser.format_help()
                    else:
                        subcmd = self._subparses.get(_cmd)
                        if subcmd:
                            rest_args = subcmd.format_help()
                        else:
                            rest_args = self._cmd_parser.parser.format_usage()
                            rest_args += (
                                f"\n asyncmd error: command {_cmd}"
                                f" not in {list(self._cmd_lib.keys())}"
                            )

                elif _cmd:
                    top_cmd = _cmd.split()[0]
                    if top_cmd.replace("!", "") in self._cmd_lib:
                        command, rest_args, args = self._cmd_parser.sh_cmd(_cmd)
                        command_sent = False
                        if "!" in _cmd:
                            help_command = command
                    else:
                        help_command = f"ERROR: {_cmd}"

                        rest_args = self._cmd_parser.parser.format_usage()
                        rest_args += (
                            f"\n asyncmd error: command {_cmd}"
                            f" not in {list(self._cmd_lib.keys())}"
                        )
            else:
                if cmd_inp.startswith("@"):
                    self._last_cmd = cmd_inp.replace("@", "")
                    command = self._last_cmd

            # get info
            for node in _nodes:
                data = self._data_buffer[node]
                _max_hn = self.get_sep("hostname", _HL, data, TM_FMT)
                _max_hns.append(_max_hn)

                _max_sep_nd = {k: self.get_sep(k, _HL, data, TM_FMT) for k in _HL}
                for k in _HL:
                    _max_seps[k] += [_max_sep_nd[k]]

            _max_hn = max(_max_hns)
            _max_sep = {k: max(v) for k, v in _max_seps.items()}

            node_info_str = []
            for node in _nodes:
                node_info_str += [f"Device: {node}"]
                data = self._data_buffer[node]
                node_info_str += self.get_node_info(data, width)

            if self._info_enabled:
                self.print_node_info(stdscr, ptr, node_info_str, width)
            else:
                node_info_str = [" " * width]
                ptr.newline()
                ptr.newline()

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
            if filt_serv:
                status_bar_str = status_bar_str.replace(
                    "STATS", f"STATS | filter: {filt_serv}"
                )

            self.print_upper_status_bar(
                stdscr, width, status_bar_str, len(node_info_str)
            )

            for node in _nodes:
                data = self._data_buffer[node]

                vm_status_list = [
                    f" {data['hostname']:{_max_hn}s}"
                    f"{serv:{_max_sep['SERVICE']}s}"
                    + "".join(
                        [
                            f"{self.get_val(hdr, data, serv, TM_FMT):{_max_sep[hdr]}s}"
                            for hdr in ["STATUS", "SINCE", "DONE_AT", "RESULT", "STATS"]
                        ]
                    )
                    for serv in sorted(data)
                    if serv != "hostname"
                ]  # --> services row
                status_bar_item_length = 3
                if filt_serv:
                    data_filt = {
                        ks: data[ks] for ks in node_match(filt_serv, data.keys())
                    }
                    vm_status_list = [
                        f" {data['hostname']:{_max_hn}s}"
                        f"{srv:{_max_sep['SERVICE']}s}"
                        + "".join(
                            [
                                f"{self.get_val(hd, data, srv, TM_FMT):{_max_sep[hd]}s}"
                                for hd in [
                                    "STATUS",
                                    "SINCE",
                                    "DONE_AT",
                                    "RESULT",
                                    "STATS",
                                ]
                            ]
                        )
                        for srv in sorted(data_filt)
                        if srv != "hostname"
                    ]  # --> services row
                self.print_vm_info(
                    stdscr, ptr, vm_status_list, status_bar_item_length, width
                )

            if show_config and not (self._last_cmd or help_command):
                if len(_nodes) == 1:
                    ptr.newline()
                    stdscr.attron(curses.color_pair(3))
                    self.printline(stdscr, f" CONFIG {' ' * (width - 7)}", ptr, width)
                    stdscr.attroff(curses.color_pair(3))
                    ptr.newline()
                    for node in _nodes:
                        _conf = self._conf_buffer.get(node)
                        if _conf:
                            _ptr_h0 = ptr.x
                            _config_str = yaml.dump(_conf).splitlines()
                            n_lines = len(_config_str)
                            n_cols = int(n_lines / (height - _ptr_h0))
                            cols_y_w = width
                            if n_cols > 1:
                                cols_y_w = int(
                                    (
                                        width
                                        - (
                                            max(
                                                [
                                                    len(s)
                                                    for s in _config_str
                                                    if "/" not in s
                                                ]
                                            )
                                            + 4
                                        )
                                    )
                                    / n_cols
                                )

                            for line in _config_str:
                                if ptr.x > (height - 2):
                                    ptr.x = _ptr_h0
                                    ptr.y += cols_y_w
                                if len(line) > cols_y_w - 4:
                                    for _line in textwrap.wrap(line, cols_y_w - 4):
                                        self.printline(stdscr, f"{_line}\n", ptr, width)
                                else:
                                    if not line.startswith(" "):
                                        _serv = _conf.get(line.split(":")[0])
                                        if _serv.get("enabled"):
                                            stdscr.attron(curses.color_pair(3))
                                        else:
                                            stdscr.attron(curses.color_pair(9))

                                        self.printline(stdscr, line, ptr, width)
                                        stdscr.attroff(curses.color_pair(3))
                                        stdscr.attroff(curses.color_pair(9))
                                    else:
                                        self.printline(stdscr, line, ptr, width)
                        if refresh_devconfig:
                            _msg = json.dumps({"config": {"get": "*"}})

                            await self._client.publish(
                                f"device/{node}/service", payload=_msg
                            )
                    refresh_devconfig = False
            elif self._log_enabled and not (self._last_cmd or help_command):
                if len(_nodes) >= 1:
                    ptr.newline()
                    stdscr.attron(curses.color_pair(3))
                    if self._log_mode == b"log":
                        self.printline(
                            stdscr,
                            f" LOG | filter: {filt_log}{' ' * (width - 7)}",
                            ptr,
                            width,
                        )
                    else:
                        self.printline(
                            stdscr,
                            f" ERROR.LOG | filter: {filt_log} {' ' * (width - 7)}",
                            ptr,
                            width,
                        )
                    stdscr.attroff(curses.color_pair(3))
                    ptr.newline()
                    _buffer_log = ""
                    v_lines = (height - 2) - ptr.x
                    # if self._line_index > 0:
                    v_lines -= self._line_index
                    for node in _nodes:
                        if self._log_mode == b"log":
                            _log = self._log_buffer.get(node)
                        else:
                            _log = self._errlog_buffer.get(node)
                        if _log:
                            _n_lines = len(_log.splitlines())
                            for line in _log.splitlines():
                                if line not in _buffer_log:
                                    if filt_log:
                                        if node_match(filt_log, [line]):
                                            _buffer_log += f"{line}\n"
                                    else:
                                        _buffer_log += f"{line}\n"
                    if _buffer_log:
                        _log_lines = _buffer_log.splitlines()
                        _log_lines.sort()
                        for line in _log_lines[-v_lines:]:
                            self.printline(stdscr, line, ptr, width)
            elif help_command:
                self.draw_section(stdscr, ptr, help_command, str(rest_args), width)
            if command:
                if not command_sent:
                    command_sent = not command_sent
                    if command in ["start", "stop", "debug", "report", "traceback"]:
                        if command == "debug":
                            try:
                                assert rest_args.endswith(".service")
                                msg = json.dumps({"status": f"{rest_args}:/debug"})
                            except Exception:
                                msg = json.dumps(
                                    {"status": f"{rest_args}.service:/debug"}
                                )

                        else:
                            msg = json.dumps({command: rest_args})
                        if _nodes == [
                            nd for nd in list(self._data_buffer.keys()) if nd != "all"
                        ]:
                            await self._client.publish(
                                "device/all/service", payload=msg
                            )
                        else:
                            for node in _nodes:
                                await self._client.publish(
                                    f"device/{node}/service", payload=msg
                                )
                        self._last_cmd = command

                    elif command in ["enable", "disable", "config"]:
                        refresh_devconfig = True
                        if command in ["enable", "disable"]:
                            rest_args = [
                                _serv.replace(".service", "")
                                for _serv in rest_args
                                if _serv.endswith(".service")
                            ]
                            msg = json.dumps({"config": {command: rest_args}})
                        else:
                            # config
                            _serv = rest_args
                            act = "set"
                            _configf = False
                            if os.path.exists(rest_args):
                                _configf = parse_config_file(rest_args)
                            if not _configf:
                                if _serv.endswith(".service"):
                                    _serv = _serv.replace(".service", "")
                                if args.kwargs is None:
                                    args.kwargs = {}
                                if args.args is None:
                                    args.args = []
                                msg = json.dumps(
                                    {
                                        "config": {
                                            act: {
                                                _serv: {
                                                    "args": args.args,
                                                    "kwargs": args.kwargs,
                                                }
                                            }
                                        }
                                    }
                                )
                            else:
                                enabled_servs = {
                                    serv: {
                                        "args": _configf[serv].get("args", []),
                                        "kwargs": _configf[serv].get("kwargs", {}),
                                    }
                                    for serv in _configf
                                    if _configf[serv].get("enabled", False)
                                }
                                msg = json.dumps({"config": {act: enabled_servs}})

                        if _nodes == [
                            nd for nd in list(self._data_buffer.keys()) if nd != "all"
                        ]:
                            await self._client.publish(
                                "device/all/service", payload=msg
                            )
                        else:
                            for node in _nodes:
                                await self._client.publish(
                                    f"device/{node}/service", payload=msg
                                )
                    elif command == "wconf":
                        config_file = rest_args
                        resp_config = ""
                        for dev in _nodes:
                            if dev in self._conf_buffer:
                                with open(f"{dev}_{config_file}", "w") as cf:
                                    cf.write(yaml.dump(self._conf_buffer[dev]))

                                self._last_cmd = command
                                resp_config += (
                                    f"Device {dev} config saved in "
                                    f"{dev}_{config_file}\n"
                                )

                    elif command == "e":
                        file_to_edit = rest_args
                        if not os.path.exists(file_to_edit):
                            if file_to_edit.endswith(".service"):
                                if file_to_edit in self._services_path:
                                    file_to_edit = self._services_path[file_to_edit]
                        if file_to_edit.endswith(".mpy"):
                            file_to_edit = file_to_edit.replace(".mpy", ".py")
                        editor = os.environ.get("EDITOR", "vim")
                        shell_cmd_str = shlex.split(f"{editor} {file_to_edit}")

                        old_action = signal.signal(signal.SIGINT, signal.SIG_IGN)

                        def preexec_function(action=old_action):
                            signal.signal(signal.SIGINT, action)

                        try:
                            subprocess.call(shell_cmd_str, preexec_fn=preexec_function)
                            signal.signal(signal.SIGINT, old_action)
                        except Exception:
                            pass

                        shortcuts.clear()
                        stdscr.erase()
                        stdscr.refresh()

                    elif command == "stats":
                        self._last_cmd = command

                    elif command == "errlog":
                        self._last_cmd = ""
                        self._log_enabled = True
                        if not args.n:
                            self._log_mode = b"error.log"
                        else:
                            self._log_mode = f"error.log.{args.n}".encode("utf-8")
                        self._errlog_query = False
                    elif command == "q":
                        self._close_flag = True
                        break

                if self._last_cmd:
                    resp = ""

                    if self._last_cmd == "help" or "?" in self._last_cmd:
                        # device help

                        for node in _nodes:
                            dev_help = self._help_buffer.get(node)
                            if dev_help:
                                if "?" in self._last_cmd:
                                    last_cmd_resp = dev_help.get(
                                        self._last_cmd.replace("?", "")
                                    )
                                else:
                                    last_cmd_resp = dev_help
                                if last_cmd_resp:
                                    resp += f"{node}: [{self._last_cmd.upper()}]"
                                    resp += f" {str(last_cmd_resp)}\n\n"
                    elif self._last_cmd == "stats":
                        for node in _nodes:
                            dev_data = self._data_buffer.get(node)
                            dev_stats_serv = dev_data.get(rest_args, {}).get("stats")
                            if dev_stats_serv:
                                resp += f"> {node}: [{rest_args.upper()}]\n"
                                for line in yaml.dump(dev_stats_serv).splitlines():
                                    resp += f"    {line}\n"
                                resp += "\n"
                    elif self._last_cmd == "traceback":
                        for node in _nodes:
                            dev_data = self._data_buffer.get(node)
                            dev_tb_serv = dev_data.get(rest_args, {}).get("traceback")
                            if dev_tb_serv:
                                resp += f"[{node}]:\n"
                                for line in dev_tb_serv.splitlines():
                                    resp += f"    {line}\n"
                                resp += "\n"
                    elif self._last_cmd == "report":
                        for node in _nodes:
                            dev_report = self._report_buffer.get(node)
                            if dev_report:
                                _rp = dev_report.get(rest_args)
                                resp += f"[{node}]:\n"
                                for line in _rp.splitlines():
                                    resp += f"    {line}\n"
                                resp += "\n"

                    elif self._last_cmd == "debug":
                        for node in _nodes:
                            e_offset = 0
                            dev_data = self._data_buffer.get(node)
                            # use regex

                            resp += f"[{node}] \n"

                            if filt_serv:
                                _debug_servs = set(
                                    node_match(filt_serv, dev_data.keys())
                                )
                            else:
                                _debug_servs = set(
                                    [rest_args] + node_match(rest_args, dev_data.keys())
                                )
                            for _dserv in sorted(_debug_servs):
                                dev_stats_serv = dev_data.get(_dserv, {})
                                if dev_stats_serv and "info" in dev_stats_serv:
                                    if dev_data.get("aiomqtt.service")["stats"][
                                        "platform"
                                    ] in ["esp32"]:
                                        e_offset = _EPOCH_2000
                                    resp_buffer = io.StringIO()
                                    if not self._services_path.get(_dserv):
                                        self._services_path[
                                            _dserv
                                        ] = dev_stats_serv.get("path")
                                    if dev_stats_serv.get("status") == "error":
                                        if not dev_stats_serv.get("traceback"):
                                            msg = json.dumps(
                                                {"status": f"{_dserv}:/debug"}
                                            )

                                            await self._client.publish(
                                                f"device/{node}/service", payload=msg
                                            )
                                            await asyncio.sleep(0.2)

                                    if node in self._log_buffer:
                                        # add new log lines match
                                        for line in self._log_buffer[node].splitlines()[
                                            -20:
                                        ]:
                                            if f"[{_dserv}]" in line or service_match(
                                                _dserv, line
                                            ):
                                                if line not in dev_stats_serv["log"]:
                                                    dev_stats_serv["log"] += f"{line}\n"
                                    debug_st.get_status(
                                        {_dserv: dev_stats_serv, "hostname": node},
                                        file=resp_buffer,
                                        epoch_offset=e_offset,
                                        colored=True,
                                        highligth_services=True,
                                    )
                                    resp_buffer.seek(0)
                                    resp += resp_buffer.read()
                            resp += "\n\n"

                    else:
                        for node in _nodes:
                            dev_resp = self._cmd_resps.get(node)
                            if dev_resp:
                                last_cmd_resp = dev_resp.get(self._last_cmd)
                                if last_cmd_resp:
                                    resp += f"{node}: [{self._last_cmd.upper()}]"
                                    resp += f" {str(last_cmd_resp)}\n\n"
                    if resp:
                        self.draw_section(
                            stdscr,
                            ptr,
                            f"CMD: {command.upper()}",
                            resp,
                            width,
                            colored=self._last_cmd in ("debug", "report"),
                        )

                    if self._last_cmd in ["wconf"]:
                        self.draw_section(
                            stdscr,
                            ptr,
                            f"CMD: {self._last_cmd.upper()}",
                            resp_config,
                            width,
                        )

            if not cmd:
                self.print_bottom_status_bar(stdscr, len(_nodes), width, height)
            stdscr.noutrefresh()
            curses.doupdate()
            stdscr.timeout(update_interval)
            await asyncio.sleep(0.1)
        curses.endwin()

    async def run(self, stdscr, upint):
        self._feed_task = asyncio.create_task(self.data_feed())
        self._log_task = asyncio.create_task(self.data_log())
        self._draw_task = asyncio.create_task(self.draw(stdscr, upint))
        self._tasks_set = {self._feed_task, self._draw_task, self._log_task}
        await asyncio.gather(*self._tasks_set)

    def start(self, stdscr, upint):
        return asyncio.run(self.run(stdscr, upint))
