import os
import sys
import json


# Generate default services.config
if "services.config" not in os.listdir():
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

    config = {
        service.replace("_service", ""): {"enabled": False} for service in services
    }

    config["watcher"]["enabled"] = True

else:
    with open("services.config", "r") as sc:
        config = json.load(sc)
        services = [f"{name}_service" for name in config.keys()]


print("[ASYNCMD] Default services:\n")
for service in services:
    print(service)

print("[ASYNCMD] Default config:\n")
print(json.dumps(config, indent=4))

if ".env" not in os.listdir():
    lit = False
    envfile = """HOSTNAME={sys.platform}
LED_PIN=2
AIOREPL=True
"""
else:
    lit = True
    with open(".env", "r") as env:
        envfile = env.read()


print("[ASYNCMD] Default .env:\n")
print(envfile)

with open("frz_services.py", "w") as frz_services:
    frz_services.write("import sys\n\n")
    frz_services.write(f"services = {services}\n\n")
    frz_services.write(f"config = {config}\n\n")
    if not lit:
        frz_services.write(f"envfile = f'''{envfile}'''\n\n")
    else:
        frz_services.write(f"envfile = '''{envfile}'''\n\n")


# Generate default frozen services from services.config

# Generate default .env file from board/<BOARD_NAME>/.env
