import wss_repl
from machine import Pin
from hostname import NAME
import upylog
import sys
from aiolog import streamlog
import aioctl


aioctl.set_log(streamlog)
# Logger
upylog.basicConfig(level="INFO", format="TIME_LVL_MSG", stream=streamlog)
log = upylog.getLogger(
    f"{sys.platform}@{NAME}",
    log_to_file=False,
    rotate=5000,
)
log.setLogfileLevel("ERROR")
# LED
led = Pin(2, Pin.OUT)
log.info(f"Device Ready at {log.get_datetime()}")

try:
    import app

    app.run(log)
except Exception as e:
    log.error(e)
    sys.print_exception(e)
