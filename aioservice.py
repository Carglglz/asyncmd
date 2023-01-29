import sys

sys.path.append("./aioservices")

from services import Services

_SERVICES_GROUP = {service.name: service for service in Services}


def list():
    global _SERVICES_GROUP
    for service in _SERVICES_GROUP.values():
        print(f"{service}")


def load(name=None, debug=False, log=None, debug_log=False):
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
                if debug:
                    print(f"[ \033[92mOK\x1b[0m ] {service} loaded")
                if debug_log and log:
                    log.info(f"[aioservice] [ \033[92mOK\x1b[0m ] {service} loaded")
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

            if debug:
                print(f"[ \033[92mOK\x1b[0m ] {service} loaded")
            if debug_log and log:
                log.info(f"[aioservice] [ \033[92mOK\x1b[0m ] {service} loaded")


def enable():
    pass


def disable():
    pass
