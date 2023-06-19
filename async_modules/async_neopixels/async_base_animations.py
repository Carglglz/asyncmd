# NeoPixel Animations
import time
import random
from neopixel import NeoPixel
from machine import Pin
import asyncio


class Animation:
    RED = (255, 0, 0)
    YELLOW = (255, 150, 0)
    GREEN = (0, 255, 0)
    CYAN = (0, 255, 255)
    BLUE = (0, 0, 255)
    PURPLE = (180, 0, 255)
    SUNSET_VEC = [
        (250, 219, 50),
        (220, 185, 20),
        (200, 143, 10),
        (180, 109, 5),
        (150, 20, 0),
        (0, 0, 0),
    ]

    def __init__(self, neopixels):
        self.np = neopixels
        self._kr_start = 0

    def wheel(self, pos):
        # Input a value 0 to 255 to get a color value.
        # The colours are a transition r - g - b - back to r.
        if pos < 0 or pos > 255:
            return (0, 0, 0)
        if pos < 85:
            return (255 - pos * 3, pos * 3, 0)
        if pos < 170:
            pos -= 85
            return (0, 255 - pos * 3, pos * 3)
        pos -= 170
        return (pos * 3, 0, 255 - pos * 3)

    async def color_chase(self, color, wait):
        for i in range(self.np.n):
            self.np[i] = color
            await asyncio.sleep(wait)
            self.np.write()

    async def rainbow_cycle(self, wait, loops=0):
        if loops:
            for i in range(loops):
                for j in range(255):
                    for i in range(self.np.n):
                        rc_index = (i * 256 // self.np.n) + j
                        self.np[i] = self.wheel(rc_index & 255)
                    self.np.write()
                    await asyncio.sleep(wait)
        else:
            while True:
                for j in range(255):
                    for i in range(self.np.n):
                        rc_index = (i * 256 // self.np.n) + j
                        self.np[i] = self.wheel(rc_index & 255)
                    self.np.write()
                    await asyncio.sleep(wait)

    async def as_rainbow(self, wait, loops=0):
        if loops:
            for i in range(loops):
                for j in range(255):
                    for i in range(self.np.n):
                        rc_index = (i * 256 // self.np.n) + j
                        self.np[i] = self.wheel(rc_index & 255)
                    self.np.write()
                    await asyncio.sleep(wait)
        else:
            while True:
                for j in range(255):
                    for i in range(self.np.n):
                        rc_index = (i * 256 // self.np.n) + j
                        self.np[i] = self.wheel(rc_index & 255)
                    self.np.write()
                    await asyncio.sleep(wait)

    async def _kr_loop(self, color, wait, length=1):
        for p in range(self._kr_start, self.np.n):
            self.np.fill((0, 0, 0))
            for i in range(length):
                if (p - i > 0) and (p - i < self.np.n):
                    self.np[p - i] = color
            self.np[p] = color
            self.np.write()
            await asyncio.sleep(wait)
        for p in range(self.np.n - 2, -1, -1):
            self.np.fill((0, 0, 0))
            for i in range(length):
                if (p - i > 0) and (p - i < self.np.n):
                    self.np[p - i] = color
            self.np[p] = color
            self.np.write()
            await asyncio.sleep(wait)

    async def kr(self, color, wait, loops=0, length=1):
        self._kr_start = 0
        if loops:
            for i in range(loops):
                await self._kr_loop(color, wait, length=length)
                self._kr_start = 1
        else:
            while True:
                await self._kr_loop(color, wait, length=length)
                self._kr_start = 1

    async def _rand_loop(self, wait, clear):
        for p in range(self.np.n):
            if clear:
                self.np.fill((0, 0, 0))
            self.np[random.randint(0, self.np.n - 1)] = (
                random.randint(0, 255),
                random.randint(0, 255),
                random.randint(0, 255),
            )
            self.np.write()
            await asyncio.sleep(wait)

    async def random(self, wait, loops=0, clear=True):
        if loops:
            for i in range(loops):
                await self._rand_loop(wait, clear)

        else:
            while True:
                await self._rand_loop(wait, clear)

    async def fade_out(self, color, wait):
        # calc wait time to go from 255 to 0
        for c in range(max(color), -1, -1):
            _rgb = [int((c / max(color)) * ch) for ch in color]
            self.np.fill(_rgb)
            self.np.write()
            await asyncio.sleep(wait / max(color))

    async def fade_in(self, color, wait):
        for c in range(max(color) + 1):
            _rgb = [int((c / max(color)) * ch) for ch in color]
            self.np.fill(_rgb)
            self.np.write()
            await asyncio.sleep(wait / max(color))

    async def fade_colors(
        self, color1, color2, wait, cycle=False, random_cycle=False, bf=False
    ):
        # Go from color1 to color2
        step_color = list(color1)
        _real_color = step_color
        _invert = False
        _r_grad = color2[0] - color1[0]
        _g_grad = color2[1] - color1[1]
        _b_grad = color2[2] - color1[2]
        # max_grad = max(abs(_r_grad), abs(_g_grad), abs(_b_grad))
        diff_vector = (_r_grad / 255, _g_grad / 255, _b_grad / 255)
        indx = 0
        # t0 = time.time()
        while True:
            indx += 1
            real_color = [
                _real_color[0] + diff_vector[0],
                _real_color[1] + diff_vector[1],
                _real_color[2] + diff_vector[2],
            ]
            _real_color = real_color
            _rgb = [int(round(col, 0)) for col in real_color]
            # print(f"R: {_rgb[0]:^3} G: {_rgb[1]:^3} B: {_rgb[2]:^3}, I: {indx}")
            if not cycle:
                self.np.fill(_rgb)
                self.np.write()
                # await asyncio.sleep(wait/max_grad)
            else:
                if not random_cycle:
                    if not bf:
                        self.np[indx % self.np.n] = _rgb
                    else:
                        if _invert:
                            self.np[(self.np.n - 1) - (indx % self.np.n)] = _rgb
                        else:
                            self.np[indx % self.np.n] = _rgb
                        if indx % self.np.n == self.np.n - 1:
                            _invert = not _invert

                else:
                    self.np[random.randint(0, self.np.n - 1)] = _rgb
                self.np.write()
            if _rgb == list(color2):
                break
            await asyncio.sleep(wait / 255)

        # print(time.time() - t0)

    async def sunset_fade(self, wait):
        for index, color in enumerate(self.SUNSET_VEC):
            if color != self.SUNSET_VEC[-1]:
                color2 = self.SUNSET_VEC[index + 1]
                await self.fade_colors(color, color2, wait)
        self.fill((0, 0, 0))
        self.clear()

    async def breathe(self, color, wait, loops=0):
        if loops:
            for i in range(loops):
                asyncio.wait_for(self.fade_in(color, wait), 60)

                asyncio.wait_for(self.fade_out(color, wait), 60)
        else:
            while True:
                await self.fade_in(color, wait)
                await self.fade_out(color, wait)

    async def pulse(self, color, wait, beats=2, wait_beats=0.2, loops=0):
        if loops:
            for i in range(loops):
                for k in range(beats):
                    self.fill(color)
                    await asyncio.sleep(wait_beats)
                    self.clear()
                    await asyncio.sleep(wait_beats)
                await asyncio.sleep(wait)

        else:
            while True:
                for i in range(beats):
                    self.fill(color)
                    await asyncio.sleep(wait_beats)
                    self.clear()
                    await asyncio.sleep(wait_beats)
                await asyncio.sleep(wait)

    async def random_walk_fill(
        self, color, wait, time_walk=0, max_step=1, rand_step=True
    ):
        self.fill(color)
        _rgb = [0, 0, 0]
        if time_walk:
            t0 = time.time()
            while abs(time.time() - t0) < time_walk:
                _rgb[:] = [
                    self._rand_step(ch, max_step, rand_step) for ch in self.np[0]
                ]
                self.fill(_rgb)
                await asyncio.sleep(wait)
        else:
            while True:
                _rgb[:] = [
                    self._rand_step(ch, max_step, rand_step) for ch in self.np[0]
                ]
                self.fill(_rgb)
                await asyncio.sleep(wait)

    async def _rand_step(self, ch, max_step, rand_step):
        if rand_step:
            val = ch + random.choice((-1, 1)) * random.randint(0, max_step)
        else:
            val = ch + random.choice((-1, 1)) * max_step
        if val > 255:
            val = 255
        if val < 0:
            val = 0
        return val

    async def random_walk_breathe(
        self, color, wait, time_walk=0, max_step=1, rand_step=True
    ):
        self.fill(color)
        _breathe_color = list(color)
        _rgb = [0, 0, 0]
        if time_walk:
            t0 = time.time()
            while abs(time.time() - t0) < time_walk:
                _rgb[:] = [
                    self._rand_step(ch, max_step, rand_step) for ch in _breathe_color
                ]
                _breathe_color[:] = _rgb[:]
                try:
                    await self.breathe(_rgb, wait, loops=1)
                except ZeroDivisionError:
                    pass
                # await asyncio.sleep(wait)
        else:
            while True:
                _rgb[:] = [
                    self._rand_step(ch, max_step, rand_step) for ch in _breathe_color
                ]
                _breathe_color[:] = _rgb[:]
                try:
                    await self.breathe(_rgb, wait, loops=1)
                except ZeroDivisionError:
                    pass

    async def random_walk_fade(
        self,
        color1,
        color2,
        wait,
        time_walk=0,
        max_step=1,
        rand_step=True,
        cycle=False,
        random_cycle=False,
        bf=False,
    ):
        self.fill(color1)
        _init_fade_color = list(color1)
        _rgb = [0, 0, 0]
        if time_walk:
            t0 = time.time()
            await self.fade_colors(
                _init_fade_color, color2, wait, cycle, random_cycle, bf
            )
            _init_fade_color = list(color2)
            while abs(time.time() - t0) < time_walk:
                _rgb[:] = [
                    self._rand_step(ch, max_step, rand_step) for ch in _init_fade_color
                ]
                try:
                    await self.fade_colors(
                        _init_fade_color, _rgb, wait, cycle, random_cycle, bf
                    )
                except ZeroDivisionError:
                    pass
                _init_fade_color[:] = _rgb[:]
                # await asyncio.sleep(wait)
        else:
            await self.fade_colors(
                _init_fade_color, color2, wait, cycle, random_cycle, bf
            )
            _init_fade_color = list(color2)
            while True:
                _rgb[:] = [
                    self._rand_step(ch, max_step, rand_step) for ch in _init_fade_color
                ]
                try:
                    await self.fade_colors(
                        _init_fade_color, _rgb, wait, cycle, random_cycle, bf
                    )
                except ZeroDivisionError:
                    pass
                _init_fade_color[:] = _rgb[:]

    def fill(self, color):
        self.np.fill(color)
        self.np.write()

    def clear(self):
        self.np.fill((0, 0, 0))
        self.np.write()


def _loadnpxy(npin, npx, timing):
    np = NeoPixel(Pin(npin), npx, timing=timing)
    return Animation(np)
