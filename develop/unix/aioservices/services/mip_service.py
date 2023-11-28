import os
import asyncio
import aioctl
from aioclass import Service
import async_mip
import machine
import json
import sys


class MIPService(Service):
    def __init__(self, name):
        super().__init__(name)
        self.version = "1.0"
        self.info = f"MIP updater Service v{self.version}"
        self.type = "schedule.service"
        self.enabled = True
        self.docs = "https://github.com/Carglglz/asyncmd/blob/main/README.md"
        self.args = []
        self.kwargs = {
            "autoupdate": True,
            "restart": True,
            "packages": [],
            "config": "packages.config",
            "loglevel": "INFO",
            "service_logger": True,
        }
        self.schedule = {"start_in": 20, "repeat": 90}
        self.log = None
        self.packages = {}  # name: {url:"", version:""}
        self.packages_config = ""  # packages.config
        self.new_packages = False
        self.packages_to_update = {}
        self.updated_packages = set()
        # Populate packages from packages.config if not pased as argument

    def __call__(self, stream=sys.stdout):
        for pk, info in self.packages.items():
            print(f"{pk} v{info['version']}: {info['url']}", file=stream)

    def show(self):
        if not self.new_packages:
            return "Packages Status", "Up to date"
        else:
            return (
                "Packages Status",
                f"{len(self.packages_to_update)} can be updated: "
                + ", ".join((p for p in self.packages_to_update.keys())),
            )

    def report(self, stream=sys.stdout):
        self.__call__(stream=stream)
        print(*self.show(), file=stream, sep=": ")

    def stats(self):
        _stats_packages = {
            "update_n": len(self.packages_to_update),
            "packages_n": len(self.packages),
            "packages": self.packages,
            "update": self.packages_to_update,
        }

        if not self.new_packages:
            _stats_packages["status"] = "up to date"
        else:
            _stats_packages["status"] = "outdated"

        return _stats_packages

    def check_version(self, new, current):
        va = new.split(".")
        vb = current.split(".")
        if len(va) < 3:
            va += ["0"]
        if len(vb) < 3:
            vb += ["0"]
        va = [int(v) for v in va]
        vb = [int(v) for v in vb]
        xa, ya, za = va
        xb, yb, zb = vb
        if xa > xb:
            return True
        elif xa == xb:
            if ya > yb:
                return True
            elif ya == yb:
                if za > zb:
                    return True

    def fetch_config(self):
        _exists = False
        try:
            # exists
            os.stat(self.packages_config)
            _exists = True
        except Exception:
            # create new one
            pass
        if _exists:  # load
            try:
                with open(self.packages_config, "r") as pkc:
                    return json.load(pkc)
            except Exception as e:
                if self.log:
                    self.log.error(f"{e}")
                    self.log.error("error fetching " + f"{self.packages_config}")

    def save_config(self, conf):
        try:
            with open(self.packages_config, "w") as packages_conf:
                json.dump(conf, packages_conf)
            return True
        except Exception as e:
            sys.print_exception(e, sys.stdout)
            return

    async def check_packages(self, _debug=False):
        async_mip._DEBUG = _debug
        for pk, info in self.packages.items():
            if self.log:
                self.log.info(f"Fetching package {pk}...")
            pack = await async_mip.fetch(info["url"])

            if self.log:
                self.log.info(
                    f"Package {pk} fetched"
                    + f" version: {pack['version']}, current version"
                    + f": {info['version']}"
                )
            if self.check_version(pack["version"], info["version"]):
                self.packages_to_update[pk] = {
                    "url": info["url"],
                    "version": pack["version"],
                    "service": info.get("service"),
                }
                self.new_packages = True

                if self.log:
                    self.log.info(
                        f"Package {pk} can be updated to"
                        + f" version: {pack['version']}"
                    )
            else:
                if self.log:
                    self.log.info(f"Package {pk} up to date")

    async def update(self, _debug=False):
        async_mip._DEBUG = _debug
        reset = False
        for pk, info in self.packages_to_update.items():
            if self.log:
                self.log.info(f"Installing Package {pk}")
            _target = None
            is_service = info.get("service")
            if is_service:
                _target = "."
            installed = await async_mip.install(info["url"], target=_target)
            if installed:
                self.updated_packages.update([pk])
                self.packages[pk] = info
                # save to packages.config

                if self.log:
                    self.log.info(f"Package {pk} installed")
                reset = True

        # update
        if self.updated_packages:
            self.save_config(self.packages)
        for pk in self.updated_packages:
            self.packages_to_update.pop(pk)
        if not self.packages_to_update:
            self.new_packages = False
        self.updated_packages.clear()
        return reset

    @aioctl.aiotask
    async def reset(self, *args, **kwargs):
        await asyncio.sleep(10)
        if self.log:
            self.log.info("Rebooting now...")

        await asyncio.sleep(2)
        machine.reset()

    @aioctl.aiotask
    async def task(
        self,
        autoupdate=True,
        restart=True,
        packages=[],
        config="pacakges.config",
        log=None,
        loglevel="INFO",
        service_logger=False,
    ):
        self.add_logger(log, level=loglevel, service_logger=service_logger)
        self.packages_config = config
        if not packages and not self.packages:
            # decide if fetch every time or only first time
            self.packages = self.fetch_config()
            # fetch packages from packages.config

        if packages and not self.packages:
            # fetch from services.config mip packages kwarg
            self.packages = packages

        await asyncio.sleep(5)
        if self.log:
            self.log.info("Fetching packages..")
        await self.check_packages()

        if self.packages_to_update:
            if autoupdate:
                if self.log:
                    self.log.info("Updating packages..")
                do_reboot = await self.update()
                if do_reboot and restart:
                    if self.log:
                        self.log.info("Reboot scheduled")
                    self.add_ctask(aioctl, self.reset, "reset")
                    return "New packages installed, reboot scheduled"
                return "New packages installed, available at next boot"
            else:
                return (
                    f"{len(self.packages_to_update)} packages available" + " for update"
                )

        else:
            if self.log:
                self.log.info("Packages up to date")
            return "Packages up to date"


service = MIPService("mip")
