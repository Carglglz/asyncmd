
# Documentation for `aioschedule`

## Introduction

`aioschedule` is a lazy implementation of an asynchronous scheduling library that allows you to schedule tasks to run at specific times or intervals. It is designed to work with `aioctl`.


## Usage

### `@aioschedule.schedule_task`

This decorator is used to mark a function as a scheduled task and add it to the
schedule group. The function should be a coroutine, and be used in conjunction
with `@aioctl.aiotask`. It takes `start_in` and `repeat` as keyword arguments.
`start_in` indicates start time (since event loop start) and accepts seconds (`int`) or a time tuple, and `repeat` accepts seconds (`int`) or `False`
,e.g.
```python
import aioctl
import aioschedule

@aioschedule.schedule_task(start_in=10, repeat=60) # decorators should be used in this order
@aioctl.aiotask
async def my_task(var):
    print(f"Hello, {var}!")
    ....
```
Which will schedule the task to start in 10 seconds from event loop start and
repeat it every minute.

### `aioschedule.schedule`

The `aioschedule.schedule` function is used to schedule a task to run at a specific time or interval indicating the name of the task (which should be present in `aioctl.group()`)
e.g.

```python
import aioschedule
import aioctl
import time


@aioctl.aiotask
async def my_task(var):
    print("Hello, {var}!")

aioctl.add(my_task, "Foo", name="greeting")

# Schedule the task to run every 30 seconds
aioschedule.schedule("greeting", start_in=time.localtime(time.time() + 20), repeat=30)
```

### `aioschedule.unschedule`

The `aioschedule.unschedule` function is used to unschedule a task that has been previously scheduled.

```python

# Unscheduled the task
aioschedule.unschedule("greetings")
```

### `schedule_loop`

The `schedule_loop` is the task that runs the scheduling loop. This task should be should added to `aioctl` too.

```python
aioctl.add(aioschedule.schedule_loop)
```

### `watcher_loop`

The `watcher_loop` task is used to run the watcher loop. This tasks iterates over `aioctl.result()` task's result catching and registering errors and then it restarts the failing task, effectively adding a layer of resilience to the asyncio application.

e.g. a full example using `aioschedule` would be:

```python
import aioctl
import aioschedule
import uasyncio as asyncio
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


@aioschedule.schedule_task(start_in=10, repeat=120)
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
    # start the watcher task
    aioctl.add(aioschedule.watcher_loop)
    # start the scheduler task
    aioctl.add(aioschedule.schedule_loop)

    await asyncio.gather(*aioctl.tasks())


asyncio.run(main())
```

```
>>> import aioctl
>>> aioctl.status()
● repl: status: running since 2023-03-29 12:06:47; 1 s ago
<-------------------------------------------------------------------------------->
● test: status: scheduled @ 2023-03-29 12:06:49 --> result:
    ┗━► schedule: starts in 10 s @ 2023-03-29 12:06:59
<-------------------------------------------------------------------------------->
● test_from: status: scheduled @ 2023-03-29 12:06:52 --> result:
    ┗━► schedule: starts in 20 s @ 2023-03-29 12:07:12
<-------------------------------------------------------------------------------->
● watcher_loop: status: running since 2023-03-29 12:06:47; 1 s ago
<-------------------------------------------------------------------------------->
● schedule_loop: status: running since 2023-03-29 12:06:47; 1 s ago
<-------------------------------------------------------------------------------->


```

