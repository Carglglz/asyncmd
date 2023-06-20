import sys
import os


def unique_id():
    return os.urandom(8)


def reset():
    sys.exit(1)


class Pin:
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
