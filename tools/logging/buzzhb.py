import logging


class BuzzHeartBeat:
    def __init__(self, buzz):
        self.buzz = buzz

    def notify(self, level):
        if level == logging.WARNING:
            self.buzz.warning()
        if level >= logging.ERROR:
            self.buzz.error()
