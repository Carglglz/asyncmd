import asyncio
import aioctl
from aioclass import Service
import network
import json
from machine import unique_id
from binascii import hexlify
import sys
from ntptime import settime
from machine import Pin

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
            "hostname": aioctl.getenv("HOSTNAME", NAME),
            "notify": True,
            "led": aioctl.getenv("LED_PIN", 2),
            "webrepl_on": True,
            "ntp_host": None,
            "rsyslog": False,
            "timeoffset": "+00:00",
            "autoconfig": False,
        }
        # TODO: add wlan.config
        self.wlan = network.WLAN(network.STA_IF)
        self.net_status = "Disconnected"
        self.ssid = ""
        self.wlan.active(True)
        self.ap = None
        self.led = None
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
        scan_tuples = [(x[0].decode(), x[1], x[3]) for x in scan]
        # Sort by dBm
        scan_tuples.sort(key=lambda x: x[2], reverse=True)
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
        _APs_in_range = [x[:2] for x in scan_tuples if x[0] in wifi_config.keys()]
        if _APs_in_range:
            _ssid, _bssid = _APs_in_range[0]
            if not self.wlan.isconnected():
                if notify:
                    if self.log:
                        self.log.info(
                            f"[{self.name}.service] Connecting to {_ssid} network"
                        )
                    else:
                        print("Connecting to network...")
                self.wlan.connect(_ssid, wifi_config[_ssid], bssid=_bssid)
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
    async def task(
        self,
        timeout=10,
        hostname=NAME,
        notify=True,
        log=None,
        led=None,
        webrepl_on=True,
        ntp_host=None,
        rsyslog=False,
        timeoffset="+00:00",
        autoconfig=False,
    ):
        self.log = log
        if led:
            self.led = Pin(led, Pin.OUT)

        connected = await self.setup_network(
            timeout=timeout, hostname=hostname, notify=True
        )
        if connected:
            if ntp_host:
                import ntptime

                ntptime.host = ntp_host
            settime()
        else:
            await self.setup_ap()

        if webrepl_on:
            self.add_ctask(
                aioctl,
                self.webrepl_setup,
                "webrepl",
            )

        for i in range(10):
            self.led.value(not self.led.value())
            await asyncio.sleep(0.2)
        self.led.value(False)

        if connected:
            if rsyslog and self.log:
                try:
                    from ursyslogger import RsysLogger
                    from rsysloghandler import RsysLogHandler
                    import logging

                    if autoconfig:
                        rsyslog = autoconfig.get(self.ssid, rsyslog)
                    self.rsysloghandler = RsysLogHandler(
                        RsysLogger(rsyslog, hostname=hostname, t_offset=timeoffset)
                    )
                    formatter = logging.Formatter(
                        "%(asctime)s [%(name)s] [%(levelname)s] %(message)s"
                    )
                    self.rsysloghandler.setLevel(logging.INFO)
                    self.rsysloghandler.setFormatter(formatter)
                    self.log.addHandler(self.rsysloghandler)

                except Exception as e:
                    if self.log:
                        self.log.error(e)
            return "WLAN: ENABLED"
        else:
            return "AP: ENABLED"

    @aioctl.aiotask
    async def webrepl_setup(self, *args, **kwargs):
        import webrepl

        webrepl.start()
        if self.log:
            self.log.info(f"[{self.name}.service.webrepl] WebREPL setup done")

        return "WEBREPL: ENABLED"


service = NetworkService("network")
