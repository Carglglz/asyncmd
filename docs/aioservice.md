
## Documentation for `aioservice`

## Introduction
The aioservice library provides a set of functions to manage **asynchronous services**. It allows to easily load, unload, enable, disable, and configure services.

This concept of *asynchronous service* is just a simple class with at least a main **async task** and optionally one or more **child async tasks**. 

This idea of wrapping an *async task* with a *Service* class allows to extend async tasks with more functionality like :
- configuring args and kwargs 
- display custom information for debugging and documentation 
- inspect/change tasks internal variables states
- creating one or more child tasks
- other customizable features like custom service function call, status report ...

To see how to create `aioservices` check [aioservices conventions](https://github.com/Carglglz/asyncmd/blob/main/docs/aioservices.md)

## Functions
The following functions are available in the `aioservice` library:

### `service(name)`
This function returns the indicated service instance
```
>>> hs = aioservice.service("hello")
>>> hs
Service: hello.service from ./aioservices/services/hello_service.mpy
```

### `list()`
This function prints a list of all available loaded services.
```
>>> aioservice.list()
Service: watcher.service from ./aioservices/services/watcher_service.mpy
Service: devop.service from ./aioservices/services/devop_service.mpy
Service: hello.service from ./aioservices/services/hello_service.mpy
```

### `status(name)`
This function returns the status of a service or all if name is `None`
```
>>> aioservice.status("hello")
[ OK ] Service: hello.service from ./aioservices/services/hello_service.mpy loaded
>>> aioservice.status()
[ OK ] Service: watcher.service from ./aioservices/services/watcher_service.mpy loaded
[ OK ] Service: devop.service from ./aioservices/services/devop_service.mpy loaded
[ OK ] Service: hello.service from ./aioservices/services/hello_service.mpy loaded
```

### `load(name=None, debug=False, log=None, debug_log=False, config=False)`
This function loads a service. Keyword options:
 - debug: print debug info 
 - log: a Logger instance to write debugging info and pass the logger to the service
 - debug_log: log debug info
 - config: wether to load service configuration from `services.config` file
``` 
>>> aioservice.load("world")
[ OK ] Service: world.service from ./aioservices/services/world_service.mpy loaded
```

### `unload(name)`
This function unloads a service.
```
>>> aioservice.unload("world")
True
```

### `init(debug=True, log=None, debug_log=False, config=True, init_schedule=True)`
Keywords option same as `load` plus:
- init_schedule: loads `schedule_loop` task if there is a scheduled task.

This function initializes and load enabled services of type `runtime` and `schedule`.

### `boot(debug=True, log=None, debug_log=False, config=True)`
This function load services of type `core`. This means services that must be loaded first (before `runtime`/`schedule` services)
`core` services can have other `core` service requirements, so these services will be loaded one by one following this dependency requeriment or 
in parallel when there is not any requirement. Also `core` services must be `one shot` .i.e they must end before loading `runtime`/`schedule` services.

`boot` is an async function, e.g. how to use `boot` and `init`

```python
def run(logger):
    async def main(logger):
        aioctl.set_log(streamlog)
        # boot must be awaited 
        await aioservice.boot(log=logger, debug_log=True)

        aioctl.add(aiorepl.task, name="repl")
        aioservice.init(log=logger, debug_log=True)

        await asyncio.gather(*aioctl.tasks())

    asyncio.run(main(logger))


run(logger)
```
```
[ OK ] Service: hello_core.service from ./aioservices/services/hello_core_service.mpy loaded
[ OK ] Service: watcher.service from ./aioservices/services/watcher_service.mpy loaded
[ OK ] Service: devop.service from ./aioservices/services/devop_service.mpy loaded
[ OK ] Service: hello.service from ./aioservices/services/hello_service.mpy loaded
Starting asyncio REPL...
```

### `config(name, enabled, *args, **kwargs)`
This function configures a service.
It takes at least two arguments: the name of the service and `bool` to indicate `enabled` (`True`) or `disabled` (`False`).
Further `*args` and `**kwargs` are saved for configuring `args` and  `kwargs` of the service. 

It returns a boolean indicating whether the service was successfully configured or not.
Services configuration file is saved in `services.config`


### `enable(name)`
This function enables a service. It takes one argument: the name of the service. It returns a boolean indicating whether the service was successfully enabled or not.


### `disable(name)`
This function disables a service. It takes one argument: the name of the service. It returns a boolean indicating whether the service was successfully disabled or not.

### `get_config(name=None)`
This function returns the configuration of a service. It takes one argument: the name of the service. It returns a dictionary containing the configuration parameters (enabled, args and kwargs) of the service. If name is `None` return the configuration of all services.
```
>>> aioservice.get_config("hello")
{'enabled': True, 'args': [3, 2]}
```

### `traceback(name)`
This function returns the traceback of an error that occurred during the loading phase of a service. It takes one argument: the name of the service. It returns a string containing the traceback of the service.

```
[ OK ] Service: hello.service from ./aioservices/services/hello_service.mpy loaded
[ OK ] Service: devop.service from ./aioservices/services/devop_service.mpy loaded
[ ERROR ] Service: dofail.service from ./aioservices/services/dofail_service.mpy not loaded: Error: ZeroDivisionError
[ OK ] Service: watcher.service from ./aioservices/services/watcher_service.mpy loaded
Starting asyncio REPL...

>>> aioservice.traceback("dofail")
dofail: Traceback
Traceback (most recent call last):
  File "./aioservices/services/__init__.py", line 52, in <module>
  File "aioservices/services/dofail_service.py", line 16, in <module>
  File "aioservices/services/dofail_service.py", line 13, in __init__
ZeroDivisionError: divide by zero
>>>
```


