set(SDKCONFIG_DEFAULTS
    ${CMAKE_CURRENT_LIST_DIR}/sdkconfig_ssl.base
    ${CMAKE_CURRENT_LIST_DIR}/sdkconfig.ble_off
	${CMAKE_CURRENT_LIST_DIR}/sdkconfig.ota
	${CMAKE_CURRENT_LIST_DIR}/sdkconfig.board

)

if(NOT MICROPY_FROZEN_MANIFEST)
	set(MICROPY_FROZEN_MANIFEST ${CMAKE_CURRENT_LIST_DIR}/manifest.py)
endif()
