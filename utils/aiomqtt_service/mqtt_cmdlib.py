from machine import Pin
import sys
import uasyncio as asyncio

try:
    from hostname import NAME
except Exception:
    NAME = sys.platform

try:
    from pinconfig import LED_PIN
except Exception:
    LED_PIN = 2

led = Pin(LED_PIN, Pin.OUT)


async def blink(n, sleep_ms=(100, 200)):
    for i in range(n):
        led.on()
        await asyncio.sleep_ms(sleep_ms[0])
        led.off()
        await asyncio.sleep_ms(sleep_ms[1])


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
    "blink": {
        "cmd": blink,
        "args": [5],
        "kwargs": {"sleep_ms": (100, 200)},
        "async": True,
        "log": "BLINK BLINK",
        "resp": {"topic": f"device/{NAME}/resp", "msg": "BLINK"},
    },
}

_help_mqtt_cmds = {
    "help": {
        k: {"args": v.get("args"), "kwargs": v.get("kwargs"), "help": v.get("help")}
        for k, v in mqtt_cmds.items()
    },
}
mqtt_cmds.update(**_help_mqtt_cmds)
