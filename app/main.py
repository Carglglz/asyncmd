import wss_repl  # noqa
import gc  # noqa
import sys
import machine
import aioctl
from aiolog import streamlog

aioctl.set_log(streamlog)
gc.collect()
gc.threshold(gc.mem_free() // 4 + gc.mem_alloc())

machine.freq(240000000)

try:
    import app

    app.run(streamlog)
except Exception as e:
    sys.print_exception(e)
