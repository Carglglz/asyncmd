import uasyncio as asyncio
import aiorepl
import aioctl
from aiolog import streamlog
import aioservice


async def _main(logger):
    print("starting tasks...")
    aioctl.set_log(streamlog)
    aioctl.add(aiorepl.task, name="repl")
    print(">>> ")
    aioservice.init(log=logger, debug_log=True)
    print(">>> ")
    await asyncio.gather(*aioctl.tasks())
