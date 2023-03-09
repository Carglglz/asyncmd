from aioclass import Service
import aioctl
from micropython import const
import uasyncio as asyncio
import aioble
import bluetooth
import random
import struct

try:
    from hostname import NAME

except Exception:
    NAME = "esp-mpy"


class AiobleTempService(Service):
    # org.bluetooth.service.environmental_sensing
    _ENV_SENSE_UUID = bluetooth.UUID(0x181A)
    # org.bluetooth.characteristic.temperature
    _ENV_SENSE_TEMP_UUID = bluetooth.UUID(0x2A6E)
    # org.bluetooth.characteristic.gap.appearance.xml
    _ADV_APPEARANCE_GENERIC_THERMOMETER = const(768)

    # How frequently to send advertising beacons.
    _ADV_INTERVAL_MS = 250_000

    def __init__(self, name):
        super().__init__(name)
        self.version = "1.0"
        self.info = f"Aioble Temp Sensor v{self.version}"
        self.type = "runtime.service"  # continuous running, other types are
        self.enabled = True
        self.docs = "https://github.com/Carglglz/mpy-aiotools/blob/main/README.md"
        self.args = [NAME]
        self.kwargs = {
            "adv_interval": self._ADV_INTERVAL_MS,
            "on_stop": self.on_stop,
            "on_error": self.on_error,
            "main": None,
            "appearance": None,
            "indicate": True,
        }
        # Register GATT server.
        self.appearance = const(768)
        self.temp_service = aioble.Service(self._ENV_SENSE_UUID)
        self.temp_characteristic = aioble.Characteristic(
            self.temp_service,
            self._ENV_SENSE_TEMP_UUID,
            read=True,
            notify=True,
            indicate=True,
        )

        self.t = 0
        self.connected_device = None
        self.connection = None
        self.main_service = None
        self.ble_services = [self.temp_service]

    def show(self):
        return ("Stats", f"   Device: {self.connected_device}, Temp: {self.t}")

    def on_stop(self, *args, **kwargs):  # same args and kwargs as self.task
        if self.log:
            self.log.info(f"[{self.name}.service] stopped")

        return

    def on_error(self, e, *args, **kwargs):
        if self.log:
            self.log.error(f"[{self.name}.service] Error callback {e}")
        return e

    # Helper to encode the temperature characteristic encoding
    # (sint16, hundredths of a degree).
    def _encode_temperature(self, temp_deg_c):
        return struct.pack("<h", int(temp_deg_c * 100))

    # Serially wait for connections. Don't advertise while a central is
    # connected.
    @aioctl.aiotask
    async def task(
        self,
        adv_name,
        main=None,
        adv_interval=250_000,
        appearance=None,
        indicate=True,
        log=None,
    ):
        self.log = log
        if appearance:
            self.appearance = const(appearance)
        if not main:
            aioble.register_services(self.temp_service)
            aioble.core.ble.config(gap_name=adv_name)
            while True:
                if self.log:
                    self.log.info(f"[{self.name}.service] Advertising services...")
                async with await aioble.advertise(
                    adv_interval,
                    name=adv_name,
                    services=[self._ENV_SENSE_UUID],
                    appearance=self.appearance,
                ) as connection:
                    if self.log:
                        self.log.info(
                            f"[{self.name}.service] Connection from"
                            + f" {connection.device}",
                        )
                    else:
                        print("Connection from", connection.device)

                    self.connected_device = connection.device
                    self.connection = connection

                    if "aioble_temp.service.sense" in aioctl.group().tasks:
                        aioctl.delete("aioble_temp.service.sense")
                    aioctl.add(
                        self.sense,
                        self,
                        name="aioble_temp.service.sense",
                        _id="aioble_temp.service.sense",
                        on_stop=self.on_stop,
                        on_error=self.on_error,
                        indicate=indicate,
                    )
                    if self.log:
                        self.log.info(f"[{self.name}.service] Sensing task enabled")
                    await connection.disconnected(timeout_ms=None)
                    self.connected_device = None
                    self.connection = None

                    if self.log:
                        self.log.info(f"[{self.name}.service] Device disconnected")
        else:
            while main not in aioctl.group().tasks:
                await asyncio.sleep(1)

            self.main_service = aioctl.group().tasks[main].service

            while True:
                while not self.main_service.connection:
                    await asyncio.sleep(1)

                self.connection = self.main_service.connection
                self.connected_device = self.connection.device

                if "aioble_temp.service.sense" in aioctl.group().tasks:
                    aioctl.delete("aioble_temp.service.sense")
                aioctl.add(
                    self.sense,
                    self,
                    name="aioble_temp.service.sense",
                    _id="aioble_temp.service.sense",
                    on_stop=self.on_stop,
                    on_error=self.on_error,
                    indicate=indicate,
                )
                if self.log:
                    self.log.info(f"[{self.name}.service] Sensing task enabled")

                while self.main_service.connection:
                    await asyncio.sleep(1)

                self.connected_device = None
                self.connection = None
                aioctl.stop("aioble_temp.service.sense")

    # This would be periodically polling a hardware sensor.
    @aioctl.aiotask
    async def sense(self, *args, **kwargs):
        self.t = 24.5
        while True:
            self.temp_characteristic.write(self._encode_temperature(self.t))
            if self.connection:
                if kwargs.get("indicate"):
                    await self.temp_characteristic.indicate(self.connection)
            if self.log:
                self.log.info(f"[{self.name}.service.sense] Temperature: {self.t} C")

            self.t += random.uniform(-0.5, 0.5)
            await asyncio.sleep_ms(5000)


service = AiobleTempService("aioble_temp")
