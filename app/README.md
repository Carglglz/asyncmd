

## A simple asynchronous app example

Once services are installed/frozen, making an *asyncio* app is pretty simple, 
check and upload `main.py` and `app.py`, where the important bit is in `_main`
function


```python
async def _main(logger):
    # load core services
    print("Booting core services...")
    await aioservice.boot(log=logger, debug_log=True)
    print("Starting aiorepl...")
    
    # add aiorepl
    aioctl.add(aiorepl.task, name="repl")
    print("Loading services...")
    # load runtime and schedule services
    aioservice.init(log=logger, debug_log=True)
    print(">>> ")


    # now all tasks are running
    await asyncio.gather(*aioctl.tasks())
```

For example running the app in a `pyboard` with
`watcher.service`,`hello.service` and `world.service` enabled (and a *splash
screen*):

```
Running app...

    █████████████████  █████████████████
    █████████████████  █████████████████
    █████████████████  █████████████████
    █████████████████  █████████████████
    ████████  ███████  ███████  ████████
    ████████  ███████  ███████  ████████
    ████████  ███████  ███████  ████████
    ████████  ███████  ███████  ████████
    ████████  ███████  ███████  ████████
    ████████  ███████  ███████  ████████
    ████████  ███████  ███████  ████████
    ████████  ███████  ███████  ████████
    ████████  ███████  ███████  ████████
    ████████  ████████████████  ███  ███
    ████████  ████████████████  ███  ███
    ████████  ████████████████  ████████


 Version: MicroPython v1.20.0-162-g08b6c8808-dirty on 2023-06-02
 Machine: PYBv1.1 with STM32F405RG

Booting core services...
Starting aiorepl...
Loading services...
[ OK ] Service: watcher.service from ./aioservices/services/watcher_service.mpy loaded
[ OK ] Service: world.service from ./aioservices/services/world_service.mpy loaded
[ OK ] Service: hello.service from ./aioservices/services/hello_service.mpy loaded
>>>
# At this point aiorepl is running and we can check services/tasks states using
aioctl/aioservice

--> import aioctl
--> import aioservice
--> aioctl.status(log=False)
● world.service: status: scheduled - done @ 2023-06-04 00:35:21; 25 s ago --> result:
    ┗━► schedule: last @ 2023-06-04 00:35:16 --> next in 00:01:00 @ 2023-06-04 00:36:46
● repl: status: running since 2023-06-04 00:25:56; 00:09:50 ago
● watcher.service.wdt: status: running since 2023-06-04 00:26:06; 00:09:40 ago
● schedule_loop: status: running since 2023-06-04 00:25:56; 00:09:50 ago
● watcher.service: status: running since 2023-06-04 00:25:56; 00:09:50 ago
● hello.service: status: running since 2023-06-04 00:35:37; 9 s ago
-->
--> aioctl.debug()
--> aioctl.status("*.service")
● world.service - World example runner v1.0
    Loaded: Service: world.service from ./aioservices/services/world_service.mpy
    Active: status: scheduled - done @ 2023-06-04 00:35:21; 00:01:15 ago --> result:
    Type: schedule.service
    Docs: https://github.com/Carglglz/asyncmd/blob/main/README.md
    Task: <Taskctl object at 200066b0>
    ┗━► runtime: 5 s
    ┗━► schedule: last @ 2023-06-04 00:35:16 --> next in 9 s @ 2023-06-04 00:36:46
    ┗━► schedule opts: last_dt=(2023, 6, 4, 0, 35, 16, 6, 155), repeat=90, start_in=-1, _start_in=20, last=739154116
    ┗━► args: (Service: world.service from ./aioservices/services/world_service.mpy, 2, 5)
    ┗━► kwargs: { '_id': 'world.service',
                  'log': <Logger object at 2000c620> }
<-------------------------------------------------------------------------------->
● watcher.service - Watcher Service v1.0 - Restarts services on failed state
    Loaded: Service: watcher.service from ./aioservices/services/watcher_service.mpy
    Active: (active) running since 2023-06-04 00:25:56; 00:10:41 ago
    Type: runtime.service
    Docs: https://github.com/Carglglz/asyncmd/blob/main/README.md
    Stats:     # ERRORS: 16    Report: {'hello.service': {'ZeroDivisionError': {'count': 7, 'err': ZeroDivisionError('divide by zero',)}, 'ValueError': {'count': 9, 'err': ValueError()}}}
    CTasks: 1
        ┗━► ● watcher.service.wdt: status: running since 2023-06-04 00:26:06; 00:10:31 ago
                Task: <Taskctl object at 2000f250>
                ┗━► args: (Service: watcher.service from ./aioservices/services/watcher_service.mpy, 30000)
                ┗━► kwargs: { '_id': 'watcher.service.wdt',
                              'on_error': <bound_method> }
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    Task: <Taskctl object at 20007b10>
    ┗━► args: (Service: watcher.service from ./aioservices/services/watcher_service.mpy, 30)
    ┗━► kwargs: { 'watchdog': True,
                  'log': <Logger object at 2000c620>,
                  'on_error': <bound_method>,
                  'wdfeed': 30000,
                  'max_errors': 0,
                  'on_stop': <bound_method>,
                  '_id': 'watcher.service' }
2023-06-04 00:36:07 [pyboard] [INFO] [watcher.service] Error @ Task hello.service ValueError:
2023-06-04 00:36:07 [pyboard] [INFO] [watcher.service] Restarting Task hello.service
<-------------------------------------------------------------------------------->
● hello.service - Hello example runner v1.0
    Loaded: Service: hello.service from ./aioservices/services/hello_service.mpy
    Active: (active) running since 2023-06-04 00:36:07; 30 s ago
    Type: runtime.service
    Docs: https://github.com/Carglglz/asyncmd/blob/main/README.md
    Stats:     Temp: 25.5643 C   Loop info: exec time: 7 ms; # loops: 196
    Task: <Taskctl object at 20012c70>
    ┗━► args: (Service: hello.service from ./aioservices/services/hello_service.mpy, 3, 2)
    ┗━► kwargs: { 'on_error': <bound_method>,
                  '_id': 'hello.service',
                  'log': <Logger object at 2000c620>,
                  'on_stop': <bound_method> }
2023-06-04 00:35:49 [pyboard] [INFO] [hello.service] LED 1 toggled!
2023-06-04 00:35:51 [pyboard] [INFO] [hello.service] LED 1 toggled!
2023-06-04 00:35:53 [pyboard] [INFO] [hello.service] LED 4 toggled!
2023-06-04 00:35:55 [pyboard] [INFO] [hello.service] LED 3 toggled!
2023-06-04 00:35:57 [pyboard] [INFO] [hello.service] LED 3 toggled!
2023-06-04 00:35:59 [pyboard] [INFO] [hello.service] LED 1 toggled!
2023-06-04 00:36:01 [pyboard] [INFO] [hello.service] LED 1 toggled!
2023-06-04 00:36:03 [pyboard] [INFO] [hello.service] LED 2 toggled!
2023-06-04 00:36:05 [pyboard] [INFO] [hello.service] LED 4 toggled!
2023-06-04 00:36:05 [pyboard] [ERROR] [hello.service] ValueError: None
2023-06-04 00:36:06 [pyboard] [ERROR] [hello.service] Error callback
2023-06-04 00:36:07 [pyboard] [INFO] [hello.service] LED 3 toggled!
2023-06-04 00:36:09 [pyboard] [INFO] [hello.service] LED 3 toggled!
2023-06-04 00:36:11 [pyboard] [INFO] [hello.service] LED 2 toggled!
2023-06-04 00:36:13 [pyboard] [INFO] [hello.service] LED 2 toggled!
2023-06-04 00:36:15 [pyboard] [INFO] [hello.service] LED 1 toggled!
2023-06-04 00:36:17 [pyboard] [INFO] [hello.service] LED 4 toggled!
2023-06-04 00:36:19 [pyboard] [INFO] [hello.service] LED 2 toggled!
2023-06-04 00:36:21 [pyboard] [INFO] [hello.service] LED 2 toggled!
2023-06-04 00:36:23 [pyboard] [INFO] [hello.service] LED 4 toggled!
2023-06-04 00:36:25 [pyboard] [INFO] [hello.service] LED 3 toggled!
2023-06-04 00:36:27 [pyboard] [INFO] [hello.service] LED 3 toggled!
2023-06-04 00:36:29 [pyboard] [INFO] [hello.service] LED 2 toggled!
2023-06-04 00:36:31 [pyboard] [INFO] [hello.service] LED 2 toggled!
2023-06-04 00:36:33 [pyboard] [INFO] [hello.service] LED 2 toggled!
2023-06-04 00:36:35 [pyboard] [INFO] [hello.service] LED 3 toggled!
<-------------------------------------------------------------------------------->




```
