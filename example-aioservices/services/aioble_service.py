from aioclass import Service
import aioctl
from micropython import const
import uasyncio as asyncio
import aioble
import bluetooth
import random
import struct
import os
import sys

try:
    from hostname import NAME

except Exception:
    NAME = "esp-mpy"


class AiobleService(Service):
    # org.bluetooth.service.environmental_sensing
    _ENV_SENSE_UUID = bluetooth.UUID(0x181A)
    # org.bluetooth.characteristic.temperature
    _ENV_SENSE_TEMP_UUID = bluetooth.UUID(0x2A6E)
    # org.bluetooth.characteristic.gap.appearance.xml
    _ADV_APPEARANCE_GENERIC_THERMOMETER = const(768)

    # How frequently to send advertising beacons.
    _ADV_INTERVAL_MS = 250_000

    # org.bluetooth.service.device_information
    _DEV_INF_SERV_UUID = bluetooth.UUID(0x180A)

    # org.bluetooth.characteristic.gap.appearance

    # _MANUFACT_ESPRESSIF = const(741)

    systeminfo = os.uname()
    _MODEL_NUMBER = systeminfo.sysname
    _FIRMWARE_REV = f"{sys.implementation[0]}-{systeminfo.release}"

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
        }
        # Register GATT server.
        self.appearance = const(768)
        self.temp_service = aioble.Service(self._ENV_SENSE_UUID)
        self.devinfo_service = aioble.Service(self._DEV_INF_SERV_UUID)
        self.temp_characteristic = aioble.Characteristic(
            self.temp_service,
            self._ENV_SENSE_TEMP_UUID,
            read=True,
            notify=True,
            indicate=True,
        )

        self.app_char = aioble.Characteristic(
            self.devinfo_service,
            bluetooth.UUID(0x2A01),
            read=True,
        )

        self.manufact_char = aioble.Characteristic(
            self.devinfo_service,
            bluetooth.UUID(0x2A29),
            read=True,
        )
        self.modeln_char = aioble.Characteristic(
            self.devinfo_service,
            bluetooth.UUID(0x2A24),
            read=True,
        )

        self.firmware_char = aioble.Characteristic(
            self.devinfo_service,
            bluetooth.UUID(0x2A26),
            read=True,
        )
        aioble.register_services(self.temp_service, self.devinfo_service)
        self.app_char.write(struct.pack("h", self.appearance))
        self.manufact_char.write(bytes("Espressif Incorporated", "utf8"))
        self.modeln_char.write(bytes(self._MODEL_NUMBER, "utf8"))
        self.firmware_char.write(bytes(self._FIRMWARE_REV, "utf8"))
        self.t = 0
        self.connected_device = None
        self.connection = None

    def show(self):
        return ("Stats", f"   Device: {self.connected_device}, Temp: {self.t}")

    def on_stop(self, *args, **kwargs):  # same args and kwargs as self.task
        self.connected_device = None
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
    async def task(self, adv_name, adv_interval=250_000, log=None):
        self.log = log
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

                if "aioble.service.sense" in aioctl.group().tasks:
                    aioctl.delete("aioble.service.sense")
                aioctl.add(
                    self.sense,
                    self,
                    name="aioble.service.sense",
                    _id="aioble.service.sense",
                    on_stop=self.on_stop,
                    on_error=self.on_error,
                )
                if self.log:
                    self.log.info(f"[{self.name}.service] Sensing task enabled")
                await connection.disconnected(timeout_ms=None)
                self.connected_device = None
                self.connection = None

                if self.log:
                    self.log.info(f"[{self.name}.service] Device disconnected")

    # This would be periodically polling a hardware sensor.
    @aioctl.aiotask
    async def sense(self, *args, **kwargs):
        self.t = 24.5
        while True:
            self.temp_characteristic.write(self._encode_temperature(self.t))
            if self.connection:
                await self.temp_characteristic.indicate(self.connection)
            if self.log:
                self.log.info(f"[{self.name}.service.sense] Temperature: {self.t} C")

            self.t += random.uniform(-0.5, 0.5)
            await asyncio.sleep_ms(5000)


service = AiobleService("aioble")
