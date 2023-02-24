import uasyncio as asyncio
import aioctl
from aioclass import Service
import network
import json
from machine import unique_id
from binascii import hexlify
import sys

try:
    from hostname import NAME
except Exception:
    NAME = f"{sys.platform}-{hexlify(unique_id())}"


class WPASupplicantService(Service):
    def __init__(self, name):
        super().__init__(name)
        self.version = "1.0"
        self.info = f"WPA Supplicant Service v{self.version}"
        self.type = "schedule.service"
        self.enabled = True
        self.docs = "https://github.com/Carglglz/mpy-aiotools/blob/main/README.md"
        self.args = []
        self.kwargs = {
            "timeout": 10,
            "hostname": NAME,
            "notify": True,
            "restart_services": [],
        }
        self.schedule = {"start_in": 20, "repeat": 60}
        self.wlan = network.WLAN(network.STA_IF)
        self.net_status = "Disconnected"
        self.ssid = ""
        self.wlan.active(True)
        self.restart_services = []
        self.log = None
        # core.service --> run one time at boot
        # schedule.service --> run and stop following a schedule

    def show(self):
        if self.wlan.isconnected():
            rssi = self.wlan.status("rssi")
            return (
                "Network Status",
                f"{self.net_status} | RSSI: {rssi} dBm"
                + f"\n    IFConfig: {self.wlan.ifconfig()}",
            )
        else:
            return "Network Status", "Disconnected"

    def check_network(self):
        if self.wlan.isconnected():
            self.net_status = f"Connected to {self.ssid}"
            return True
        else:
            if self.log:
                self.log.info(f"[{self.name}.service] WLAN not connected")
            else:
                print("WLAN not connected, scanning for APs...")
            self.wlan.disconnect()
            return False

    async def setup_network(self, timeout=10, hostname=NAME, notify=True):
        n = 0
        if self.log:
            self.log.info(f"[{self.name}.service] Scanning for APs nearby...")
        else:
            print("Scanning for APs nearby...")
        scan = self.wlan.scan()
        scan_tuples = [(x[0].decode(), x[3]) for x in scan]
        # Sort by dBm
        scan_tuples.sort(key=lambda x: x[1], reverse=True)
        # Set device hostname
        self.wlan.config(dhcp_hostname=hostname)
        try:
            with open("wpa_supplicant.config", "r") as wpa_conf:
                wifi_config = json.load(wpa_conf)
        except Exception as e:
            if self.log:
                self.log.error(
                    f"[{self.name}.service] wpa_supplicant.config not found {e}"
                )
            else:
                sys.print_exception(e, sys.stdout)
            return
        _APs_in_range = [x[0] for x in scan_tuples if x[0] in wifi_config.keys()]
        if _APs_in_range:
            _ssid = _APs_in_range[0]
            if not self.wlan.isconnected():
                if notify:
                    if self.log:
                        self.log.info(
                            f"[{self.name}.service] Connecting to {_ssid} network"
                        )
                    else:
                        print("Connecting to network...")
                self.wlan.connect(_ssid, wifi_config[_ssid])
                while not self.wlan.isconnected():
                    n += 1
                    await asyncio.sleep(1)
                    if n > timeout:
                        return False
            if notify:
                if self.log:
                    self.log.info(f"[{self.name}.service] Connected to {_ssid}")
                    self.log.info(
                        f"[{self.name}.service] Network Config:"
                        + f"{self.wlan.ifconfig()}"
                    )
                else:
                    print(f"Connected to {_ssid}")
                    print("Network Config:", self.wlan.ifconfig())
            self.net_status = f"Connected to {_ssid}"
            self.ssid = _ssid
            return True

    @aioctl.aiotask
    async def task(
        self, timeout=10, hostname=NAME, notify=True, restart_services=[], log=None
    ):
        self.log = log
        self.restart_services = restart_services
        self.ssid = self.wlan.config("ssid")
        if not self.check_network():
            connected = await self.setup_network(
                timeout=timeout, hostname=hostname, notify=True
            )
            if connected:
                for service in self.restart_services:
                    if aioctl.stop(service):
                        if self.log:
                            self.log.info(f"[{self.name}.service] stopping {service}")
                        else:
                            print(f"Stopping {service}")
                for service in self.restart_services:
                    if aioctl.start(service):
                        if self.log:
                            self.log.info(
                                f"[{self.name}.service] {service}" + " started"
                            )
                        else:
                            print(f"{service} started")
                # restart services that depend on network


service = WPASupplicantService("wpa_supplicant")
