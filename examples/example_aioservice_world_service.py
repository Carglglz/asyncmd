import uasyncio as asyncio
import pyb
import aiorepl
import aioctl
from aiolog import streamlog
import aioservice
import upylog
import aioschedule

upylog.basicConfig(level="INFO", format="TIME_LVL_MSG", stream=streamlog)
log = upylog.getLogger(
    "pyb", log_to_file=False, rotate=1000
)  # This log to file 'error.log';


@aioctl.aiotask
async def task_button(log=None):
    while True:
        if pyb.Switch().value():
            pyb.LED(3).toggle()
            if log:
                log.info("[task_button] button pressed!")
        else:
            pyb.LED(3).off()
        await asyncio.sleep_ms(200)
    return True


# start the aiorepl task.


async def main():
    print("starting tasks...")
    aioctl.set_log(streamlog)
    aioctl.add(aiorepl.task, name="repl")
    aioservice.load(debug=True, log=log, debug_log=True, config=True)

    aioctl.add(aioschedule.schedule_loop, alog=None)  # must be the last one

    await asyncio.gather(*aioctl.tasks())


asyncio.run(main())
