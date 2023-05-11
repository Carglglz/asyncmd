from machine import Timer, PWM, Pin
import time


class Buzzer:
    def __init__(self, pin, timer=2, freq=440, duty=512):
        self.buzz = PWM(Pin(pin), freq=freq, duty=duty)
        self.buzz.deinit()
        # self.buz_tim = Timer(timer)

    def play(self, freq, msec):
        if freq > 0:
            self.buzz.init()
            self.buzz.freq(freq)
            time.sleep_ms(msec)
            self.buzz.deinit()

    def buzz_beep(self, sleeptime, ntimes, ntimespaced, fq):
        for i in range(ntimes):
            self.play(fq, sleeptime)
            time.sleep_ms(ntimespaced)

    def warning(self, fl=4000, fh=800, ts=100, ntimes=10):
        for i in range(ntimes):
            self.play(fl, ts)
            self.play(fh, ts)

    def error(self, fq=100):
        self.buzz_beep(350, 2, 50, fq)
