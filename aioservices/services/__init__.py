import os
from . import *

__modules__ = [srv for srv in os.listdir(__path__) if srv.endswith("_service.py")]
__services__ = {}
# print(__modules__)
for _srv in __modules__:
    # print(f'services.{_srv.replace(".py", "")}')
    _tmp = __import__(f'services.{_srv.replace(".py", "")}', [], [], ["service"])
    _tmp.service.path = f"{__path__}/{_srv}"
    __services__[_srv.replace(".py", "")] = _tmp.service

modules = __modules__
services = __services__


Services = (sv for sv in __services__.values())

__all__ = [modules, Services]
