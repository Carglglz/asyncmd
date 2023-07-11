import sys
import os
import random
import time


def unique_id():
    return os.urandom(8)


def reset():
    sys.exit(1)


def deepsleep(n=0):
    if not n:
        sys.exit(1)
    else:
        time.sleep_ms(n)


class Pin:
    OUT = 0
    IN = 1
    def __init__(self, *args, **kwargs):
        ...

    def on(self):
        return

    def off(self):
        return


class I2C:
    def __init__(self, *args, **kwargs):
        ...


class WDT:
    def __init__(self, *args, **kwargs):
        ...

    def feed(self):
        return


class ADC:
    ATTN_11DB = 0

    def __init__(self, *args, **kwargs):
        ...

    def atten(self, n):
        return

    def read(self):
        return random.randint(1024, 2500)
