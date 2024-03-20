import asyncio
import aioctl
from aioclass import Service
import random
from gui import display, draw565, logo  # noqa
import gui.fonts as fonts
import sdl2  # noqa
import sys
import time


class GUIService(Service):
    def __init__(self, name):
        super().__init__(name)
        self.info = "GUI demo service"
        self.type = "runtime.service"  # continuous running, other types are
        self.enabled = True
        self.docs = "https://github.com/Carglglz/asyncmd/blob/main/README.md"
        self.args = []
        self.kwargs = {
            "on_stop": self.on_stop,
            "on_error": self.on_error,
            "service_logger": True,
            "loglevel": "INFO",
            "width": 640,
            "height": 320,
            "x_scale": 2,
            "y_scale": 2,
            "title": "Asyncmd",
            "fps": 25,
        }
        self.log = None
        self.tft = None
        self.dw = None
        self.loop_diff = 0

    def show(self):
        _stat_1 = f"   FPS: {int(1000/self.loop_diff)}"
        return "Stats", f"{_stat_1}"  # return Tuple, "Name",

    def stats(self):
        return {"FPS": int(1000 / self.loop_diff)}

    def on_stop(self, *args, **kwargs):  # same args and kwargs as self.task
        res = random.random()
        if self.log:
            self.log.info(f"stopped result: {res}")
        return res

    def on_error(self, e, *args, **kwargs):
        if self.log:
            self.log.error(f"Error callback {e}")
        return e

    def setup(self, width, height, x_scale, y_scale, title):
        self.tft = display.Display(
            width, height, x_scale=x_scale, y_scale=y_scale, title=title
        )

        self.dw = draw565.Draw565(self.tft)
        self.dw.set_font(fonts.sans18)

        self.dw.blit(logo.micropython, 180, 2)
        mpv = f"Version: {sys.version.split(';')[-1].strip().split("-")[0]}"
        mpm = f"Machine: {sys.implementation._machine}"
        self.dw.string(mpv, 120, 250)
        self.dw.string(mpm, 120, 270)
        self.tft.text("Press any key to continue", 180, 300, 0xFFFF)
        self.tft.show()

    @aioctl.aiotask
    async def task(
        self,
        width=640,
        height=320,
        x_scale=2,
        y_scale=2,
        title="Asyncmd",
        fps=25,
        log=None,
        service_logger=False,
        loglevel="INFO",
    ):
        self.add_logger(log, level=loglevel, service_logger=service_logger)
        self.setup(width, height, x_scale, y_scale, title)
        fps_sleep_ms = int(1000 / fps)  # target FPS

        while True:
            t0 = time.ticks_ms()
            event = self.tft.poll_event()

            if not event:
                await asyncio.sleep_ms(fps_sleep_ms)

                self.loop_diff = time.ticks_diff(time.ticks_ms(), t0)
                continue
            # print(event)

            # TODO: Simple GUI App demo to display service stats e.g. sensor
            # data

            # await app.tick(self.tft, self.dw, event, self.log)

            if event[sdl2.TYPE] == sdl2.SDL_KEYDOWN:
                key = event[sdl2.KEYNAME]
                mod = event[sdl2.MOD]
                self.tft.clear()
                self.tft.text(key, 180, 180, 0xFFFF)
            # if the event is SDL_QUIT, exit
            if event[sdl2.TYPE] == sdl2.SDL_QUIT:
                break

            # if the event is SDL_MOUSEBUTTONDOWN, get the mouse position
            if event[sdl2.TYPE] == sdl2.SDL_MOUSEBUTTONDOWN:
                p_x = event[sdl2.X]
                p_y = event[sdl2.Y]
                self.log.info(f"CLICK @ ({p_x}, {p_y})")

            # if the event is SDL_MOUSEBUTTONUP, stop drawing
            elif event[sdl2.TYPE] == sdl2.SDL_MOUSEBUTTONUP:
                pass
            # if the event is SDL_MOUSEMOTION, and we are drawing, draw the pixel
            elif event[sdl2.TYPE] == sdl2.SDL_MOUSEMOTION:
                pass
            # update the display
            self.tft.show()

            self.loop_diff = time.ticks_diff(time.ticks_ms(), t0)

            await asyncio.sleep_ms(fps_sleep_ms)


service = GUIService("gui")
