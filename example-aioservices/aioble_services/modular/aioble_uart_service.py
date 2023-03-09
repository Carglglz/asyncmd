from aioclass import Service
import aioctl
from micropython import const
import uasyncio as asyncio
import aioble
import bluetooth

try:
    from hostname import NAME

except Exception:
    NAME = "esp-mpy"


class AiobleUARTService(Service):
    _UART_UUID = bluetooth.UUID("6E400001-B5A3-F393-E0A9-E50E24DCCA9E")
    _UART_TX = bluetooth.UUID("6E400003-B5A3-F393-E0A9-E50E24DCCA9E")
    _UART_RX = bluetooth.UUID("6E400002-B5A3-F393-E0A9-E50E24DCCA9E")

    # How frequently to send advertising beacons.
    _ADV_INTERVAL_MS = 250_000

    def __init__(self, name):
        super().__init__(name)
        self.version = "1.0"
        self.info = f"Aioble UART v{self.version}"
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
            "echo": True,
        }
        # Register GATT server.
        self.appearance = const(128)
        self.uart_service = aioble.Service(self._UART_UUID)
        self.uart_tx_characteristic = aioble.Characteristic(
            self.uart_service,
            self._UART_TX,
            read=False,
            notify=True,
            indicate=True,
        )
        self.uart_rx_characteristic = aioble.Characteristic(
            self.uart_service, self._UART_RX, write=True
        )

        self._rx_buffer = bytearray()
        self._tx_available = True
        self.connected_device = None
        self.connection = None
        self.main_service = None
        self.ble_services = [self.uart_service]

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

    def setup(self):
        aioble.core.ble.gatts_set_buffer(
            self.uart_rx_characteristic._value_handle, 512, True
        )
        aioble.core.ble.gatts_set_buffer(self.uart_tx_characteristic._value_handle, 512)

    def any(self):
        return len(self._rx_buffer)

    def read(self, sz=None):
        if not sz:
            sz = len(self._rx_buffer)
        result = self._rx_buffer[0:sz]
        self._rx_buffer = self._rx_buffer[sz:]
        return result

    async def write(self, data):
        while True:
            try:
                self.uart_tx_characteristic.write(data)
                if self.connection:
                    await self.uart_tx_characteristic.indicate(self.connection)
                if self.log:
                    self.log.info(f"[{self.name}.service] TX: {data}")
                self._tx_available = True
                break
            except Exception:
                self._tx_available = False
                await asyncio.slee_ms(200)

    def rx_handler(self):
        if self.log:
            self.log.info(
                f"[{self.name}.service.rx] RX: {self.read().decode().strip()}"
            )
        else:
            print(f"RX: {self.read().decode().strip()}")

    # Serially wait for connections. Don't advertise while a central is
    # connected.
    @aioctl.aiotask
    async def task(
        self,
        adv_name,
        main=None,
        adv_interval=250_000,
        appearance=None,
        echo=True,
        log=None,
    ):
        self.log = log

        if appearance:
            self.appearance = const(appearance)
        if not main:
            aioble.register_services(self.uart_service)
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
                    services=[self._UART_UUID],
                    appearance=self.appearance,
                ) as connection:
                    if self.log:
                        self.log.info(
                            f"[{self.name}.service] Connection from"
                            + f" {connection.device}",
                        )
                    else:
                        print("Connection from", connection.device)

                    if "aioble_uart.service.rx" in aioctl.group().tasks:
                        aioctl.delete("aioble_uart.service.rx")
                    aioctl.add(
                        self.rx,
                        self,
                        name="aioble_uart.service.rx",
                        _id="aioble_uart.service.rx",
                        on_stop=self.on_stop,
                        on_error=self.on_error,
                        echo=echo,
                    )
                    if self.log:
                        self.log.info(f"[{self.name}.service] RX task enabled")

                    self.connected_device = connection.device
                    self.connection = connection

                    await connection.disconnected(timeout_ms=None)

                    self.connected_device = None
                    self.connection = None

                    if self.log:
                        self.log.info(f"[{self.name}.service] Device disconnected")
        else:
            while main not in aioctl.group().tasks:
                await asyncio.sleep(1)

            self.main_service = aioctl.group().tasks[main].service

            while not self.main_service._registered_services:
                await asyncio.sleep_ms(200)
            self.setup()

            while True:
                while not self.main_service.connection:
                    await asyncio.sleep(1)

                self.connection = self.main_service.connection
                self.connected_device = self.connection.device

                if "aioble_uart.service.rx" in aioctl.group().tasks:
                    aioctl.delete("aioble_uart.service.rx")
                aioctl.add(
                    self.rx,
                    self,
                    name="aioble_uart.service.rx",
                    _id="aioble_uart.service.rx",
                    on_stop=self.on_stop,
                    on_error=self.on_error,
                    echo=echo,
                )
                if self.log:
                    self.log.info(f"[{self.name}.service] RX task enabled")

                while self.main_service.connection:
                    await asyncio.sleep(1)

                self.connected_device = None
                self.connection = None
                aioctl.stop("aioble_uart.service.rx")

    @aioctl.aiotask
    async def rx(self, *args, **kwargs):
        while True:
            conn_write = await self.uart_rx_characteristic.written()
            if conn_write:
                data = self.uart_rx_characteristic.read()
                if self.log:
                    self.log.info(
                        f"[{self.name}.service.rx] DATA {data} from {conn_write.device}"
                    )
                self._rx_buffer += data
                self.rx_handler()
                if kwargs.get("echo"):
                    await self.write(data)


service = AiobleUARTService("aioble_uart")
