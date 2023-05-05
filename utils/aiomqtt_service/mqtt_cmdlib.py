from machine import Pin
import sys

try:
    from hostname import NAME
except Exception:
    NAME = sys.platform

try:
    from pinconfig import LED_PIN
except Exception:
    LED_PIN = 2

led = Pin(LED_PIN, Pin.OUT)


mqtt_cmds = {
    "on": {
        "cmd": led.on,
        # "args": [],
        # "kwargs": {},
        "log": "LED ON",
        "resp": {"topic": f"device/{NAME}/resp", "msg": "LED ON"},
    },
    "off": {
        "cmd": led.off,
        # "args": [],
        # "kwargs": {},
        "log": "LED OFF",
        "resp": {"topic": f"device/{NAME}/resp", "msg": "LED OFF"},
    },
}
