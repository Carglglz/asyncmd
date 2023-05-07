import logging
import time


class LEDHeartBeat:
    def __init__(self, led):
        self.led = led

    def notify(self, level):
        if level == logging.INFO:
            self.led(2).on()
            time.sleep_ms(10)
            self.led(2).off()

        if level == logging.WARNING:
            self.led(3).on()
            time.sleep_ms(10)
            self.led(3).off()

        if level >= logging.ERROR:
            self.led(1).on()
            time.sleep_ms(10)
            self.led(1).off()
