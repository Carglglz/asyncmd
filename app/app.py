import uasyncio as asyncio
import aiorepl
import aioctl
import aioservice


async def _main(logger):
    # Boot core services
    await aioservice.boot(log=logger, debug_log=True)
    print("starting tasks...")
    aioctl.add(aiorepl.repl)
    print(">>> ")
    # Load runtime and schedule services
    aioservice.init(log=logger, debug_log=True)
    print(">>> ")
    _net = aioservice.service("network")
    _wpa = aioservice.service("wpa_supplicant")
    if _net and _wpa:
        _wpa.ssid = _net.ssid
    await asyncio.gather(*aioctl.tasks())


def run(logger):
    asyncio.run(_main(logger))
