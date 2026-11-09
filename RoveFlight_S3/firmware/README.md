# ESP-IDF bring-up skeleton

Targets ESP-IDF 6.1 / ESP32-S3 GPIO APIs. Requires an installed ESP-IDF toolchain:

```sh
idf.py set-target esp32s3
idf.py menuconfig
idf.py build
```

Select 8-MB flash and the exact N8R2 Quad PSRAM configuration. This source has not been built with an ESP-IDF toolchain or run on fabricated hardware in this delivery. It holds the hardware interlock cleared, all four PWM pins low and the watchdog heartbeat stopped. Only the status LED blinks. It provides no arming command, sensor drivers, flight estimator, PID controller, radio stack or OTA implementation. See ../docs/Firmware_Architecture.md for the required modules and commissioning sequence. Remove JP1 and all propellers during programming and bring-up.
