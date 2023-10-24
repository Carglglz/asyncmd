import asyncio
import aioctl
from aioclass import Service
from aioping import ping


class PingService(Service):
    def __init__(self, name):
        super().__init__(name)
        self.info = "Ping service v1.0"
        self.type = "runtime.service"  # continuous running, other types are
        self.enabled = True
        self.docs = "https://github.com/Carglglz/asyncmd/blob/main/README.md"
        self.args = []
        self.kwargs = {
            "host": "localhost",
            "sleep": 60,
            "rx_size": 84,
            "on_stop": self.on_stop,
            "on_error": self.on_error,
        }
        self.log = None
        self._ping_stats = {}

    def show(self):
        _stat_1 = ", ".join([f"{k}={v}" for k, v in self._ping_stats.items()])
        return "Stats", f"    {_stat_1}"  # return Tuple, "Name",
        # "info" to display

    def stats(self):
        return self._ping_stats

    def on_stop(self, *args, **kwargs):  # same args and kwargs as self.task
        if self.log:
            self.log.info(f"[ping.service] stopped result: {self._ping_stats}")

    def on_error(self, e, *args, **kwargs):
        if self.log:
            self.log.error(f"[ping.service] Error callback {e}")
        return e

    @aioctl.aiotask
    async def task(self, host="localhost", sleep=60, rx_size=84, log=None):
        self.log = log
        await asyncio.sleep(1)
        while True:
            self._ping_stats = await ping(
                host, quiet=True, rx_size=rx_size, loop=False, rtn_dict=True
            )

            if log:
                log.info(
                    f"[ping.service] ping {host} OK @ {self._ping_stats.get('avg'):.0f} ms"
                )

            await asyncio.sleep(sleep)


service = PingService("ping")
