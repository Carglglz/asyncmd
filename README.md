
# Tools for MicroPython Async Development

Inspired by [aiorepl](https://github.com/micropython/micropython-lib/tree/master/micropython/aiorepl), 
mpy-aiotools is an asyncio based set of tools to help with the development of asynchronous applications implemented in MicroPython.

Asyncio is ideal for running multiple tasks concurrently\*, however an easy way to 
interactively track/inspect the asyncio event loop and its running tasks was lacking
until the introduction of [aiorepl](https://github.com/micropython/micropython-lib/tree/master/micropython/aiorepl).

This set of tools builds upon this *aiorepl* capacity to interact with tasks running in the event loop, running
blocking or non-blocking (async) functions.

mpy-aiotools is intended to be flexible and extensible i.e. minium requirement is aioctl.py
and then every script builds upon *aioctl* functionality.

#### Features

* Create async tasks that can be controlled/tracked/managed/debugged or profiled --> `aioctl.py`


    Create a task that can be stopped or restarted, inspect its result/return value, 
    internal error, traceback message, know how long it has been running or how long it has been done.
    Also allows to add a custom name/id to the task, or run a callback function when the task is stopped
    or throws an error. 
    
    e.g. ``● hello_task: status: running since 2015-01-01 00:00:19; 4 s ago``

* Asynchronous RAM logging --> `aiolog.py`
    
    Create a "ring buffered stream" to log tasks output indefinitely. It 
    allocates a predefined amount of RAM and rotates automatically so it never allocates
    more RAM than the one predefined. 
    Also allows to "cat"+"grep" or async follow+grep its content.
    
    e.g. `2015-01-01 00:00:19 [pyb] [INFO] [hello_task] LED 3 toggled!`


* Asynchronous scheduling --> `aioschedule.py`

    Create a task and run it in `s` seconds (*from event loop start or task creation*) or at a time `(timetuple)` and repeat every `n` seconds. 
    This has a "scheduler task loop" that checks every second its schedule and runs a scheduled task when the time is due.

    e.g. 
    
    ```
    ● world_task: status: done @ 2015-01-01 00:12:44; 48 s ago --> result:
         
    ┗━► schedule: last @ 2015-01-01 00:12:39 --> next in 37 s
    ```


* Asynchronous services* --> `aioservice.py`, `aioclass.py`, `aioservices/services`, `services.config`

    Create a service that can have one or more tasks, install/list/get status of services, load/unload, config services 
    as enabled or disabled or service main task args and keyword args, get the traceback of services that failed to load, init/boot services 
    following a priority depending of another service dependency...

    e.g. 
    ```
    [ OK ] Service: hello_core.service from ./aioservices/services/hello_core_service.py loaded
    [ OK ] Service: hello_low.service from ./aioservices/services/hello_low_service.py loaded
    [ OK ] Service: world.service from ./aioservices/services/world_service.mpy loaded
    [ OK ] Service: hello.service from ./aioservices/services/hello_service.mpy loaded
    [ OK ] Service: watcher.service from ./aioservices/services/watcher_service.mpy loaded
    [ ERROR ] Service: dofail.service from ./aioservices/services/dofail_service.mpy not loaded: Error: ZeroDivisionError
    ```
    
    As a bonus enabling debug mode in `aioctl` gives the full service status
    
    ```
    ● hello.service - Hello example runner v1.0
        Loaded: Service: hello.service from ./aioservices/services/hello_service.mpy
        Active: (active) running since 2015-01-01 00:35:00; 00:02:31 ago
        Type: runtime.service
        Docs: https://github.com/Carglglz/mpy-aiotools/blob/main/README.md
        Stats:     Temp: 25.79095 C   Loop info: exec time: 5 ms; # loops: 186
        Task: <Taskctl object at 20003010>
        ┗━► args: (Service: hello.service from ./aioservices/services/hello_service.mpy, 3, 10)
        ┗━► kwargs: { 'on_error': <bound_method>,
                      '_id': 'hello.service',
                      'log': <Logger object at 20008010>,
                      'on_stop': <bound_method> }
    2015-01-01 00:35:10 [pyb] [INFO] [hello.service] LED 3 toggled!
    2015-01-01 00:35:20 [pyb] [INFO] [hello.service] LED 2 toggled!
    ```

-----
> \* **NOTE** 
*Multiple tasks concurrently where timing precision is only needed to be held up to a certain degree
which can vary with the number of tasks running and the amount of time they
take to run and how frequent they are scheduled*
----

> \* **NOTE 2**: *Inspiration comes obviously from Linux [systemd](https://github.com/systemd/systemd) specially `sysctl` and `journalctl`.*

## Install

For `aioctl.py`, `aioschedule.py`, `ailog.py`, `aioservice.py` and `aioclass.py` just upload the scripts to the device*

\*(better if compiled i.e. `.mpy` using `mpy-cross` to save memory)

For `aioservices/services` make the directories first and then upload  `aioservices/services/__init__.py` (or directly sync `aioservices`)

Then to install a service upload it to this directory or use 
e.g. 

```  
 >>> aioservice.install("myserv_service.py")
```

This set of tools (with exception of `aioservices/services`) can be frozen in the firmware too which will be the best option for saving memory.

---
> \* **NOTE 3**: `aiolog` stream class needs a logger class the only writes to the stream (not print, see # for context).

---


## Example
Simple example demonstrating @aioctl.aiotask decorator

More examples in examples/README.md

## Tools

### aioctl --> tools/aioctl.md



### aiolog



### aioschedule



### aioservice


### aioclass


### aioservices


### app

#### aio- mqtt, neopixels, webserver

Async based classes of MQTT client, neopixels animations and a WebServer
based on Microdot


### logger

Logging module compatible with `AioStream` class from `aiolog.py`


## Examples 

Set of examples of increasing complexity to show the capabilities
of these tools.








