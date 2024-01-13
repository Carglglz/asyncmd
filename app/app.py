import asyncio
import aiorepl
import logging
import sys
import aioctl


def bootloader(log):
    import os

    try:
        os.stat("./aioservices")
    except Exception:
        log.info("asyncmd bootloader setup")
        import asyncmd_boot

        asyncmd_boot.setup(log)
    try:
        os.stat("services.config")
        os.stat(".env")
    except Exception:
        from asyncmd_boot import config_setup

        log.info("asyncmd config setup")
        config_setup(log)


async def _main(logger, repl=True):
    import aioservice

    await aioservice.boot(debug=False, log=logger, debug_log=True)
    print("loading services...")
    repl = aioctl.getenv("AIOREPL", repl)
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


def run(log_stream, file_logging=False):
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

    if aioctl.getenv("FILE_LOGGING", file_logging):
        from filehandler import FileRotationHandler

        # File
        file_handler = FileRotationHandler("error.log", mode="a")
        file_handler.setLevel(getattr(logging, aioctl.getenv("FILE_LEVEL", "ERROR")))
        file_handler.setFormatter(formatter)
        log.addHandler(file_handler)

    # Sys.stdout
    sys_handler = logging.StreamHandler(stream=sys.stdout)
    sys_handler.setLevel(getattr(logging, LOGLEVEL))
    sys_handler.setFormatter(formatter)
    log.addHandler(sys_handler)

    # Bootloader
    log.info("Booting asyncmd...")
    bootloader(log)

    asyncio.run(_main(log))
