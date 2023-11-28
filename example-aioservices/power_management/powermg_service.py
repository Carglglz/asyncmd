import asyncio
import aioctl
from aioclass import Service
from machine import ADC, Pin
import machine
from array import array


class Battery:
    def __init__(self, batt_pin):
        self.bat = batt_pin
        self.db = array("f", (0 for i in range(2)))

    def status(self):
        self.db[0] = self.read()
        self.db[1] = round((self.db[0] - 3.3) / (4.23 - 3.3) * 100, 1)
        self.db[0] = round(self.db[0], 2)
        # return (round(volt, 2), percentage)

    def read(self):
        if hasattr(self.bat, "voltage"):
            return self.bat.voltage()
        else:
            return ((self.bat.read() * 2) / 4095) * 3.6


class PowerMgService(Service):
    def __init__(self, name):
        super().__init__(name)
        self.info = "Power Management Service v1.0"
        self.type = "runtime.service"  # continuous running, other types are
        self.enabled = True
        self.docs = "https://github.com/Carglglz/asyncmd/blob/main/README.md"
        self.args = []
        self.kwargs = {
            "on_stop": self.on_stop,
            "on_error": self.on_error,
            "batt_pin": 35,
            "deepsleep": 30000,
            "threshold": 40,
            "loglevel": "INFO",
            "service_logger": True,
        }
        self.log = None
        self.battery = None

    async def setup(self, batt_pin):
        if isinstance(batt_pin, int):
            bat = ADC(Pin(batt_pin))
            bat.atten(ADC.ATTN_11DB)
        else:
            while batt_pin not in aioctl.group().tasks:
                await asyncio.sleep(1)
            bat = aioctl.group().tasks.get(batt_pin).service

            while not hasattr(bat, "sensor"):
                await asyncio.sleep(1)

            while not hasattr(bat.sensor, "voltage"):
                await asyncio.sleep(1)

            bat = bat.sensor

        self.battery = Battery(bat)

    def show(self):
        self.battery.status()
        _stat_1 = f"   Battery: {self.battery.db[1]} %"
        _stat_2 = f"   Voltage: {self.battery.db[0]} V"
        return "Stats", f"{_stat_1}{_stat_2}"  # return Tuple, "Name",
        # "info" to display

    def stats(self):
        if not self.battery:
            return {"battery": None, "voltage": None}
        return {"battery": self.battery.db[1], "voltage": self.battery.db[0]}

    def on_stop(self, *args, **kwargs):  # same args and kwargs as self.task
        if self.log:
            self.log.info("stopped")

    def on_error(self, e, *args, **kwargs):
        if self.log:
            self.log.error(f"Error callback {e}")
        return e

    @aioctl.aiotask
    async def task(
        self,
        batt_pin=35,
        deepsleep=True,
        threshold=40,
        log=None,
        loglevel="INFO",
        service_logger=False,
    ):
        self.add_logger(log, level=loglevel, service_logger=service_logger)
        await self.setup(batt_pin)
        await asyncio.sleep(5)
        while True:
            self.battery.status()
            if self.battery.db[1] <= threshold:
                self.log.warning(f"Battery @ {self.battery.db[1]} %")
                if deepsleep is not False:
                    if self.log:
                        self.log.info("Deep sleep now...")
                        await asyncio.sleep(2)
                        machine.deepsleep(deepsleep)
            else:
                self.log.info(f"Battery @ {self.battery.db[1]} %")
            await asyncio.sleep(60)


service = PowerMgService("powermg")
