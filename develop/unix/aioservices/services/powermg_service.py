import asyncio
import aioctl
from aioclass import Service
from machine import ADC, Pin
import machine


class Battery:
    def __init__(self, batt_pin):
        self.bat = batt_pin

    def status(self):
        volt = ((self.bat.read() * 2) / 4095) * 3.6
        percentage = round((volt - 3.3) / (4.23 - 3.3) * 100, 1)
        return (round(volt, 2), percentage)


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
        self._batt = None
        self._volt = None
        self.battery = None

    def setup(self, batt_pin):
        bat = ADC(Pin(batt_pin))
        bat.atten(ADC.ATTN_11DB)

        self.battery = Battery(bat)

    def show(self):
        self._volt, self._batt = self.battery.status()
        _stat_1 = f"   Battery: {self._batt} %"
        _stat_2 = f"   Voltage: {self._volt} V"
        return "Stats", f"{_stat_1}{_stat_2}"  # return Tuple, "Name",
        # "info" to display

    def stats(self):
        return {"battery": self._batt, "voltage": self._volt}

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
        self.setup(batt_pin)
        await asyncio.sleep(5)
        while True:
            self._volt, self._batt = self.battery.status()
            if self._batt <= threshold:
                self.log.warning(f"Battery @ {self._batt} %")
                if deepsleep is not False:
                    if self.log:
                        self.log.info("Deep sleep now...")
                        await asyncio.sleep(2)
                        machine.deepsleep(deepsleep)
            else:
                self.log.info(f"Battery @ {self._batt} %")
            await asyncio.sleep(60)


service = PowerMgService("powermg")
