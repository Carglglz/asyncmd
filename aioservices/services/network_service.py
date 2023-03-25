import uasyncio as asyncio
import aioctl
from aioclass import Service
import network
import json
from machine import unique_id
from binascii import hexlify
import sys
from ntptime import settime
import webrepl
from machine import Pin
import uptime

try:
    from hostname import NAME
except Exception:
    NAME = f"{sys.platform}-{hexlify(unique_id())}"


class NetworkService(Service):
    def __init__(self, name):
        super().__init__(name)
        self.version = "1.0"
        self.info = f"Network Setup Service v{self.version}"
        self.type = "core.service"
        self.enabled = True
        self.docs = "https://github.com/Carglglz/asyncmd/blob/main/README.md"
        self.args = []
        self.kwargs = {
            "timeout": 10,
            "hostname": NAME,
            "notify": True,
        }
        self.wlan = network.WLAN(network.STA_IF)
        self.net_status = "Disconnected"
        self.ssid = ""
        self.wlan.active(True)
        self.ap = None
        self.led = Pin(2, Pin.OUT)
        self.log = None

    def show(self):
        if self.wlan.isconnected():
            rssi = self.wlan.status("rssi")
            return (
                "Network Status",
                f"{self.net_status} | RSSI: {rssi} dBm"
                + f"\n    IFConfig: {self.wlan.ifconfig()}",
            )
        else:
            if self.ap:
                return (
                    "Network Status",
                    f"AP: {self.ssid}" + f"\n    IFConfig: {self.ap.ifconfig()}",
                )
            else:
                return "Network Status", "Disconnected"

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

    async def setup_ap(self):
        self.ap = network.WLAN(network.AP_IF)
        with open("ap_.config", "r") as ap_file:
            ap_config = json.load(ap_file)
        self.ap.active(True)
        self.ap.config(
            essid=ap_config["ssid"],
            authmode=network.AUTH_WPA_WPA2_PSK,
            password=ap_config["password"],
        )
        if self.log:
            self.log.info("Acces point configurated: {}".format(ap_config["ssid"]))
            self.log.info(self.ap.ifconfig())
        self.ssid = ap_config["ssid"]

    @aioctl.aiotask
    async def task(self, timeout=10, hostname=NAME, notify=True, log=None):
        self.log = log
        connected = await self.setup_network(
            timeout=timeout, hostname=hostname, notify=True
        )
        if connected:
            settime()
            uptime.settime()
        else:
            await self.setup_ap()

        aioctl.add(
            self.webrepl_setup,
            self,
            name=f"{self.name}.service.webrepl",
            _id=f"{self.name}.service.webrepl",
        )

        for i in range(10):
            self.led.value(not self.led.value())
            await asyncio.sleep(0.2)
        self.led.value(False)

        if connected:
            return "WLAN: ENABLED"
        else:
            return "AP: ENABLED"

    @aioctl.aiotask
    async def webrepl_setup(self, *args, **kwargs):
        webrepl.start()
        if self.log:
            self.log.info(f"[{self.name}.service] WebREPL setup done")
        return "WEBREPL: ENABLED"


service = NetworkService("network")
