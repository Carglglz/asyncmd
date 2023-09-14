
## Asyncmd CLI

Intended to be a tool for managing, monitoring and debugging devices over MQTT, it expects devices using `aiomqtt.service` and `watcher.service` at least.

### Install

Install with (if cwd is `asyncmd/cli`)
```bash
pip install .
```
or 
```bash
pip install cli/
```
if in top level directory

### Usage

The `asyncmd` CLI tool has several commands:

* `pub`: publish a message to one or more topics.
* `sub`: subscribe to one or more topics.
* `ota`: perform an OTA firmware update.
* `otasrv`: start the asynchronous OTA server.
* `sha`: check the SHA256 hash of the device's current application firmware.
* `services`: list available aioservices.
* `dtop`: display the status of one or more devices aioservices with a htop-like UI.
* `devconfig`: get or set device configuration options.
* `config`: configure default settings for the `asyncmd` CLI.

There is also several optional arguments:

* `-h, --help`: show this help message and exit.
* `-v`: show program's version number and exit.
* `-c`: check config file.
* `--conf CONF`: config file to use, default: `~/.asyncmd/asyncmd.config`.
* `--dconf [DCONF ...]`: config options for devconfig, options: `[get, set, enable, disable]`.
* `--args [ARGS ...]`: arguments for devconfig.
* `--kwargs KWARGS`: kwargs for devconfig.
* `-sub SUB`: override subscription topic.
* `-ht HT`: host.
* `-p P`: port.
* `-t T`: topic.
* `-m M`: message.
* `-d D`: device.
* `-ff [FF ...]`: firmware file/s, default: `[micropython.bin]`.
* `--cafile CAFILE`: CA cert.
* `--key KEY`: client key.
* `--cert CERT`: client cert.
* `--ota-cafile OTA_CAFILE`: OTA server CA cert.
* `--ota-key OTA_KEY`: OTA server key.
* `--ota-key-pph OTA_KEY_PPH`: OTA server key passphrase.
* `--ota-cert OTA_CERT`: OTA server cert.
* `-f [F]`: Force default configuration of any argument.
* `-nl`: disable logging for devconfig cmd.
* `-dflev DFLEV`: debug file mode level, options `[debug, info, warning, error, critical]`.
* `-dslev DSLEV`: debug sys out mode level, options `[debug, info, warning, error, critical]`.

