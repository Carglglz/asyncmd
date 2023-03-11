import uasyncio as asyncio
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


# start the aiorepl task.


async def main():
    print("starting tasks...")
    aioctl.set_log(streamlog)
    aioctl.add(aiorepl.task, name="repl")
    aioservice.load("hello", debug=True, log=log, debug_log=True, config=False)

    await asyncio.gather(*aioctl.tasks())


asyncio.run(main())
