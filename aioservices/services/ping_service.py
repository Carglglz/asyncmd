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
            "nodes": [],
            "sleep": 60,
            "rx_size": 84,
            "on_stop": self.on_stop,
            "on_error": self.on_error,
        }
        self.log = None
        self._ping_stats = {}
        self._ping_stats_nodes = {}
        self._ping_lock = asyncio.Lock()

    def show(self):
        _stat_1 = ", ".join([f"{k}={v}" for k, v in self._ping_stats.items()])
        return "Stats", f"    {_stat_1}"  # return Tuple, "Name",
        # "info" to display

    def stats(self):
        self._ping_stats.update(**self._ping_stats_nodes)
        return self._ping_stats

    def on_stop(self, *args, **kwargs):  # same args and kwargs as self.task
        if self.log:
            self.log.info(f"[ping.service] stopped result: {self._ping_stats}")

    def on_error(self, e, *args, **kwargs):
        if self.log:
            self.log.error(f"[ping.service] Error callback {e}")
        return e

    @aioctl.aiotask
    async def task(self, host="localhost", nodes=[], sleep=60, rx_size=84, log=None):
        self.log = log
        await asyncio.sleep(1)
        # add ping child tasks to ping n hosts
        # add per host stats

        for node in nodes:
            nodename = node.replace(".local", "")
            if f"{self.name}.service.{nodename}" in aioctl.group().tasks:
                aioctl.delete(f"{self.name}.service.{nodename}")
            aioctl.add(
                self.cping,
                self,
                host=node,
                name=f"{self.name}.service.{nodename}",
                _id=f"{self.name}.service.{nodename}",
                on_stop=self.on_stop,
                on_error=self.on_error,
                log=log,
            )
            if self.log:
                self.log.info(f"[{self.name}.service] cping @ {node} enabled")
        self._ping_stats.update(host=host)
        while True:
            async with self._ping_lock:
                self._ping_stats.update(
                    **await ping(
                        host, quiet=True, rx_size=rx_size, loop=False, rtn_dict=True
                    )
                )

                if log:
                    log.info(
                        f"[ping.service] ping {host} OK @ {self._ping_stats.get('avg'):.0f} ms"
                    )

            await asyncio.sleep(sleep)

    @aioctl.aiotask
    async def cping(self, host="localhost", sleep=60, rx_size=84, log=None):
        self.log = log
        await asyncio.sleep(10)
        self._ping_stats_nodes[host] = {}
        while True:
            async with self._ping_lock:
                self._ping_stats_nodes[host].update(
                    **await ping(
                        host, quiet=True, rx_size=rx_size, loop=False, rtn_dict=True
                    )
                )
                if log:
                    log.info(
                        f"[ping.service] ping {host} OK @ {self._ping_stats_nodes[host].get('avg'):.0f} ms"
                    )

            await asyncio.sleep(sleep)


service = PingService("ping")
