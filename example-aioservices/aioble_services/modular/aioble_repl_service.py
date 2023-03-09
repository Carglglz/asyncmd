from aioclass import Service
import aioctl
from micropython import const
import uasyncio as asyncio
import aioble
import bluetooth
import io
import os
import micropython
import machine
import struct
import sys

try:
    from hostname import NAME

except Exception:
    NAME = "esp-mpy"


uart = None

_MP_STREAM_POLL = const(3)
_MP_STREAM_POLL_RD = const(0x0001)

# TODO: Remove this when STM32 gets machine.Timer.
if hasattr(machine, "Timer"):
    _timer = machine.Timer(-1)
else:
    _timer = None


# Batch writes into 50ms intervals.
def schedule_in(handler, delay_ms):
    def _wrap(_arg):
        handler()

    if _timer:
        _timer.init(mode=machine.Timer.ONE_SHOT, period=delay_ms, callback=_wrap)
    else:
        micropython.schedule(_wrap, None)


# Simple buffering stream to support the dupterm requirements.
class BLEUARTStream(io.IOBase):
    def __init__(self, uart):
        self._uart = uart
        self._tx_buf = bytearray()
        self._uart.irq(self._on_rx)

    def _on_rx(self):
        # Needed for ESP32.
        if hasattr(os, "dupterm_notify"):
            os.dupterm_notify(None)

    def read(self, sz=None):
        return self._uart.read(sz)

    def readinto(self, buf):
        avail = self._uart.read(len(buf))
        if not avail:
            return None
        for i in range(len(avail)):
            buf[i] = avail[i]
        return len(avail)

    def ioctl(self, op, arg):
        if op == _MP_STREAM_POLL:
            if self._uart.any():
                return _MP_STREAM_POLL_RD
        return 0

    def _flush(self):
        if self._uart._tx_available:
            if len(self._uart._tx_buffer) < 512:
                data = self._tx_buf[0:512]
                self._tx_buf = self._tx_buf[512:]
                self._uart.write_queue(data)
            if self._tx_buf:
                schedule_in(self._flush, 25)

    def write(self, buf):
        empty = not self._tx_buf
        self._tx_buf += buf
        if empty:
            schedule_in(self._flush, 25)


class AiobleREPLService(Service):
    _UART_UUID = bluetooth.UUID("6E400001-B5A3-F393-E0A9-E50E24DCCA9E")
    _UART_TX = bluetooth.UUID("6E400003-B5A3-F393-E0A9-E50E24DCCA9E")
    _UART_RX = bluetooth.UUID("6E400002-B5A3-F393-E0A9-E50E24DCCA9E")

    # How frequently to send advertising beacons.
    _ADV_INTERVAL_MS = 250_000

    def __init__(self, name):
        super().__init__(name)
        self.version = "1.0"
        self.info = f"Aioble REPL v{self.version}"
        self.type = "runtime.service"  # continuous running, other types are
        self.enabled = True
        self.docs = "https://github.com/Carglglz/mpy-aiotools/blob/main/README.md"
        self.args = [NAME]
        self.kwargs = {
            "adv_interval": self._ADV_INTERVAL_MS,
            "on_stop": self.on_stop,
            "on_error": self.on_error,
            "echo": True,
            "main": None,
            "appearance": None,
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
        self._tx_buffer = bytearray()
        self._tx_available = True
        self._writable = True
        self._rx_handler = None
        self._echo = True
        self.connected_device = None
        self.connection = None
        self.stream = None
        self.main_service = None
        self.ble_services = [self.uart_service]

    def setup(self):
        aioble.core.ble.gatts_set_buffer(
            self.uart_rx_characteristic._value_handle, 512, True
        )
        aioble.core.ble.gatts_set_buffer(self.uart_tx_characteristic._value_handle, 512)

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

    def any(self):
        return len(self._rx_buffer)

    def read(self, sz=None):
        if not sz:
            sz = len(self._rx_buffer)
        result = self._rx_buffer[0:sz]
        self._rx_buffer = self._rx_buffer[sz:]
        return result

    def write_queue(self, data):
        self._tx_buffer += data

    async def write(self, data):
        while True:
            try:
                self.uart_tx_characteristic.write(data)
                if self.connection:
                    await self.uart_tx_characteristic.indicate(self.connection)
                if self.log and self._echo:
                    self.log.info(f"[{self.name}.service] TX: {data}")
                self._tx_available = True
                break
            except Exception:
                self._tx_available = False
                await asyncio.sleep_ms(25)

    def rx_handler(self):
        if self._rx_handler:
            self._rx_handler()
        # if self.log:
        #     self.log.info(
        #         f"[{self.name}.service.rx] RX: {self.read().decode().strip()}"
        #     )
        # else:
        #     print(f"RX: {self.read().decode().strip()}")

    def irq(self, handler):
        self._rx_handler = handler

    # Serially wait for connections. Don't advertise while a central is
    # connected.
    @aioctl.aiotask
    async def task(
        self,
        adv_name,
        adv_interval=250_000,
        main=None,
        appearance=None,
        echo=True,
        log=None,
    ):
        self.stream = BLEUARTStream(self)
        self._echo = echo
        self.log = log

        if appearance:
            self.appearance = const(appearance)
        if not main:
            aioble.register_services(*self.ble_services)

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

                    self.connection = connection

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
                    if "aioble_uart.service.tx" in aioctl.group().tasks:
                        aioctl.delete("aioble_uart.service.tx")
                    aioctl.add(
                        self.tx,
                        self,
                        name="aioble_uart.service.tx",
                        _id="aioble_uart.service.tx",
                        on_stop=self.on_stop,
                        on_error=self.on_error,
                        echo=echo,
                    )
                    if self.log:
                        self.log.info(f"[{self.name}.service] RX/TX tasks enabled")
                    self.connected_device = connection.device
                    os.dupterm(self.stream)
                    await connection.disconnected(timeout_ms=None)
                    self.connection = None
                    self.connected_device = None

                    if self.log:
                        self.log.info(f"[{self.name}.service] Device disconnected")
                    os.dupterm(None)
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
                if "aioble_uart.service.tx" in aioctl.group().tasks:
                    aioctl.delete("aioble_uart.service.tx")
                aioctl.add(
                    self.tx,
                    self,
                    name="aioble_uart.service.tx",
                    _id="aioble_uart.service.tx",
                    on_stop=self.on_stop,
                    on_error=self.on_error,
                    echo=echo,
                )
                if self.log:
                    self.log.info(f"[{self.name}.service] RX/TX tasks enabled")

                os.dupterm(self.stream)

                while self.main_service.connection:
                    await asyncio.sleep(1)

                self.connected_device = None
                self.connection = None
                aioctl.stop("aioble_uart.service.rx")
                aioctl.stop("aioble_uart.service.tx")
                os.dupterm(None)

    @aioctl.aiotask
    async def rx(self, *args, **kwargs):
        while True:
            conn_write = await self.uart_rx_characteristic.written()
            if conn_write:
                data = self.uart_rx_characteristic.read()
                if self.log and self._echo:
                    self.log.info(
                        f"[{self.name}.service.rx] DATA {data} from {conn_write.device}"
                    )
                self._rx_buffer += data
                self.rx_handler()
                # if kwargs.get("echo"):
                #     await self.write(data)

    @aioctl.aiotask
    async def tx(self, *args, **kwargs):
        while True:
            if len(self._tx_buffer):
                if self._tx_buffer.endswith(b"\r\n>>> ") or self._tx_buffer.endswith(
                    b">>> "
                ):
                    if len(self._tx_buffer) > 512:
                        await self.write(self._tx_buffer[:512])
                        self._tx_buffer[:] = self._tx_buffer[512:]
                    else:
                        await self.write(self._tx_buffer)
                        self._tx_buffer[:] = b""

                elif len(self._tx_buffer) >= 128:
                    await self.write(self._tx_buffer[:128])
                    self._tx_buffer[:] = self._tx_buffer[128:]

                else:
                    await asyncio.sleep_ms(25)
            else:
                await asyncio.sleep_ms(50)


service = AiobleREPLService("aioble_repl")
