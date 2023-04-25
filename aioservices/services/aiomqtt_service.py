import time
import ssl as _ssl
from aioclass import Service
import aioctl
from async_mqtt import MQTTClient
import uasyncio as asyncio
import json
import gc
import socket
import io
from hostname import NAME
import aiostats


class MQTTService(Service):
    _STATE_TOPIC = "device/{}/state"
    _STATUS_TOPIC = "device/{}/status"
    _SERVICE_TOPIC = "device/{}/service"
    _TASK_TOPIC = "device/{}/task"

    def __init__(self, name):
        super().__init__(name)
        self.version = "1.0"
        self.info = f"Async MQTT Controller client v{self.version}"
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
        }

        self.sslctx = False
        self.client = None
        self.sensor = None
        self.n_msg = 0
        self.n_pub = 0
        self.td = 0
        self.id = NAME
        self.lock = asyncio.Lock()
        self._stat_buff = io.StringIO(2000)

    def _suid(self, _aioctl, name):
        _name = name
        _id = 0
        if _aioctl.group():
            while name in _aioctl.group().tasks:
                _id += 1
                name = f"{_name}@{_id}"
        return name

    @aioctl.aiotask
    async def do_action(self, action, service):
        if action == "status":
            self._stat_buff.seek(0)
            json.dump({service: {action: aiostats.stats(service)}}, self._stat_buff)
            len_b = self._stat_buff.tell()
            self._stat_buff.seek(0)
            async with self.lock:
                await self.client.publish(
                    self._STATUS_TOPIC, self._stat_buff.read(len_b).encode("utf-8")
                )
            self.n_pub += 1
            if self.log:
                self.log.info(f"[{self.name}.service] @ [{action.upper()}]: {service}")

        elif action == "start":
            for _task in aioctl.tasks_match(service):
                aioctl.start(_task)
                if _task in aioctl.group().tasks:
                    async with self.lock:
                        await self.client.publish(
                            self._STATUS_TOPIC,
                            json.dumps(
                                {service: {action: aiostats.task_status(_task)}}
                            ),
                        )

                    self.n_pub += 1
                    if self.log:
                        self.log.info(
                            f"[{self.name}.service] @ [{action.upper()}]: {service}"
                        )

        elif action == "stop":
            for _task in aioctl.tasks_match(service):
                aioctl.stop(_task)

                if _task in aioctl.group().tasks:
                    async with self.lock:
                        await self.client.publish(
                            self._STATUS_TOPIC,
                            json.dumps(
                                {service: {action: aiostats.task_status(_task)}}
                            ),
                        )

                    self.n_pub += 1
                    if self.log:
                        self.log.info(
                            f"[{self.name}.service] @ [{action.upper()}]: {service}"
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
            "npub": self.n_pub,
            "nrecv": self.n_msg,
        }

    def on_stop(self, *args, **kwargs):  # same args and kwargs as self.task
        # self.app awaits self.app.server.wait_closed which
        # consumes Cancelled error so this does not run
        if self.log:
            self.log.info(f"[{self.name}.service] stopped")
            # aioctl.add(self.app.shutdown)
        if f"{self.name}.service.disconnect" in aioctl.group().tasks:
            aioctl.delete(f"{self.name}.service.disconnect")
        aioctl.add(
            self.disconnect,
            self,
            name=f"{self.name}.service.disconnect",
            _id=f"{self.name}.service.disconnect",
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
            if topic == self._SERVICE_TOPIC:
                act = json.loads(msg.decode())
                for action, serv in act.items():
                    if isinstance(serv, list):
                        for srv in serv:
                            _name = self._suid(aioctl, f"{self.name}.service.do_action")
                            aioctl.add(
                                self.do_action, self, action, srv, name=_name, _id=_name
                            )

                    else:
                        _name = self._suid(aioctl, f"{self.name}.service.do_action")
                        aioctl.add(
                            self.do_action, self, action, serv, name=_name, _id=_name
                        )

        except Exception as e:
            if self.log:
                self.log.error(f"[{self.name}.service] Receive callback: {e}")

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
        if isinstance(self._SERVICE_TOPIC, str):
            self._TASK_TOPIC = self._TASK_TOPIC.format(client_id).encode("utf-8")
            self._SERVICE_TOPIC = self._SERVICE_TOPIC.format(client_id).encode("utf-8")
            self._STATUS_TOPIC = self._STATUS_TOPIC.format(client_id).encode("utf-8")
            self._STATE_TOPIC = self._STATE_TOPIC.format(client_id).encode("utf-8")
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

        if self.log:
            self.log.info(f"[{self.name}.service] MQTT client connected")

        # Subscribe to service topic
        async with self.lock:
            await self.client.subscribe(self._SERVICE_TOPIC)
            # Subscribe to task topic
            await self.client.subscribe(self._TASK_TOPIC)
            # Subscribe to state topic
            await self.client.subscribe(self._STATE_TOPIC)
        if self.log:
            self.log.info(
                f"[{self.name}.service] MQTT Client Services and Tasks enabled!"
            )

        # Add PING subtask

        if f"{self.name}.service.ping" in aioctl.group().tasks:
            aioctl.delete(f"{self.name}.service.ping")
        aioctl.add(
            self.ping,
            self,
            name=f"{self.name}.service.ping",
            _id=f"{self.name}.service.ping",
            on_stop=self.on_stop,
            on_error=self.on_error,
        )
        if self.log:
            self.log.info(f"[{self.name}.service] MQTT ping task enabled")

        # Add clean subtask

        if f"{self.name}.service.clean" in aioctl.group().tasks:
            aioctl.delete(f"{self.name}.service.clean")
        aioctl.add(
            self.clean,
            self,
            name=f"{self.name}.service.clean",
            _id=f"{self.name}.service.clean",
            on_error=self.on_error,
        )
        if self.log:
            self.log.info(f"[{self.name}.service] MQTT clean task enabled")

        # Wait for messages
        while True:
            await self.client.wait_msg()
            await asyncio.sleep(1)

    @aioctl.aiotask
    async def ping(self, *args, **kwargs):
        while True:
            async with self.lock:
                await self.client.publish(self._STATE_TOPIC, b"OK")
            self.n_pub += 1
            await asyncio.sleep(5)

    @aioctl.aiotask
    async def clean(self, *args, **kwargs):
        while True:
            for _ctask in aioctl.tasks_match(f"{self.name}.service.do_action*"):
                if aiostats.task_status(_ctask) == "done":
                    self._child_tasks.remove(_ctask)
                    aioctl.delete(_ctask)
                    if self.log:
                        self.log.info(f"[{self.name}.service] {_ctask} cleaned")
                    gc.collect()

            await asyncio.sleep(5)

    @aioctl.aiotask
    async def disconnect(self, *args, **kwargs):
        if self.client:
            async with self.lock:
                await self.client.disconnect()
        self.sslctx = None
        self.client = None
        gc.collect()


service = MQTTService("aiomqtt")
