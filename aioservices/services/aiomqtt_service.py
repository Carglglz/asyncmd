import sys
import os
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
import machine


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
            "stats": False,
            "services": "*.service",
            "restart": ["aiomqtt.service"],
            "topics": [
                "device/all/cmd",
                f"device/{NAME}/cmd",
                "device/all/ota",
                f"device/{NAME}/ota",
            ],
        }

        self.sslctx = False
        self.client = None
        self.sensor = None
        self.n_msg = 0
        self.n_pub = 0
        self.td = 0
        self.id = NAME
        self.lock = asyncio.Lock()
        self._stat_buff = io.StringIO(3000)
        self._callbacks = {}
        self._topics = []

    def _suid(self, _aioctl, name):
        _name = name
        _id = 0
        if _aioctl.group():
            while name in _aioctl.group().tasks:
                _id += 1
                name = f"{_name}@{_id}"
        return name

    def add_callback(self, topic, callback):
        self._callbacks[topic] = callback

    def _df(self):
        size_info = os.statvfs("")
        self._total_b = size_info[0] * size_info[2]
        self._used_b = (size_info[0] * size_info[2]) - (size_info[0] * size_info[3])
        self._free_b = size_info[0] * size_info[3]

    def _taskinfo(self):
        self._tasks_total = len(aioctl.tasks_match("*"))
        self._services_total = len(aioctl.tasks_match("*.service"))
        self._ctasks_total = len(aioctl.tasks_match("*.service.*"))

    @aioctl.aiotask
    async def do_action(self, action, service):
        if action == "status":
            self._stat_buff.seek(0)
            json.dump(aiostats.stats(service), self._stat_buff)
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
        elif action == "ota":
            msg = service

            _ota_task = aioctl.group().tasks.get("ota.service")
            if _ota_task:
                _ota_service = _ota_task.service
                _ota_params = json.loads(msg.decode())
                # check if != hash
                # await publish TRUE --> start ota
                # await publish FALSE --> don't
                _ota_service.start_ota(
                    _ota_params["host"],
                    _ota_params["port"],
                    _ota_params["sha"],
                    blocks=_ota_params["blocks"],
                    bg=_ota_params["bg"],
                )
                while not _ota_service._OK:
                    await asyncio.sleep(1)
                async with self.lock:
                    await self.client.publish(
                        f"device/{self.id}/otaok".encode("utf-8"), b"OK"
                    )
            else:
                self.log.info(f"[{self.name}.service] No OTA service found")

        else:
            # topic-command-lib {"on":{"cmd": led.on, args:[], kwargs:{}, log:"LED ON",
            # resp:{"topic":"", "msg":""}}}  --> tpc["on"]()
            try:
                _resp = None
                if isinstance(action, str):
                    if "args" in service[action]:
                        _resp = service[action]["cmd"](
                            *service[action]["args"], **service[action]["kwargs"]
                        )
                    else:
                        _resp = service[action]["cmd"]()
                    if "log" in service[action]:
                        if self.log:
                            self.log.info(
                                f"[{self.name}.service] [CMD]: {service[action]['log']}"
                            )

                    if "resp" in service[action]:
                        async with self.lock:
                            await self.client.publish(
                                service[action]["resp"]["topic"].encode(),
                                json.dumps(
                                    {
                                        "cmd": action,
                                        "resp": _resp,
                                        "msg": service[action]["resp"]["msg"],
                                        "hostname": NAME,
                                    }
                                ),
                            )

                else:
                    pass
            except Exception as e:
                raise e

    def show(self):
        return (
            "Stats",
            f"   Messages: Received: {self.n_msg}, Published: "
            + f"{self.n_pub}"
            + f" Delta HS: {self.td} s",
        )

    def stats(self):
        # fs,mem,tasks,firmware
        self._df()
        self._taskinfo()
        gc.collect()
        return {
            "fstotal": self._total_b,
            "fsfree": self._free_b,
            "fsused": self._used_b,
            "mtotal": gc.mem_free() + gc.mem_alloc(),
            "mfree": gc.mem_free(),
            "mused": gc.mem_alloc(),
            "tasks": self._tasks_total,
            "services": self._services_total,
            "ctasks": self._ctasks_total,
            "requests": self.n_msg,
            "firmware": sys.version,
            "machine": sys.implementation._machine,
            "platform": sys.platform,
            "npub": self.n_pub,
            "nrecv": self.n_msg,
        }

    def on_stop(self, *args, **kwargs):  # same args and kwargs as self.task
        # self.app awaits self.app.server.wait_closed which
        # consumes Cancelled error so this does not run
        if self.log:
            self.log.info(f"[{self.name}.service] stopped")
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
            elif topic.decode() in self._callbacks:
                _tp = topic.decode()
                _cb_name = self._callbacks[_tp]["name"]
                _name = self._suid(aioctl, f"{self.name}.service.do_action.{_cb_name}")
                aioctl.add(
                    self._callbacks[_tp]["task"],
                    self._callbacks[_tp]["service"],
                    topic,
                    msg,
                    name=_name,
                    _id=_name,
                )

            elif topic.decode() in self._topics:
                if topic.decode().endswith("cmd"):
                    if msg.decode() == "reset":
                        self.log.info(f"[CMD]: {msg.decode()}")

                        _name = self._suid(
                            aioctl, f"{self.name}.service.{msg.decode()}"
                        )
                        aioctl.add(
                            self.reset,
                            self,
                            *self.args,
                            **self.kwargs,
                            name=_name,
                            _id=_name,
                        )
                        return
                    try:
                        from mqtt_cmdlib import mqtt_cmds

                        try:
                            act = json.loads(msg.decode())
                        except Exception:
                            act = msg.decode()
                        if isinstance(act, str):
                            _cmd_name = act
                        else:
                            _cmd_name = act["cmd"]

                        if _cmd_name in mqtt_cmds:
                            _name = self._suid(
                                aioctl, f"{self.name}.service.do_action.{_cmd_name}"
                            )

                            aioctl.add(
                                self.do_action,
                                self,
                                act,
                                mqtt_cmds,
                                name=_name,
                                _id=_name,
                            )
                        else:
                            if self.log:
                                self.log.error(
                                    f"[{self.name}.service] "
                                    + f"Command {_cmd_name} not found"
                                )

                    except Exception as e:
                        if self.log:
                            self.log.error(
                                f"[{self.name}.service] Command lib not found: {e}"
                            )
                elif topic.decode().endswith("ota"):
                    _name = self._suid(aioctl, f"{self.name}.service.do_action.ota")
                    aioctl.add(self.do_action, self, "ota", msg, name=_name, _id=_name)

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
        stats=False,
        services="*.service",
        restart=True,
        topics=[],
        log=None,
    ):
        self.log = log
        self._topics = topics
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

            for tp in topics:
                if isinstance(tp, str):
                    tp = tp.encode("utf-8")
                await self.client.subscribe(tp)
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
            restart=restart,
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

        # Add stats pub
        if stats:
            if f"{self.name}.service.stats" in aioctl.group().tasks:
                aioctl.delete(f"{self.name}.service.stats")
            aioctl.add(
                self.stats_pub,
                self,
                services=services,
                name=f"{self.name}.service.stats",
                _id=f"{self.name}.service.stats",
                on_error=self.on_error,
                restart=restart,
            )
            if self.log:
                self.log.info(f"[{self.name}.service] MQTT stats task enabled")

        # Wait for messages
        while True:
            await self.client.wait_msg()
            await asyncio.sleep(1)

            if self.log and debug:
                self.log.info(f"[{self.name}.service] MQTT waiting...")

    @aioctl.aiotask
    async def ping(self, *args, **kwargs):
        while True:
            async with self.lock:
                # await self.client.publish(self._STATE_TOPIC, b"OK")
                await self.client.ping()
                # await self.client.wait_msg()
                self.n_pub += 1
            await asyncio.sleep(5)

    @aioctl.aiotask
    async def stats_pub(self, *args, **kwargs):
        service = kwargs.get("services")
        while True:
            self._stat_buff.seek(0)
            json.dump(aiostats.stats(service), self._stat_buff)
            len_b = self._stat_buff.tell()
            self._stat_buff.seek(0)
            async with self.lock:
                await self.client.publish(
                    self._STATUS_TOPIC, self._stat_buff.read(len_b).encode("utf-8")
                )
            self.n_pub += 1
            if self.log:
                self.log.info(f"[{self.name}.service] @ [STATUS]: {service}")
            await asyncio.sleep(10)

    @aioctl.aiotask
    async def clean(self, *args, **kwargs):
        while True:
            for _ctask in aioctl.tasks_match(f"{self.name}.service.do_action*"):
                if aiostats.task_status(_ctask) == "done":
                    if _ctask in self._child_tasks:
                        self._child_tasks.remove(_ctask)
                    else:
                        aioctl.group().tasks[_ctask].service._child_tasks.remove(_ctask)
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

    @aioctl.aiotask
    async def reset(self, *args, **kwargs):
        _res = 5
        if self.log and kwargs.get("debug"):
            self.log.info(f"[{self.name}.service] Rebooting in {_res} s")
        await asyncio.sleep(_res)
        for service in aioctl.tasks_match("*.service*"):
            if service != f"{self.name}.service.reset":
                self.log.info(f"[{self.name}.service] Stopping {service}")
                aioctl.stop(service)

        if self.log and kwargs.get("debug"):
            self.log.info(f"[{self.name}.service] Rebooting now")

        await asyncio.sleep(1)
        machine.reset()


service = MQTTService("aiomqtt")
