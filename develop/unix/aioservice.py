import sys
import json
import os

sys.path.append("./aioservices")

from services import Services, failed_services

_SERVICES_GROUP = {service.name: service for service in Services}
_SERVICES_CONFIG = "services.config"
_SERVICES_STATUS = {"loaded": set(), "failed": set()}
_SERVICE_LOGGER = None


def service(name=None):
    global _SERVICES_GROUP
    if not name:
        return _SERVICES_GROUP
    elif name in _SERVICES_GROUP:
        return _SERVICES_GROUP[name]


def list():
    global _SERVICES_GROUP
    for service in _SERVICES_GROUP.values():
        print(f"{service}")


def status(name=None):
    global _SERVICES_STATUS
    if not name:
        for _service in _SERVICES_STATUS["loaded"]:
            print(f"[ \033[92mOK\x1b[0m ] {_service} loaded")
        for _service in _SERVICES_STATUS["failed"]:
            print(f"[ \u001b[31;1mERROR\u001b[0m ] {_service} not loaded:", end="")
            print(f" Error: {_service.info.__class__.__name__}")
    else:
        if service(name) in _SERVICES_STATUS["loaded"]:
            print(f"[ \033[92mOK\x1b[0m ] {service(name)} loaded")
        elif service(name) in _SERVICES_STATUS["failed"]:
            print(f"[ \u001b[31;1mERROR\u001b[0m ] {service(name)} not loaded:", end="")
            print(f" Error: {service(name).info.__class__.__name__}")


def call(name):
    if callable(service(name)):
        service(name)()


def _suid(_aioctl, name):
    name = f"{name}.service"
    _name = name
    _id = 0
    if _aioctl.group():
        while name in _aioctl.group().tasks:
            _id += 1
            name = f"{_name}@{_id}"
    return name


def load(name=None, debug=False, log=None, debug_log=False, config=False):
    global _SERVICES_GROUP, _SERVICES_STATUS, _SERVICE_LOGGER
    import aioctl

    if log:
        _SERVICE_LOGGER = log
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
                            service.kwargs.update(
                                **_servs_config[service.name]["kwargs"]
                            )

                            if "schedule" in service.kwargs and hasattr(
                                service, "schedule"
                            ):
                                service.schedule = service.kwargs.pop("schedule")
                    else:
                        service.enabled = False
            # catch failed load services
            if service.name in failed_services or not service.loaded:
                _SERVICES_STATUS["failed"].add(service)
                if debug:
                    print(
                        f"[ \u001b[31;1mERROR\u001b[0m ] {service} not loaded:", end=""
                    )
                    print(f" Error: {service.info.__class__.__name__}")
                if debug_log and log:
                    _err = f"{service} not loaded:"
                    _err += f" Error: {service.info.__class__.__name__}"
                    log.error(f"[aioservice] [ \u001b[31;1mERROR\u001b[0m ] {_err}")
                continue

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
                _SERVICES_STATUS["loaded"].add(service)
    else:
        if name in _SERVICES_GROUP.keys():
            service = _SERVICES_GROUP[name]
            if config and name not in failed_services:
                _serv_config = get_config(name)
                if _serv_config:
                    if "args" in _serv_config:
                        service.args = _serv_config["args"]

                    if "kwargs" in _serv_config:
                        service.kwargs.update(**_serv_config["kwargs"])
                        if "schedule" in service.kwargs and hasattr(
                            service, "schedule"
                        ):
                            service.schedule = service.kwargs.pop("schedule")

            # catch failed load services
            if service.name in failed_services or not service.loaded:
                _SERVICES_STATUS["failed"].add(service)
                if debug:
                    print(
                        f"[ \u001b[31;1mERROR\u001b[0m ] {service} not loaded:", end=""
                    )
                    print(f" Error: {service.info.__class__.__name__}")
                if debug_log and log:
                    _err = f"{service} not loaded:"
                    _err += f" Error: {service.info.__class__.__name__}"
                    log.error(f"[aioservice] [ \u001b[31;1mERROR\u001b[0m ] {_err}")
                return False

            _name = _suid(aioctl, service.name)

            aioctl.add(
                service.task,
                service,
                *service.args,
                **service.kwargs,
                name=_name,
                _id=_name,
                log=log,
            )
            if aioctl._SCHEDULE:
                if hasattr(service, "schedule"):
                    aioctl.stop(_name, stop_sch=False)
                    import aioschedule

                    aioschedule.schedule(_name, **service.schedule)

            if debug:
                print(f"[ \033[92mOK\x1b[0m ] {service} loaded")
            if debug_log and log:
                log.info(f"[aioservice] [ \033[92mOK\x1b[0m ] {service} loaded")

            _SERVICES_STATUS["loaded"].add(service)

        else:
            if "./aioservices/services" not in sys.path:
                sys.path.append("./aioservices/services")
            try:
                from services import modules

                end = "py"
                if f"{name}_service.{end}" not in modules:
                    end = "mpy"
                if f"{name}_service.{end}" not in modules:
                    return False

                _tmp = __import__(f"{name}_service", [], [], ["service"])
                _tmp.service.path = f"./aioservices/services/{name}_service.{end}"
                _SERVICES_GROUP[name] = _tmp.service
                load(
                    name,
                    debug=True,
                    log=_SERVICE_LOGGER,
                    debug_log=True,
                    config=config,
                )
            except Exception as e:
                sys.print_exception(e)


def unload(name):
    global _SERVICES_GROUP, _SERVICES_STATUS
    import aioctl

    try:
        aioctl.stop(f"{name}.service*")
        aioctl.delete(f"{name}.service*")
        if name in _SERVICES_GROUP:
            uns = _SERVICES_GROUP.pop(name)
            if uns in _SERVICES_STATUS["loaded"]:
                _SERVICES_STATUS["loaded"].remove(uns)
            elif uns in _SERVICES_STATUS["failed"]:
                _SERVICES_STATUS["failed"].remove(uns)
            return True
    except Exception as e:
        sys.print_exception(e)


def init(debug=True, log=None, debug_log=False, config=True, init_schedule=True):
    import aioctl

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

    if aioctl._SCHEDULE and init_schedule:
        import aioschedule

        if aioschedule.group():
            if "schedule_loop" not in aioctl.group().tasks:
                aioctl.add(aioschedule.schedule_loop)


async def boot(debug=True, log=None, debug_log=False, config=True):
    import aioctl
    import asyncio

    core_services = [
        srv for srv in _SERVICES_GROUP.values() if srv.type == "core.service"
    ]
    core_hp_services = []
    core_lp_services = []

    if config:
        _servs_config = get_config()
        for srv in core_services:
            srv.args = _servs_config[srv.name].get("args", srv.args)
            srv.kwargs.update(**_servs_config[srv.name].get("kwargs", srv.kwargs))
    # check if any requirement for core.service
    serv_rq = [srv for srv in core_services if "require" in srv.kwargs]
    serv_core = [srv for srv in core_services if srv not in serv_rq]
    # true -> from aioclass import PQeue
    if serv_rq:
        from aioclass import PQueue

        # -> add core services
        # -> psolve
        # -> get a priority core hp list, load core_lp
        pq = PQueue()
        pq.add(*serv_core, *serv_rq)
        pl, hp, lp = pq.psolve()

        if debug:
            print("[ \033[92mOK\x1b[0m ] Priority core services solved... ")
            print("[ Booting ] Order: ", end="")
            for s, p in pl:
                print(f"--> {s} ", end="")
            print("")
        if debug_log and log:
            log.info(
                "[aioservice] [ \033[92mOK\x1b[0m ] Priority "
                + "core services solved..."
            )
            _boot_ord = "[ Booting ] Order: "
            for s, p in pl:
                _boot_ord += f"--> {s} "

            log.info(_boot_ord)

        core_hp_services = hp
        core_lp_services = lp
    else:
        core_lp_services = serv_core

    # -> await core_hp serialy
    # -> gather core_lp concurrently
    # false ->
    # -> all are core_lp
    for service in core_hp_services:
        if isinstance(service.info, Exception):
            res = service.info
        else:
            load(
                service.name,
                debug=debug,
                log=log,
                debug_log=debug_log,
                config=config,
            )

            if debug:
                print(f"[ \033[92mOK\x1b[0m ] Booting {service.name}.service... ")
            if debug_log and log:
                log.info(
                    "[aioservice] [ \033[92mOK\x1b[0m ] Booting "
                    + f"{service.name}.service..."
                )
            res = await aioctl.group().tasks[f"{service.name}.service"].task
        if res:
            if not issubclass(res.__class__, Exception):
                if debug:
                    print("[ \033[92mOK\x1b[0m ] " + f"{service.name}.service {res} ")
                if debug_log and log:
                    log.info(
                        "[aioservice] [ \033[92mOK\x1b[0m ] "
                        + f"{service.name}.service {res}"
                    )
            else:
                if debug:
                    print(
                        f"[ \u001b[31;1mERROR\u001b[0m ] {service.name}:",
                        end="",
                    )
                    print(f" Error: {res.__class__.__name__}: {res}")
                if debug_log and log:
                    _err = f"{service.name}:"
                    _err += f" Error: {res.__class__.__name__}: {res}"
                    log.error(f"[aioservice] [ \u001b[31;1mERROR\u001b[0m ] {_err}")

    for service in core_lp_services:
        load(
            service.name,
            debug=debug,
            log=log,
            debug_log=debug_log,
            config=config,
        )

    if core_lp_services:
        await asyncio.gather(*aioctl.tasks())
    asyncio.new_event_loop()


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
        if name not in _service_config:
            _service_config[name] = {}
        _service_config[name]["enabled"] = enable
        if args:
            _service_config[name]["args"] = args
        if kwargs:
            if "kwargs" in _service_config[name]:
                _service_config[name]["kwargs"].update(**kwargs)
            else:
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


def traceback(name=None, rtn=False):
    global _SERVICES_GROUP
    if name in _SERVICES_GROUP:
        _tb = _SERVICES_GROUP[name].info
        if issubclass(_tb.__class__, Exception):
            if rtn:
                return True
            print(f"{name}: Traceback")
            sys.print_exception(_tb)
        else:
            if rtn:
                return False
