import gc
import sys

sys.path.append("..")
sys.path.append("../tools")

import aioctl
from aiolog import streamlog

aioctl.set_log(streamlog)
gc.collect()
gc.threshold(gc.mem_free() // 4 + gc.mem_alloc())


try:
    import app
    from splash import MPY_BANNER

    print(MPY_BANNER)
    app.run(streamlog)
except Exception as e:
    sys.print_exception(e)
