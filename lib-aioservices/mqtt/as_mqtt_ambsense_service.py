import ssl as _ssl
from aioclass import Service
import aioctl
from async_mqtt import MQTTClient
import asyncio
import json
import random
import gc
from machine import Pin, I2C
import socket
import sys

try:
    from bme280 import BME280
except Exception:
    pass
try:
    from hostname import NAME
except Exception:
    NAME = sys.platform


class FakeBME280:
    def __init__(self, i2c=None):
        self.i2c = i2c

    def read_compensated_data(self):
        return (
            25 + random.random() * 2,
            90000 + random.random() * 100,
            60 + random.random() * 10,
        )


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
        self.info = "Async MQTT BME280 client v1.0"
        self.type = "runtime.service"  # continuous running, other types are
        self.enabled = True
        self.docs = "https://github.com/Carglglz/asyncmd/blob/main/README.md"
        self.args = [NAME]
        self.kwargs = {
            "server": "0.0.0.0",
            "port": 1883,
            "hostname": None,
            "ssl": False,
            "ssl_params": {},
            "keepalive": 300,
            "debug": True,
            "on_stop": self.on_stop,
            "on_error": self.on_error,
            "i2c": (22, 21),
        }

        self.sslctx = False
        self.client = None
        self.sensor = None
        self.n_msg = 0
        self.n_pub = 0
        self.id = NAME
        self.i2c = None
        self._temp = None
        self._hum = None
        self._press = None

    def setup(self):
        self.unique_id = "AmbienceSensor_{}".format(self.id.split()[0].lower())
        self.sensor = BME280(i2c=self.i2c)
        self._cfg_temp = {"topic": self._CONFIG_TOPIC.format(NAME + "T"), "payload": ""}
        self._cfg_hum = {"topic": self._CONFIG_TOPIC.format(NAME + "H"), "payload": ""}
        self._cfg_pr = {"topic": self._CONFIG_TOPIC.format(NAME + "P"), "payload": ""}
        self._stat_t = self._STATE_TOPIC.format(NAME)

        self._cfg_temp["payload"] = json.dumps(
            dict(
                device_class="temperature",
                name="Temperature",
                unique_id="{}_temperature".format(self.id),
                state_topic=self._stat_t,
                unit_of_measurement="C",
                value_template="{{ value_json.temperature}}",
            )
        )
        self._cfg_hum["payload"] = json.dumps(
            dict(
                device_class="humidity",
                name="Humidity",
                unique_id="{}_humidity".format(self.id),
                state_topic=self._stat_t,
                unit_of_measurement="%",
                value_template="{{ value_json.humidity}}",
            )
        )
        self._cfg_pr["payload"] = json.dumps(
            dict(
                device_class="pressure",
                name="Pressure",
                unique_id="{}_pressure".format(self.id),
                state_topic=self._stat_t,
                unit_of_measurement="Pa",
                value_template="{{ value_json.pressure}}",
            )
        )

    def show(self):
        return (
            "Stats",
            f"   Messages: Received: {self.n_msg}, Published: " + f"{self.n_pub}",
        )

    def stats(self):
        return {
            "temp": self._temp,
            "hum": self._hum,
            "press": self._press,
            "npub": self.n_pub,
            "nrecv": self.n_msg,
        }

    def on_stop(self, *args, **kwargs):  # same args and kwargs as self.task
        # self.app awaits self.app.server.wait_closed which
        # consumes Cancelled error so this does not run
        if self.log:
            self.log.info(f"[{self.name}.service] stopped")
            # aioctl.add(self.app.shutdown)
        if "as_mqtt_ambsense.service.disconnect" in aioctl.group().tasks:
            aioctl.delete("as_mqtt_ambsense.service.disconnect")
        aioctl.add(
            self.disconnect,
            self,
            name="as_mqtt_ambsense.service.disconnect",
            _id="as_mqtt_ambsense.service.disconnect",
        )

        return

    def on_error(self, e, *args, **kwargs):
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
            # if topic == b"homeassistant/sensor/esphome/pulse":
            #     color = json.loads(msg.decode())
            #     R, G, B = color["R"], color["G"], color["B"]
            #     if "as_mqtt.service.pulse" in aioctl.group().tasks:
            #         aioctl.delete("as_mqtt.service.pulse")
            #     aioctl.add(
            #         self.pulse,
            #         self,
            #         (R, G, B),
            #         1,
            #         loops=2,
            #         name="as_mqtt.service.pulse",
            #         _id="as_mqtt.service.pulse",
            #     )
        except Exception as e:
            if self.log:
                self.log.error(f"[{self.name}.service] {e}")

    @aioctl.aiotask
    async def task(
        self,
        client_id,
        server="0.0.0.0",
        port=1883,
        ssl=False,
        ssl_params={},
        hostname=None,
        keepalive=300,
        debug=True,
        log=None,
        i2c=(22, 21),
    ):
        self.log = log

        self.i2c = I2C(1, scl=Pin(i2c[0]), sda=Pin(i2c[1]))
        self.setup()
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
        await self.client.connect()
        # Subscribe
        # await self.client.subscribe(b"homeassistant/sensor/esphome/state")
        # await self.client.subscribe(b"homeassistant/sensor/esphome/pulse")
        if self.log:
            self.log.info(f"[{self.name}.service] MQTT client connected")
        # Discovery
        await self.client.publish(self._cfg_temp["topic"], self._cfg_temp["payload"])
        await asyncio.sleep(1)
        # HUMIDITY
        await self.client.publish(self._cfg_hum["topic"], self._cfg_hum["payload"])
        await asyncio.sleep(1)
        # PRESSURE
        # print(self._cfg_pr["payload"], self._cfg_pr["topic"])
        await self.client.publish(self._cfg_pr["topic"], self._cfg_pr["payload"])
        if self.log:
            self.log.info(f"[{self.name}.service] MQTT Client Discovery done!")

        self.n_pub += 3
        # Add subtask

        if "as_mqtt_ambsense.service.sense" in aioctl.group().tasks:
            aioctl.delete("as_mqtt_ambsense.service.sense")
        aioctl.add(
            self.sense,
            self,
            name="as_mqtt_ambsense.service.sense",
            _id="as_mqtt_ambsense.service.sense",
            on_stop=self.on_stop,
            on_error=self.on_error,
        )
        if self.log:
            self.log.info(f"[{self.name}.service] MQTT publish task enabled")

        # Wait for messages
        while True:
            await self.client.wait_msg()
            await asyncio.sleep(1)

    # @aioctl.aiotask
    # async def pulse(self, *args, **kwargs):
    #     if self.log:
    #         self.log.info(f"[as_mqtt.service.pulse] {args} {kwargs} pulse")
    #     await self.anm.pulse(*args, **kwargs)

    @aioctl.aiotask
    async def sense(self, *args, **kwargs):
        while True:
            temp, press, hum = self.sensor.read_compensated_data()
            self._temp = temp
            self._press = press
            self._hum = hum
            if self.log:
                self.log.info(
                    f"[{self.name}.service.sense] {temp} C {press} Pa {hum} %"
                )
            await self.client.publish(
                self._stat_t,
                json.dumps(
                    {
                        "temperature": f"{temp:.1f}",
                        "pressure": f"{press:.1f}",
                        "humidity": f"{hum:.1f}",
                    }
                ),
            )
            self.n_pub += 1
            await asyncio.sleep(5)

    @aioctl.aiotask
    async def disconnect(self, *args, **kwargs):
        if self.client:
            await self.client.disconnect()
        self.sslctx = None
        self.client = None
        gc.collect()


service = MQTTService("as_mqtt_ambsense")
