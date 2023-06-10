import aioctl
import aioschedule
import uasyncio as asyncio
import sys
import os
from binascii import hexlify

try:
    from hostname import NAME
except Exception:
    from machine import unique_id

    NAME = f"{sys.platform}-{hexlify(unique_id())}"


async def display(taskm="*"):
    try:
        for t in aioctl.tasks_match(taskm):
            log_line = logtail(f"*\[{t}\]*")

            aioctl.status(name=t, log=False)
            if not log_line:
                print(log_line)
            else:
                print(f"┗━► {log_line}", end="")
            print("")

        while True:
            states = {name: task_status(name) for name in aioctl.tasks_match(taskm)}
            states_lines = {t: logtail(f"*\[{t}\]*") for t in aioctl.tasks_match(taskm)}

            await asyncio.sleep(1)
            states_now = {name: task_status(name) for name in aioctl.tasks_match(taskm)}
            states_lines_now = {
                t: logtail(f"*\[{t}\]*") for t in aioctl.tasks_match(taskm)
            }
            for st in states_now:
                if st not in states:
                    states[st] = states_now[st]
            clean = "\r"
            for st in states_lines_now:
                if st not in states_lines:
                    states_lines[st] = states_lines_now[st]
            # Set right height
            for t in aioctl.tasks_match(taskm):
                clean += "\033[A" * 3
                if t in aioschedule.group():
                    if aioschedule.group()[t]["repeat"]:
                        clean += "\033[A"

                    elif aioschedule.group()[t]["start_in"] >= 0:
                        clean += "\033[A"

            clean += "\033[K"
            print(clean, end="")

            for t in aioctl.tasks_match(taskm):
                if states_now[t] != states[t]:
                    print("\033[K", end="")

                if t in aioschedule.group():
                    if aioschedule.group()[t]["repeat"]:
                        print("\n\033[K\r\033[A", end="")

                    elif aioschedule.group()[t]["start_in"] >= 0:
                        print("\n\033[K\r\033[A", end="")
                log_line = states_lines_now[t]

                aioctl.status(name=t, log=False)

                if log_line != states_lines[t]:
                    print("\033[K\r", end="")

                if not log_line:
                    print(log_line)
                else:
                    print(f"┗━► {log_line}", end="")
                print("")
    except Exception as e:
        sys.print_exception(e)


def task_status(name):
    _status = "running"
    if name not in aioctl.group().tasks:
        return "unknown"
    if aioctl.group().tasks[name].task.done():
        _status = "done"
        if aioctl.group().tasks[name].cancelled:
            _status = "stopped"
        if name in aioschedule.group():
            if aioschedule.group()[name]["start_in"] != -1:
                _status = "scheduled"
            if aioschedule.group()[name]["repeat"]:
                _status = f"scheduled - {_status}"
        data = aioctl.result(name)

        if issubclass(data.__class__, Exception):
            _status = "error"

    return _status


def logtail(grep="", log=aioctl._AIOCTL_LOG):
    last_line = ""
    index = log.tell()
    if log._comp:
        log.readline()
    if grep:
        for line in log:
            if (
                line
                and ("*" in grep or isinstance(grep, list))
                and log._grep(grep, line)
            ):
                last_line = line
            elif isinstance(grep, str):
                if grep in line:
                    last_line = line
    else:
        for line in log:
            if line.strip():
                last_line = line

    log.seek(0)
    # read and grep for regex
    if grep:
        for line in log:
            if (
                line
                and ("*" in grep or isinstance(grep, list))
                and log._grep(grep, line)
            ):
                last_line = line

            elif isinstance(grep, str):
                if grep in line:
                    last_line = line
            if log.tell() >= index:
                log.seek(index)
                return last_line
    else:
        for line in log:
            if line.strip():
                last_line = line
            if log.tell() >= index:
                log.seek(index)
                return last_line
    log.seek(index)
    return last_line


# stats/metrics --> like aioctl.status but dict/parseable format -->
# forward/export data to external services
# stats.service (alternative to using aiorepl for remote/automate debugging)
# {service}.stats() --> name, info, state, ts, runtime, type, ctasks, custom_stats,
# schedule, args, kwargs, log
# --> json api exporting aioctl status + metrics data.
# --> mqtt publisher exporting aioctl status + metrics data.
# --> time series database (influx) publisher --> aioctl status + metrics data


def stats(taskm="*", debug=False):
    _stats = {}
    for task in aioctl.tasks_match(taskm):
        task_stats = {
            "status": task_status(task),
            "result": aioctl.result(task),
            "done_at": aioctl.group().tasks[task].done_at,
            "since": aioctl.group().tasks[task].since,
            "service": aioctl.group().tasks[task]._is_service,
        }
        if issubclass(task_stats["result"].__class__, Exception):
            task_stats["result"] = (
                f"{task_stats['result'].__class__.__name__}:"
                + f"{task_stats['result'].value}"
            )
        if task_stats["service"]:
            if hasattr(aioctl.group().tasks[task].service, "stats"):
                task_stats["stats"] = aioctl.group().tasks[task].service.stats()
            else:
                task_stats["stats"] = None
            if debug and debug == "/debug":

                task_stats["log"] = logtail(grep=task),
                task_stats["ctasks"] = list(
                    aioctl.group().tasks[task].service._child_tasks
                )
                task_stats["docs"] = aioctl.group().tasks[task].service.docs
                task_stats["type"] = aioctl.group().tasks[task].service.type
                task_stats["path"] = aioctl.group().tasks[task].service.path
                task_stats["info"] = aioctl.group().tasks[task].service.info
                task_stats["args"] = aioctl.group().tasks[task].service.args
                task_stats["kwargs"] = {
                    k: str(v)
                    for k, v in aioctl.group().tasks[task].service.kwargs.items()
                }

        _stats[task] = task_stats
    _stats["hostname"] = NAME
    return _stats


async def pipelog(client, topic, from_idx=None, log=aioctl._AIOCTL_LOG):
    index = log.tell()
    try:
        if log._comp:
            log.readline()
        if from_idx is None:
            for line in log:
                if line.strip():
                    await client.publish(topic, line.encode("utf-8"))

            log.seek(0)
            # read and grep for regex
            for line in log:
                if line.strip():
                    await client.publish(topic, line.encode("utf-8"))
                if log.tell() >= index:
                    log.seek(index)
                    return
        else:
            log.seek(from_idx)
            log.readline()
            if index <= from_idx:  # log rotated
                for line in log:
                    if line.strip():
                        await client.publish(topic, line.encode("utf-8"))

                log.seek(0)
                # read and grep for regex
                for line in log:
                    if line.strip():
                        await client.publish(topic, line.encode("utf-8"))
                    if log.tell() >= index:
                        log.seek(index)
                        return
            elif index > from_idx:
                for line in log:
                    if line.strip():
                        await client.publish(topic, line.encode("utf-8"))
                    if log.tell() >= index:
                        log.seek(index)
                        return
    except Exception as e:
        log.seek(index)
        raise e


async def pipefile(client, topic, file):
    try:
        os.stat(file)
    except Exception:
        return

    with open(file, "r") as pfile:
        for line in pfile:
            if line.strip():
                await client.publish(topic, line.encode("utf-8"))
