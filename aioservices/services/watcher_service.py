import asyncio
import aioctl
from aioclass import Service
import sys
import machine
import time


class WatcherService(Service):
    def __init__(self, name):
        super().__init__(name)
        self.version = "1.0"
        self.info = (
            f"Watcher Service v{self.version} - Restarts services on failed state"
        )
        self.type = "runtime.service"
        self.enabled = True
        self.docs = "https://github.com/Carglglz/asyncmd/blob/main/README.md"
        self.args = [30]
        self.kwargs = {
            "on_stop": self.on_stop,
            "on_error": self.on_error,
            "max_errors": 0,
            "watchdog": True,
            "wdfeed": 60000,
            "debug": False,
            "save_report": False,
            "err_service_limit": False,
            "loglevel": "INFO",
            "service_logger": True,
        }
        self.err_count = 0
        self.err_report = {}
        self._report_updated = False
        self.log = None
        self._wdt = None
        # core.service --> run one time at boot
        # schedule.service --> run and stop following a schedule

    def __call__(self, stream=sys.stdout):
        self.display_report(stream=stream)

    def show(self):
        _stat_1 = f"   # ERRORS: {self.err_count} "
        _stat_2 = f"   Report: {self.err_report}"
        return "Stats", f"{_stat_1}{_stat_2}"  # return Tuple, "Name",
        # "info" to display

    def stats(self):
        return {
            "errors": self.err_count,
            "report": {k: list(v) for k, v in self.err_report.items()},
        }

    def report(self, stream=sys.stdout):
        self.__call__(stream=stream)
        print(*self.show(), file=stream, sep=": ")

    def display_report(self, stream=sys.stdout):
        for _serv, rep in self.err_report.items():
            print(f"--> {_serv}:", file=stream)
            for err_name, err in rep.items():
                print(f"    - {err_name} : {err['count']}; Traceback: ", file=stream)
                sys.print_exception(err["err"], stream)
            print("<", "-" * 80, ">", file=stream)

    def on_stop(self, *args, **kwargs):  # same args and kwargs as self.task
        if self.log:
            self.log.info(f"stopped result: {self.err_count}")
        return self.err_report

    def on_error(self, e, *args, **kwargs):
        if self.log:
            self.log.error(f"Error callback {e}")
        return e

    def update_report(self, name, res):
        if name not in self.err_report:
            self.err_report[name] = {res.__class__.__name__: {"count": 1, "err": res}}
            self._report_updated = True
        else:
            if res.__class__.__name__ in self.err_report[name]:
                self.err_report[name][res.__class__.__name__]["count"] += 1
            else:
                self.err_report[name][res.__class__.__name__] = {"count": 1, "err": res}
                self._report_updated = True

    def err_count_by_service(self, name):
        if name not in self.err_report:
            return 0
        else:
            return sum(
                (
                    errc.get("count", 0)
                    for errname, errc in self.err_report[name].items()
                )
            )

    @aioctl.aiotask
    async def task(
        self,
        sleep,
        max_errors=0,
        watchdog=True,
        wdfeed=10000,
        debug=False,
        save_report=False,
        err_service_limit=False,
        log=None,
        loglevel="INFO",
        service_logger=True,
    ):
        self.add_logger(log, level=loglevel, service_logger=service_logger)
        self._save_report = save_report
        await asyncio.sleep(10)
        excl = []
        if watchdog:
            self.add_ctask(
                aioctl,
                self.wdt,
                "wdt",
                wdfeed,
                on_error=self.on_error,
                debug=debug,
            )
            if self.log:
                self.log.info("WDT task enabled")

        while True:
            for name, res in aioctl.result_all(as_dict=True).items():
                if issubclass(res.__class__, Exception):
                    self.err_count += 1
                    self.update_report(name, res)
                    if log:
                        _err = f"Error @ Task {name} {res.__class__.__name__}: {res}"
                        self.log.info(f"{_err}")
                    if aioctl.group().tasks[name].kwargs.get("restart", True):
                        pass
                    else:
                        continue
                    if log:
                        self.log.info(f"Restarting Task: {name}")
                    res = aioctl.group().tasks[name].kwargs.get("restart", True)
                    if isinstance(res, (list, set)):
                        for _name in res:
                            if _name not in excl:
                                try:
                                    aioctl.stop(f"{_name}.*")
                                    if self.log:
                                        self.log.info(
                                            "Restarting Service:" + f" {_name}"
                                        )
                                    await asyncio.sleep_ms(500)
                                    aioctl.start(_name)
                                    excl.append(_name)
                                except Exception as e:
                                    if self.log:
                                        self.log.error(f"[watcher.service] {e}")
                                    else:
                                        sys.print_exception(e)

                    else:
                        if name not in excl:
                            aioctl.start(name)
            excl = []
            if self._save_report and self._report_updated:
                if self.log:
                    self.log.info("saving report..")

                done_at = aioctl.get_datetime(time.localtime())

                with open(f".{self.name}.service", "w") as rp:
                    rp.write(f"{self.name}.service;{done_at} [\x1b[92mOK\x1b[0m]\n")
                    self.display_report(rp)
                self._report_updated = False

            await asyncio.sleep(sleep)
            if self.err_count > max_errors and max_errors > 0:
                if self.log:
                    self.log.info("Error limit reached")
                    self.log.info("Rebooting now...")
                    await asyncio.sleep(5)
                machine.reset()

            if err_service_limit:
                for sname, err_limit in err_service_limit.items():
                    if err_limit <= self.err_count_by_service(sname):
                        if self.log:
                            self.log.info(f"Error limit @ {sname} reached")
                            self.log.info("Rebooting now...")
                            await asyncio.sleep(5)
                        machine.reset()

    @aioctl.aiotask
    async def wdt(self, timeout, debug=False):
        self._wdt = machine.WDT(timeout=timeout)
        _asleep = int(timeout / 3)
        while True:
            self._wdt.feed()
            await asyncio.sleep_ms(_asleep)
            if self.log and debug:
                self.log.debug("feeding WDT", cname="wdt")


service = WatcherService("watcher")
