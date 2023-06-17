import time
import sys

# stats = {
#     "world.service": {
#         "args": [2, 5],
#         "path": "/home/cgg/Develop/MICROPYTHON/micropython/extmod/asyncmd/tests/unix/aioservices/services/world_service.py",
#         "since": 1686401906.721135,
#         "status": "scheduled - done",
#         "result": None,
#         "info": "World example runner v1.0",
#         "docs": "https://github.com/Carglglz/asyncmd/blob/main/README.md",
#         "kwargs": {},
#         "ctasks": [],
#         "done_at": 1686401911.721803,
#         "stats": None,
#         "type": "schedule.service",
#         "log": "2023-06-10 13:58:31 [linux@unix] [INFO] [world.service] done: LED 2 toggled!\n",
#         "service": True,
#     },
#     "stats.service": {
#         "args": [],
#         "path": "/home/cgg/Develop/MICROPYTHON/micropython/extmod/asyncmd/tests/unix/aioservices/services/stats_service.py",
#         "since": 1686284541.230181,
#         "status": "running",
#         "result": None,
#         "info": "Stats JSON API v1.0",
#         "docs": "https://github.com/Carglglz/asyncmd/blob/main/README.md",
#         "kwargs": {
#             "ssl": "False",
#             "ssl_params": "{}",
#             "on_error": "<bound_method 7fdb64a1bc60 Service: stats.service from /home/cgg/Develop/MICROPYTHON/micropython/extmod/asyncmd/tests/unix/aioservices/services/stats_service.py.<function on_error at 0x7fdb64a1b080>>",
#             "debug": "True",
#             "on_stop": "<bound_method 7fdb64a1b520 Service: stats.service from /home/cgg/Develop/MICROPYTHON/micropython/extmod/asyncmd/tests/unix/aioservices/services/stats_service.py.<function on_stop at 0x7fdb64a1b060>>",
#             "host": "0.0.0.0",
#             "port": "8234",
#         },
#         "ctasks": [],
#         "done_at": None,
#         "stats": {
#             "ctasks": 1,
#             "requests": 8,
#             "firmware": "3.4.0; MicroPython v1.19.1-847-g8c94ededb-dirty on 2023-01-26",
#             "machine": "linux [GCC 9.4.0] version",
#             "fsfree": 42850263040,
#             "mfree": 1963232,
#             "fsused": 74664833024,
#             "fstotal": 117515096064,
#             "tasks": 6,
#             "platform": "linux",
#             "services": 4,
#             "mtotal": 2072832,
#             "mused": 109600,
#         },
#         "type": "runtime.service",
#         "log": "2023-06-10 13:59:25 [linux@unix] [INFO] [stats.service] GET /debug HTTP/1.1\n",
#         "service": True,
#     },
#     "hostname": "unix",
#     "watcher.service": {
#         "args": [30],
#         "path": "/home/cgg/Develop/MICROPYTHON/micropython/extmod/asyncmd/tests/unix/aioservices/services/watcher_service.py",
#         "since": 1686284541.229753,
#         "status": "running",
#         "result": None,
#         "info": "Watcher Service v1.0 - Restarts services on failed state",
#         "docs": "https://github.com/Carglglz/asyncmd/blob/main/README.md",
#         "kwargs": {
#             "wdfeed": "30000",
#             "max_errors": "0",
#             "on_error": "<bound_method 7fdb64a1f4a0 Service: watcher.service from /home/cgg/Develop/MICROPYTHON/micropython/extmod/asyncmd/tests/unix/aioservices/services/watcher_service.py.<function on_error at 0x7fdb64a1e820>>",
#             "on_stop": "<bound_method 7fdb64a1f480 Service: watcher.service from /home/cgg/Develop/MICROPYTHON/micropython/extmod/asyncmd/tests/unix/aioservices/services/watcher_service.py.<function on_stop at 0x7fdb64a1e8a0>>",
#             "watchdog": "True",
#         },
#         "ctasks": ["watcher.service.wdt"],
#         "done_at": None,
#         "stats": {
#             "errors": 1506,
#             "report": {"hello.service": ["ValueError", "ZeroDivisionError"]},
#         },
#         "type": "runtime.service",
#         "log": "2023-06-10 13:59:01 [linux@unix] [INFO] [watcher.service] Restarting Task hello.service\n",
#         "service": True,
#     },
#     "hello.service": {
#         "args": [2, 5],
#         "path": "/home/cgg/Develop/MICROPYTHON/micropython/extmod/asyncmd/tests/unix/aioservices/services/hello_service.py",
#         "since": 1686401941.818903,
#         "status": "running",
#         "result": None,
#         "info": "Hello example runner v1.0",
#         "docs": "https://github.com/Carglglz/asyncmd/blob/main/README.md",
#         "kwargs": {
#             "on_stop": "<bound_method 7fdb64a189e0 Service: hello.service from /home/cgg/Develop/MICROPYTHON/micropython/extmod/asyncmd/tests/unix/aioservices/services/hello_service.py.<function on_stop at 0x7fdb64a17d60>>",
#             "on_error": "<bound_method 7fdb64a18a00 Service: hello.service from /home/cgg/Develop/MICROPYTHON/micropython/extmod/asyncmd/tests/unix/aioservices/services/hello_service.py.<function on_error at 0x7fdb64a17d20>>",
#         },
#         "ctasks": [],
#         "done_at": None,
#         "stats": None,
#         "type": "runtime.service",
#         "log": "2023-06-10 13:59:21 [linux@unix] [INFO] [hello.service] LED 4 toggled!\n",
#         "service": True,
#     },
# }

_dt_list = [0, 1, 2, 3, 4, 5]


def pprint_dict(kw, sep=" ", ind=1, fl=True, ls=",", lev=0, file=sys.stdout):
    if kw == {}:
        print(f"{sep}{kw}", file=file)
        return
    if fl:
        if lev == 0:
            ind += 2
        else:
            ind += 1
        print(sep + "{", end="", file=file)
    for k, v in kw.items():
        if v == list(kw.values())[-1]:
            if lev == 0:
                ls = " }"
            else:
                ls = " },"
        if isinstance(v, dict) and v:
            if fl:
                fl = False
                print(f"{sep}{repr(k)}:", end="", file=file)
            else:
                print(f"{sep*ind}{repr(k)}:", end="", file=file)
            pprint_dict(
                v,
                sep=sep,
                ind=len(f"{sep*ind}{repr(k)}:" + " {"),
                fl=True,
                lev=lev + 1,
                file=file,
            )
        else:
            if fl:
                fl = False
                print(f"{sep}{repr(k)}: {repr(v)}{ls}", file=file)
            else:
                print(f"{sep*ind}{repr(k)}: {repr(v)}{ls}", file=file)


def _dt_format(number):
    n = str(int(number))
    if len(n) == 1:
        n = "0{}".format(n)
        return n
    else:
        return n


def _ft_datetime(t_now):
    return [_dt_format(t_now[i]) for i in _dt_list]


def get_datetime(_dt):
    return "{}-{}-{} {}:{}:{}".format(*_ft_datetime(_dt))


def time_str(uptime_tuple):
    upt = [_dt_format(i) for i in uptime_tuple[1:]]
    up_str_1 = f"{uptime_tuple[0]} days, "
    up_str_2 = f"{upt[0]}:{upt[1]}:{upt[2]}"
    if uptime_tuple[0] > 0:
        return up_str_1 + up_str_2
    elif uptime_tuple[-2] > 0 or uptime_tuple[-3] > 0:
        return up_str_2
    return f"{int(uptime_tuple[-1])} s"


def tmdelta_fmt(dt):
    if dt < 0:
        return f"the past by {tmdelta_fmt(abs(dt))} "
    dd, hh, mm, ss = (0, 0, 0, 0)
    mm = dt // 60
    ss = dt % 60
    if mm:
        pass
    else:
        return time_str((dd, hh, mm, ss))
    hh = mm // 60
    if hh:
        mm = mm % 60
    else:
        return time_str((dd, hh, mm, ss))
    dd = hh // 24
    if dd:
        hh = hh % 24
    else:
        return time_str((dd, hh, mm, ss))

    return time_str((dd, hh, mm, ss))


def status_sc(schedule, file=sys.stdout, debug=False, epoch_offset=0):
    last = schedule.get("last_dt")
    _last_tm = schedule.get("last")
    if _last_tm:
        _last_tm += epoch_offset
    repeat = schedule.get("repeat")
    _schedule = schedule
    _sch_str = ", ".join([f"{k}={v}" for k, v in _schedule.items()])
    _next = None
    start_in = None
    if last:
        last = get_datetime(last)
        if repeat:
            _next = repeat - (time.time() - _last_tm)
    else:
        start_in = schedule.get("start_in")
        if start_in < 0:
            start_in = None
        if start_in > 0:
            if isinstance(start_in, tuple):
                _next = time.mktime(start_in) - time.time()
            else:
                _next = schedule.get("t0") + epoch_offset + start_in - time.time()
    if repeat:
        if last:
            print(
                f"    ┗━► schedule: last @ {last} "
                + f"--> next in {tmdelta_fmt(_next)}",
                end="",
                file=file,
            )
            print(f" @ {get_datetime(time.localtime(time.time() + _next))}", file=file)
        else:
            print(f"    ┗━► schedule: next in {tmdelta_fmt(_next)}", end="", file=file)
            print(f" @ {get_datetime(time.localtime(time.time() + _next))}", file=file)

    elif start_in:
        print(f"    ┗━► schedule: starts in {tmdelta_fmt(_next)}", end="", file=file)
        print(f" @ {get_datetime(time.localtime(time.time() + _next))}", file=file)

    if debug:
        print(f"    ┗━► schedule opts: {_sch_str}", file=file)


def get_status(
    req,
    debug=True,
    log=True,
    indent="    ",
    file=sys.stdout,
    epoch_offset=0,
    colored=True,
):
    req.pop("hostname")
    for service in req:
        name = service
        _srv = req.get(service)
        _done_at = _srv["done_at"]
        _since = _srv["since"] + epoch_offset
        if _done_at:
            _done_at += epoch_offset
            _done_at_const = _srv["done_at"] + epoch_offset
            _dot = "●"
            data = _srv.get("result")
            if _srv["status"] == "done":
                _status = "done"
            if _srv["status"] == "stopped":
                _status = "\u001b[33;1mstopped\u001b[0m"
                _dot = "\u001b[33;1m●\u001b[0m"

            if _done_at:
                _done_at = time.localtime(_done_at)
                _done_at = get_datetime(_done_at)
                _done_delta = time.time() - _done_at_const
                _done_at += f"; {tmdelta_fmt(_done_delta)} ago"
            if _srv.get("type") == "schedule.service":
                if _srv["status"] == "scheduled":
                    _status = "scheduled"
                    _dot = "\u001b[36m●\u001b[0m"
                    # if _done_at is None:
                    #     _done_at = get_datetime(
                    #         time.localtime(
                    #             aioschedule._AIOCTL_SCHEDULE_T0
                    #             + aioschedule.group()[name]["start_in"]
                    #         )
                    #     )
                else:
                    _status = _srv["status"]
                    _dot = "\u001b[36m●\u001b[0m"
            if _srv["status"] == "error":
                _err = "ERROR"
                if _srv["service"]:
                    _err = "failed"
                _status = f"\u001b[31;1m{_err}\u001b[0m"
                data = (
                    f"\u001b[31;1m{_srv['result']}\u001b[0m:"
                    # + f" {data.value.value}"
                )
                _dot = "\u001b[31;1m●\u001b[0m"
            if debug:
                if _srv["service"]:
                    info = _srv["info"]
                    path = _srv["path"]
                    docs = _srv["docs"]
                    _type = _srv["type"]
                    print(f"{_dot} {name} - {info}", file=file)
                    print(f"    Loaded: {path}", file=file)
                    print(f"    Active: status: {_status} ", end="", file=file)
                    print(f"@ {_done_at} --> result: " + f"{data}", file=file)
                    print(f"    Type: {_type}", file=file)
                    print(f"    Docs: {docs}", file=file)
                    if _srv["stats"]:
                        _show = [
                            "Stats",
                            ", ".join([f"{k}={v}" for k, v in _srv["stats"].items()]),
                        ]

                        print(f"    {_show[0]}:  {_show[1]}", file=file)

                    if _srv["ctasks"]:
                        print(f"    CTasks: {_srv['ctasks']}", file=file)
                        # for _ctsk in c_task.service._child_tasks:
                        #     print("        ┗━► ", end="")
                        #     status(_ctsk, log=False, debug=True, indent=" " * 16)
                        # print("    " + "━" * 60)
                else:
                    print(f"{_dot} {name}: status: {_status} ", end="", file=file)
                    print(f"@ {_done_at} --> result: " + f"{data}", file=file)

            else:
                print(f"{_dot} {name}: status: {_status} ", end="", file=file)
                print(f"@ {_done_at} --> result: " + f"{data}", file=file)
            if debug:
                # c_task = _AIOCTL_GROUP.tasks[name]
                print(f"{indent}Task:", file=file)
                if _done_at:
                    _delta_runtime = _done_at_const - _since
                    _delta_runtime = tmdelta_fmt(_delta_runtime)
                    print(f"{indent}┗━► runtime: {_delta_runtime}", file=file)

                if "schedule" in _type:
                    if _srv.get("schedule"):
                        status_sc(
                            _srv.get("schedule"),
                            file=file,
                            debug=debug,
                            epoch_offset=epoch_offset,
                        )
                print(f"{indent}┗━► args: {_srv['args']}", file=file)
                print(f"{indent}┗━► kwargs:", end="", file=file)
                pprint_dict(_srv["kwargs"], ind=len(f"{indent}┗━► kwargs: "), file=file)
                if _srv.get("traceback"):
                    print(f"{indent}┗━► traceback: ", file=file)
                    for tbline in _srv.get("traceback").splitlines()[1:]:
                        print(indent + " " * 14 + tbline, file=file)
                    print("", file=file)
            # if _SCHEDULE and not debug:
            #     if name in aioschedule._AIOCTL_SCHEDULE_GROUP:
            #         aioschedule.status_sc(name, debug=debug)

            if "schedule" in _type and not debug:
                if _srv.get("schedule"):
                    status_sc(
                        _srv.get("schedule"),
                        file=file,
                        debug=debug,
                        epoch_offset=epoch_offset,
                    )

            if log:
                # if (
                #     _AIOCTL_GROUP.tasks[name]._is_service
                #     and _AIOCTL_GROUP.tasks[name]._is_parent
                # ):
                #     c_task = _AIOCTL_GROUP.tasks[name]
                #     _ctsks = [f"*\[{_ctsk}\]*" for _ctsk in c_task.service._child_tasks]
                #     _AIOCTL_LOG.cat(grep=[f"*\[{name}\]*"] + _ctsks)
                # else:
                # _AIOCTL_LOG.cat(grep=f"[{name}])

                for logline in _srv["log"].splitlines()[-10:]:
                    print(f"{logline}", file=file)
                print("<" + "-" * 80 + ">", file=file)
        else:
            _dot = "\033[92m●\x1b[0m"
            _since_str = time.localtime(_since)
            _since_delta = time.time() - _since
            _since_str = get_datetime(_since_str)
            _since_str += f"; {tmdelta_fmt(_since_delta)}"
            if debug:
                if _srv["service"]:
                    info = _srv["info"]
                    path = _srv["path"]
                    docs = _srv["docs"]
                    _type = _srv["type"]
                    print(f"{_dot} {name} - {info}", file=file)
                    print(f"    Loaded: {path}", file=file)
                    if colored:
                        print(
                            "    Active: \u001b[32;1m(active) running\x1b[0m ",
                            end="",
                            file=file,
                        )
                    else:
                        print(
                            "    Active: (active) running ",
                            end="",
                            file=file,
                        )

                    print(f"since {_since_str} ago", file=file)
                    print(f"    Type: {_type}", file=file)
                    print(f"    Docs: {docs}", file=file)

                    if _srv["stats"]:
                        _show = [
                            "Stats",
                            ", ".join([f"{k}={v}" for k, v in _srv["stats"].items()]),
                        ]

                        print(f"    {_show[0]}:  {_show[1]}", file=file)

                    if _srv["ctasks"]:
                        print(f"    CTasks: {_srv['ctasks']}", file=file)

                    # if c_task.service._child_tasks:
                    #     print(f"    CTasks: {len(c_task.service._child_tasks)}")
                    #     for _ctsk in c_task.service._child_tasks:
                    #         print("        ┗━► ", end="")
                    #         status(_ctsk, log=False, debug=True, indent=" " * 16)
                    #     print("    " + "━" * 60)

                else:
                    print(
                        f"{_dot} {name}: status: \u001b[32;1mrunning\x1b[0m ",
                        end="",
                        file=file,
                    )
                    print(f"since {_since_str} ago", file=file)

            else:
                print(
                    f"{_dot} {name}: status: \u001b[32;1mrunning\x1b[0m ",
                    end="",
                    file=file,
                )
                print(f"since {_since_str} ago", file=file)
            if debug:
                # c_task = _AIOCTL_GROUP.tasks[name]
                print(f"{indent}Task: ", file=file)

                if "schedule" in _type:
                    if _srv.get("schedule"):
                        status_sc(
                            _srv.get("schedule"),
                            file=file,
                            debug=debug,
                            epoch_offset=epoch_offset,
                        )

                # if _SCHEDULE:
                #     if name in aioschedule._AIOCTL_SCHEDULE_GROUP:
                #         aioschedule.status_sc(name, debug=debug)

                print(f"{indent}┗━► args: {_srv['args']}", file=file)
                print(f"{indent}┗━► kwargs:", end="", file=file)
                pprint_dict(_srv["kwargs"], ind=len(f"{indent}┗━► kwargs: "), file=file)
            # if _SCHEDULE and not debug:
            #     if name in aioschedule._AIOCTL_SCHEDULE_GROUP:
            #         aioschedule.status_sc(name, debug=debug)

            if "schedule" in _type and not debug:
                if _srv.get("schedule"):
                    status_sc(
                        _srv.get("schedule"),
                        file=file,
                        debug=debug,
                        epoch_offset=epoch_offset,
                    )
            if log:
                # if (
                #     _AIOCTL_GROUP.tasks[name]._is_service
                #     and _AIOCTL_GROUP.tasks[name]._is_parent
                # ):
                #     c_task = _AIOCTL_GROUP.tasks[name]
                #     _ctsks = [f"*\[{_ctsk}\]*" for _ctsk in c_task.service._child_tasks]
                #     _AIOCTL_LOG.cat(grep=[f"*\[{name}\]*"] + _ctsks)
                # else:
                #     _AIOCTL_LOG.cat(grep=f"[{name}]")
                for logline in _srv["log"].splitlines()[-10:]:
                    print(f"{logline}", file=file)

                print("<" + "-" * 80 + ">", file=file)


# get_status(stats)
