import sys
import os
import time
import ssl as _ssl
from aioclass import Service
import aioctl
from async_mqtt import MQTTClient
import asyncio
import json
import gc
import socket
import io
import aiostats
import machine
import re


class MQTTService(Service):
    _STATE_TOPIC = "device/{}/state"
    _STATUS_TOPIC = "device/{}/status"
    _SERVICE_TOPIC = "device/{}/service"
    _TASK_TOPIC = "device/{}/task"

    def __init__(self, name):
        super().__init__(name)
        self.version = "1.0"
        self.info = f"Async MQTT Controller client v{self.version}"
        self.type = "runtime.service"
        self.enabled = True
        self.docs = "https://github.com/Carglglz/asyncmd/blob/main/README.md"
        self.id = aioctl.getenv("HOSTNAME", sys.platform)
        self.args = [self.id]
        self.kwargs = {
            "server": "0.0.0.0",
            "port": 1883,
            "hostname": None,
            "ssl": False,
            "ssl_params": {},
            "autoconfig": False,
            "keepalive": 300,
            "debug": True,
            "on_stop": self.on_stop,
            "on_error": self.on_error,
            "stats": False,
            "services": "*.service",
            "restart": {"aiomqtt.service"},
            "topics": [],
            "ota_check": True,
            "fwfile": None,
            "fwf_re": True,
            "loglevel": "INFO",
            "service_logger": True,
        }

        self.sslctx = False
        self.client = None
        self.sensor = None
        self.n_msg = 0
        self.n_pub = 0
        self.td = 0
        self.lock = asyncio.Lock()
        self.client_ready = asyncio.Event()
        self._stat_buff = io.StringIO(5000)
        self._tb_buff = io.StringIO(800)
        self._callbacks = {}
        self._topics = {
            "device/all/cmd",
            f"device/{self.id}/cmd",
            "device/all/ota",
            f"device/{self.id}/ota",
            "device/all/logger",
            f"device/{self.id}/logger",
            "device/all/service",
        }

        self._ota_check = False
        self._fwfile = None
        self._fwf_re = None
        self._log_idx = None
        self._reset_causes = {
            machine.PWRON_RESET: "POWER ON",
            machine.HARD_RESET: "HARD RESET",
            machine.WDT_RESET: "WDT RESET",
            machine.DEEPSLEEP_RESET: "DEEP SLEEP",
            machine.SOFT_RESET: "SOFT RESET",
        }

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
        size_info = os.statvfs(".")
        self._total_b = size_info[0] * size_info[2]
        self._used_b = (size_info[0] * size_info[2]) - (size_info[0] * size_info[3])
        self._free_b = size_info[0] * size_info[3]

    def _taskinfo(self):
        self._tasks_total = len(aioctl.tasks_match("*"))
        self._services_total = len(aioctl.tasks_match("*.service"))
        self._ctasks_total = len(aioctl.tasks_match("*.service.*"))

    def _grep(self, patt, filename):
        if isinstance(patt, list):
            pass
        else:
            patt = [patt]
        _pattlst = (
            re.compile(_patt.replace(".", r"\.").replace("*", ".*") + "$")
            for _patt in patt
        )
        try:
            return any(_pattrn.match(filename) for _pattrn in _pattlst)
        except Exception:
            return None

    @aioctl.aiotask
    async def do_action(self, action, service):
        if action == "status":
            self._stat_buff.seek(0)
            if ":" in service:
                service, _debug = service.split(":")
                json.dump(
                    aiostats.stats(service, debug=_debug, traceback=self._tb_buff),
                    self._stat_buff,
                )
            else:
                json.dump(aiostats.stats(service), self._stat_buff)
            len_b = self._stat_buff.tell()
            self._stat_buff.seek(0)
            async with self.lock:
                await self.client.publish(
                    self._STATUS_TOPIC, self._stat_buff.read(len_b).encode("utf-8")
                )
            self.n_pub += 1
            if self.log:
                self.log.info(f"@ [{action.upper()}]: {service}")

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
                        self.log.info(f"@ [{action.upper()}]: {service}")

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
                        self.log.info(f"@ [{action.upper()}]: {service}")
        elif action == "traceback":
            self._stat_buff.seek(0)
            self._tb_buff.seek(0)
            aioctl.traceback(service, file=self._tb_buff)
            len_tb = self._tb_buff.tell()
            self._tb_buff.seek(0)
            json.dump(
                {service: {action: self._tb_buff.read(len_tb)}, "hostname": self.id},
                self._stat_buff,
            )
            len_b = self._stat_buff.tell()
            self._stat_buff.seek(0)

            async with self.lock:
                await self.client.publish(
                    self._STATUS_TOPIC, self._stat_buff.read(len_b).encode("utf-8")
                )
            self.n_pub += 1
            if self.log:
                self.log.info(f"@ [{action.upper()}]: {service}")

        elif action == "report":
            try:
                os.stat(f".{service}")
                if self.log:
                    self.log.info(f"sending {service} report...")
                async with self.lock:
                    await aiostats.pipefile(
                        self.client,
                        f"device/{self.id}/report/{service}".encode("utf-8"),
                        file=f".{service}",
                    )
            except Exception as e:
                if self.log:
                    self.log.error(f"@ [{action.upper()}]:{e}")

        elif action == "log":
            async with self.lock:
                await aiostats.pipelog(
                    self.client,
                    f"device/{self.id}/log".encode("utf-8"),
                    from_idx=self._log_idx,
                )

            self._log_idx = aioctl._AIOCTL_LOG.tell()
        elif "error.log" in action and isinstance(action, str):
            if action.startswith("error.log"):
                async with self.lock:
                    await aiostats.pipefile(
                        self.client,
                        f"device/{self.id}/log".encode("utf-8"),
                        file=action,
                    )
        elif action == "env":
            try:
                os.stat(service)
                if self.log:
                    self.log.info(f"sending DOTENV: {service} ...")
                async with self.lock:
                    await aiostats.pipefile(
                        self.client,
                        f"device/{self.id}/env/{service}".encode("utf-8"),
                        file=f"{service}",
                    )
            except Exception as e:
                if self.log:
                    self.log.error(f"@ [{action.upper()}]:{e}")
        elif action == "set":
            try:
                import dotenv

                for env, vals in service.items():
                    dotenv.set_env_values(env, vals)

                for env in service:
                    os.stat(env)
                    if self.log:
                        self.log.info(f"sending DOTENV: {env} ...")
                    async with self.lock:
                        await aiostats.pipefile(
                            self.client,
                            f"device/{self.id}/env/{env}".encode("utf-8"),
                            file=f"{env}",
                        )

            except Exception as e:
                if self.log:
                    self.log.error(f"@ [{action.upper()}]: {e}")

        elif action == "config":
            import aioservice

            try:
                for _act, _serv in service.items():
                    if _act == "get":
                        if _serv == "*":
                            _serv = None
                        async with self.lock:
                            await self.client.publish(
                                self._STATUS_TOPIC.replace(b"status", b"config"),
                                json.dumps(aioservice.get_config(_serv)),
                            )

                        self.n_pub += 1
                        if self.log:
                            self.log.info(f"@ [CONFIG]:{_act} {_serv}")
                    elif _act in ["set", "enable", "disable"]:
                        if _act == "enable":
                            if isinstance(_serv, list):
                                for _sv in _serv:
                                    aioservice.enable(_sv)
                            else:
                                aioservice.enable(_serv)
                        elif _act == "disable":
                            if isinstance(_serv, list):
                                for _sv in _serv:
                                    aioservice.disable(_sv)
                            else:
                                aioservice.disable(_serv)
                        else:
                            for kserv, _conf in _serv.items():
                                aioservice.config(
                                    kserv, True, *_conf["args"], **_conf["kwargs"]
                                )

                        if self.log:
                            self.log.info(f"@ [CONFIG]:{_act} {_serv}")
            except Exception as e:
                if self.log:
                    self.log.error(f"@ [CONFIG]:{_act} {_serv} {e}")

        elif action == "ota":
            msg = service

            _ota_task = aioctl.group().tasks.get("ota.service")
            if msg.decode() == "check" and _ota_task:
                if self._ota_check:
                    _ota_task.service._new_sha_check = True
                _csha = _ota_task.service._comp_sha_ota("", rtn=True)
                ip = None
                if "network.service" in aioctl.group().tasks:
                    ip = (
                        aioctl.group()
                        .tasks["network.service"]
                        .service.wlan.ifconfig()[0]
                    )
                if _csha:
                    async with self.lock:
                        await self.client.publish(
                            f"device/{self.id}/otacheck".encode("utf-8"),
                            json.dumps(
                                {"sha": _csha, "fwfile": self._fwfile, "ip": ip}
                            ),
                        )
                return

            if _ota_task:
                _ota_service = _ota_task.service
                _ota_params = json.loads(msg.decode())
                # check if != hash
                if self._ota_check:
                    _ota_service._new_sha_check = True
                    if self._fwfile:
                        if self._fwfile != _ota_params["fwfile"]:
                            if not self._fwf_re:
                                if self.log:
                                    self.log.info("No new OTA update")
                                return
                            elif not self._grep(self._fwfile, _ota_params["fwfile"]):
                                if self.log:
                                    self.log.info("No new OTA update")
                                return
                    else:
                        self._fwfile = _ota_params["fwfile"]
                if _ota_service._comp_sha_ota(_ota_params["sha"]):
                    if self.log:
                        self.log.info("No new OTA update")
                    return
                if self._ota_check and self._fwfile:
                    async with self.lock:
                        await self.client.publish(
                            f"device/{self.id}/otacheck".encode("utf-8"),
                            json.dumps(
                                {
                                    "notify": False,
                                    "sha": _ota_service._comp_sha_ota("", rtn=True),
                                    "fwfile": self._fwfile
                                    if not self._fwf_re
                                    else _ota_params["fwfile"],
                                    "ip": (
                                        aioctl.group()
                                        .tasks["network.service"]
                                        .service.wlan.ifconfig()[0]
                                    ),
                                }
                            ),
                        )

                _ota_service.start_ota(
                    _ota_params["host"],
                    _ota_params["port"],
                    _ota_params["sha"],
                    blocks=_ota_params["blocks"],
                    bg=_ota_params["bg"],
                )
                while not _ota_service._OK:
                    await asyncio.sleep(1)

                await asyncio.sleep(1)
                async with self.lock:
                    await self.client.publish(
                        f"device/{self.id}/otaok".encode("utf-8"), b"OK"
                    )
            else:
                if self.log:
                    self.log.info("No OTA service found")
        elif action == "help" or "?" in action:
            if action == "help":
                _resp = service.get(action)
            else:
                action = action.replace("?", "")
                _resp = service.get("help").get(action)
            if _resp:
                async with self.lock:
                    await self.client.publish(
                        f"device/{self.id}/help".encode("utf-8"),
                        json.dumps(_resp),
                    )

        else:
            # topic-command-lib {"on":{"cmd": led.on, args:[], kwargs:{}, log:"LED ON",
            # resp:{"topic":"", "msg":""}}}  --> tpc["on"]()
            try:
                _resp = None
                if isinstance(action, str):
                    if "args" in service[action]:
                        if "async" in service[action]:
                            _resp = await service[action]["cmd"](
                                *service[action]["args"], **service[action]["kwargs"]
                            )
                        else:
                            _resp = service[action]["cmd"](
                                *service[action]["args"], **service[action]["kwargs"]
                            )
                    else:
                        if "async" in service[action]:
                            _resp = await service[action]["cmd"]()
                        else:
                            _resp = service[action]["cmd"]()
                    if "log" in service[action]:
                        if self.log:
                            self.log.info(f"[CMD]: {service[action]['log']}")

                    if "resp" in service[action]:
                        async with self.lock:
                            await self.client.publish(
                                service[action]["resp"]["topic"].encode(),
                                json.dumps(
                                    {
                                        "cmd": action,
                                        "resp": _resp,
                                        "msg": service[action]["resp"]["msg"],
                                        "hostname": self.id,
                                    }
                                ),
                            )

                else:  # json command
                    _args = action.get("args")
                    _kwargs = action.get("kwargs")
                    action = action["cmd"]
                    if not _args:
                        _args = service[action].get("args")
                    if not _kwargs:
                        _kwargs = service[action].get("kwargs")
                    if "args" in service[action]:
                        if "async" in service[action]:
                            _resp = await service[action]["cmd"](*_args, **_kwargs)
                        else:
                            _resp = service[action]["cmd"](*_args, **_kwargs)
                    else:
                        if "async" in service[action]:
                            _resp = await service[action]["cmd"]()
                        else:
                            _resp = service[action]["cmd"]()
                    if "log" in service[action]:
                        if self.log:
                            self.log.info(f"[CMD]: {service[action]['log']}")

                    if "resp" in service[action]:
                        async with self.lock:
                            await self.client.publish(
                                service[action]["resp"]["topic"].encode(),
                                json.dumps(
                                    {
                                        "cmd": action,
                                        "resp": _resp,
                                        "msg": service[action]["resp"]["msg"],
                                        "hostname": self.id,
                                    }
                                ),
                            )

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
            "reset": self._reset_causes.get(machine.reset_cause()),
        }

    def on_stop(self, *args, **kwargs):  # same args and kwargs as self.task
        # self.app awaits self.app.server.wait_closed which
        # consumes Cancelled error so this does not run
        self.client_ready.clear()
        if self.log:
            self.log.info("stopped")

        self.add_ctask(aioctl, self.disconnect, "disconnect")
        return

    def on_error(self, e, *args, **kwargs):
        self.client_ready.clear()
        if self.log:
            self.log.error(f"Error callback {e}")
        return e

    def on_receive(self, topic, msg):
        try:
            self.n_msg += 1
            if self.log:
                self.log.info(f"@ [{topic.decode()}]:" + f" {msg.decode()}")
            if topic == self._SERVICE_TOPIC or topic.endswith(b"/service"):
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

                        if (
                            _cmd_name in mqtt_cmds
                            or _cmd_name.replace("?", "") in mqtt_cmds
                        ):
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
                                self.log.error("" + f"Command {_cmd_name} not found")

                    except Exception as e:
                        if self.log:
                            self.log.error(f"Command lib not found: {e}")
                elif topic.decode().endswith("ota"):
                    _name = self._suid(aioctl, f"{self.name}.service.do_action.ota")
                    aioctl.add(self.do_action, self, "ota", msg, name=_name, _id=_name)

                elif topic.decode().endswith("logger"):
                    _name = self._suid(aioctl, f"{self.name}.service.do_action.logger")
                    aioctl.add(
                        self.do_action, self, msg.decode(), msg, name=_name, _id=_name
                    )

        except Exception as e:
            if self.log:
                self.log.error(f"Receive callback: {e}")

    @aioctl.aiotask
    async def task(
        self,
        client_id,
        server="0.0.0.0",
        port=1883,
        ssl=False,
        ssl_params={},
        hostname=None,
        autoconfig=False,
        keepalive=300,
        debug=True,
        stats=False,
        services="*.service",
        restart=True,
        topics=[],
        ota_check=True,
        fwfile=None,
        fwf_re=True,
        log=None,
        loglevel="INFO",
        service_logger=False,
    ):
        self.add_logger(log, level=loglevel, service_logger=service_logger)
        self.client_ready.clear()
        for top in topics:
            self._topics.add(top)
        self._ota_check = ota_check
        self._fwfile = aioctl.getenv("FWFILE", fwfile)
        self._fwf_re = fwf_re
        if isinstance(self._SERVICE_TOPIC, str):
            self._TASK_TOPIC = self._TASK_TOPIC.format(client_id).encode("utf-8")
            self._SERVICE_TOPIC = self._SERVICE_TOPIC.format(client_id).encode("utf-8")
            self._STATUS_TOPIC = self._STATUS_TOPIC.format(client_id).encode("utf-8")
            self._STATE_TOPIC = self._STATE_TOPIC.format(client_id).encode("utf-8")
        if autoconfig:
            if "network.service" in aioctl.group().tasks:
                ssid = aioctl.group().tasks.get("network.service").service.ssid
                server, port, hostname, ssl = autoconfig.get(
                    ssid, [server, port, hostname, ssl]
                )

        if ssl:
            if not self.sslctx:
                self.sslctx = _ssl.SSLContext(_ssl.PROTOCOL_TLS_CLIENT)
                self.sslctx.load_verify_locations(cafile=ssl_params["ca"])
                if ssl_params.get("cert") and ssl_params.get("key"):
                    self.sslctx.load_cert_chain(ssl_params["cert"], ssl_params["key"])
        ai = socket.getaddrinfo(server, port)
        _server = ai[0][-1]
        if isinstance(_server, tuple):
            server = _server[0]
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
            self.log.info("MQTT client connected")

        # Subscribe to service topic
        async with self.lock:
            await self.client.subscribe(self._SERVICE_TOPIC)
            # Subscribe to task topic
            await self.client.subscribe(self._TASK_TOPIC)
            # Subscribe to state topic
            await self.client.subscribe(self._STATE_TOPIC)

            for tp in self._topics:
                if isinstance(tp, str):
                    tp = tp.encode("utf-8")
                await self.client.subscribe(tp)
        if self.log:
            self.log.info("MQTT Client Services and Tasks enabled!")

        # Add PING subtask

        self.add_ctask(
            aioctl,
            self.ping,
            "ping",
            on_stop=self.on_stop,
            on_error=self.on_error,
            restart=restart,
        )

        if self.log:
            self.log.info("MQTT ping task enabled")

        # Add clean subtask
        self.add_ctask(aioctl, self.clean, "clean", on_error=self.on_error)

        if self.log:
            self.log.info("MQTT clean task enabled")

        # Add stats pub
        if stats:
            self.add_ctask(
                aioctl,
                self.stats_pub,
                "stats",
                services=services,
                on_error=self.on_error,
                restart=restart,
            )
            if self.log:
                self.log.info("MQTT stats task enabled")

        if ota_check:
            if self.log:
                self.log.info("MQTT checking OTA update..")
            _name = self._suid(aioctl, f"{self.name}.service.do_action.ota_check")
            aioctl.add(self.do_action, self, "ota", b"check", name=_name, _id=_name)

        # Wait for messages
        async with self.lock:
            await self.client.ping()

        self.client_ready.set()
        while True:
            try:
                # prevent waiting forever, blocking incoming messages
                async with self.lock:
                    await asyncio.sleep_ms(200)

                await asyncio.wait_for(self.client.wait_msg(), 30)
                # self.client_ready.set()
                await asyncio.sleep_ms(500)

                if self.log and debug:
                    self.log.info("MQTT waiting...")
            except asyncio.TimeoutError as e:
                if self.log:
                    self.log.error(f"Error: Client Timeout {e}")
                aioctl.stop(f"{self.name}.service.*")
                self.client_ready.clear()
                await asyncio.sleep(1)
                raise e
            # self.client_ready.clear()

    @aioctl.aiotask
    async def ping(self, *args, **kwargs):
        while True:
            async with self.lock:
                # await self.client.publish(self._STATE_TOPIC, b"OK")
                if self.client:
                    if self.client.is_connected():
                        await self.client.ping()
                        # await self.client.wait_msg()
                        self.n_pub += 1
                        # self.log.debug("PING")
            await asyncio.sleep(5)

    @aioctl.aiotask
    async def stats_pub(self, *args, **kwargs):
        service = kwargs.get("services")
        while True:
            try:
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
                    self.log.info(f"@ [STATUS]: {service}")
            except Exception as e:
                if self.log:
                    self.log.error(f"ERROR {e}", cname="stats")
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
                        self.log.info(f"{_ctask} cleaned")
                    gc.collect()

            await asyncio.sleep(5)

    @aioctl.aiotask
    async def disconnect(self, *args, **kwargs):
        if self.client:
            async with self.lock:
                if self.client.is_connected():
                    await self.client.disconnect()
        self.sslctx = None
        self.client = None
        gc.collect()

    @aioctl.aiotask
    async def reset(self, *args, **kwargs):
        _res = 5
        if self.log and kwargs.get("debug"):
            self.log.info(f"Rebooting in {_res} s")
        await asyncio.sleep(_res)
        for service in aioctl.tasks_match("*.service*"):
            if service != f"{self.name}.service.reset":
                self.log.info(f"Stopping {service}")
                aioctl.stop(service)

        if self.log and kwargs.get("debug"):
            self.log.info("Rebooting now")

        await asyncio.sleep(1)
        machine.reset()


service = MQTTService("aiomqtt")
