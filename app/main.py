import logging
import sys
from aiolog import streamlog
import aioctl

try:
    from hostname import NAME
except Exception:
    NAME = "mpy"


aioctl.set_log(streamlog)
# Logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=streamlog,
)

log = logging.getLogger(f"{sys.platform}@{NAME}")

log.info("Device Ready")


try:
    import app

    app.run(log)
except Exception as e:
    log.error(e)
    sys.print_exception(e)
