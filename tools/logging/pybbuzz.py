from pyb import Pin, Timer
import time


class Buzzer:
    def __init__(self, pin, timer=2, freq=440, channel=1):
        self.buzz_pin = Pin(pin)
        self.buz_tim = Timer(timer, freq=freq)
        self.buz_ch = self.buz_tim.channel(
            channel, Timer.PWM, pin=self.buzz_pin, pulse_width=0
        )

    def play(self, freq, msec):
        if freq > 0:
            self.buz_tim.freq(freq)
            self.buz_ch.pulse_width_percent(50)
            time.sleep_ms(int(msec * 0.9))
            self.buz_ch.pulse_width_percent(0)
            time.sleep_ms(int(msec * 0.1))

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
