import uqr
import qrcode
import display
import sys

WIDTH = 240
HEIGHT = 240

message = sys.argv.pop()
if not message:
    message = "hello world"
tft = display.Display(WIDTH, HEIGHT, x_scale=2, y_scale=2, title="QRCode")
tft.init()

_q = uqr.make(message)

qrc = qrcode.QRCode(_q)

qrc.display(tft, y0=50, x0=50)
