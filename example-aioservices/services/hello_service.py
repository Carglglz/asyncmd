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
        self.type = "runtime.service"  # continuous running, other types are
        self.enabled = True
        self.docs = "https://github.com/Carglglz/asyncmd/blob/main/README.md"
        self.args = [2, 5]
        self.kwargs = {"on_stop": self.on_stop, "on_error": self.on_error}
        self.n_led = 1
        self.log = None
        self.loop_diff = 0
        self.n_loop = 0
        # core.service --> run one time at boot
        # schedule.service --> run and stop following a schedule

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
