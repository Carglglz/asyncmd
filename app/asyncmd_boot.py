from frz_services import services, config, envfile
import os
import json

AIOSERVICES_INIT = """

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

"""

_SERVICE = "from {} import service"


def setup(log):
    try:
        os.mkdir("aioservices")
        os.mkdir("aioservices/services")
        with open("aioservices/services/__init__.py", "w") as aioinit:
            aioinit.write(AIOSERVICES_INIT)

        log.info("aioservices init setup [ \033[92mOK\x1b[0m ]")
    except Exception as e:
        log.error(e)

    for service in services:
        with open(f"aioservices/services/{service}.py", "w") as srv:
            srv.write(_SERVICE.format(service))
        log.info(f"Service {service} setup [ \033[92mOK\x1b[0m ]")


def gen_services_config(log):
    try:
        os.stat("services.config")
        return
    except Exception:
        pass

    services_config = {}

    for service in (_srv.replace("_service", "") for _srv in services):
        services_config[service] = config.get(service, {"enabled": False})

    with open("services.config", "w") as sconf:
        sconf.write(json.dumps(services_config))

    log.info("services.config setup [ \033[92mOK\x1b[0m ]")


def gen_env(log):
    try:
        os.stat(".env")
        return
    except Exception:
        pass

    with open(".env", "w") as envf:
        envf.write(envfile)

    log.info("dotenv file setup [ \033[92mOK\x1b[0m ]")


def config_setup(log):
    # Generate services.config from frz_services module
    gen_services_config(log)
    # Generate .env file
    gen_env(log)
