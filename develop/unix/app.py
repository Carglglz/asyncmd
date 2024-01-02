import asyncio
import aiorepl
import logging
import sys
import aioctl


def bootloader(log):
    import os

    try:
        os.stat("./aioservices")
        return
    except Exception:
        log.info("asyncmd bootloader setup")

    import asyncmd_boot

    asyncmd_boot.setup(log)
    asyncmd_boot.config_setup(log)


async def _main(logger):
    import aioservice

    await aioservice.boot(debug=False, log=logger, debug_log=True)
    print("loading services...")

    repl = aioctl.getenv("AIOREPL", False)
    if repl:
        aioctl.add(aiorepl.task, name="repl")
        print(">>> ")
    sys_handler = False
    for i, handler in enumerate(logger.handlers):
        if isinstance(handler, logging.StreamHandler):
            if handler.stream == sys.stdout:
                sys_handler = logger.handlers.pop(i)
    aioservice.init(log=logger, debug_log=True)
    if not repl and sys_handler:
        logger.addHandler(sys_handler)

    await asyncio.gather(*aioctl.tasks())


def run(log_stream):
    # Logger
    NAME = aioctl.getenv("HOSTNAME", sys.platform, debug=True)
    LOGLEVEL = aioctl.getenv("LOGLEVEL", "INFO")
    logging.basicConfig(
        level=getattr(logging, LOGLEVEL),
        format="%(asctime)s [%(name)s] [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=log_stream,
    )

    log = logging.getLogger(f"{sys.platform}@{NAME}")
    formatter = logging.Formatter("%(asctime)s [%(name)s] [%(levelname)s] %(message)s")

    # Stream
    stream_handler = logging.StreamHandler(stream=log_stream)
    stream_handler.setLevel(getattr(logging, LOGLEVEL))
    stream_handler.setFormatter(formatter)
    log.addHandler(stream_handler)

    # Sys.stdout
    sys_handler = logging.StreamHandler(stream=sys.stdout)
    sys_handler.setLevel(getattr(logging, LOGLEVEL))
    sys_handler.setFormatter(formatter)
    log.addHandler(sys_handler)

    # Bootloader
    log.info("Booting asyncmd...")
    bootloader(log)

    # App
    asyncio.run(_main(log))
