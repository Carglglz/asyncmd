import sys

services = [
    "aiomqtt_sensor_bme280_service",
    "aiomqtt_sensor_ina219_solar_service",
    "aiomqtt_service",
    "mip_service",
    "powermg_service",
    "stats_service",
    "unittest_core_service",
    "watcher_service",
    "ota_service",
    "network_service",
    "wpa_supplicant_service",
    "ping_service",
]

config = {service: {"enabled": False} for service in services}

# Set default config for services

config["watcher_service"]["enabled"] = True


envfile = f"""HOSTNAME={sys.platform}
LED_PIN=2
AIOREPL=True
"""
