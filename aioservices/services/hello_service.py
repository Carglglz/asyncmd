import uasyncio as asyncio
import pyb
import aioctl
from aioclass import Service


class HelloService(Service):
    def __init__(self, name):
        super().__init__(name)
        self.info = "Hello example runner v1.0"
        self.type = "runtime.service"  # continuous running, other types are
        self.enabled = True
        self.docs = "https://github.com/Carglglz/mpy-wpa_supplicant/blob/main/README.md"
        self.args = [2, 5]
        self.kwargs = {}
        # core.service --> run one time at boot
        # schedule.service --> run and stop following a schedule

    @aioctl.aiotask
    async def task(self, n, s, log=None):
        count = 12
        while True:
            pyb.LED(n).toggle()
            asyncio.sleep_ms(200)
            pyb.LED(n).toggle()
            if log:
                log.info(f"[hello.service] LED {n} toggled!")

            await asyncio.sleep(s)
            if n > 3:
                count -= n
            res = s / count


service = HelloService("hello")
