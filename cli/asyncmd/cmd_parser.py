import yaml
import argparse  # noqa
import shlex
from . import __version__ as version

rawfmt = argparse.RawTextHelpFormatter


def get_args(arg):
    if arg.isdecimal():
        if "." in arg:
            return float(arg)
        else:
            return int(arg)
    return arg


START = dict(
    help="start async tasks or services",
    desc="",
    subcmd=dict(
        help="task or service (accepts * wildcards) ",
        default="wpa_supplicant.service",
        metavar="task/service",
        nargs="*",
    ),
    options={},
)

STOP = dict(
    help="stop async tasks or services",
    desc="",
    subcmd=dict(
        help="task or service (accepts * wildcards) ",
        default="wpa_supplicant.service",
        metavar="task/service",
        nargs="*",
    ),
    options={},
)


ENABLE = dict(
    help="enable one or more services",
    desc="",
    subcmd=dict(
        help="enable one or more services",
        default="wpa_supplicant.service",
        metavar="service",
        nargs="*",
    ),
    options={},
)

DISABLE = dict(
    help="disable one or more services",
    desc="",
    subcmd=dict(
        help="disable one or more services",
        default="wpa_supplicant.service",
        metavar="service",
        nargs="*",
    ),
    options={},
)
CONFIG = dict(
    help="config args and kwargs of a service",
    desc="",
    subcmd=dict(
        help="service or service.config file",
        default="service.config",
        metavar="service",
    ),
    options={
        "--args": dict(
            help="args for service",
            required=False,
            nargs="*",
            type=get_args,
        ),
        "--kwargs": dict(
            help="kwargs for seervice", required=False, type=yaml.safe_load
        ),
    },
)
SHELL_CMD_DICT_PARSER = {
    "start": START,
    "stop": STOP,
    "enable": ENABLE,
    "disable": DISABLE,
    "config": CONFIG,
}

SHELL_CMD_SUBPARSERS = {}


usag = """command [options]\n
"""
descmds = "asyncmd commands"
_kb_info_cmd = "Do CTRL-k to see keybindings info"
_help_subcmds = "[command] -h or ?[command] to see further help of any command"

shparser = argparse.ArgumentParser(
    prog="asyncmd",
    description=("asyncmd develop tool" "\n\n" + _kb_info_cmd + "\n" + _help_subcmds),
    formatter_class=rawfmt,
    usage=usag,
    prefix_chars="-",
)
subshparser_cmd = shparser.add_subparsers(
    title="commands", prog="", dest="m", description="Available commands"
)
shparser.version = f"asyncmd : {version}"
shparser.add_argument("-v", action="version")

for command, subcmd in SHELL_CMD_DICT_PARSER.items():
    if "desc" in subcmd.keys():
        _desc = f"{subcmd['help']}\n\n{subcmd['desc']}"
    else:
        _desc = subcmd["help"]
    _subparser = subshparser_cmd.add_parser(
        command, help=subcmd["help"], description=_desc, formatter_class=rawfmt
    )
    for pos_arg in subcmd.keys():
        if pos_arg not in ["subcmd", "help", "desc", "options", "alt_ops"]:
            _subparser.add_argument(pos_arg, **subcmd[pos_arg])
    if subcmd["subcmd"]:
        _subparser.add_argument("subcmd", **subcmd["subcmd"])
    for option, op_kargs in subcmd["options"].items():
        _subparser.add_argument(option, **op_kargs)

    SHELL_CMD_SUBPARSERS[command] = _subparser


class CmdParser:
    def __init__(self, parser=shparser):
        self.parser = parser

    def parseap(self, command_args):
        try:
            return self.parser.parse_known_args(command_args)
        except SystemExit:  # argparse throws these because it assumes you only want
            # to do the command line
            return None  # should be a default one

    def cmd(self, cmdline):
        try:
            # catch concatenated commands with &&
            if " && " in cmdline:
                for _cmdline in cmdline.split(" && "):
                    self.sh_cmd(_cmdline)
            else:
                self.sh_cmd(cmdline)
        except KeyboardInterrupt:
            return

    def sh_cmd(self, cmd_inp):
        # debug command:
        if cmd_inp.startswith("!"):
            args = self.parseap(shlex.split(cmd_inp[1:]))
            return ("DEBUG CMD", str(args), args)

        # PARSE ARGS
        command_line = shlex.split(cmd_inp)

        all_args = self.parseap(command_line)

        if not all_args:
            return None, None, None
        else:
            args, unknown_args = all_args
        if hasattr(args, "subcmd"):
            command, rest_args = args.m, args.subcmd
            if rest_args is None:
                rest_args = []
        else:
            command, rest_args = args.m, []

        return (command, rest_args, args)  # noqa
