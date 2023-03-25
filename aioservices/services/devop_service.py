import time
import uasyncio as asyncio
import aioctl
from aioclass import Service
import machine
import os
import json
import sys
import io


class DevOpService(Service):
    def __init__(self, name):
        super().__init__(name)
        self.version = "1.0"
        self.info = f"Device Operation Controller v{self.version}"
        self.type = "schedule.service"
        self.enabled = True
        self.docs = "https://github.com/Carglglz/asyncmd/blob/main/README.md"
        self.args = []
        self.kwargs = {
            "on_stop": self.on_stop,
            "on_error": self.on_error,
            "config": "services.config",
            "bootmode": "test",
            "devmodes": {
                "test": ["hello.service", "watcher.service"],
                "app": ["world.service", "watcher.service"],
            },
            "cycle": ["test", "app"],
            "reset": {
                "test": {"reset": True, "in": 30, "waitfor": ["hello.service"]},
                "app": {"reset": False},
            },
            "report": {"test": ["hello.service"]},
            "debug": True,
        }
        self.schedule = {"start_in": 5, "repeat": False}
        self._config = "services.config"
        self._devmode = None
        self._devmodes = []
        self._bootmode = None
        self._cycle = []
        self._bootconfigured = False
        self._reports = None
        self.log = None
        self._rpb = io.StringIO(1500)

        # current mode: devmode , next: bootmode

    def __call__(self, stream=sys.stdout):
        print(self.get_report(), file=stream)

    def config(self, name, enable, *args, **kwargs):
        _exists = False
        try:
            # exists
            os.stat(self._config)
            _exists = True
        except Exception:
            # create new one
            pass
        if _exists:  # load
            _service_config = self.get_config()
            if name not in _service_config:
                _service_config[name] = {}
            _service_config[name]["enabled"] = enable
            if args:
                _service_config[name]["args"] = args
            if kwargs:
                if "kwargs" in _service_config[name]:
                    _service_config[name]["kwargs"].update(**kwargs)
                else:
                    _service_config[name]["kwargs"] = kwargs
        else:  # create
            _service_config = {}
            _service_config[name] = {}
            _service_config[name]["enabled"] = enable
            if args:
                _service_config[name]["args"] = args
            if kwargs:
                _service_config[name]["kwargs"] = kwargs

        try:
            with open(self._config, "w") as servs_conf:
                json.dump(_service_config, servs_conf)
            return True
        except Exception as e:
            sys.print_exception(e, sys.stdout)
            raise e
            # create

    def enable(self, name):
        self.config(name, True)

    def disable(self, name):
        self.config(name, False)

    def get_config(self, name=None):
        try:
            with open(self._config, "r") as servs_conf:
                service_config = json.load(servs_conf)
        except Exception as e:
            sys.print_exception(e, sys.stdout)
            raise e

        if not name:
            return service_config
        else:
            if name in service_config:
                return service_config[name]
            else:
                return False

    @property
    def devmode(self):
        return self._devmode

    @devmode.setter
    def devmode(self, x):
        self._devmode = x

    @property
    def bootmode(self):
        return self._bootmode

    @bootmode.setter
    def bootmode(self, x):
        self._bootmode = x

    def get_report(self):
        if not self._reports:
            _rep = ""

            for rp in self.kwargs["report"]:
                try:
                    with open(f".{rp}", "r") as _rp:
                        _rep += "\n" + " " * 8
                        _rep += f"{rp}: "
                        for line in _rp:
                            if (
                                line.strip().split(";", 1)[0]
                                in self.kwargs["report"][rp]
                            ):
                                _rep += "\n" + " " * 12
                                _rpserv, ts = line.strip().split(";", 1)
                                _rep += f"● [{_rpserv}] @ {ts}"
                                _ind = 4
                                _do_ind = True
                            else:
                                if _do_ind:
                                    _rep += "\n"

                                _rep += " " * 12
                                if _do_ind:
                                    _rep += "┗━► "
                                else:
                                    _rep += " " * _ind

                                _rep += f"{line.strip()}\n"
                                _do_ind = False
                except Exception:
                    pass

            self._reports = _rep

        return self._reports

    def show(self):
        _stat_1 = f"   Dev Mode: {self.devmode} "
        _stat_2 = f"   Next: Boot mode: {self.bootmode}"
        _stat_2 += f"\n    Reports: {self.get_report()}"
        return "DevOp", f"{_stat_1}{_stat_2}"

    def on_stop(self, *args, **kwargs):
        if self.log:
            self.log.info(f"[{self.name}.service] stopped ")

    def on_error(self, e, *args, **kwargs):
        if self.log:
            self.log.error(f"[{self.name}.service] Error callback {e}")
        return e

    def next_mode(self, mode, cycle):
        cmi = cycle.index(mode)
        cmi += 1
        nmi = cmi % len(cycle)
        return nmi

    @aioctl.aiotask
    async def task(
        self,
        config="services.config",
        bootmode="",
        devmodes={},
        cycle=[],
        reset={},
        report=[],
        debug=False,
        log=None,
    ):
        if log and not self.log:
            self.log = log
        if not self._bootconfigured:
            await asyncio.sleep(5)
            self._config = config
            self._cycle = cycle
            self.devmode = bootmode
            # get next from cycle, set bootmode
            self.bootmode = cycle[self.next_mode(bootmode, cycle)]
        # set bootmode config
        if not self._bootconfigured:
            all_services = self.get_config()

            if debug and self.log:
                self.log.info(
                    f"[{self.name}.service] setting bootmode {self.bootmode}..."
                )
            for service in all_services:
                if (
                    f"{service}.service" in devmodes[self.bootmode]
                    or service == self.name
                ):
                    if not all_services[service]["enabled"]:
                        if debug and self.log:
                            self.log.info(
                                f"[{self.name}.service] {service}.service enabled"
                            )
                        self.enable(service)
                else:
                    if all_services[service]["enabled"]:
                        if debug and self.log:
                            self.log.info(
                                f"[{self.name}.service] {service}.service disabled"
                            )
                        self.disable(service)

            if debug and self.log:
                self.log.info(f"[{self.name}.service] Current Dev Mode: {self.devmode}")
                self.log.info(f"[{self.name}.service] Next Bootmode: {self.bootmode}")
            self.config(self.name, True, bootmode=self.bootmode)
            self._bootconfigured = True

        if log:
            self.log.info(f"[{self.name}.service] Started")

        # schedule reset
        if reset:
            if self.devmode in reset:
                if reset[self.devmode]["reset"]:
                    if "waitfor" in reset[self.devmode]:
                        # wait for x service to end to get result/report
                        _wfservices = reset[self.devmode]["waitfor"]
                        while True:
                            all_done = True
                            for _wfs in _wfservices:
                                all_done = (
                                    all_done and aioctl.group().tasks[_wfs].task.done()
                                )
                            if all_done:
                                break
                            await asyncio.sleep(5)
        # get report
        if report:
            if self.devmode in report:
                _OK = "[ \033[92mOK\x1b[0m ]"
                for _rpserv in report[self.devmode]:
                    if _rpserv in aioctl.group().tasks:
                        _serv = aioctl.group().tasks[_rpserv].service
                        done_at = aioctl.group().tasks[_rpserv].done_at
                        if done_at:
                            done_at = time.localtime(done_at)
                            done_at = aioctl.aioschedule.get_datetime(done_at)
                        if hasattr(_serv, "report"):
                            self._rpb.write(f"{_rpserv};{done_at} {_OK}\n")
                            _serv.report(self._rpb)
                        else:
                            res = aioctl.result(_rpserv)
                            if issubclass(res.__class__, Exception):
                                _res = (
                                    "[ \u001b[31;1mERROR\u001b[0m ] @"
                                    + f" {res.__class__.__name__}: {res}"
                                )
                                self._rpb.write(f"{_rpserv};{done_at} {_OK}\n{_res}\n")
                                sys.print_exception(res, self._rpb)
                            else:
                                self._rpb.write(f"{_rpserv};{done_at} {_OK}\n{res}")
                                self._rpb.write("\n")
                    else:
                        # not in tasks so failed to load?
                        import aioservice

                        if _rpserv.split(".", 1)[0] in aioservice.failed_services:
                            _serv = aioservice.failed_services[_rpserv.split(".", 1)[0]]
                            if _serv in aioservice._SERVICES_STATUS["failed"]:
                                self._rpb.write(
                                    f"{_rpserv};[ \u001b[31;1mERROR\u001b[0m ]"
                                )
                                self._rpb.write(" not loaded:\n")
                                self._rpb.write(" Error: \u001b[31;1m")
                                self._rpb.write(
                                    f"{_serv.info.__class__.__name__}\u001b[0m \n"
                                )

                                if issubclass(_serv.info.__class__, Exception):
                                    sys.print_exception(_serv.info, self._rpb)

                        else:
                            self._rpb.write(
                                f"{_rpserv};[ \u001b[31;1mERROR\u001b[0m ] Not Found \n"
                            )

                if self._rpb.tell():
                    self._rpb.seek(0)
                    if debug and self.log:
                        self.log.info(f"[{self.name}.service] Saving reports..")
                    with open(f".{self.devmode}", "w") as rp:
                        for line in self._rpb:
                            rp.write(line)

        if reset:
            if self.devmode in reset:
                if "in" in reset[self.devmode]:
                    aioctl.add(
                        self.reset,
                        self,
                        name=f"{self.name}.service.reset",
                        _id=f"{self.name}.service.reset",
                        _in=reset[self.devmode]["in"],
                        debug=debug,
                        devmodes=devmodes,
                        on_stop=self.on_stop,
                        on_error=self.on_error,
                        log=self.log,
                    )

        if log:
            self.log.info(f"[{self.name}.service] Done")

        return f"Mode: {self.devmode.upper()}, Boot: {self.bootmode.upper()}"

    @aioctl.aiotask
    async def reset(self, *args, **kwargs):
        _res = 5
        _res = kwargs.get("_in", _res)
        if self.log and kwargs.get("debug"):
            self.log.info(f"[{self.name}.service] Rebooting in {_res} s")
        await asyncio.sleep(_res)
        for service in kwargs.get("devmodes")[self.devmode]:
            if service in aioctl.group().tasks:
                if self.log and kwargs.get("debug"):
                    self.log.info(f"[{self.name}.service] Stopping {service}")
                aioctl.stop(service)

        if self.log and kwargs.get("debug"):
            self.log.info(f"[{self.name}.service] Rebooting in now")

        await asyncio.sleep(1)
        machine.reset()


service = DevOpService("devop")
