import sys

services = [
    "unittest_core_service",
    "watcher_service",
]

config = {service: {"enabled": False} for service in services}

# Set default config for services

config["watcher_service"]["enabled"] = True


envfile = f"""HOSTNAME={sys.platform}
LED_PIN=2
AIOREPL=False
"""
