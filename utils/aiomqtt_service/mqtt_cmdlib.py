from machine import Pin
from hostname import NAME

led = Pin(2, Pin.OUT)


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
