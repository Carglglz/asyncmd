import sys
import json
import os

sys.path.append("./aioservices")

from services import Services

_SERVICES_GROUP = {service.name: service for service in Services}
_SERVICES_CONFIG = "services.config"


def list():
    global _SERVICES_GROUP
    for service in _SERVICES_GROUP.values():
        print(f"{service}")


def load(name=None, debug=False, log=None, debug_log=False, config=False):
    global _SERVICES_GROUP
    import aioctl

    if not name:
        if config:
            _servs_config = get_config()
        for service in _SERVICES_GROUP.values():
            if config:
                if service.name in _servs_config.keys():
                    if _servs_config[service.name]["enabled"]:
                        service.enabled = True
                        if "args" in _servs_config[service.name]:
                            service.args = _servs_config[service.name]["args"]

                        if "kwargs" in _servs_config[service.name]:
                            service.kwargs = _servs_config[service.name]["kwargs"]

                            if "schedule" in service.kwargs and hasattr(
                                service, "schedule"
                            ):
                                service.schedule = service.kwargs.pop("schedule")
                    else:
                        service.enabled = False
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

                if aioctl._SCHEDULE:
                    if hasattr(service, "schedule"):
                        import aioschedule

                        aioschedule.schedule(
                            f"{service.name}.service", **service.schedule
                        )
                if debug:
                    print(f"[ \033[92mOK\x1b[0m ] {service} loaded")
                if debug_log and log:
                    log.info(f"[aioservice] [ \033[92mOK\x1b[0m ] {service} loaded")
    else:
        if name in _SERVICES_GROUP.keys():

            service = _SERVICES_GROUP[name]
            if config:
                _serv_config = get_config(name)
                if _serv_config:
                    if "args" in _serv_config:
                        service.args = _serv_config["args"]

                    if "kwargs" in _serv_config:
                        service.kwargs = _serv_config["kwargs"]
                        if "schedule" in service.kwargs and hasattr(
                            service, "schedule"
                        ):
                            service.schedule = service.kwargs.pop("schedule")

            aioctl.add(
                service.task,
                service,
                *service.args,
                **service.kwargs,
                name=f"{service.name}.service",
                _id=f"{service.name}.service",
                log=log,
            )
            if aioctl._SCHEDULE:
                if hasattr(service, "schedule"):
                    import aioschedule

                    aioschedule.schedule(f"{service.name}.service", **service.schedule)

            if debug:
                print(f"[ \033[92mOK\x1b[0m ] {service} loaded")
            if debug_log and log:
                log.info(f"[aioservice] [ \033[92mOK\x1b[0m ] {service} loaded")


def init(debug=True, log=None, debug_log=False, config=True):

    for service in _SERVICES_GROUP.values():
        if hasattr(service, "type"):
            if service.type != "core.service":
                load(
                    service.name,
                    debug=debug,
                    log=log,
                    debug_log=debug_log,
                    config=config,
                )


def boot(debug=True, log=None, debug_log=False, config=True):
    global _SERVICES_GROUP

    for service in _SERVICES_GROUP.values():
        if hasattr(service, "type"):
            if service.type == "core.service":
                load(
                    service.name,
                    debug=debug,
                    log=log,
                    debug_log=debug_log,
                    config=config,
                )


def config(name, enable, *args, **kwargs):
    global _SERVICES_CONFIG
    _exists = False
    try:
        # exists
        os.stat(_SERVICES_CONFIG)
        _exists = True
    except Exception:
        # create new one
        pass
    if _exists:  # load
        _service_config = get_config()
        _service_config[name]["enabled"] = enable
        if args:
            _service_config[name]["args"] = args
        if kwargs:
            _service_config[name]["kwargs"] = kwargs
    else:  # create
        _service_config = {}
        _service_config[name] = {}
        _service_config[name]["enabled"] = enable
        if args:
            _service_config[name]["args"] = args
        if kwargs:
            _service_config[name]["kwargs"] = kwargs

    try:
        with open(_SERVICES_CONFIG, "w") as servs_conf:
            json.dump(_service_config, servs_conf)
        return True
    except Exception as e:
        sys.print_exception(e, sys.stdout)
        return
        # create


def enable(name):
    config(name, True)


def disable(name):
    config(name, False)


def get_config(name=None):
    global _SERVICES_CONFIG

    try:
        with open(_SERVICES_CONFIG, "r") as servs_conf:
            service_config = json.load(servs_conf)
    except Exception as e:
        sys.print_exception(e, sys.stdout)
        return

    if not name:
        return service_config
    else:
        if name in service_config:
            return service_config[name]
        else:
            return False
