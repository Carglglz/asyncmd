import asyncio
import pyb
import aiorepl
import aioctl
import random
from aiolog import streamlog


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


# start the aiorepl task.


async def main():
    print("starting tasks...")
    aioctl.set_log(streamlog)
    aioctl.add(aiorepl.task, name="repl", prompt=">>> ")

    await asyncio.gather(*aioctl.tasks())


asyncio.run(main())
