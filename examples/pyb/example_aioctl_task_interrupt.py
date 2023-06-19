from aiolog import streamlog
import pyb
import random
import aiorepl
import asyncio
import aioctl
import logging
import sys


# Logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=streamlog,
)

log = logging.getLogger(sys.platform)


state = 20
aioctl.set_log(streamlog)
sw = pyb.Switch()
_TOGGLE_AIOREPL = False


def start_aiorepl_cb(x=None):
    global _TOGGLE_AIOREPL

    _TOGGLE_AIOREPL = not _TOGGLE_AIOREPL


sw.callback(start_aiorepl_cb)


def toggle_sysprint():
    log.handlers[0].stream = sys.stderr


@aioctl.aiotask
async def dbg_repl():
    await aiorepl.task(prompt=">>> ", shutdown_on_exit=False, exit_cb=toggle_sysprint)


@aioctl.aiotask
async def start_aiorepl():
    global _TOGGLE_AIOREPL
    while True:
        if _TOGGLE_AIOREPL:
            _TOGGLE_AIOREPL = not _TOGGLE_AIOREPL

            if "repl" not in aioctl.group().tasks:
                aioctl.add(dbg_repl, name="repl")
            else:
                if aioctl.group().tasks["repl"].task.done():
                    log.handler[0].stream = streamlog
                    aioctl.start("repl")
                else:
                    print("aiorepl is running...")
        await asyncio.sleep_ms(200)


@aioctl.aiotask
async def task_led(n, t, alog=log):
    try:
        i = 10 - n
        while state:
            # print("task 1")
            await asyncio.sleep_ms(t)
            pyb.LED(n).toggle()
            await asyncio.sleep_ms(50)
            pyb.LED(n).toggle()
            alog.info(f"[task_led_{n}] toggled LED {n}")
            if n > 3:
                i = round(i / (i - 1))
        pyb.LED(n).off()
        return random.random()
    except asyncio.CancelledError:
        pyb.LED(n).off()
        return random.random()
    except Exception as e:
        log.error(
            f"[task_led_{n}]" + f" {e.__class__.__name__}: {e.errno}",
        )
        pyb.LED(n).off()
        return e


_watcher_loop = aioctl.aioschedule.watcher_loop


@aioctl.aiotask
async def watcher_loop(alog=log):
    await _watcher_loop(alog=alog)


async def main():
    print("starting tasks...")

    # start other program tasks.

    aioctl.add(task_led, 1, 10500, name="task_led_1", _id="task_led_1")
    aioctl.add(task_led, 2, 10400, name="task_led_2", _id="task_led_2")
    aioctl.add(task_led, 3, 10300, name="task_led_3", _id="task_led_3")
    aioctl.add(task_led, 4, 10200, name="task_led_4", _id="task_led_4")
    # start the aiorepl task.
    # aioctl.add(aiorepl.task, name="repl", prompt=">>> ")
    # start the aiorepl toggle task
    aioctl.add(start_aiorepl, name="aiotoggle")
    aioctl.add(watcher_loop, alog=log)

    await asyncio.gather(*aioctl.tasks())


asyncio.run(main())
