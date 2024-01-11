import gc
import sys
import machine
import aioctl
from aiolog import streamlog

aioctl.set_log(streamlog)
gc.collect()
gc.threshold(gc.mem_free() // 4 + gc.mem_alloc())

mf = machine.freq()
if isinstance(mf, tuple):
    mf = mf[0]
machine.freq(aioctl.getenv("MACHINE_FREQ", mf))

try:
    import app

    try:
        from splash import MPY_BANNER

        print(MPY_BANNER)
    except Exception:
        pass

    app.run(streamlog)
except Exception as e:
    sys.print_exception(e)
