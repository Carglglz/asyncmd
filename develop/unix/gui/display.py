"""
display.py: Display is a subclass of framebuf.FrameBuffer. It can be used to
create a display object to emulate a graphical display on the screen with
minimal changes to the code. It also support polling for SDL events,
like mouse clicks and key presses.
"""

BLACK = const(0x0000)
BLUE = const(0x001F)
RED = const(0xF800)
GREEN = const(0x07E0)
CYAN = const(0x07FF)
MAGENTA = const(0xF81F)
YELLOW = const(0xFFE0)
WHITE = const(0xFFFF)

import framebuf
import sdl2


# pylint: disable=too-many-arguments
class Display(framebuf.FrameBuffer):
    """A framebuf based display driver for SDL2"""

    def __init__(
        self,
        width=320,
        height=240,
        x=sdl2.SDL_WINDOWPOS_CENTERED,
        y=sdl2.SDL_WINDOWPOS_CENTERED,
        x_scale=1,
        y_scale=1,
        title="MicroPython",
        window_flags=sdl2.SDL_WINDOW_SHOWN,
        render_flags=sdl2.SDL_RENDERER_ACCELERATED,
    ):
        self.buffer = bytearray(width * height * 2)

        self.width = width
        self.height = height
        self._x0 = 0
        self._y0 = 0
        self._wi = 0
        self._wrev = True
        self.display = sdl2.SDL2(
            width,
            height,
            x=x,
            y=y,
            x_scale=x_scale,
            y_scale=y_scale,
            title=title,
            window_flags=window_flags,
            render_flags=render_flags,
        )

        super().__init__(self.buffer, width, height, framebuf.RGB565)

        self._lb = bytearray(2 * width)

        self.linebuffer = memoryview(self._lb)
        self.window_buff = bytearray(width * height * 2)
        self.init_display()
        self.quick_write = self.write_data

    def init_display(self):
        """Reset and initialize the display."""
        self.reset()

        self.fill(0)
        self.init()

    def write_data(self, buf):
        # revert bline
        if not self._wrev:
            self.window_buff[self._wi : len(buf)] = buf[:]
            self._wi += len(buf)
        else:
            self.window_buff[self._wi - len(buf) : self._wi] = buf[:]
            self._wi -= len(buf)

    def poweroff(self):
        """Put the display into sleep mode."""
        pass

    def poweron(self):
        """Wake the display and leave sleep mode."""
        pass

    def invert(self, invert):
        """Invert the display.

        :param bool invert: True to invert the display, False for normal mode.
        """
        pass
        # if invert:
        #     self.write_cmd(_INVON)
        # else:
        #     self.write_cmd(_INVOFF)

    def mute(self, mute):
        """Mute the display.

        When muted the display will be entirely black.

        :param bool mute: True to mute the display, False for normal mode.

        """
        pass
        # if mute:
        #     self.write_cmd(_DISPOFF)

    # else:
    #     self.write_cmd(_DISPON)

    def quick_start(self):
        """Prepare for an optimized write sequence.

        Optimized write sequences allow applications to produce data in chunks
        without having any overhead managing the chip select.
        """
        # self.cs(0)
        pass

    def quick_end(self):
        """Complete an optimized write sequence."""
        # self.cs(1)
        pass

    # @micropython.native
    def set_window(self, x, y, width, height, bpx=2, reverse=False):
        """Set the clipping rectangle.

        All writes to the display will be wrapped at the edges of the rectangle.

        :param x:  X coordinate of the left-most pixels of the rectangle
        :param y:  Y coordinate of the top-most pixels of the rectangle
        :param w:  Width of the rectangle, defaults to None (which means select
                   the right-most pixel of the display)
        :param h:  Height of the rectangle, defaults to None (which means select
                   the bottom-most pixel of the display)
        """
        # write_cmd = self.write_cmd
        self._x0 = x
        self._y0 = y
        self._wx = width
        self._wh = height

        # self.linebuffer = memoryview(bytearray(2 * width))
        self._lb[:] = bytearray(2 * width)
        self.window_buff = bytearray(width * height * bpx)
        if reverse:
            self._wrev = True
            self._wi = len(self.window_buff)
        else:
            self._wrev = False
            self._wi = 0

    def refresh_window(self):
        self.window = framebuf.FrameBuffer(
            self.window_buff, self._wx, self._wh, framebuf.RGB565
        )

        self.draw(self._x0, self._y0)

    def rawblit(self, buf, x, y, width, height):
        """Blit raw pixels to the display.

        :param buf: Pixel buffer
        :param x:  X coordinate of the left-most pixels of the rectangle
        :param y:  Y coordinate of the top-most pixels of the rectangle
        :param w:  Width of the rectangle, defaults to None (which means select
                   the right-most pixel of the display)
        :param h:  Height of the rectangle, defaults to None (which means select
                   the bottom-most pixel of the display)
        """
        self.set_window(x, y, width, height)
        self.window_buff[:] = buf
        self.blit(self.window, x, y)

    def draw(self, x, y):
        self.blit(self.window, x, y)

    def rfill(self, bg, x=0, y=0, w=None, h=None):
        """Draw a solid colour rectangle.

        If no arguments a provided the whole display will be filled with
        the background colour (typically black).

        :param bg: Background colour (in RGB565 format)
        :param x:  X coordinate of the left-most pixels of the rectangle
        :param y:  Y coordinate of the top-most pixels of the rectangle
        :param w:  Width of the rectangle, defaults to None (which means select
                   the right-most pixel of the display)
        :param h:  Height of the rectangle, defaults to None (which means select
                   the bottom-most pixel of the display)
        """
        self.rect(x, y, w, h, bg, True)
        # if not w:
        #     w = self.width - x
        # if not h:
        #     h = self.height - y
        # self.set_window(x, y, w, h)

        # # Populate the line buffer
        # buf = self.linebuffer[0 : 2 * w]
        # for xi in range(0, 2 * w, 2):
        #     buf[xi] = bg >> 8
        #     buf[xi + 1] = bg & 0xFF

        # # Do the fill
        # for yi in range(h):
        #     self.write_data(buf)

    def show(self):
        """show the buffer on the display"""
        self.display.show(self.buffer)

    def init(self):
        return self.poll_event()

    def print(self, txt, x, y, c=WHITE):
        self.text(txt, x, y, c)
        self.show()

    def reset(self):
        self.clear()

    def clear(self):
        self.fill(0)
        self.show()

    def save(self, file_name):
        """save the buffer to a BMP"""
        self.display.save(self.buffer, file_name)

    def poll_event(self):
        """poll for a SDL_Event and return it"""
        return self.display.poll_event()

    def deinit(self):
        """deinitialize the display"""
        self.display.deinit()
