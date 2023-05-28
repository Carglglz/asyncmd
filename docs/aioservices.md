
### aioservices 


Conventions for *aioservices*[^1] 

Consider `hello_service.py` as an example that meets the following conventions:

```python
import uasyncio as asyncio
import pyb
import aioctl
from aioclass import Service
import random
import time


class HelloService(Service):
    def __init__(self, name):
        super().__init__(name)
        self.info = "Hello example runner v1.0"
        self.type = "runtime.service"  
        self.enabled = True
        self.docs = "https://github.com/Carglglz/asyncmd/blob/main/README.md"
        self.args = [2, 5]
        self.kwargs = {"on_stop": self.on_stop, "on_error": self.on_error}
        self.n_led = 1
        self.log = None
        self.loop_diff = 0
        self.n_loop = 0

    def show(self):
        _stat_1 = f"   Temp: {25+random.random()} C"
        _stat_2 = f"   Loop info: exec time: {self.loop_diff} ms;"
        _stat_2 += f" # loops: {self.n_loop}"
        return "Stats", f"{_stat_1}{_stat_2}"  # return Tuple, "Name",
        # "info" to display

    def on_stop(self, *args, **kwargs):  # same args and kwargs as self.task
        res = random.random()
        if self.log:
            self.log.info(f"[hello.service] stopped result: {res}")
        return res

    def on_error(self, e, *args, **kwargs):
        if self.log:
            self.log.error(f"[hello.service] Error callback {e}")
        return e

    @aioctl.aiotask
    async def task(self, n, s, log=None):
        self.log = log
        count = 12
        self.n_led = n
        while True:
            t0 = time.ticks_ms()
            pyb.LED(self.n_led).toggle()
            asyncio.sleep_ms(200)
            pyb.LED(self.n_led).toggle()
            if log:
                log.info(f"[hello.service] LED {self.n_led} toggled!")

            if self.n_led > 3:
                count -= self.n_led
            try:
                res = s / count
            except Exception as e:
                raise random.choice([e, ValueError])
            self.loop_diff = time.ticks_diff(time.ticks_ms(), t0)
            self.n_loop += 1
            self.n_led = random.choice([1, 2, 3, 4])
            await asyncio.sleep(s)


service = HelloService("hello")

```

- Inherit from `aioclass.Service`, i.e requires `aioclass.py`
- File name *xxx_service.py* or frozen as *xxx_service.mpy*
- Attributes:
    - info: --> brief description of the service .e.g "Hello example runner v1.0" 
    - type: --> {*core.service*, *runtime.service*, *schedule.service*}[^2]
    - enabled: --> if enabled by default, should be loaded by service
      discovery and *aioservice.boot* or *aioservice.init*
    - docs: --> reference link for documentation about a service.
    - args: --> args that will be passed to `HelloService.task`
    - kwargs: --> kwargs that will be passed to `HelloService.task`
    - log: --> variable to store the logger class. 
    - custom (optional) --> other variables to store info about the service
      .e.g. `loop_diff` --> measure loop execution time, `n_loop` counts how
      many loops, etc.

- Methods:
    - show method: (optional) --> display custom information about the service
      when explored by *aioctl.status* in *debug* mode
    - report method: (optional) --> return a report of service
      status/info/result (used by *devop.service*)
    - stats method: (optional) --> return service's custom info/stats as *dict* (used by *stats.service*)
    - `__call__` method: (optional) --> make a service callable and return service's custom info (used by *aioservice.service("name")()*)
    - on_stop method callback: --> method to call when service main task is
      stopped.
    - on_error method callback: --> method to call when main task throws an
      error.
    - method named task and decorated with *`@aioctl.aiotask`*: service's main *async* task 
    - (optional) *aiotask* decorated child tasks created by main task.

- declare e.g. service = HelloService("hello")
- placed in `aioservices/services` for service discovery.

aioservice discovery/loader --> `aioservices/services/__init__.py`
will discover available services and load them if enabled when using `aioservice.init` or `aioservice.boot`



how to create child tasks

how to use aioservice.init --> runtime/schedule services 

how to use aioservice.boot --> core services 

in async main task


### Notes 

[^1]: check in `aioservice-examples/` service  `hello_service.py` or `world_service.py` as template).
[^2]: check *aioservice* documentation to see what each type means.

