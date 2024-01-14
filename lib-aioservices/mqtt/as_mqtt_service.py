import ssl as _ssl
from async_base_animations import _loadnpxy
from aioclass import Service
import aioctl
from async_mqtt import MQTTClient
import asyncio
import json
import random
import gc


class MQTTService(Service):
    def __init__(self, name):
        super().__init__(name)
        self.info = "Async MQTT client v1.0"
        self.type = "runtime.service"  # continuous running, other types are
        self.enabled = True
        self.docs = "https://github.com/Carglglz/asyncmd/blob/main/README.md"
        self.args = ["async_mqtt_client"]
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
        }
        self.anm = _loadnpxy(18, 71, timing=(400, 850, 850, 400))

        self.sslctx = False
        self.client = None
        self.n_msg = 0
        self.n_pub = 0

    def show(self):
        return (
            "Stats",
            f"   Messages: Received: {self.n_msg}, Published: " + f"{self.n_pub}",
        )

    def on_stop(self, *args, **kwargs):  # same args and kwargs as self.task
        # self.app awaits self.app.server.wait_closed which
        # consumes Cancelled error so this does not run
        if self.log:
            self.log.info(f"[{self.name}.service] stopped")
            # aioctl.add(self.app.shutdown)
        if "as_mqtt.service.disconnect" in aioctl.group().tasks:
            aioctl.delete("as_mqtt.service.disconnect")
        aioctl.add(
            self.disconnect,
            self,
            name="as_mqtt.service.disconnect",
            _id="as_mqtt.service.disconnect",
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
            if topic == b"homeassistant/sensor/esphome/pulse":
                color = json.loads(msg.decode())
                R, G, B = color["R"], color["G"], color["B"]
                if "as_mqtt.service.pulse" in aioctl.group().tasks:
                    aioctl.delete("as_mqtt.service.pulse")
                aioctl.add(
                    self.pulse,
                    self,
                    (R, G, B),
                    1,
                    loops=2,
                    name="as_mqtt.service.pulse",
                    _id="as_mqtt.service.pulse",
                )
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
    ):
        self.log = log
        if ssl:
            if not self.sslctx:
                self.sslctx = _ssl.SSLContext(_ssl.PROTOCOL_TLS_CLIENT)
                self.sslctx.load_verify_locations(cafile=ssl_params["ca"])
                self.sslctx.load_cert_chain(ssl_params["cert"], ssl_params["key"])
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
        await self.client.subscribe(b"homeassistant/sensor/esphome/state")
        await self.client.subscribe(b"homeassistant/sensor/esphome/pulse")
        # Add subtask

        if "as_mqtt.service.sense" in aioctl.group().tasks:
            aioctl.delete("as_mqtt.service.sense")
        aioctl.add(
            self.sense,
            self,
            42,
            sense_param="low",
            name="as_mqtt.service.sense",
            _id="as_mqtt.service.sense",
            on_stop=self.on_stop,
        )
        # Wait for messages
        while True:
            await self.client.wait_msg()
            await asyncio.sleep(1)

    @aioctl.aiotask
    async def pulse(self, *args, **kwargs):
        if self.log:
            self.log.info(f"[as_mqtt.service.pulse] {args} {kwargs} pulse")
        await self.anm.pulse(*args, **kwargs)

    @aioctl.aiotask
    async def sense(self, *args, **kwargs):
        while True:
            val = random.random()
            if self.log:
                self.log.info(
                    f"[{self.name}.service.sense] {args} {kwargs} " + f"@ sensor: {val}"
                )
            await self.client.publish(
                b"homeassistant/sensor/esphome/state", f"{val}".encode()
            )
            self.n_pub += 1
            await asyncio.sleep(30)

    @aioctl.aiotask
    async def disconnect(self, *args, **kwargs):
        if self.client:
            await self.client.disconnect()
        self.sslctx = None
        self.client = None
        gc.collect()


service = MQTTService("as_mqtt")
