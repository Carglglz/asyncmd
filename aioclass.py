
class Service:
    def __init__(self, name):
        self.name = name
        self.path = ""
        self.info = ""
        self.type = "runtime.service"  # continuous running, other types are
        self.docs = ""
        self.enabled = False  # preset
        # core.service --> run one time at boot
        # schedule.service --> run and stop following a schedule

    def __repr__(self):
        return f"Service: {self.name}.service from {self.path}"
