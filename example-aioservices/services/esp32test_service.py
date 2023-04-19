import uasyncio as asyncio
from machine import Pin
import aioctl
from aioclass import Service
from async_base_animations import _loadnpxy


anm = _loadnpxy(18, 71, timing=(400, 850, 850, 400))


class HelloService(Service):
    def __init__(self, name):
        super().__init__(name)
        self.info = "Hello example runner v1.0"
        self.type = "runtime.service"  # continuous running, other types are
        self.enabled = True
        self.docs = "https://github.com/Carglglz/asyncmd/blob/main/README.md"
        self.args = [(20, 25, 0), 20]
        self.kwargs = {"loops": 2}
        # core.service --> run one time at boot
        # schedule.service --> run and stop following a schedule

    @aioctl.aiotask
    async def task(self, n, s, log=None, loops=3):
        while True:
            await anm.pulse(n, 1, loops=loops)
            await asyncio.sleep_ms(200)
            if log:
                log.info(f"[hello.service] NEOPIXELS with COLOR {n} toggled!")

            await asyncio.sleep(s)


service = HelloService("hello")
