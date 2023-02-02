import uasyncio as asyncio
import aiorepl
import aioctl
from aiolog import streamlog
import aioservice
import upylog

upylog.basicConfig(level="INFO", format="TIME_LVL_MSG", stream=streamlog)
log = upylog.getLogger(
    "esp32", log_to_file=False, rotate=1000
)  # This log to file 'error.log';


# start the aiorepl task.


async def main():
    print("starting tasks...")
    aioctl.set_log(streamlog)
    aioctl.add(aiorepl.repl, name="repl")
    aioservice.load("hello", debug=True, log=log, debug_log=True, config=False)

    await asyncio.gather(*aioctl.tasks())


asyncio.run(main())
