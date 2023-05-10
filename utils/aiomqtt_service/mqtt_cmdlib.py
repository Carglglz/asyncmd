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


async def blink():
    for i in range(5):
        led.on()
        await asyncio.sleep_ms(100)
        led.off()
        await asyncio.sleep_ms(200)


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
        # "args": [],
        # "kwargs": {},
        "async": True,
        "log": "BLINK BLINK",
        "resp": {"topic": f"device/{NAME}/resp", "msg": "BLINK"},
    },
}
