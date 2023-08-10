import time
import ssl as _ssl
from aioclass import Service
import aioctl
from async_mqtt import MQTTClient
import asyncio
import json
import random
from machine import Pin, I2C
import socket
import sys
from array import array

# from ina219 import BME280
try:
    from hostname import NAME
except Exception:
    NAME = sys.platform

try:
    from ina219 import INA219

except Exception:

    class INA219:
        def __init__(self, *args, **kwargs):
            pass

        def configure(self):
            pass

        def voltage(self):  # V
            return random.random() + 3

        def current(self):  # mA
            return random.random() + 50

        def power(self):  # mW
            return random.random() + 150


class MQTTService(Service):
    _CONFIG_TOPIC = "homeassistant/sensor/{}/config"
    _STATE_TOPIC = "homeassistant/sensor/{}/state"
    _CONFIG_PAYLOAD = {
        "device_class": "",
        "name": "",
        "state_topic": "",
        "unit_of_measurement": "",
        "value_template": "",
    }

    def __init__(self, name):
        super().__init__(name)
        self.version = "1.0"
        self.info = f"Async MQTT INA219 client v{self.version}"
        self.type = "runtime.service"  # continuous running, other types are
        self.enabled = True
        self.docs = "https://github.com/Carglglz/asyncmd/blob/main/README.md"
        self.args = [NAME]
        self.kwargs = {
            "main": "aiomqtt.service",
            "server": "0.0.0.0",
            "port": 1883,
            "hostname": None,
            "ssl": False,
            "ssl_params": {},
            "keepalive": 300,
            "debug": False,
            "on_stop": self.on_stop,
            "on_error": self.on_error,
            "restart": ["aiomqtt_sensor_ina219_solar.service"],
            "topics": [f"device/{NAME}/state", "device/all/state"],
            "i2c": (22, 23),
            "address": 0x44,
            "address_solar": 0x40,
            "shunt_ohms": 0.1,
        }

        self.sslctx = False
        self.client = None
        self.sensor = None
        self.n_msg = 0
        self.n_pub = 0
        self._dbb = array("f", (0 for i in range(3)))
        self._dbs = array("f", (0 for i in range(3)))
        self.td = 0
        self.id = NAME
        self.i2c = None

    def setup(self, shunt, addr, addr_solar):
        self.unique_id = "PowerSensor_{}".format(self.id.split()[0].lower())
        self.sensor = INA219(shunt, self.i2c, address=addr, log=self.log)
        self.sensor.configure()
        self.sensor_solar = INA219(shunt, self.i2c, address=addr_solar, log=self.log)
        self.sensor_solar.configure()
        self._cfg_volt = {"topic": self._CONFIG_TOPIC.format(NAME + "V"), "payload": ""}
        self._cfg_curr = {"topic": self._CONFIG_TOPIC.format(NAME + "C"), "payload": ""}
        self._cfg_pow = {"topic": self._CONFIG_TOPIC.format(NAME + "P"), "payload": ""}
        self._stat_t = self._STATE_TOPIC.format(NAME)
        self._cfg_volt["payload"] = json.dumps(
            dict(
                device_class="voltage",
                name="Voltage",
                unique_id="{}_voltage".format(self.id),
                state_topic=self._stat_t,
                unit_of_measurement="V",
                value_template="{{ value_json.voltage}}",
            )
        )
        self._cfg_curr["payload"] = json.dumps(
            dict(
                device_class="current",
                name="Current",
                unique_id="{}_current".format(self.id),
                state_topic=self._stat_t,
                unit_of_measurement="mA",
                value_template="{{ value_json.current}}",
            )
        )
        self._cfg_pow["payload"] = json.dumps(
            dict(
                device_class="power",
                name="Power",
                unique_id="{}_power".format(self.id),
                state_topic=self._stat_t,
                unit_of_measurement="mW",
                value_template="{{ value_json.power}}",
            )
        )

    def show(self):
        return (
            "Stats",
            f"   Messages: Received: {self.n_msg}, Published: "
            + f"{self.n_pub}"
            + f" Delta HS: {self.td} s",
        )

    def stats(self):
        return {
            "voltage": self._dbb[0],
            "current": self._dbb[1],
            "power": self._dbb[2],
            "voltage_sol": self._dbs[0],
            "current_sol": self._dbs[1],
            "power_sol": self._dbs[2],
            "npub": self.n_pub,
            "nrecv": self.n_msg,
        }

    def on_stop(self, *args, **kwargs):  # same args and kwargs as self.task
        # self.app awaits self.app.server.wait_closed which
        # consumes Cancelled error so this does not run
        self.client = None
        if self.log:
            self.log.info(f"[{self.name}.service] stopped")

        return

    def on_error(self, e, *args, **kwargs):
        self.client = None
        if self.log:
            self.log.error(f"[{self.name}.service] Error callback {e}")
        return e

    def on_receive(self, topic, msg):
        try:
            self.n_msg += 1
            if self.log:
                self.log.info(
                    f"[{self.name}.service] @ [{topic.decode()}]:" + f" {msg.decode()}"
                )
        except Exception as e:
            if self.log:
                self.log.error(f"[{self.name}.service] {e}")

    @aioctl.aiotask
    async def task(
        self,
        client_id,
        main="aiomqtt.service",
        server="0.0.0.0",
        port=1883,
        ssl=False,
        ssl_params={},
        hostname=None,
        keepalive=300,
        debug=True,
        restart=True,
        topics=[],
        i2c=(22, 23),
        shunt_ohms=0.1,
        address=0x44,
        address_solar=0x40,
        log=None,
    ):
        self.log = log
        self.i2c = I2C(1, scl=Pin(i2c[0]), sda=Pin(i2c[1]))
        self.setup(shunt_ohms, address, address_solar)
        if not main:
            if ssl:
                if not self.sslctx:
                    self.sslctx = _ssl.SSLContext(_ssl.PROTOCOL_TLS_CLIENT)
                    self.sslctx.load_verify_locations(cafile=ssl_params["ca"])
                    self.sslctx.load_cert_chain(ssl_params["cert"], ssl_params["key"])
            ai = socket.getaddrinfo(server, port)
            server = ai[0][-1][0]
            self.client = MQTTClient(
                client_id,
                server,
                port,
                keepalive=keepalive,
                ssl=self.sslctx,
                ssl_params={"server_hostname": hostname},
            )
            self.client.set_callback(self.on_receive)
            t0 = time.ticks_ms()
            await self.client.connect()

            self.td = time.ticks_diff(time.ticks_ms(), t0) / 1e3
            self.lock = asyncio.Lock()
        else:
            while main not in aioctl.group().tasks:
                await asyncio.sleep(1)

            self.aiomqtt_service = aioctl.group().tasks[main].service

            # add restart
            if isinstance(restart, list):
                for _tsk in restart:
                    aioctl.group().tasks[main].kwargs["restart"].add(_tsk)

            while not self.aiomqtt_service.client:
                await asyncio.sleep(1)

            while not self.aiomqtt_service.client.a_writer:
                await asyncio.sleep(1)

            await self.aiomqtt_service.client_ready.wait()
            self.client = self.aiomqtt_service.client
            self.lock = self.aiomqtt_service.lock
            await asyncio.sleep_ms(1000)

            # add callback

            # Subscribe
            async with self.lock:
                for tp in topics:
                    self.aiomqtt_service.add_callback(
                        tp, {"name": "sense_p", "task": self.sense_cb, "service": self}
                    )
                    if isinstance(tp, str):
                        tp = tp.encode("utf-8")
                    await self.client.subscribe(tp)

        if self.log:
            self.log.info(f"[{self.name}.service] MQTT client connected")
        # Discovery
        async with self.lock:
            # Voltage
            await self.client.publish(
                self._cfg_volt["topic"], self._cfg_volt["payload"]
            )
            # await asyncio.sleep(1)
            # Current
            await self.client.publish(
                self._cfg_curr["topic"], self._cfg_curr["payload"]
            )
            # await asyncio.sleep(1)
            # Power
            await self.client.publish(self._cfg_pow["topic"], self._cfg_pow["payload"])
        if self.log:
            self.log.info(f"[{self.name}.service] MQTT Client Discovery done!")

        self.n_pub += 3
        # Add subtask

        if f"{self.name}.service.sense" in aioctl.group().tasks:
            aioctl.delete(f"{self.name}.service.sense")
        aioctl.add(
            self.sense,
            self,
            name=f"{self.name}.service.sense",
            _id=f"{self.name}.service.sense",
            on_stop=self.on_stop,
            on_error=self.on_error,
            restart=restart,
        )
        if self.log:
            self.log.info(f"[{self.name}.service] MQTT publish task enabled")

        # Wait for messages
        if not main:
            while True:
                await self.client.wait_msg()
                await asyncio.sleep(1)
        else:
            while True:
                assert self.client == self.aiomqtt_service.client
                await asyncio.sleep(5)

                if self.log and debug:
                    self.log.info(f"[{self.name}.service] MQTT sensor OK")

    @aioctl.aiotask
    async def sense_cb(self, topic, msg):
        self.on_receive(topic, msg)
        volt = self.sensor.voltage()
        current = self.sensor.current()
        power = self.sensor.power()

        if self.log:
            self.log.info(
                f"[{self.name}.service.sense_cb] {volt} V " + f"{current} mA {power} mW"
            )
        async with self.lock:
            await self.client.publish(
                topic.replace(b"state", b"sense"),
                json.dumps(
                    {
                        "voltage": f"{volt:.1f}",
                        "current": f"{current:.1f}",
                        "power": f"{power:.1f}",
                        "hostname": NAME,
                    }
                ),
            )
        self.n_pub += 1

    @aioctl.aiotask
    async def sense(self, *args, **kwargs):
        while True:
            self._dbb[0] = self.sensor.voltage()
            self._dbb[1] = self.sensor.current()
            self._dbb[2] = self.sensor.power()

            self._dbs[0] = self.sensor_solar.voltage()
            self._dbs[1] = self.sensor_solar.current()
            self._dbs[2] = self.sensor_solar.power()

            if self.log:
                self.log.info(
                    f"[{self.name}.service.sense] {self._dbb[0]} V "
                    + f"{self._dbb[1]} mA {self._dbb[2]} mW"
                )

                self.log.info(
                    f"[{self.name}.service.sense] {self._dbs[0]} Vsol "
                    + f"{self._dbs[1]} mAsol {self._dbs[2]} mWsol"
                )

            # await self.aiomqtt_service.client_ready.wait()
            async with self.lock:
                await self.client.publish(
                    self._stat_t,
                    json.dumps(
                        {
                            "voltage": f"{self._dbb[0]:.1f}",
                            "current": f"{self._dbb[1]:.1f}",
                            "power": f"{self._dbb[2]:.1f}",
                            "voltage_sol": f"{self._dbs[0]:.1f}",
                            "current_sol": f"{self._dbs[1]:.1f}",
                            "power_sol": f"{self._dbs[2]:.1f}",
                            "hostname": NAME,
                        }
                    ),
                )
            self.n_pub += 1
            await asyncio.sleep(5)

    # @aioctl.aiotask
    # async def disconnect(self, *args, **kwargs):
    #     if self.client:
    #         await self.client.disconnect()
    #     self.sslctx = None
    #     self.client = None
    #     gc.collect()


service = MQTTService("aiomqtt_sensor_ina219_solar")
