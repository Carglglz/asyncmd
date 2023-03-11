import uasyncio as asyncio
import aiorepl
import aioctl
import aioservice


async def _main(logger):
    await aioservice.boot(log=logger, debug_log=True)
    print("starting tasks...")
    aioctl.add(aiorepl.task, name="repl")
    print(">>> ")
    aioservice.init(log=logger, debug_log=True)
    print(">>> ")
    await asyncio.gather(*aioctl.tasks())


def run(logger):
    asyncio.run(_main(logger))
