import sys

services = ['aiomqtt_sensor_bme280_service', 'aiomqtt_sensor_ina219_solar_service', 'aiomqtt_service', 'mip_service', 'powermg_service', 'stats_service', 'unittest_core_service', 'watcher_service', 'network_service', 'wpa_supplicant_service', 'ping_service']

config = {'aiomqtt_sensor_bme280': {'enabled': False}, 'aiomqtt_sensor_ina219_solar': {'enabled': False}, 'aiomqtt': {'enabled': False}, 'mip': {'enabled': False}, 'powermg': {'enabled': False}, 'stats': {'enabled': False}, 'unittest_core': {'enabled': False}, 'watcher': {'enabled': True}, 'network': {'enabled': False}, 'wpa_supplicant': {'enabled': False}, 'ping': {'enabled': False}}

envfile = f'''HOSTNAME={sys.platform}
LED_PIN=2
AIOREPL=True
'''

