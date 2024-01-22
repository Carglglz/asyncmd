freeze("$(PORT_DIR)/modules")
include("$(MPY_DIR)/extmod/asyncio")
require("neopixel")
require("aiorepl")

# Useful networking-related packages.
require("bundle-networking")

# asyncmd
include("asyncmd_manifest.py")
