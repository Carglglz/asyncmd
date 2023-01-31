import os
import json
from . import *

_SERVICES_CONFIG = "services.config"
__modules__ = [srv for srv in os.listdir(__path__) if srv.endswith("_service.py")]
__services__ = {}
# print(__modules__)


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
    if _current_config and _srv.replace("_service.py", "") in _current_config:
        if not _current_config[_srv.replace("_service.py", "")]["enabled"]:
            # print(f"not loading {_srv}")
            continue
    _tmp = __import__(f'services.{_srv.replace(".py", "")}', [], [], ["service"])
    _tmp.service.path = f"{__path__}/{_srv}"
    __services__[_srv.replace(".py", "")] = _tmp.service

modules = __modules__
services = __services__


Services = (sv for sv in __services__.values())

__all__ = [modules, Services]
