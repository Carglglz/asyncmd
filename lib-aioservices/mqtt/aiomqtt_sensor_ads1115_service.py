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


if aioctl.getenv("ADS1115", False):
    from ads1115 import ADS1115
else:

    class ADS1115:
        def __init__(self, *args, **kwargs):
            pass

        def read(self):
            return 1 + random.random()

        def raw_to_v(self):
            return random.random()


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
        self.info = f"Async MQTT ADS1115 client v{self.version}"
        self.type = "runtime.service"  # continuous running, other types are
        self.enabled = True
        self.docs = "https://github.com/Carglglz/asyncmd/blob/main/README.md"
        self.id = aioctl.getenv("HOSTNAME", sys.platform)
        self.args = [self.id]
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
            "restart": ["aiomqtt_sensor_ads1115.service"],
            "topics": [f"device/{self.id}/state", "device/all/state"],
            "i2c": (22, 21),
            "address": 72,
            "gain": 1,
            "loglevel": "INFO",
            "service_logger": True,
        }

        self.sslctx = False
        self.client = None
        self.sensor = None
        self.n_msg = 0
        self.n_pub = 0
        self._dA = array("f", (0 for i in range(10)))
        self._dB = array("f", (0 for i in range(10)))
        self.td = 0
        self.i2c = None

    def setup(self, addr, gain):
        self.unique_id = "PressureSensor_{}".format(self.id.split()[0].lower())
        self.sensor = ADS1115(self.i2c, addr, gain)
        self._cfg_pA = {
            "topic": self._CONFIG_TOPIC.format(self.id + "PA"),
            "payload": "",
        }
        self._cfg_pB = {
            "topic": self._CONFIG_TOPIC.format(self.id + "PB"),
            "payload": "",
        }
        self._stat_t = self._STATE_TOPIC.format(self.id)

        self._cfg_pA["payload"] = json.dumps(
            dict(
                device_class="pressure",
                name="PressureA",
                unique_id="{}_pressureA".format(self.id),
                state_topic=self._stat_t,
                unit_of_measurement="BAR",
                value_template="{{ value_json.pressureA}}",
            )
        )
        self._cfg_pB["payload"] = json.dumps(
            dict(
                device_class="pressure",
                name="PressureB",
                unique_id="{}_pressureB".format(self.id),
                state_topic=self._stat_t,
                unit_of_measurement="BAR",
                value_template="{{ value_json.pressureB}}",
            )
        )

    def measureA(self):
        pressA = self.sensor.raw_to_v(self.sensor.read())
        pressA = ((pressA * 25) - 12.5) * 0.0689476
        return pressA

    def measureB(self):
        pressB = self.sensor.raw_to_v(self.sensor.read(channel1=3))
        pressB = ((pressB * 25) - 12.5) * 0.0689476
        return pressB

    def averagePA(self):
        return sum(self._dA) / len(self._dA)

    def averagePB(self):
        return sum(self._dB) / len(self._dB)

    def show(self):
        return (
            "Stats",
            f"   Messages: Received: {self.n_msg}, Published: "
            + f"{self.n_pub}"
            + f" Delta HS: {self.td} s",
        )

    def stats(self):
        return {
            "pressA": self.averagePA(),
            "pressB": self.averagePB(),
        }

    def on_stop(self, *args, **kwargs):  # same args and kwargs as self.task
        # self.app awaits self.app.server.wait_closed which
        # consumes Cancelled error so this does not run
        self.client = None
        if self.log:
            self.log.info("stopped")

        return

    def on_error(self, e, *args, **kwargs):
        self.client = None
        if self.log:
            self.log.error(f"Error callback {e}")
        return e

    def on_receive(self, topic, msg):
        try:
            self.n_msg += 1
            if self.log:
                self.log.info(f"@ [{topic.decode()}]:" + f" {msg.decode()}")
        except Exception as e:
            if self.log:
                self.log.error(f"{e}")

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
        i2c=(22, 21),
        gain=1,
        address=72,
        log=None,
        loglevel="INFO",
        service_logger=True,
    ):
        self.add_logger(log, level=loglevel, service_logger=service_logger)
        self.i2c = I2C(1, scl=Pin(i2c[0]), sda=Pin(i2c[1]))
        self.setup(address, gain)
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

            # add callback

            # Subscribe
            async with self.lock:
                for tp in topics:
                    self.aiomqtt_service.add_callback(
                        tp, {"name": "sense_pr", "task": self.sense_cb, "service": self}
                    )
                    if isinstance(tp, str):
                        tp = tp.encode("utf-8")
                    await self.client.subscribe(tp)

        if self.log:
            self.log.info("MQTT client connected")
        # Discovery
        async with self.lock:
            # PressA
            await self.client.publish(self._cfg_pA["topic"], self._cfg_pA["payload"])
            # PressB
            await self.client.publish(self._cfg_pB["topic"], self._cfg_pB["payload"])
        if self.log:
            self.log.info("MQTT Client Discovery done!")

        self.n_pub += 3
        # Add subtask

        self.add_ctask(
            aioctl,
            self.sense,
            "sense",
            on_stop=self.on_stop,
            on_error=self.on_error,
            restart=restart,
        )

        if self.log:
            self.log.info("MQTT publish task enabled")

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
                    self.log.info("MQTT sensor OK")

    @aioctl.aiotask
    async def sense_cb(self, topic, msg):
        self.on_receive(topic, msg)

        for i in range(10):
            self._dA[i] = self.measureA()
        for i in range(10):
            self._dB[i] = self.measureB()

        if self.log:
            self.log.info(
                f"[{self.name}.service.sense_cb] {self.averagePA()} Abar "
                + f"{self.averagePB()} Bbar",
                cname="sense",
            )
        async with self.lock:
            await self.client.publish(
                topic.replace(b"state", b"sense"),
                json.dumps(
                    {
                        "pressA": f"{self.averagePA():.2f}",
                        "pressB": f"{self.averagePB():.2f}",
                        "hostname": self.id,
                    }
                ),
            )
        self.n_pub += 1

    @aioctl.aiotask
    async def sense(self, *args, **kwargs):
        while True:
            for i in range(10):
                self._dA[i] = self.measureA()
            for i in range(10):
                self._dB[i] = self.measureB()

            if self.log:
                self.log.info(
                    f"[{self.name}.service.sense] {self.averagePA()} Abar "
                    + f"{self.averagePB()} Bbar",
                    cname="sense",
                )

            async with self.lock:
                await self.client.publish(
                    self._stat_t,
                    json.dumps(
                        {
                            "pressA": f"{self.averagePA():.2f}",
                            "pressB": f"{self.averagePB():.2f}",
                            "hostname": self.id,
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


service = MQTTService("aiomqtt_sensor_ads1115")
