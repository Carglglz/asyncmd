import uasyncio as asyncio
import pyb
import aiorepl
import aioctl
import random
import upylog
from aiolog import streamlog


upylog.basicConfig(level="INFO", format="TIME_LVL_MSG", stream=streamlog)
log = upylog.getLogger(
    "pyb", log_to_file=False, rotate=1000
)  # This log to file 'error.log';


aioctl.set_log(streamlog)


@aioctl.aiotask
async def task_led(n, t, log=None):
    i = 10 - n
    while True:
        await asyncio.sleep_ms(t)
        pyb.LED(n).toggle()
        await asyncio.sleep_ms(50)
        pyb.LED(n).toggle()
        if log:
            log.info(f"[task_led_{n}] toggled LED {n}")
        if n > 3:
            i = round(i / (i - 1))
    pyb.LED(n).off()
    return random.random()


@aioctl.aiotask
async def task_button(log=None):
    while True:
        if pyb.Switch().value():
            pyb.LED(3).toggle()
            if log:
                log.info("[task_button] button pressed!")
        else:
            pyb.LED(3).off()
        await asyncio.sleep_ms(200)
    return True


async def main():
    print("starting tasks...")
    aioctl.add(task_led, 2, 5000, name="task_led_2", _id="task_led_2", log=log)
    aioctl.add(task_button, log=log)
    aioctl.add(aiorepl.task, name="repl", prompt=">>> ")

    await asyncio.gather(*aioctl.tasks())


asyncio.run(main())
