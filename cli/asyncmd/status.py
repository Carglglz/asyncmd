import time

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


def pprint_dict(kw, sep=" ", ind=1, fl=True, ls=",", lev=0):
    if kw == {}:
        print(f"{sep}{kw}")
        return
    if fl:
        if lev == 0:
            ind += 2
        else:
            ind += 1
        print(sep + "{", end="")
    for k, v in kw.items():
        if v == list(kw.values())[-1]:
            if lev == 0:
                ls = " }"
            else:
                ls = " },"
        if isinstance(v, dict) and v:
            if fl:
                fl = False
                print(f"{sep}{repr(k)}:", end="")
            else:
                print(f"{sep*ind}{repr(k)}:", end="")
            pprint_dict(
                v, sep=sep, ind=len(f"{sep*ind}{repr(k)}:" + " {"), fl=True, lev=lev + 1
            )
        else:
            if fl:
                fl = False
                print(f"{sep}{repr(k)}: {repr(v)}{ls}")
            else:
                print(f"{sep*ind}{repr(k)}: {repr(v)}{ls}")


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
        return f"the past by {tmdelta_fmt(abs(dt))} s"
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


def get_status(req, debug=True, log=True, indent="    "):
    req.pop("hostname")
    for service in req:
        name = service
        _srv = req.get(service)
        _done_at = _srv["done_at"]
        if _done_at:
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
                _done_delta = time.time() - _srv["done_at"]
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
                    print(f"{_dot} {name} - {info}")
                    print(f"    Loaded: {path}")
                    print(f"    Active: status: {_status} ", end="")
                    print(f"@ {_done_at} --> result: " + f"{data}")
                    print(f"    Type: {_type}")
                    print(f"    Docs: {docs}")
                    if _srv["stats"]:
                        _show = [
                            "Stats",
                            ", ".join([f"{k}={v}" for k, v in _srv["stats"].items()]),
                        ]

                        print(f"    {_show[0]}:  {_show[1]}")

                    if _srv["ctasks"]:
                        print(f"    CTasks: {_srv['ctasks']}")
                        # for _ctsk in c_task.service._child_tasks:
                        #     print("        ┗━► ", end="")
                        #     status(_ctsk, log=False, debug=True, indent=" " * 16)
                        # print("    " + "━" * 60)
                else:
                    print(f"{_dot} {name}: status: {_status} ", end="")
                    print(f"@ {_done_at} --> result: " + f"{data}")

            else:
                print(f"{_dot} {name}: status: {_status} ", end="")
                print(f"@ {_done_at} --> result: " + f"{data}")
            if debug:
                # c_task = _AIOCTL_GROUP.tasks[name]
                print(f"{indent}Task:")
                if _done_at:
                    _delta_runtime = _srv["done_at"] - _srv["since"]
                    _delta_runtime = tmdelta_fmt(_delta_runtime)
                    print(f"{indent}┗━► runtime: {_delta_runtime}")

                # if _SCHEDULE:
                #     if name in aioschedule._AIOCTL_SCHEDULE_GROUP:
                #         aioschedule.status_sc(name, debug=debug)
                print(f"{indent}┗━► args: {_srv['args']}")
                print(f"{indent}┗━► kwargs:", end="")
                pprint_dict(_srv["kwargs"], ind=len(f"{indent}┗━► kwargs: "))
                # if traceback(name, rtn=True):
                #     print(f"{indent}┗━► traceback: ", end="")
                #     traceback(name, indent=indent + " " * 14)
                #     print("")
            # if _SCHEDULE and not debug:
            #     if name in aioschedule._AIOCTL_SCHEDULE_GROUP:
            #         aioschedule.status_sc(name, debug=debug)
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
                print(_srv["log"])
                print("<" + "-" * 80 + ">")
        else:
            _dot = "\033[92m●\x1b[0m"
            _since_str = time.localtime(_srv["since"])
            _since_delta = time.time() - _srv["since"]
            _since_str = get_datetime(_since_str)
            _since_str += f"; {tmdelta_fmt(_since_delta)}"
            if debug:
                if _srv["service"]:
                    info = _srv["info"]
                    path = _srv["path"]
                    docs = _srv["docs"]
                    _type = _srv["type"]
                    print(f"{_dot} {name} - {info}")
                    print(f"    Loaded: {path}")
                    print("    Active: \033[92m(active) running\x1b[0m ", end="")
                    print(f"since {_since_str} ago")
                    print(f"    Type: {_type}")
                    print(f"    Docs: {docs}")

                    if _srv["stats"]:
                        _show = [
                            "Stats",
                            ", ".join([f"{k}={v}" for k, v in _srv["stats"].items()]),
                        ]

                        print(f"    {_show[0]}:  {_show[1]}")

                    if _srv["ctasks"]:
                        print(f"    CTasks: {_srv['ctasks']}")

                    # if c_task.service._child_tasks:
                    #     print(f"    CTasks: {len(c_task.service._child_tasks)}")
                    #     for _ctsk in c_task.service._child_tasks:
                    #         print("        ┗━► ", end="")
                    #         status(_ctsk, log=False, debug=True, indent=" " * 16)
                    #     print("    " + "━" * 60)

                else:
                    print(f"{_dot} {name}: status: \033[92mrunning\x1b[0m ", end="")
                    print(f"since {_since_str} ago")

            else:
                print(f"{_dot} {name}: status: \033[92mrunning\x1b[0m ", end="")
                print(f"since {_since_str} ago")
            if debug:
                # c_task = _AIOCTL_GROUP.tasks[name]
                print(f"{indent}Task: ")

                # if _SCHEDULE:
                #     if name in aioschedule._AIOCTL_SCHEDULE_GROUP:
                #         aioschedule.status_sc(name, debug=debug)

                print(f"{indent}┗━► args: {_srv['args']}")
                print(f"{indent}┗━► kwargs:", end="")
                pprint_dict(_srv["kwargs"], ind=len(f"{indent}┗━► kwargs: "))
            # if _SCHEDULE and not debug:
            #     if name in aioschedule._AIOCTL_SCHEDULE_GROUP:
            #         aioschedule.status_sc(name, debug=debug)
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
                print(_srv["log"])

                print("<" + "-" * 80 + ">")


# get_status(stats)
