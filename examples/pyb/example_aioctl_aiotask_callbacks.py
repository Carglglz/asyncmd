from aiolog import streamlog
import pyb
import random
import aiorepl
import uasyncio as asyncio
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


aioctl.set_log(streamlog)


@aioctl.aiotask
async def task_led(n, t, alog=log):
    i = 10 - n
    while True:
        await asyncio.sleep_ms(t)
        pyb.LED(n).toggle()
        await asyncio.sleep_ms(50)
        pyb.LED(n).toggle()
        alog.info(f"[task_led_{n}] toggled LED {n}")
        if n > 3:
            i = round(i / (i - 1))


def _stop_cb(n, t, alog=log):
    pyb.LED(n).off()
    alog.info(f"[task_led_{n}] stopped")
    return random.random()


def _error_cb(e, n, t, alog=log):
    pyb.LED(n).off()
    return e


async def main():
    print("starting tasks...")

    # start other program tasks.

    aioctl.add(
        task_led,
        1,
        10500,
        name="task_led_1",
        _id="task_led_1",
        on_stop=_stop_cb,
        on_error=_error_cb,
    )
    aioctl.add(
        task_led,
        2,
        10400,
        name="task_led_2",
        _id="task_led_2",
        on_stop=_stop_cb,
        on_error=_error_cb,
    )
    aioctl.add(
        task_led,
        3,
        10300,
        name="task_led_3",
        _id="task_led_3",
        on_stop=_stop_cb,
        on_error=_error_cb,
    )
    aioctl.add(
        task_led,
        4,
        10200,
        name="task_led_4",
        _id="task_led_4",
        on_stop=_stop_cb,
        on_error=_error_cb,
    )
    # start the aiorepl task.
    aioctl.add(aiorepl.task, name="repl", prompt=">>> ")

    await asyncio.gather(*aioctl.tasks())


asyncio.run(main())
