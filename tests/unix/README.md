
Install `aiorepl`, `asyncmd` (.i.e `aioctl.py`, `aioservice.py`...), `logging`,
`time`

Then in unix micropython run test.py

```
 $ micropython
MicroPython v1.20.0-162-g08b6c8808-dirty on 2023-06-04; darwin [GCC 4.2.1] version
Use Ctrl-D to exit, Ctrl-E for paste mode
>>> import test

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


 Version: MicroPython v1.20.0-162-g08b6c8808-dirty on 2023-06-04
 Machine: darwin [GCC 4.2.1] version

starting tasks...
>>>
[ OK ] Service: watcher.service from ./aioservices/services/watcher_service.py loaded
[ OK ] Service: stats.service from ./aioservices/services/stats_service.py loaded
[ OK ] Service: hello.service from ./aioservices/services/hello_service.py loaded
[ OK ] Service: world.service from ./aioservices/services/world_service.py loaded
>>>
Starting asyncio REPL...
```
Use `aioctl`, `aioservice ` or install `tools/aiostats.py` for real time debugging

```
>>> import aiostats
import aiostats
>>>  await aiostats.display("*.service")
 await aiostats.display("*.service")
● watcher.service: status: running since 2023-06-04 13:07:05; 00:08:24 ago
┗━► 2023-06-04 13:14:45 [darwin@unix] [INFO] [watcher.service] Restarting Task hello.service

● world.service: status: scheduled - done @ 2023-06-04 13:15:02; 26 s ago --> result:
    ┗━► schedule: last @ 2023-06-04 13:14:57 --> next in 58 s @ 2023-06-04 13:16:27
┗━► 2023-06-04 13:15:02 [darwin@unix] [INFO] [world.service] done: LED 2 toggled!

● hello.service: status: running since 2023-06-04 13:14:45; 44 s ago
┗━► 2023-06-04 13:15:25 [darwin@unix] [INFO] [hello.service] LED 1 toggled!

● stats.service: status: running since 2023-06-04 13:07:05; 00:08:24 ago
┗━► 2023-06-04 13:15:02 [darwin@unix] [INFO] [stats.service] HTTP/1.1 200 OK

```

Then on another terminal use curl to get info about running services (provided
by `stats.service`) 

```
$ curl http://localhost:8888/ | python -m json.tool
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100   975  100   975    0     0   7442      0 --:--:-- --:--:-- --:--:--  7442
{
    "world.service": {
        "status": "scheduled - done",
        "done_at": 1685881627.792578,
        "result": null,
        "service": true,
        "stats": null,
        "since": 1685881622.790579
    },
    "stats.service": {
        "status": "running",
        "done_at": null,
        "result": null,
        "service": true,
        "stats": {
            "ctasks": 1,
            "requests": 6,
            "firmware": "3.4.0; MicroPython v1.20.0-162-g08b6c8808-dirty on 2023-06-04",
            "machine": "darwin [GCC 4.2.1] version",
            "fsfree": 12639898959872,
            "mfree": 1998592,
            "fsused": 51535608283136,
            "fstotal": 64175507243008,
            "tasks": 7,
            "platform": "darwin",
            "services": 4,
            "mtotal": 2072832,
            "mused": 74240
        },
        "since": 1685880425.190416
    },
    "hostname": "unix",
    "watcher.service": {
        "status": "running",
        "done_at": null,
        "result": null,
        "service": true,
        "stats": {
            "errors": 15,
            "report": {
                "hello.service": [
                    "ZeroDivisionError",
                    "ValueError"
                ]
            }
        },
        "since": 1685880425.189758
    },
    "hello.service": {
        "status": "running",
        "done_at": null,
        "result": null,
        "service": true,
        "stats": null,
        "since": 1685881575.309743
    }
}

```
