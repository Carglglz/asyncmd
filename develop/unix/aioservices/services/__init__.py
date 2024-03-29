import os
import json
from . import *
from aioclass import Service

_SERVICES_CONFIG = "services.config"
__modules__ = {
    srv
    for srv in os.listdir(__path__)
    if srv.endswith("_service.py") or srv.endswith("_service.mpy")
}
__services__ = {}
__failed__ = {}
# print(__modules__)


def getserv(script):
    return script.replace("_service.py", "").replace("_service.mpy", "")


def getmod(script):
    return script.replace(".py", "").replace(".mpy", "")


def get_config(name=None):
    global _SERVICES_CONFIG

    try:
        with open(_SERVICES_CONFIG, "r") as servs_conf:
            service_config = json.load(servs_conf)
    except Exception:
        return False

    if not name:
        return service_config
    else:
        if name in service_config:
            return service_config[name]
        else:
            return False


_current_config = get_config()

for _srv in __modules__:
    # print(f'services.{_srv.replace(".py", "")}')
    if _current_config and getserv(_srv) in _current_config:
        if not _current_config[getserv(_srv)]["enabled"]:
            # print(f"not loading {_srv}")
            continue
    try:
        _tmp = __import__(f"services.{getmod(_srv)}", [], [], ["service"])
        _tmp.service.path = f"{__path__}/{_srv}"
        __services__[getmod(_srv)] = _tmp.service
    except Exception as e:
        _fs = Service(getserv(_srv))
        _fs.path = f"{__path__}/{_srv}"
        _fs.info = e
        _fs.loaded = False
        __failed__[getserv(_srv)] = _fs
        __services__[getmod(_srv)] = _fs


modules = __modules__
services = __services__
failed_services = __failed__


Services = (sv for sv in __services__.values())

__all__ = [modules, Services, failed_services]
