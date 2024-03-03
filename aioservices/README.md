
### aioservices


- aioble.service --> main/basic *aioble* service.  

- aiomqtt.service --> main/basic *mqtt* service, requires `aiostats` (required for `asyncmd dtop`)

- mip.service --> automate mip updates. (packages info is stored in `packages.config`)

- network.service --> core service to connect to WiFi and optionally enable `WebREPL`, requires `wpa_supplicant.config`

- ota.service --> async firmware OTA service to be used with `asyncmd otasrv`, (requires `aiomqtt.service`)

- ping.service --> service to ping periodically a set of nodes. (requires `aioping.py`)

- stats.service --> a mini json web server that sends services stats. (requires `aiostats.py`)

- unittest.service --> run tests on tests/code changes.

- unittest_core.service --> core service to run tests at start.

- watcher.service --> service to restart tasks/services in failed state. It can enable/feed the hardware watchdog and heartbeat task. 

- wpa_supplicant.service --> schedule service to assert connectivity and reconnect in case of disconnection, requires `wpa_supplicant.config`.
