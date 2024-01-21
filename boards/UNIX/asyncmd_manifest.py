import sys
import os

sys.path.append(os.path.dirname("__file__"))


# Services
include("../../mod/asyncmd.py")
include("../../mod/network.py")
include("../../mod/sense.py")
include("../../mod/powermg.py")
include("../../mod/test.py")

# Config
module("frz_services.py", opt=3)
