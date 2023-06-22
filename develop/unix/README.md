
Install `aiorepl`, `logging` and
`time` using `micropython -m mip install` see [mip](https://docs.micropython.org/en/latest/reference/packages.html?#using-mip-on-the-unix-port)

Then in unix micropython run `asyncmd_aiorepl.py`

```
 $ micropython -i asyncmd_aiorepl.py
MicroPython v1.20.0-162-g08b6c8808-dirty on 2023-06-04; darwin [GCC 4.2.1] version
Use Ctrl-D to exit, Ctrl-E for paste mode

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
--> import aiostats
import aiostats
--> await aiostats.display("*.service")
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


Or another option to see logging output directly instead of a repl
```
$ micropython -i asyncmd_logging.py

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


 Version: MicroPython v1.20.0-250-g76b17f451-dirty on 2023-06-22
 Machine: darwin [GCC 4.2.1] version

starting tasks...
>>>
[ OK ] Service: aiomqtt_sensor_bme280.service from ./aioservices/services/aiomqtt_sensor_bme280_service.py loaded
[ OK ] Service: mip.service from ./aioservices/services/mip_service.py loaded
[ OK ] Service: world.service from ./aioservices/services/world_service.py loaded
[ OK ] Service: watcher.service from ./aioservices/services/watcher_service.py loaded
[ OK ] Service: stats.service from ./aioservices/services/stats_service.py loaded
[ OK ] Service: unittest.service from ./aioservices/services/unittest_service.py loaded
[ OK ] Service: aiomqtt.service from ./aioservices/services/aiomqtt_service.py loaded
[ OK ] Service: hello.service from ./aioservices/services/hello_service.py loaded
>>>
2023-06-22 20:13:31 [darwin@macos] [INFO] [aiomqtt.service] MQTT client connected
2023-06-22 20:13:31 [darwin@macos] [INFO] [aiomqtt.service] MQTT Client Services and Tasks enabled!
2023-06-22 20:13:31 [darwin@macos] [INFO] [aiomqtt.service] MQTT ping task enabled
2023-06-22 20:13:31 [darwin@macos] [INFO] [aiomqtt.service] MQTT clean task enabled
2023-06-22 20:13:31 [darwin@macos] [INFO] [aiomqtt.service] MQTT stats task enabled
2023-06-22 20:13:31 [darwin@macos] [INFO] [aiomqtt.service] MQTT checking OTA update..
2023-06-22 20:13:31 [darwin@macos] [INFO] [aiomqtt.service] No OTA service found
2023-06-22 20:13:31 [darwin@macos] [INFO] [aiomqtt.service] @ [STATUS]: *.service
2023-06-22 20:13:32 [darwin@macos] [INFO] [aiomqtt_sensor_bme280.service] MQTT client connected
2023-06-22 20:13:32 [darwin@macos] [INFO] [aiomqtt_sensor_bme280.service] MQTT Client Discovery done!
2023-06-22 20:13:32 [darwin@macos] [INFO] [aiomqtt_sensor_bme280.service] MQTT publish task enabled
2023-06-22 20:13:32 [darwin@macos] [INFO] [aiomqtt_sensor_bme280.service.sense] 26.24506863641332 C 90037.72151670812 Pa 68.13135766072817 %
2023-06-22 20:13:32 [darwin@macos] [INFO] [aiomqtt.service] MQTT waiting...
2023-06-22 20:13:34 [darwin@macos] [INFO] [aiomqtt.service] @ [device/macos/logger]: log
2023-06-22 20:13:35 [darwin@macos] [INFO] [aiomqtt.service] MQTT waiting...
test_sum (test_mymodule_unittest.TestSum) ... ok
test_sum_tuple (test_mymodule_unittest.TestSum) ... ok
----------------------------------------------------------------------
Ran 2 tests

OK
test_sum (test_sum_unittest.TestSum) ... ok
test_sum_tuple (test_sum_unittest.TestSum) ... ok
----------------------------------------------------------------------
Ran 2 tests

OK
test_sum (test_mymodule_local.TestSum) ... ok
test_sum_tuple (test_mymodule_local.TestSum) ... ok
test_diff_tuple (test_mymodule_local.TestSum) ... ok
----------------------------------------------------------------------
Ran 3 tests

OK
test_sum (test_mymodule.TestSum) ... ok
test_sum_tuple (test_mymodule.TestSum) ... ok
test_diff_tuple (test_mymodule.TestSum) ... ok
----------------------------------------------------------------------
Ran 3 tests

OK
2023-06-22 20:13:35 [darwin@macos] [INFO] [unittest.service] Checking tests...
2023-06-22 20:13:35 [darwin@macos] [INFO] [unittest.service] Ran 4 test files --> Total 10 tests
2023-06-22 20:13:35 [darwin@macos] [INFO] [unittest.service] Tests OK [✔]
2023-06-22 20:13:35 [darwin@macos] [INFO] [unittest.service] tests/test_mymodule_unittest.py: OK [✔]
2023-06-22 20:13:35 [darwin@macos] [INFO] [unittest.service] tests/test_sum_unittest.py: OK [✔]
2023-06-22 20:13:35 [darwin@macos] [INFO] [unittest.service] tests/mymodule/test_mymodule_local.py: OK [✔]
2023-06-22 20:13:35 [darwin@macos] [INFO] [unittest.service] /Users/carlosgilgonzalez/.micropython/lib/tests/mymodule/test_mymodule.py: OK [✔]
2023-06-22 20:13:36 [darwin@macos] [INFO] [unittest.service] saving report..
2023-06-22 20:13:36 [darwin@macos] [INFO] [hello.service] LED 3 toggled!
2023-06-22 20:13:36 [darwin@macos] [INFO] [aiomqtt.service] aiomqtt.service.do_action.ota_check cleaned
2023-06-22 20:13:36 [darwin@macos] [INFO] [aiomqtt.service] aiomqtt.service.do_action.logger cleaned
2023-06-22 20:13:37 [darwin@macos] [INFO] [aiomqtt_sensor_bme280.service.sense] 25.2344944142894 C 90050.45233167302 Pa 66.93157568302628 %
2023-06-22 20:13:37 [darwin@macos] [INFO] [aiomqtt.service] MQTT waiting...
2023-06-22 20:13:41 [darwin@macos] [INFO] [watcher.service] WDT task enabled
2023-06-22 20:13:41 [darwin@macos] [INFO] [hello.service] LED 4 toggled!
2023-06-22 20:13:41 [darwin@macos] [INFO] [aiomqtt.service] @ [STATUS]: *.service
2023-06-22 20:13:42 [darwin@macos] [INFO] [aiomqtt_sensor_bme280.service.sense] 25.54855599280143 C 90060.85354494523 Pa 69.5005128618825 %
2023-06-22 20:13:42 [darwin@macos] [INFO] [aiomqtt.service] MQTT waiting...
2023-06-22 20:13:44 [darwin@macos] [INFO] [aiomqtt.service] @ [device/macos/logger]: log
2023-06-22 20:13:45 [darwin@macos] [INFO] [aiomqtt.service] MQTT waiting...
2023-06-22 20:13:46 [darwin@macos] [INFO] [hello.service] LED 3 toggled!
2023-06-22 20:13:46 [darwin@macos] [INFO] [aiomqtt.service] aiomqtt.service.do_action.logger cleaned
2023-06-22 20:13:47 [darwin@macos] [INFO] [aiomqtt_sensor_bme280.service.sense] 26.01973728293817 C 90098.06971534145 Pa 68.08584872438773 %
2023-06-22 20:13:47 [darwin@macos] [INFO] [aiomqtt.service] MQTT waiting...

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

Or use `asyncmd` CLI to get a formatted output with 
`$ asyncmd status -d localhost`
```

● aiomqtt.service - Async MQTT Controller client v1.0
    Loaded: ./aioservices/services/aiomqtt_service.py
    Active: (active) running since 2023-06-22 20:13:31; 00:07:32 ago
    Type: runtime.service
    Docs: https://github.com/Carglglz/asyncmd/blob/main/README.md
    Stats:  firmware=3.4.0; MicroPython v1.20.0-250-g76b17f451-dirty on 2023-06-22, fsused=50995043237888, mtotal=2072832, npub=137, ctasks=5, services=8, nrecv=45, fstotal=64175507243008, mfree=1812256, platform=darwin, tasks=14, requests=45, mused=260576, machine=darwin [GCC 4.2.1] version, fsfree=13180464005120
    CTasks: ['aiomqtt.service.stats', 'aiomqtt.service.clean', 'aiomqtt.service.ping']
    Task:
    ┗━► args: ['macos']
    ┗━► kwargs: { 'fwfile': 'None',
                  'ssl': 'True' }
                  'port': '8883' }
                  'topics': '[]' }
                  'services': '*.service' }
                  'hostname': 'amd.local' }
                  'restart': "['aiomqtt.service']" }
                  'on_stop': '<bound_method 7fd31fd15240 Service: aiomqtt.service from ./aioservices/services/aiomqtt_service.py.<function on_stop at 0x7fd31fd14740>>' }
                  'ota_check': 'True' }
                  'on_error': '<bound_method 7fd31fd15260 Service: aiomqtt.service from ./aioservices/services/aiomqtt_service.py.<function on_error at 0x7fd31fd14760>>' }
                  'server': 'amd.local' }
                  'keepalive': '300' }
                  'stats': 'True' }
                  'ssl_params': "{'ca': 'ca.crt'}" }
                  'debug': 'True' }
2023-06-22 20:21:03 [darwin@macos] [INFO] [aiomqtt.service] MQTT waiting...
<-------------------------------------------------------------------------------->
● aiomqtt_sensor_bme280.service - Async MQTT BME280 client v1.0
    Loaded: ./aioservices/services/aiomqtt_sensor_bme280_service.py
    Active: (active) running since 2023-06-22 20:13:31; 00:07:33 ago
    Type: runtime.service
    Docs: https://github.com/Carglglz/asyncmd/blob/main/README.md
    Stats:  temp=25.4157775202111, npub=94, press=90027.19031525549, nrecv=0, hum=67.6254328375023
    CTasks: ['aiomqtt_sensor_bme280.service.sense']
    Task:
    ┗━► args: ['macos']
    ┗━► kwargs: { 'ssl': 'False',
                  'i2c': '(22, 21)',
                  'port': '1883',
                  'topics': "['device/macos/state', 'device/all/state']",
                  'hostname': 'amd.local',
                  'restart': "['aiomqtt_sensor_bme280.service']",
                  'debug': 'False',
                  'keepalive': '300',
                  'on_error': '<bound_method 7fd31fd12f60 Service: aiomqtt_sensor_bme280.service from ./aioservices/services/aiomqtt_sensor_bme280_service.py.<function on_error at 0x7fd31fd12300>>',
                  'server': '0.0.0.0',
                  'on_stop': '<bound_method 7fd31fd12f40 Service: aiomqtt_sensor_bme280.service from ./aioservices/services/aiomqtt_sensor_bme280_service.py.<function on_stop at 0x7fd31fd12240>>',
                  'ssl_params': '{}',
                  'main': 'aiomqtt.service' }
2023-06-22 20:21:02 [darwin@macos] [INFO] [aiomqtt_sensor_bme280.service.sense] 25.4157775202111 C 90027.19031525549 Pa 67.6254328375023 %
<-------------------------------------------------------------------------------->
● hello.service - Hello example runner v1.0
    Loaded: ./aioservices/services/hello_service.py
    Active: (active) running since 2023-06-22 20:20:41; 25 s ago
    Type: runtime.service
    Docs: https://github.com/Carglglz/asyncmd/blob/main/README.md
    Task:
    ┗━► args: [2, 5]
    ┗━► kwargs: { 'on_stop': '<bound_method 7fd31fd17140 Service: hello.service from ./aioservices/services/hello_service.py.<function on_stop at 0x7fd31fd16320>>',
                  'on_error': '<bound_method 7fd31fd17160 Service: hello.service from ./aioservices/services/hello_service.py.<function on_error at 0x7fd31fd162e0>>' }
2023-06-22 20:21:01 [darwin@macos] [INFO] [hello.service] LED 1 toggled!
<-------------------------------------------------------------------------------->
● mip.service - MIP updater Service v1.0
    Loaded: ./aioservices/services/mip_service.py
    Active: (active) running since 2023-06-22 20:21:03; 3 s ago
    Type: schedule.service
    Docs: https://github.com/Carglglz/asyncmd/blob/main/README.md
    Stats:  status=up to date, update_n=0, packages_n=1, packages={'mymodule': {'service': False, 'url': 'http://127.0.0.1:8000/package_local_mymodule.json', 'version': '2.5'}}, update={}
    Task:
    ┗━► schedule: last @ 2023-06-22 20:21:03 --> next in 56 s @ 2023-06-22 20:22:03
    ┗━► schedule opts: last_dt=[2023, 6, 22, 20, 21, 3, 3, 173, 1], t0=1687461211.349594, _start_in=30, start_in=-1, repeat=60, last=1687461663.837656
    ┗━► args: []
    ┗━► kwargs: { 'config': 'packages.config',
                  'packages': '{}',
                  'restart': 'False',
                  'autoupdate': 'True' }
<-------------------------------------------------------------------------------->
● stats.service - Stats JSON API v1.0
    Loaded: ./aioservices/services/stats_service.py
    Active: (active) running since 2023-06-22 20:13:31; 00:07:36 ago
    Type: runtime.service
    Docs: https://github.com/Carglglz/asyncmd/blob/main/README.md
    Stats:  ctasks=5, requests=1, firmware=3.4.0; MicroPython v1.20.0-250-g76b17f451-dirty on 2023-06-22, machine=darwin [GCC 4.2.1] version, fsfree=13180464005120, mfree=1815808, fsused=50995043237888, fstotal=64175507243008, tasks=14, platform=darwin, services=8, mtotal=2072832, mused=257024
    Task:
    ┗━► args: []
    ┗━► kwargs: { 'ssl': 'False',
                  'ssl_params': '{}',
                  'on_error': '<bound_method 7fd31fd1d440 Service: stats.service from ./aioservices/services/stats_service.py.<function on_error at 0x7fd31fd1c0c0>>',
                  'debug': 'True',
                  'on_stop': '<bound_method 7fd31fd1d420 Service: stats.service from ./aioservices/services/stats_service.py.<function on_stop at 0x7fd31fd1c0a0>>',
                  'host': '0.0.0.0',
                  'port': '8888' }
2023-06-22 20:21:04 [darwin@macos] [INFO] [stats.service] GET /debug HTTP/1.1
<-------------------------------------------------------------------------------->
● unittest.service - Unittest Service v1.0
    Loaded: ./aioservices/services/unittest_service.py
    Active: status: scheduled - done @ 2023-06-22 20:20:37; 29 s ago --> result: [PASS]
    Type: schedule.service
    Docs: https://github.com/Carglglz/asyncmd/blob/main/README.md
    Stats:  run=10, test={'tests/test_mymodule_unittest.py': {'run': 2, 'status': 'OK'}, 'tests/test_sum_unittest.py': {'run': 2, 'status': 'OK'}, 'tests/mymodule/test_mymodule_local.py': {'run': 3, 'status': 'OK'}, '/Users/carlosgilgonzalez/.micropython/lib/tests/mymodule/test_mymodule.py': {'run': 3, 'status': 'OK'}}, errors=0, failures=0
    Task:
    ┗━► runtime: 2 s
    ┗━► schedule: last @ 2023-06-22 20:20:35 --> next in the past by 2 s  @ 2023-06-22 20:21:05
    ┗━► schedule opts: last_dt=[2023, 6, 22, 20, 20, 35, 3, 173, 1], t0=1687461211.349594, _start_in=2, start_in=-1, repeat=30, last=1687461635.75986
    ┗━► args: []
    ┗━► kwargs: { 'debug': 'False',
                  'save_report': 'True',
                  'testdir': 'tests',
                  'root': '',
                  'modules': "['/Users/carlosgilgonzalez/.micropython/lib']" }
<-------------------------------------------------------------------------------->
● watcher.service - Watcher Service v1.0 - Restarts services on failed state
    Loaded: ./aioservices/services/watcher_service.py
    Active: (active) running since 2023-06-22 20:13:31; 00:07:37 ago
    Type: runtime.service
    Docs: https://github.com/Carglglz/asyncmd/blob/main/README.md
    Stats:  errors=7, report={'hello.service': ['ValueError', 'ZeroDivisionError']}
    CTasks: ['watcher.service.wdt']
    Task:
    ┗━► args: [30]
    ┗━► kwargs: { 'wdfeed': '30000',
                  'max_errors': '0',
                  'on_error': '<bound_method 7fd31fd27280 Service: watcher.service from ./aioservices/services/watcher_service.py.<function on_error at 0x7fd31fd26400>>',
                  'on_stop': '<bound_method 7fd31fd270a0 Service: watcher.service from ./aioservices/services/watcher_service.py.<function on_stop at 0x7fd31fd26160>>',
                  'watchdog': 'True' }
<-------------------------------------------------------------------------------->
● world.service - World example runner v1.0
    Loaded: ./aioservices/services/world_service.py
    Active: status: scheduled - done @ 2023-06-22 20:19:58; 00:01:10 ago --> result: None
    Type: schedule.service
    Docs: https://github.com/Carglglz/asyncmd/blob/main/README.md
    Task:
    ┗━► runtime: 5 s
    ┗━► schedule: last @ 2023-06-22 20:19:53 --> next in 14 s @ 2023-06-22 20:21:23
    ┗━► schedule opts: last_dt=[2023, 6, 22, 20, 19, 53, 3, 173, 1], t0=1687461211.349594, _start_in=20, start_in=-1, repeat=90, last=1687461593.450331
    ┗━► args: [2, 5]
    ┗━► kwargs: {}
<-------------------------------------------------------------------------------->

```
