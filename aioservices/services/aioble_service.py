from aioclass import Service
import aioctl
from micropython import const
import uasyncio as asyncio
import aioble
import bluetooth
import os
import sys
import struct

try:
    from hostname import NAME

except Exception:
    NAME = "esp-mpy"


class AiobleService(Service):
    # How frequently to send advertising beacons.
    _ADV_INTERVAL_MS = 250_000

    # org.bluetooth.service.device_information
    _DEV_INF_SERV_UUID = bluetooth.UUID(0x180A)

    systeminfo = os.uname()
    _MODEL_NUMBER = systeminfo.sysname
    _FIRMWARE_REV = f"{sys.implementation[0]}-{systeminfo.release}"

    def __init__(self, name):
        super().__init__(name)
        self.version = "1.0"
        self.info = f"Aioble BLE Service v{self.version}"
        self.type = "runtime.service"  # continuous running, other types are
        self.enabled = True
        self.docs = "https://github.com/Carglglz/asyncmd/blob/main/README.md"
        self.args = [NAME]
        self.kwargs = {
            "adv_interval": self._ADV_INTERVAL_MS,
            "on_stop": self.on_stop,
            "on_error": self.on_error,
            "echo": True,
            "main": True,
            "ble_services": [],
        }
        # Register GATT server.
        self.appearance = const(128)
        self.devinfo_service = aioble.Service(self._DEV_INF_SERV_UUID)

        self.app_char = aioble.Characteristic(
            self.devinfo_service,
            bluetooth.UUID(0x2A01),
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
        self.ble_services = [self.devinfo_service]
        self._echo = True
        self._registered_services = False
        self.connected_device = None
        self.connection = None

    def setup(self):
        self.app_char.write(struct.pack("h", self.appearance))
        self.modeln_char.write(bytes(self._MODEL_NUMBER, "utf8"))
        self.firmware_char.write(bytes(self._FIRMWARE_REV, "utf8"))

    def show(self):
        return ("Stats", f"   Device: {self.connected_device}")

    def on_stop(self, *args, **kwargs):  # same args and kwargs as self.task
        if self.log:
            self.log.info(f"[{self.name}.service] stopped")

        return

    def on_error(self, e, *args, **kwargs):
        if self.log:
            self.log.error(f"[{self.name}.service] Error callback {e}")
        return e

    # Serially wait for connections. Don't advertise while a central is
    # connected.
    @aioctl.aiotask
    async def task(
        self,
        adv_name,
        adv_interval=250_000,
        appearance=None,
        main=True,
        ble_services=[],
        echo=True,
        log=None,
    ):
        self._echo = echo
        self.log = log

        if appearance:
            self.appearance = const(appearance)
        if ble_services:
            # wait to get secondary ble_services to register
            if isinstance(ble_services, list):
                pass
            else:
                if ble_services:
                    ble_services = []
                    # parse from service.config aioble_*.service
                    from aioservice import get_config

                    serv_config = get_config()
                    if serv_config:
                        for serv, conf in serv_config.items():
                            if serv.startswith("aioble_"):
                                if conf["enabled"]:
                                    _main = conf["kwargs"].get("main")
                                    if _main == "aioble.service":
                                        ble_services += [f"{serv}.service"]
                else:
                    ble_services = []

            for _ble_serv in ble_services:
                while _ble_serv not in aioctl.group().tasks:
                    await asyncio.sleep_ms(200)
                self.ble_services += (
                    aioctl.group().tasks[_ble_serv].service.ble_services
                )

        if self.log:
            self.log.info(
                f"[{self.name}.service] Registering services {self.ble_services}"
            )

        aioble.register_services(*self.ble_services)
        self._registered_services = True

        self.setup()

        try:
            aioble.core.ble.config(gap_name=adv_name, mtu=515, rxbuf=512)
        except Exception:
            # MICROPY_PY_BLUETOOTH_USE_SYNC_EVENTS
            aioble.core.ble.config(gap_name=adv_name, mtu=515)
        while True:
            if self.log:
                self.log.info(f"[{self.name}.service] Advertising services...")
            async with await aioble.advertise(
                adv_interval,
                name=adv_name,
                services=[self._DEV_INF_SERV_UUID],
                appearance=self.appearance,
            ) as connection:
                if self.log:
                    self.log.info(
                        f"[{self.name}.service] Connection from"
                        + f" {connection.device}",
                    )
                else:
                    print("Connection from", connection.device)

                self.connection = connection

                self.connected_device = connection.device
                await connection.disconnected(timeout_ms=None)
                self.connection = None
                self.connected_device = None

                if self.log:
                    self.log.info(f"[{self.name}.service] Device disconnected")


service = AiobleService("aioble")
