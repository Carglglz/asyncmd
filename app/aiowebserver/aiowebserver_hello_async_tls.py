import uasyncio as asyncio
import aiorepl
import aioctl
from aiolog import streamlog
import aioservice

# import upylog

# import aioschedule

# upylog.basicConfig(level="INFO", format="TIME_LVL_MSG", stream=streamlog)
# log = upylog.getLogger(
#     "gk32", log_to_file=False, rotate=1000
# )  # This log to file 'error.log';


async def _main(logger):
    print("starting tasks...")
    aioctl.set_log(streamlog)
    aioctl.add(aiorepl.repl)
    # aioservice.load(debug=True, log=log, debug_log=True, config=True)
    print(">>> ")
    aioservice.init(log=logger, debug_log=True)
    print(">>> ")

    # aioctl.add(aioschedule.schedule_loop, alog=None)  # must be the last one

    await asyncio.gather(*aioctl.tasks())
