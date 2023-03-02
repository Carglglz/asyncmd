# sysctl for async tasks

import uasyncio as asyncio
import sys
import time
import re

_SCHEDULE = False
try:
    import aioschedule

    _SCHEDULE = True
except Exception:
    pass

_SERVICE = False
try:
    from aioclass import Service

    _SERVICE = True
except Exception:
    pass

_AIOCTL_GROUP = None
_AIOCTL_LOG = None
_DEBUG = False


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


def aiotask(f):
    # print(f.__name__)

    async def _task(*args, **kwargs):
        on_error = kwargs.get("on_error")
        on_stop = kwargs.get("on_stop")
        _id = kwargs.get("_id")
        if on_error or "on_error" in kwargs:
            kwargs.pop("on_error")
        if on_stop or "on_stop" in kwargs:
            kwargs.pop("on_stop")
        if _id or "_id" in kwargs:
            kwargs.pop("_id")
        if not _id:
            _id = f.__name__
        try:
            result = await f(*args, **kwargs)
            if _id in group().tasks.keys():
                group().tasks[_id].done_at = time.time()
            return result
        except asyncio.CancelledError:
            if _id in group().tasks.keys():
                group().tasks[_id].done_at = time.time()
            if callable(on_stop):
                return on_stop(*args, **kwargs)
            return on_stop

        except Exception as e:
            if _id in group().tasks.keys():
                group().tasks[_id].done_at = time.time()
            log = kwargs.get("log")
            if log:
                log.error(f"[{_id}]" + f" {e.__class__.__name__}: {e.errno}")
            if callable(on_error):
                return on_error(e, *args, **kwargs)
            return e

    return _task, f.__name__


def create_task(coro, *args, **kwargs):
    name = None
    if isinstance(coro, follow.__class__):
        name = kwargs.get("name", coro.__name__)
    if "name" in kwargs:
        name = kwargs.pop("name")
    if not name and hasattr(coro, "__name__"):
        name = coro.__name__
    # print(type(coro), coro)

    # print(dir(coro))
    if isinstance(coro, tuple):
        coro, _name = coro[0], coro[1]
        if not name:
            name = _name
    if callable(coro):
        _coro = coro(*args, **kwargs)
        if isinstance(_coro, tuple):
            _coro, _name = _coro[0], _coro[1]
            if not name or name == "_schedule" or name == "_task":
                name = _name
    # print(type(_coro), _coro)
    task = asyncio.create_task(_coro)
    # print(task, coro, name)
    # print(dir(task))
    # print(dir(task.coro))
    return Taskctl(coro, task, name, args, kwargs)


class Taskctl:
    def __init__(self, coro, task, name, args, kwargs):
        self.coro = coro
        self.task = task
        self.name = name
        self.args = args
        self.kwargs = kwargs
        self.since = time.time()
        self.done_at = None
        self.schedule = None
        self.cancelled = False
        self._is_service = False
        self.service = None
        if _SERVICE:
            if args:
                if issubclass(args[0].__class__, Service):
                    self._is_service = True
                    self.service = args[0]
                    self._is_parent = f"{self.service.name}.service" == name
                    self._is_child = f"{self.service.name}.service" != name
                    if self._is_child:
                        self.service._child_tasks.add(name)


class TaskGroup:
    def __init__(self, tasks=[]):
        self.tasks = {task.name: task for task in tasks}
        self.cnt = 0
        self.results = {}

    def add_task(self, task):
        if task.name not in self.tasks:
            self.tasks[task.name] = task
            self.cnt = 0
        else:
            self.cnt += 1
            new_name = f"{task.name}_{self.cnt}"
            task.name = new_name
            self.tasks[task.name] = task


def set_group(taskgroup):
    global _AIOCTL_GROUP
    _AIOCTL_GROUP = taskgroup


def set_log(log):
    global _AIOCTL_LOG
    _AIOCTL_LOG = log


def group():
    global _AIOCTL_GROUP
    return _AIOCTL_GROUP


def tasks():
    global _AIOCTL_GROUP
    return [
        task.task
        for task in _AIOCTL_GROUP.tasks.values()
        if not task.task.done() and not task.cancelled
    ]


def tasks_match(patt):
    pattrn = re.compile(patt.replace(".", r"\.").replace("*", ".*") + "$")
    try:
        return [task for task in group().tasks.keys() if pattrn.match(task)]
    except Exception:
        return []


def add(coro, *args, **kwargs):
    global _AIOCTL_GROUP
    new_task = create_task(coro, *args, **kwargs)
    if not _AIOCTL_GROUP:
        _AIOCTL_GROUP = TaskGroup([new_task])
    else:
        _AIOCTL_GROUP.add_task(new_task)


def delete(*args):
    global _AIOCTL_GROUP
    for name in args:
        if name in _AIOCTL_GROUP.tasks.keys():
            stop(name)
            _AIOCTL_GROUP.tasks.pop(name)
        else:
            if "*" in name:
                for tm in tasks_match(name):
                    stop(tm)
                    delete(tm)
            else:
                print(f"Task {name} not found in {list(_AIOCTL_GROUP.tasks.keys())}")


def status(name=None, log=True, debug=False, indent="    "):
    global _AIOCTL_GROUP, _AIOCTL_LOG, _SCHEDULE, _DEBUG
    if _DEBUG:
        debug = _DEBUG
    if not name:
        return status_all(log=log, debug=debug)
    if name in _AIOCTL_GROUP.tasks:
        if _AIOCTL_GROUP.tasks[name].task.done():
            _AIOCTL_GROUP.results[name] = _AIOCTL_GROUP.tasks[name].task.data
            _status = "done"
            _done_at = group().tasks[name].done_at
            _dot = "●"
            if _SCHEDULE:
                if _done_at:
                    _done_at = time.localtime(_done_at)
                    _done_at = aioschedule.get_datetime(_done_at)
                    _done_delta = time.time() - group().tasks[name].done_at
                    _done_at += f"; {aioschedule.tmdelta_fmt(_done_delta)} ago"
                if name in aioschedule.group():
                    _dot = f"\u001b[36m{_dot}\u001b[0m"
            data = _AIOCTL_GROUP.results[name]
            if issubclass(data.value.__class__, Exception):
                _err = "ERROR"
                if _AIOCTL_GROUP.tasks[name]._is_service:
                    _err = "failed"
                _status = f"\u001b[31;1m{_err}\u001b[0m"
                data = (
                    f"\u001b[31;1m{data.value.__class__.__name__}\u001b[0m:"
                    + f" {data.value.value}"
                )
                _dot = "\u001b[31;1m●\u001b[0m"
            if debug:
                if (
                    _AIOCTL_GROUP.tasks[name]._is_service
                    and _AIOCTL_GROUP.tasks[name]._is_parent
                ):
                    c_task = _AIOCTL_GROUP.tasks[name]
                    print(f"{_dot} {name} - {c_task.service.info}")
                    print(f"    Loaded: {c_task.service}")
                    print(f"    Active: status: {_status} ", end="")
                    print(f"@ {_done_at} --> result: " + f"{data}")
                    print(f"    Type: {c_task.service.type}")
                    print(f"    Docs: {c_task.service.docs}")
                    if hasattr(c_task.service, "show"):
                        _show = c_task.service.show()
                        print(f"    {_show[0]}:  {_show[1]}")

                    if c_task.service._child_tasks:
                        print(f"    CTasks: {len(c_task.service._child_tasks)}")
                        for _ctsk in c_task.service._child_tasks:
                            print("        ┗━► ", end="")
                            status(_ctsk, log=False, debug=True, indent=" " * 16)
                        print("    " + "━" * 60)
                else:
                    print(f"{_dot} {name}: status: {_status} ", end="")
                    print(f"@ {_done_at} --> result: " + f"{data}")

            else:
                print(f"{_dot} {name}: status: {_status} ", end="")
                print(f"@ {_done_at} --> result: " + f"{data}")
            if debug:
                c_task = _AIOCTL_GROUP.tasks[name]
                print(f"{indent}Task: {c_task}")
                if _done_at:
                    _delta_runtime = (
                        group().tasks[name].done_at - group().tasks[name].since
                    )
                    if _SCHEDULE:
                        _delta_runtime = aioschedule.tmdelta_fmt(_delta_runtime)
                    print(f"{indent}┗━► runtime: {_delta_runtime}")

                if _SCHEDULE:
                    if name in aioschedule._AIOCTL_SCHEDULE_GROUP:
                        aioschedule.status_sc(name, debug=debug)
                print(f"{indent}┗━► args: {c_task.args}")
                print(f"{indent}┗━► kwargs:", end="")
                pprint_dict(c_task.kwargs, ind=len(f"{indent}┗━► kwargs: "))
                if traceback(name, rtn=True):
                    print(f"{indent}┗━► traceback: ", end="")
                    traceback(name)
                    print("")
            if _SCHEDULE and not debug:
                if name in aioschedule._AIOCTL_SCHEDULE_GROUP:
                    aioschedule.status_sc(name, debug=debug)
            if log and _AIOCTL_LOG:
                if (
                    _AIOCTL_GROUP.tasks[name]._is_service
                    and _AIOCTL_GROUP.tasks[name]._is_parent
                ):
                    c_task = _AIOCTL_GROUP.tasks[name]
                    _ctsks = [f"*\[{_ctsk}\]*" for _ctsk in c_task.service._child_tasks]
                    _AIOCTL_LOG.cat(grep=[f"*\[{name}\]*"] + _ctsks)
                else:
                    _AIOCTL_LOG.cat(grep=f"[{name}]")
                print("<" + "-" * 80 + ">")
        else:
            _dot = "\033[92m●\x1b[0m"
            _since_str = time.localtime(group().tasks[name].since)
            _since_delta = time.time() - group().tasks[name].since

            if _SCHEDULE:
                _since_str = aioschedule.get_datetime(_since_str)
                _since_str += f"; {aioschedule.tmdelta_fmt(_since_delta)}"
            if debug:
                if (
                    _AIOCTL_GROUP.tasks[name]._is_service
                    and _AIOCTL_GROUP.tasks[name]._is_parent
                ):
                    c_task = _AIOCTL_GROUP.tasks[name]
                    print(f"{_dot} {name} - {c_task.service.info}")
                    print(f"    Loaded: {c_task.service}")
                    print("    Active: \033[92m(active) running\x1b[0m ", end="")
                    print(f"since {_since_str} ago")
                    print(f"    Type: {c_task.service.type}")
                    print(f"    Docs: {c_task.service.docs}")

                    if hasattr(c_task.service, "show"):
                        _show = c_task.service.show()
                        print(f"    {_show[0]}:  {_show[1]}")

                    if c_task.service._child_tasks:
                        print(f"    CTasks: {len(c_task.service._child_tasks)}")
                        for _ctsk in c_task.service._child_tasks:
                            print("        ┗━► ", end="")
                            status(_ctsk, log=False, debug=True, indent=" " * 16)
                        print("    " + "━" * 60)

                else:
                    print(f"{_dot} {name}: status: \033[92mrunning\x1b[0m ", end="")
                    print(f"since {_since_str} ago")

            else:
                print(f"{_dot} {name}: status: \033[92mrunning\x1b[0m ", end="")
                print(f"since {_since_str} ago")
            if debug:
                c_task = _AIOCTL_GROUP.tasks[name]
                print(f"{indent}Task: {c_task}")
                if _SCHEDULE:
                    if name in aioschedule._AIOCTL_SCHEDULE_GROUP:
                        aioschedule.status_sc(name, debug=debug)
                print(f"{indent}┗━► args: {c_task.args}")
                print(f"{indent}┗━► kwargs:", end="")
                pprint_dict(c_task.kwargs, ind=len(f"{indent}┗━► kwargs: "))
            if _SCHEDULE and not debug:
                if name in aioschedule._AIOCTL_SCHEDULE_GROUP:
                    aioschedule.status_sc(name, debug=debug)
            if log and _AIOCTL_LOG:
                if (
                    _AIOCTL_GROUP.tasks[name]._is_service
                    and _AIOCTL_GROUP.tasks[name]._is_parent
                ):
                    c_task = _AIOCTL_GROUP.tasks[name]
                    _ctsks = [f"*\[{_ctsk}\]*" for _ctsk in c_task.service._child_tasks]
                    _AIOCTL_LOG.cat(grep=[f"*\[{name}\]*"] + _ctsks)
                else:
                    _AIOCTL_LOG.cat(grep=f"[{name}]")
                print("<" + "-" * 80 + ">")
    else:
        if "*" in name:
            for tm in tasks_match(name):
                status(tm, log=log, debug=debug)

        else:
            print(f"Task {name} not found in {list(_AIOCTL_GROUP.tasks.keys())}")


def result(name=None):
    global _AIOCTL_GROUP
    if not name:
        return result_all()

    if name in _AIOCTL_GROUP.tasks:
        if _AIOCTL_GROUP.tasks[name].task.done():
            return _AIOCTL_GROUP.tasks[name].task.data.value
    else:
        if "*" in name:
            for tm in tasks_match(name):
                print(f"{tm} --> {result(tm)}")

        else:
            print(f"Task {name} not found in {list(_AIOCTL_GROUP.tasks.keys())}")
        return


def debug():
    global _DEBUG
    _DEBUG = not _DEBUG
    print(f"debug mode: {_DEBUG}")


def result_all(as_dict=False):
    global _AIOCTL_GROUP
    if not as_dict:
        for name in _AIOCTL_GROUP.tasks.keys():
            print(f"{name} --> {result(name)}")
    else:
        return {name: result(name) for name in _AIOCTL_GROUP.tasks.keys()}


def status_all(log=True, debug=False):
    global _AIOCTL_GROUP
    for name in _AIOCTL_GROUP.tasks.keys():
        if name:
            status(name, log=log, debug=debug)


def start(name):
    global _AIOCTL_GROUP
    if name in _AIOCTL_GROUP.tasks:
        coro = _AIOCTL_GROUP.tasks[name].coro
        args = _AIOCTL_GROUP.tasks[name].args
        kwargs = _AIOCTL_GROUP.tasks[name].kwargs
        kwargs["name"] = name
        if _SCHEDULE:
            _sch = _AIOCTL_GROUP.tasks[name].schedule
            if _sch:
                aioschedule.schedule(name, **_sch)
                _AIOCTL_GROUP.tasks[name].schedule = None
                return True
        _AIOCTL_GROUP.tasks.pop(name)
        try:
            add(coro, *args, **kwargs)
        except Exception as e:
            print(e)
        return True
    else:
        if "*" in name:
            for tm in tasks_match(name):
                start(tm)
            return True
        else:
            print(f"Task {name} not found in {list(_AIOCTL_GROUP.tasks.keys())}")
        return False


def stop(name=None, stop_sch=True):
    global _AIOCTL_GROUP
    if not name:
        return stop_all()
    try:
        if name in _AIOCTL_GROUP.tasks:
            if not _AIOCTL_GROUP.tasks[name].task.done():
                _AIOCTL_GROUP.tasks[name].task.cancel()
                _AIOCTL_GROUP.tasks[name].cancelled = True

            if _SCHEDULE and stop_sch:
                if name in aioschedule.group().keys():
                    group().tasks[name].schedule = aioschedule.group().pop(name)

            _AIOCTL_GROUP.results[name] = _AIOCTL_GROUP.tasks[name].task.data
        else:
            if "*" in name:
                for tm in tasks_match(name):
                    stop(tm)
            else:
                print(f"Task {name} not found in {list(_AIOCTL_GROUP.tasks.keys())}")

    except asyncio.CancelledError:
        pass
    except RuntimeError as e:
        print(f"{e}, {name}")
        pass
    return True


def stop_all():
    global _AIOCTL_GROUP
    for name in _AIOCTL_GROUP.tasks.keys():
        stop(name)
    return True


async def follow(grep="", wait=0.05):
    global _AIOCTL_LOG

    if _AIOCTL_LOG:
        return await _AIOCTL_LOG.follow(grep=grep, wait=wait)


def log(grep=""):
    global _AIOCTL_LOG
    if _AIOCTL_LOG:
        return _AIOCTL_LOG.cat(grep=grep)


def traceback(name=None, rtn=False):
    if not name:
        return traceback_all()
    if "*" in name:
        for tm in tasks_match(name):
            traceback(tm)
        return
    _tb = result(name)
    if issubclass(_tb.__class__, Exception):
        if rtn:
            return True
        print(f"{name}: Traceback")
        sys.print_exception(_tb)
    else:
        if rtn:
            return False


def traceback_all():
    global _AIOCTL_GROUP
    for name in _AIOCTL_GROUP.tasks.keys():
        traceback(name)


def run():
    global _AIOCTL_GROUP

    async def _main():
        for name in _AIOCTL_GROUP.tasks.keys():
            start(name)
        await asyncio.gather(*tasks())

    asyncio.run(_main())


def reset(group=True, log=False):
    global _AIOCTL_GROUP, _AIOCTL_LOG

    if group:
        _AIOCTL_GROUP = None
    if log:
        _AIOCTL_LOG = None
