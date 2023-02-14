import uasyncio as asyncio
import aioctl
from aioclass import Service
import sys


class WatcherService(Service):
    def __init__(self, name):
        super().__init__(name)
        self.info = "Watcher Service v1.0 - Restarts services on failed state"
        self.type = "runtime.service"
        self.enabled = True
        self.docs = "https://github.com/Carglglz/mpy-wpa_supplicant/blob/main/README.md"
        self.args = [30]
        self.kwargs = {"on_stop": self.on_stop, "on_error": self.on_error}
        self.err_count = 0
        self.err_report = {}
        self.log = None
        # core.service --> run one time at boot
        # schedule.service --> run and stop following a schedule

    def __call__(self):
        self.display_report()

    def show(self):
        _stat_1 = f"   # ERRORS: {self.err_count} "
        _stat_2 = f"   Report: {self.err_report}"
        return "Stats", f"{_stat_1}{_stat_2}"  # return Tuple, "Name",
        # "info" to display

    def display_report(self):
        for _serv, rep in self.err_report.items():
            print(f"--> {_serv}:")
            for err_name, err in rep.items():
                print(f"    - {err_name} : {err['count']}; Traceback: ")
                sys.print_exception(err["err"])
            print("<", "-" * 80, ">")

    def on_stop(self, *args, **kwargs):  # same args and kwargs as self.task
        if self.log:
            self.log.info(f"[watcher.service] stopped result: {self.err_count}")
        return self.err_report

    def on_error(self, e, *args, **kwargs):
        if self.log:
            self.log.error(f"[watcher.service] Error callback {e}")
        return e

    def update_report(self, name, res):

        if name not in self.err_report:
            self.err_report[name] = {res.__class__.__name__: {"count": 1, "err": res}}
        else:
            if res.__class__.__name__ in self.err_report[name]:
                self.err_report[name][res.__class__.__name__]["count"] += 1
            else:
                self.err_report[name][res.__class__.__name__] = {"count": 1, "err": res}

    @aioctl.aiotask
    async def task(self, sleep, log=None):
        self.log = log
        await asyncio.sleep(10)
        while True:
            for name, res in aioctl.result_all(as_dict=True).items():
                if issubclass(res.__class__, Exception):
                    self.err_count += 1
                    self.update_report(name, res)
                    if log:
                        _err = f"Error @ Task {name} {res.__class__.__name__}: {res}"
                        self.log.info(f"[{self.name}.service] {_err}")
                    if aioctl.group().tasks[name].kwargs.get("restart", True):
                        pass
                    else:
                        continue
                    if log:
                        self.log.info(f"[{self.name}.service] Restarting Task {name}")
                    aioctl.start(name)
            await asyncio.sleep(sleep)


service = WatcherService("watcher")
