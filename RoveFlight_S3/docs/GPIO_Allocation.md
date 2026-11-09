# GPIO allocation

Exact module: ESP32-S3-WROOM-1-N8R2. USB is GPIO19/20. ADC monitoring uses ADC1 GPIO1/2. GPIO0 is BOOT; GPIO3/45/46 are unused strapping pins. GPIO35/36/37 are unused, allowing a conservative allocation around memory variants. Module flash/PSRAM pins not exposed as general-purpose signals are never assigned. Do not substitute a module variant without repeating the memory and pin review.

| GPIO | Module pad | Net |
|---:|---:|---|
| 0 | 27 | BOOT |
| 1 | 39 | CURRENT_ADC |
| 2 | 38 | BAT_ADC |
| 4 | 4 | PWM_M1 |
| 5 | 5 | PWM_M2 |
| 6 | 6 | PWM_M3 |
| 7 | 7 | PWM_M4 |
| 8 | 12 | I2C_SDA |
| 9 | 17 | IMU_INT |
| 10 | 18 | IMU_CS |
| 11 | 19 | SPI_MOSI |
| 12 | 20 | SPI_SCK |
| 13 | 21 | SPI_MISO |
| 14 | 22 | BARO_CS |
| 15 | 8 | IR_RX |
| 16 | 9 | TOF_INT |
| 17 | 10 | TOF_XSHUT |
| 18 | 11 | I2C_SCL |
| 19 | 13 | USB_DM |
| 20 | 14 | USB_DP |
| 21 | 23 | STATUS_LED |
| 38 | 31 | ARM_CLK |
| 39 | 32 | WD_HEARTBEAT |
| 40 | 33 | KILL_OD |
| 41 | 34 | RC_RX |
| 42 | 35 | RC_TX |
| 43 | 37 | DEBUG_TX |
| 44 | 36 | DEBUG_RX |
| 47 | 24 | FLOW_CS |
| 48 | 25 | FLOW_INT |

GPIO38 receives a low-to-high arm pulse only after health checks; GPIO39 sends falling watchdog edges from the healthy control task. GPIO40 is configured OPEN DRAIN and LOW before any PWM setup, then released only for deliberate arming. GPIO4–7 PWM and their buffer inputs have external pulldowns. RC UART on GPIO41/42 is separate from debug UART GPIO43/44. The single external SPI expansion shares the IMU/barometer bus; bound its transaction latency.
