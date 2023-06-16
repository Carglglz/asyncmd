import uasyncio as asyncio
import aioctl
from aioclass import Service
import aioschedule


class WorldService(Service):
    def __init__(self, name):
        super().__init__(name)
        self.info = "World example runner v1.0"
        self.type = "schedule.service"
        self.enabled = True
        self.docs = "https://github.com/Carglglz/asyncmd/blob/main/README.md"
        self.args = [2, 5]
        self.kwargs = {}
        self.schedule = {"start_in": 20, "repeat": 90}
        # core.service --> run one time at boot
        # schedule.service --> run and stop following a schedule

    @aioctl.aiotask
    async def task(self, n, s, log=None):
        # pyb.LED(n).toggle()
        asyncio.sleep_ms(200)
        # pyb.LED(n).toggle()
        if log:
            log.info(f"[{self.name}.service] started: LED {n} toggled!")

        await asyncio.sleep(s)
        for i in range(2):
            # pyb.LED(n).toggle()
            asyncio.sleep_ms(200)
            # pyb.LED(n).toggle()
        if log:
            log.info(f"[{self.name}.service] done: LED {n} toggled!")


service = WorldService("world")
