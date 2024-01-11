import sys
import os

sys.path.append(os.path.dirname("__file__"))

import make_defconfig

include("../../mod/asyncmd.py")
include("../../mod/network.py")
include("../../mod/ble.py")
include("../../mod/sense.py")
include("../../mod/powermg.py")
include("../../mod/test.py")
module("frz_services.py", opt=3)
