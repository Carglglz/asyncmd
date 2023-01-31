import uasyncio as asyncio
import pyb
import aioctl
from aioclass import Service
import random


class HelloService(Service):
    def __init__(self, name):
        super().__init__(name)
        self.info = "Hello example runner v1.0"
        self.type = "runtime.service"  # continuous running, other types are
        self.enabled = True
        self.docs = "https://github.com/Carglglz/mpy-wpa_supplicant/blob/main/README.md"
        self.args = [2, 5]
        self.kwargs = {"on_stop": self.on_stop, "on_error": self.on_error}
        self.n_led = 1
        self.log = None
        # core.service --> run one time at boot
        # schedule.service --> run and stop following a schedule

    def show(self):
        return "Temp", f"{25+random.random()} C"  # return Tuple, "Name",
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
            pyb.LED(self.n_led).toggle()
            asyncio.sleep_ms(200)
            pyb.LED(self.n_led).toggle()
            if log:
                log.info(f"[hello.service] LED {self.n_led} toggled!")

            await asyncio.sleep(s)
            if self.n_led > 3:
                count -= self.n_led
            res = s / count


service = HelloService("hello")
