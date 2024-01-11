import sys

services = ['aiomqtt_sensor_bme280_service', 'aiomqtt_sensor_ina219_solar_service', 'aiomqtt_service', 'mip_service', 'powermg_service', 'stats_service', 'unittest_core_service', 'watcher_service', 'ota_service', 'network_service', 'wpa_supplicant_service', 'ping_service']

config = {'aiomqtt_sensor_bme280_service': {'enabled': False}, 'aiomqtt_sensor_ina219_solar_service': {'enabled': False}, 'aiomqtt_service': {'enabled': False}, 'mip_service': {'enabled': False}, 'powermg_service': {'enabled': False}, 'stats_service': {'enabled': False}, 'unittest_core_service': {'enabled': False}, 'watcher_service': {'enabled': True}, 'ota_service': {'enabled': False}, 'network_service': {'enabled': False}, 'wpa_supplicant_service': {'enabled': False}, 'ping_service': {'enabled': False}}

envfile = f'''HOSTNAME={sys.platform}
LED_PIN=2
AIOREPL=True
'''

