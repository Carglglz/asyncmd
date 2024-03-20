import display
import time  # noqa
import draw565  # noqa
import logo  # noqa
import fonts.sans18  # noqa
import sdl2  # noqa
import sys  # noqa

WIDTH = 640
HEIGHT = 320


tft = display.Display(WIDTH, HEIGHT, x_scale=2, y_scale=2, title="MicroPython")

dw = draw565.Draw565(tft)
dw.set_font(fonts.sans18)

dw.blit(logo.micropython, 180, 2)
mpv = f"Version: {sys.version.split(';')[-1].strip().split("-")[0]}"
mpm = f"Machine: {sys.implementation._machine}"
dw.string(mpv, 120, 250)
dw.string(mpm, 120, 270)
tft.text("Press any key to continue", 180, 300, 0xFFFF)
tft.show()
time.sleep(1)

# for i in range(0, int(HEIGHT / 10)):
#     tft.scroll(0, -10)
#     tft.show()
while True:
    event = tft.poll_event()

    if not event:
        continue
    # print(event)

    if event[sdl2.TYPE] == sdl2.SDL_KEYDOWN:
        key = event[sdl2.KEYNAME]
        mod = event[sdl2.MOD]
        tft.clear()
        tft.text(key, 180, 180, 0xFFFF)
    # if the event is SDL_QUIT, exit
    if event[sdl2.TYPE] == sdl2.SDL_QUIT:
        break

    # if the event is SDL_MOUSEBUTTONDOWN, get the mouse position
    if event[sdl2.TYPE] == sdl2.SDL_MOUSEBUTTONDOWN:
        p_x = event[sdl2.X]
        p_y = event[sdl2.Y]

    # if the event is SDL_MOUSEBUTTONUP, stop drawing
    elif event[sdl2.TYPE] == sdl2.SDL_MOUSEBUTTONUP:
        pass
    # if the event is SDL_MOUSEMOTION, and we are drawing, draw the pixel
    elif event[sdl2.TYPE] == sdl2.SDL_MOUSEMOTION:
        pass
    # update the display
    tft.show()

    time.sleep_ms(10)
