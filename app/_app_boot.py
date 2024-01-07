import os

if "main.py" not in os.listdir():
    _main_py = """import gc
import sys
import machine
import aioctl
from aiolog import streamlog

aioctl.set_log(streamlog)
gc.collect()
gc.threshold(gc.mem_free() // 4 + gc.mem_alloc())

machine.freq(aioctl.getenv("MACHINE_FREQ", machine.freq()))

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
    """
    with open("main.py", "w") as main:
        main.write(_main_py)
