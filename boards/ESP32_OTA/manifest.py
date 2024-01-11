freeze("$(PORT_DIR)/modules")
include("$(MPY_DIR)/extmod/asyncio")
require("neopixel")
# Useful networking-related packages.
require("bundle-networking")

# asyncmd
include("asyncmd_manifest.py")
