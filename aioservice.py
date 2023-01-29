import sys

sys.path.append("./aioservices")

from services import Services

_SERVICES_GROUP = {service.name: service for service in Services}


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


def list():
    global _SERVICES_GROUP
    for service in _SERVICES_GROUP.values():
        print(f"{service}")


def load(name=None, debug=False, log=None):
    global _SERVICES_GROUP
    import aioctl

    if not name:
        for service in _SERVICES_GROUP.values():
            if service.enabled:
                aioctl.add(
                    service.task,
                    service,
                    *service.args,
                    **service.kwargs,
                    name=f"{service.name}.service",
                    _id=f"{service.name}.service",
                    log=log,
                )
    else:
        if name in _SERVICES_GROUP.keys():
            service = _SERVICES_GROUP[name]
            aioctl.add(
                service.task,
                service,
                *service.args,
                **service.kwargs,
                name=f"{service.name}.service",
                _id=f"{service.name}.service",
                log=log,
            )


def enable():
    pass


def disable():
    pass
