import asyncio
import aiorepl
import aioservice
from hostname import NAME
import logging
import sys
import aioctl


async def _main(logger, repl=False):
    await aioservice.boot(log=logger, debug_log=True)
    print("starting tasks...")
    if repl:
        aioctl.add(aiorepl.task, name="repl")
    print(">>> ")
    aioservice.init(log=logger, debug_log=True)
    print(">>> ")
    if not repl:
        asyncio.create_task(aioctl.follow())
    await asyncio.gather(*aioctl.tasks())


def run(log_stream, repl=False):
    # Logger
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=log_stream,
    )

    log = logging.getLogger(f"{sys.platform}@{NAME}")
    formatter = logging.Formatter("%(asctime)s [%(name)s] [%(levelname)s] %(message)s")
    # Stream
    stream_handler = logging.StreamHandler(stream=log_stream)
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(formatter)
    log.addHandler(stream_handler)

    log.info("Device Ready")

    asyncio.run(_main(log, repl=repl))
