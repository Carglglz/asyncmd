import aioctl
import aioschedule
import uasyncio as asyncio
import sys


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
        return "done"
    if aioctl.group().tasks[name].task.done():
        _status = "done"
        if aioctl.group().tasks[name].cancelled:
            _status = "stopped"
        if name in aioschedule.group():
            if aioschedule.group()[name]["start_in"] != -1:
                _status = "scheduled"
            if aioschedule.group()[name]["repeat"]:
                _status = f"scheduled - {_status}"
        if name not in aioctl.group().results:
            return "done"
        data = aioctl.group().results[name]
        if hasattr(data, "value"):
            if issubclass(data.value.__class__, Exception):
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
