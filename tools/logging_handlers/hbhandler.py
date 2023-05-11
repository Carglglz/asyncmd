from logging import StreamHandler


class HeartBeatHandler(StreamHandler):
    def __init__(self, heartbeatobj):
        super().__init__(stream=None)
        self.hb = heartbeatobj

    def close(self):
        super().close()
        self.stream.close()

    def emit(self, record):
        if record.levelno >= self.level:
            self.hb.notify(record.levelno)
