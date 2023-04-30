
### aioservices 


Conventions for aioservices check `hello_service.py` or `world_service.py` as template.

- Inherit from `aioclass.Service`
- Name xxx_service.py or (.mpy)
- attributes:
    - info
    - type
    - enabled
    - docs
    - args 
    - kwargs
    - log 
    - custom (optional)
- show method (optional) --> aioctl.status
- report method (optional) --> devop.service
- stats method (optional) --> stats.service
- `__call__` method (optional) --> aioservice.service("name")()
- on_stop method callback 
- on_error method callback
- method named task and decorated with aioctl.aiotask
- optional aiotask decorated child tasks 
- declare e.g. service = HelloService("hello")
- placed in `aioservices/services`

aioservice discovery/loader --> `aioservices/services/__init__.py`
will discover available services and load them if enabled when using `aioservice.init` or `aioservice.boot`


how to create a service, example hello_service.py

how to create child tasks

how to use aioservice.init --> runtime/schedule services 

how to use aioservice.boot --> core services 

in async main task
