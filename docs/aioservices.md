
### Documentation for aioservices 


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
- Attributes:
    - info: --> brief description of the service .e.g "Hello example runner v1.0" 
    - type: --> {*core.service*, *runtime.service*, *schedule.service*}[^2]
    - enabled: --> if enabled by default, should be loaded by service
      discovery and *aioservice.boot* or *aioservice.init*
    - docs: --> reference link for documentation about a service.
    - args: --> args that will be passed to `HelloService.task`
    - kwargs: --> kwargs that will be passed to `HelloService.task`
    - log: --> variable to store the logger class. 
    - schedule (optional): --> to indicate the main task schedule (for a
      *schedule* service). The schedule can be configured using `schedule`
      key in `kwargs` too.
    - custom (optional): --> other variables to store info about the service
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

- declare e.g. `service = HelloService("hello")`
- file name *xxx_service.py* or frozen as *xxx_service.mpy*
- placed in `aioservices/services` for service discovery.

*aioservice* discovery/loader --> `aioservices/services/__init__.py`
will discover available services and load them if enabled when using `aioservice.init` which
load *runtime* or *schedule* services or `aioservice.boot` which will load
*core* services.

#### Type of services
- `runtime`: the service will be loaded by `aioservice.init` and its main task will run continuously i.e. in
  a `while loop`. (see reference service `hello_service.py`) 
- `schedule`: the service will be loaded by `aioservice.init` and scheduled to
  run following its configured schedule. (see reference service
  `world_service.py`)

- `core`: the service will be loaded by `aioservice.boot` and its main task is
  expected to run just once and return. (see reference service
  `network_service.py`)

`core` services are intended to be run first and they will be run in order/sequentially
if the are any dependency requirements indicated or "asynchronously" otherwise.
They are used to setup or check a device state, .e.g setup a network (WiFi)
connection.

`schedule` and `runtime` services are loaded "asynchronously" after all `core`
services are done.

`schedule` services are intended to run every X seconds and can be used to
check and reset a device state, .e.g check network connection every minute and
reconnect if disconnected. 

`runtime` service are intended to run continuously, .e.g send a message every
5 seconds, waiting for an event and run a callback...


#### Child Tasks (CTasks)
It is also possible to add secondary tasks to a service. To do 
this the *service's main task* is where this secondary tasks are added.
For reference see `network_service.py` or more advanced examples in the *mqtt*
services .e.g `aiomqtt_service.py` or `aiomqtt_sensor_bme280_service.py`.

Consider `network_service.py` where the main task that setups a network
connection, adds a child task that setups the `WebREPL`

```python

    @aioctl.aiotask
    async def task(
        self,
        timeout=10,
        hostname=NAME,
        notify=True,
        log=None,
        led=None,
        webrepl_on=True,
    ):
        self.log = log
        if led:
            self.led = Pin(led, Pin.OUT)

        connected = await self.setup_network(
            timeout=timeout, hostname=hostname, notify=True
        )
        if connected:
            settime()
        else:
            await self.setup_ap()

        if webrepl_on:
            aioctl.add(
                self.webrepl_setup,
                self,
                name=f"{self.name}.service.webrepl",
                _id=f"{self.name}.service.webrepl",
            )

        for i in range(10):
            self.led.value(not self.led.value())
            await asyncio.sleep(0.2)
        self.led.value(False)

        if connected:
            return "WLAN: ENABLED"
        else:
            return "AP: ENABLED"

    @aioctl.aiotask
    async def webrepl_setup(self, *args, **kwargs):
        import webrepl

        webrepl.start()
        if self.log:
            self.log.info(f"[{self.name}.service.webrepl] WebREPL setup done")

        return "WEBREPL: ENABLED"



```

Where the child task is added here: 

```python
        if webrepl_on:
            aioctl.add(
                self.webrepl_setup, # --> child task as decorated async aioctl.aiotask
                self, # -->  service as first argument to be added as a child task
                name=f"{self.name}.service.webrepl", # name following [service_name].service.[child_task_name] convention
                _id=f"{self.name}.service.webrepl",
            )


```

*child task naming convention recommended* is
`{service_name}.service.{child_task_name}`, e.g. `network.service.webrepl`



### Notes 

[^1]: check in `aioservice-examples/` service  `hello_service.py` or `world_service.py` as template.
[^2]: type is used by `aioservice.init`/`aioservice.boot` to know which
    services to load.
