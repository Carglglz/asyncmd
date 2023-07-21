from logging import StreamHandler
import sys


class RsysLogHandler(StreamHandler):
    def __init__(self, rsyslogger):
        super().__init__(stream=None)
        self.rsyslog = rsyslogger
        self.rsyslog._err_print = False

    def close(self):
        super().close()

    def emit(self, record):
        if record.levelno >= self.level:
            try:
                # msg, level, timestamp, appname
                self.format(record)
                self.rsyslog.log_msg(
                    record.message,
                    record.levelname,
                    record.asctime,
                    record.name,
                )
            except Exception as e:
                sys.print_exception(e)
