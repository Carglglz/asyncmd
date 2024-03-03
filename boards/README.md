### Asyncmd Boards


Some examples of ports/boards builds with asyncmd app. 

To build from micropython repo do e.g. :

`$ make -C ports/esp32 BOARD_DIR=<path/to/asyncmd/boards/ESP32` 

The `asyncmd_manifest.py` can freeze a default `.env` and `services.config` files if present in the `BOARD_DIR` and will generate and freeze the default `frz_services.py` from that.
