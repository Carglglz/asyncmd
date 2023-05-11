import uasyncio as asyncio
import pyb
import aioctl
from aioclass import Service
import random
from machine import Pin


class PIRService(Service):
    def __init__(self, name):
        super().__init__(name)
        self.version = "1.0"
        self.info = f"PIR service v{self.version}"
        self.type = "runtime.service"  # continuous running, other types are
        self.enabled = True
        self.docs = "https://github.com/Carglglz/asyncmd/blob/main/README.md"
        self.args = ["X1", 3]
        self.kwargs = {"on_stop": self.on_stop, "on_error": self.on_error}
        self.log = None
        self.n_loop = 0
        self._state = 0
        # core.service --> run one time at boot
        # schedule.service --> run and stop following a schedule

    def show(self):
        _stat_1 = f"   Events: {self.n_loop}"
        return "Stats", _stat_1
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
    async def task(self, pin, led, log=None):
        self.pir = Pin(pin, Pin.IN)
        while True:
            state = self.pir.value()
            if state and not self._state:
                pyb.LED(led).on()
                self.n_loop += 1
                if log:
                    log.info(f"[{self.name}.service] Motion detected!")
            else:
                if not state:
                    pyb.LED(led).off()
            self._state = state
            await asyncio.sleep_ms(200)
        return True


service = PIRService("pir")
