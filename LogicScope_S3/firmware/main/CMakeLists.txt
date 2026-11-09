idf_component_register(SRCS "main.c" "acquisition.c" "protocol.c"
    INCLUDE_DIRS "."
    REQUIRES esp_driver_gpio esp_driver_ledc esp_driver_usb_serial_jtag
             esp_hw_support esp_timer esp_mm)
