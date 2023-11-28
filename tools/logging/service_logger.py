import sys
import io

CRITICAL = const(50)
ERROR = const(40)
WARNING = const(30)
INFO = const(20)
DEBUG = const(10)
NOTSET = const(0)


_level_dict = {
    "CRITICAL": CRITICAL,
    "ERROR": ERROR,
    "WARNING": WARNING,
    "INFO": INFO,
    "DEBUG": DEBUG,
}


class ServiceLogger:
    def __init__(self, logger, name, level=INFO):
        self.name = name
        self.level = _level_dict.get(level, INFO)
        self.logger = logger

    def setLevel(self, level):
        self.level = _level_dict.get(level, INFO)

    def isEnabledFor(self, level):
        return level >= self.getEffectiveLevel()

    def getEffectiveLevel(self):
        return self.level

    def getLoggerName(self, cname=None):
        if not cname:
            return f"{self.name}.service"
        else:
            return f"{self.name}.service.{cname}"

    def log(self, level, msg, *args, **kwargs):
        if self.isEnabledFor(level):
            self.logger.log(
                level,
                f"[{self.getLoggerName(kwargs.get('cname'))}] {msg}",
                *args,
            )

    def debug(self, msg, *args, **kwargs):
        self.log(DEBUG, msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        self.log(INFO, msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        self.log(WARNING, msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        self.log(ERROR, msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        self.log(CRITICAL, msg, *args, **kwargs)

    def exception(self, msg, *args, exc_info=True, **kwargs):
        self.log(ERROR, msg, *args, **kwargs)
        tb = None
        if isinstance(exc_info, BaseException):
            tb = exc_info
        elif hasattr(sys, "exc_info"):
            tb = sys.exc_info()[1]
        if tb:
            buf = io.StringIO()
            sys.print_exception(tb, buf)
            self.log(ERROR, buf.getvalue())
