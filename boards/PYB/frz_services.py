import sys

services = ['unittest_core_service', 'watcher_service']

config = {'unittest_core_service': {'enabled': False}, 'watcher_service': {'enabled': True}}

envfile = f'''HOSTNAME={sys.platform}
LED_PIN=2
AIOREPL=True
'''

