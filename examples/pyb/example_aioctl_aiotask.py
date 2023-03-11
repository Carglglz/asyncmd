from aiolog import streamlog
import pyb
import random
import logging
import aiorepl
import uasyncio as asyncio
import aioctl
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
    try:
        i = 10 - n
        while True:
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


async def main():
    print("starting tasks...")

    # start other program tasks.

    aioctl.add(task_led, 1, 10500, name="task_led_1", _id="task_led_1")
    aioctl.add(task_led, 2, 10400, name="task_led_2", _id="task_led_2")
    aioctl.add(task_led, 3, 10300, name="task_led_3", _id="task_led_3")
    aioctl.add(task_led, 4, 10200, name="task_led_4", _id="task_led_4")
    # start the aiorepl task.
    aioctl.add(aiorepl.task, name="repl", prompt=">>> ")

    await asyncio.gather(*aioctl.tasks())


asyncio.run(main())
