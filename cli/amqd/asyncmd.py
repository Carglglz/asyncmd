#!/usr/bin/env python3

import sys
import os
import json
import time
import logging
import argparse
import argcomplete
from argcomplete.completers import ChoicesCompleter
import asyncio
import asyncio_mqtt as aiomqtt
import ssl
from asyncmd_ota import OTAServer

_CONFIG_DIR = os.path.join(os.environ["HOME"], ".asyncmd")
_CONFIG_FILE = os.path.join(_CONFIG_DIR, "asyncmd.config")
_DEFAULT_ARGS = {
    "t": "device/{}/cmd",
    "m": "on",
    "d": "all",
    "ht": "localhost",
    "p": 1883,
    "cafile": "",
    "cert": "",
    "key": "",
    "f": [],
    "ff": "micropython.bin",
    "dslev": "info",
    "dflev": "error",
    "ota_cafile": "",
    "ota_cert": "",
    "ota_key": "",
}


helparg = """Mode:
- pub : publish message
- config: configure default settings
"""

usag = """%(prog)s [Mode] [options]
"""
# UPY MODE KEYWORDS AND COMMANDS
keywords_mode = ["pub", "sub", "config", "ota"]

parser = argparse.ArgumentParser(
    prog="asyncmd",
    description="asyncmd CLI tool",
    formatter_class=argparse.RawTextHelpFormatter,
    usage=usag,
)
parser.version = "0.0.1"
parser.add_argument("cmd", metavar="Mode", help=helparg).completer = ChoicesCompleter(
    keywords_mode
)
parser.add_argument("-v", action="version")
parser.add_argument(
    "-ht",
    help="host",
    required=False,
    default=_DEFAULT_ARGS["ht"],
)
parser.add_argument(
    "-p", help="port", required=False, default=_DEFAULT_ARGS["p"], type=int
)
parser.add_argument(
    "-t",
    help="topic",
    required=False,
    default=_DEFAULT_ARGS["t"],
)

parser.add_argument(
    "-m",
    help="message",
    required=False,
    default=_DEFAULT_ARGS["m"],
)
parser.add_argument(
    "-d",
    help="device",
    required=False,
    default=_DEFAULT_ARGS["d"],
)
parser.add_argument(
    "-ff",
    help="firmware file",
    required=False,
    default=_DEFAULT_ARGS["ff"],
)
parser.add_argument(
    "--cafile",
    help="CA cert",
    required=False,
    default="",
)

parser.add_argument(
    "--key",
    help="client key",
    required=False,
    default="",
)
parser.add_argument(
    "--cert",
    help="client cert",
    required=False,
    default="",
)

parser.add_argument(
    "--ota-cafile",
    help="OTA server CA cert",
    required=False,
    default="",
)

parser.add_argument(
    "--ota-key",
    help="OTA server key",
    required=False,
    default="",
)
parser.add_argument(
    "--ota-cert",
    help="OTA server cert",
    required=False,
    default="",
)
parser.add_argument(
    "-f",
    help="Force default configuration of any argument",
    required=False,
    nargs="?",
    const=["m", "t", "d", "ff"],
    default=[],
)
parser.add_argument(
    "-dflev",
    help="debug file mode level, options [debug, info, warning, error, critical]",
    default="error",
)
parser.add_argument(
    "-dslev",
    help="debug sys out mode level, options [debug, info, warning, error, critical]",
    default="info",
)

argcomplete.autocomplete(parser)
args = parser.parse_args()
args.t = args.t.format(args.d)
argconf = dict(args.__dict__)
argconf.pop("cmd")
argconf.pop("f")

# LOAD CONFIG
if not os.path.exists(_CONFIG_DIR):
    os.mkdir(_CONFIG_DIR)
else:
    # print(argconf)
    # print(args.__dict__)
    # print(_DEFAULT_ARGS)
    if os.path.exists(_CONFIG_FILE):  # LOAD_CONFIG
        with open(_CONFIG_FILE, "r") as configf:
            load_conf = json.loads(configf.read())
            for key in load_conf.keys():
                if (
                    argconf[key] == _DEFAULT_ARGS[key]
                ):  # IF args are default fallback to configuration
                    if key not in args.f:
                        args.__dict__[key] = load_conf[key]
                        argconf[key] = load_conf[key]


# LOGGING
log_levels = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL,
}
logPath = _CONFIG_DIR
logfileName = "asyncmd"
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(log_levels[args.dslev])
logging.basicConfig(
    level=log_levels["debug"],
    format=("%(asctime)s [%(name)s] [%(levelname)s] %(message)s"),
    handlers=[handler],
)
log = logging.getLogger("asyncmd")

# Filehandler for error
fh_err = logging.FileHandler(f"{logPath}/{logfileName}.log")
fh_err.setLevel(log_levels[args.dflev])
# Formatter for errors
fmt_err = logging.Formatter("%(asctime)s [%(name)s] [%(levelname)s] %(message)s")
fh_err.setFormatter(fmt_err)
log.addHandler(fh_err)


async def _pub(args, log):
    if args.cafile:
        tls_params = aiomqtt.TLSParameters(
            ca_certs=args.cafile,
            certfile=args.cert,
            keyfile=args.key,
            cert_reqs=ssl.CERT_REQUIRED,
            tls_version=ssl.PROTOCOL_TLS,
            ciphers=None,
        )
        async with aiomqtt.Client(
            hostname=args.ht, port=args.p, logger=log, tls_params=tls_params
        ) as client:
            await client.publish(args.t, payload=args.m)
    else:
        async with aiomqtt.Client(
            hostname=args.ht,
            port=args.p,
            logger=log,
        ) as client:
            await client.publish(args.t, payload=args.m)


async def _sub(args, log):
    if args.cafile:
        tls_params = aiomqtt.TLSParameters(
            ca_certs=args.cafile,
            certfile=args.cert,
            keyfile=args.key,
            cert_reqs=ssl.CERT_REQUIRED,
            tls_version=ssl.PROTOCOL_TLS,
            ciphers=None,
        )
        async with aiomqtt.Client(
            hostname=args.ht, port=args.p, logger=log, tls_params=tls_params
        ) as client:
            async with client.messages() as messages:
                await client.subscribe(args.t)
                async for message in messages:
                    log.info(message.payload)
    else:
        async with aiomqtt.Client(
            hostname=args.ht,
            port=args.p,
            logger=log,
        ) as client:
            async with client.messages() as messages:
                await client.subscribe(args.t)
                async for message in messages:
                    log.info(message.payload)


async def _ota(args, log):
    if args.cafile:
        tls_params = aiomqtt.TLSParameters(
            ca_certs=args.cafile,
            certfile=args.cert,
            keyfile=args.key,
            cert_reqs=ssl.CERT_REQUIRED,
            tls_version=ssl.PROTOCOL_TLS,
            ciphers=None,
        )
        async with aiomqtt.Client(
            hostname=args.ht, port=args.p, logger=log, tls_params=tls_params
        ) as client:
            ota_server = OTAServer(
                client,
                8014,
                args.t,
                args.ff,
                log,
                tls_params={
                    "cafile": args.ota_cafile,
                    "cert": args.ota_cert,
                    "key": args.ota_key,
                    "pph": "espkeyhack",
                },
            )
            await ota_server.start_ota()
    else:
        async with aiomqtt.Client(
            hostname=args.ht,
            port=args.p,
            logger=log,
        ) as client:
            ota_server = OTAServer(
                client,
                8014,
                args.t,
                args.ff,
                log,
            )
            await ota_server.start_ota()


def main(log):
    # print(argconf)
    # print(args.__dict__)
    # print(_DEFAULT_ARGS)
    if args.cmd == "config":
        with open(_CONFIG_FILE, "w") as configf:
            configf.write(json.dumps(argconf))

    elif args.cmd == "pub":
        log.info(f"pub @ [{args.t}] {args.m}")
        asyncio.run(_pub(args, log))

    elif args.cmd == "sub":
        log.info(f"sub @ [{args.t}]")
        asyncio.run(_sub(args, log))

    elif args.cmd == "ota":
        args.t = args.t.replace("cmd", "ota")
        log.info(f"ota @ [{args.t}]")
        asyncio.run(_ota(args, log))


if __name__ == "__main__":
    main(log)
