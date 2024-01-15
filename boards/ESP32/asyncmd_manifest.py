import sys
import os

sys.path.append(os.path.dirname("__file__"))

import make_defconfig

# Services
include("../../mod/asyncmd.py")
include("../../mod/network.py")
include("../../mod/ble.py")
include("../../mod/sense.py")
include("../../mod/powermg.py")
include("../../mod/test.py")

# Config
module("frz_services.py", opt=3)

# Drivers
module("bme280_float.py", base_path="../../drivers/sensors/bme280", opt=3)
module("ina219.py", base_path="../../drivers/sensors/ina219", opt=3)
