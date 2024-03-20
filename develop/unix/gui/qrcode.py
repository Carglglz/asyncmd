import sys


class QRCode:
    """Class to pprint any qr code to stdout"""

    def __init__(self, qr):
        self.qr = qr
        self.size = qr.packed()[0]
        self.width = qr.width()
        self.height = qr.width()

    def pprint(self):
        modcount = self.qr.width()
        for i in range(2):
            sys.stdout.write(
                "\x1b[1;47m    " + (" " * (modcount * 2 + 4)) + "\x1b[0m\n"
            )
        for r in range(modcount):
            sys.stdout.write("\x1b[1;47m    \x1b[40m")
            for c in range(modcount):
                if self.qr.get(r, c):
                    sys.stdout.write("  ")
                else:
                    sys.stdout.write("\x1b[1;47m  \x1b[40m")
            sys.stdout.write("\x1b[1;47m    \x1b[0m\n")
        for i in range(2):
            sys.stdout.write(
                "\x1b[1;47m    " + (" " * (modcount * 2 + 4)) + "\x1b[0m\n"
            )

    def display(self, screen, ps=5, x0=10, y0=10):
        # qr pixel size x=5, y=8
        xs = ps
        dpi = screen.height / screen.width
        ys = round(xs * (dpi))
        x = x0
        y = y0
        WHITE = const(0xFFFF)
        BLACK = const(0x0000)
        qrp1 = (xs, ys, WHITE, True)
        qrp2 = (xs, ys, BLACK, True)

        modcount = self.qr.width()
        # margin
        screen.rect(
            x0, y0, (modcount + 6) * xs, round((modcount + 6) * ys), WHITE, True
        )
        x0 = x0 + (2 * xs)
        y0 = y0 + (2 * ys)
        x = x0
        y = y0
        for r in range(modcount):
            y += ys
            for c in range(modcount):
                x += xs
                if self.qr.get(r, c):
                    screen.rect(x, y, *qrp2)
                else:
                    screen.rect(x, y, *qrp1)
            x = x0
        screen.show()

    def get(self, x, y):
        return self.qr.get(x, y)

    def packed(self):
        if self.rle:
            return (self.height, self.width, self.rle)
        else:
            return self.qr.packed()
