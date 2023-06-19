import aioctl
import aioschedule
import asyncio
import aiorepl
from aiolog import streamlog
import logging
import sys
import time


# Logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=streamlog,
)

log = logging.getLogger(sys.platform)


aioctl.set_log(streamlog)


@aioschedule.schedule_task(start_in=10, repeat=3600 * 25)
@aioctl.aiotask
async def test(a, b=1, alog=log, logid=""):
    if not logid:
        logid = "test"
    await asyncio.sleep_ms(100)
    alog.info(f"[{logid}] start: hello {a}, {b}")
    t0 = time.time()
    while (time.time() - t0) < 5:
        await asyncio.sleep(2)
    alog.info(f"[{logid}] done: hello {a}, {b}")
    return 42


async def main():
    print("starting tasks...")

    # start other program tasks.
    aioctl.add(test, "world", b=10)
    aioctl.add(test, "from", b=20, name="test_from", _id="test_from", logid="test_from")
    aioschedule.schedule(
        "test_from", start_in=time.localtime(time.time() + 20), repeat=30
    )
    # start the aiorepl task.
    aioctl.add(aiorepl.task, name="repl", prompt=">>> ")
    # start the aiorepl toggle task
    aioctl.add(aioschedule.schedule_loop, alog=None)

    await asyncio.gather(*aioctl.tasks())


asyncio.run(main())
