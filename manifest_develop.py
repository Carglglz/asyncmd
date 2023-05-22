module("aioctl.py", opt=3)
module("aioschedule.py", opt=3)
module("aiolog.py", opt=3)
module("aioclass.py", opt=3)
module("aioservice.py", opt=3)
module("aiostats.py", base_path="tools", opt=3)
module("async_mip.py", base_path="async_modules/async_mip", opt=3)
module("async_mqtt.py", base_path="async_modules/async_mqtt", opt=3)
module("async_urequests.py", base_path="async_modules/async_urequests", opt=3)
module("stats_service.py", base_path="aioservices/services")
module("mip_service.py", base_path="aioservices/services")
module("ota_service.py", base_path="aioservices/services")
module("devop_service.py", base_path="aioservices/services")
module("network_service.py", base_path="aioservices/services")
module("unittest_service.py", base_path="aioservices/services")
module("watcher_service.py", base_path="aioservices/services")
module("aiomqtt_service.py", base_path="aioservices/services")
module("wpa_supplicant_service.py", base_path="aioservices/services")
module("aiomqtt_sensor_bme280_service.py", base_path="example-aioservices/services")
module("filehandler.py", base_path="logging_handlers")
module("ursyslogger.py", base_path="tools")
module("rsysloghandler.py", base_path="logging_handlers")
module("mqtt_cmdlib.py", base_path="utils/aiomqtt_service")
require("aiorepl", opt=3)
require("logging")
require("time")
require("unittest")