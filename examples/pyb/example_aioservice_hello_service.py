import uasyncio as asyncio
import pyb
import aiorepl
import aioctl
from aiolog import streamlog
import aioservice
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
    aioctl.add(aiorepl.task, name="repl")
    aioservice.load(debug=True, log=log, debug_log=True, config=True)

    await asyncio.gather(*aioctl.tasks())


asyncio.run(main())
