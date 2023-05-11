from logging import StreamHandler
import os


class FileRotationHandler(StreamHandler):
    def __init__(self, filename, mode="a", encoding="UTF-8", max_size=2000):
        super().__init__(stream=None)
        self.max_size = max_size
        self.filename = filename
        self.encoding = encoding

    def close(self):
        super().close()
        self.stream.close()

    def emit(self, record):
        if record.levelno >= self.level:
            self.rotate_log()
            with open(self.filename, mode="a", encoding=self.encoding) as fl:
                fl.write(self.format(record) + self.terminator)

    def rotate_log(self):
        if self.filename in os.listdir():
            if os.stat(self.filename)[6] > self.max_size:
                os.rename(self.filename, f"{self.filename}.1")
