import sys
import os
import gc
import aioctl
from aiolog import streamlog

aioctl.set_log(streamlog)
gc.collect()
gc.threshold(gc.mem_free() // 4 + gc.mem_alloc())


try:
    _path = __file__.rsplit("/", 1)
    if len(_path) > 1:
        sys.path.append(_path[0])
        print(_path[0])
        os.chdir(_path[0])
        sys.path.append(f"{_path[0]}/aioservices")
    import app
    from splash import MPY_BANNER

    print(MPY_BANNER)
    app.run(streamlog)
except Exception as e:
    sys.print_exception(e)
