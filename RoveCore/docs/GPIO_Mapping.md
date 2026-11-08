# P-TIWARI GPIO allocation

ESP32-WROOM-32E-N8, no PSRAM. All ESP32 logic is 3.3 V. GPIO6–11 are used by module flash; GPIO20/24/28–31/37/38 are unavailable in this module. GPIO34/35/36/39 are input-only. ADC2 is unavailable for ordinary simultaneous Wi-Fi ADC use; onboard battery sensing uses ADC1 and external analog uses ADS1115.

| GPIO | Module pad | Net | Connection | Constraint |
|---:|---:|---|---|---|
| 0 | 25 | BOOT | Programming strap; button/J1 | Pullup; hold low only for download |
| 1 | 35 | U0_TX | USB bridge / J1 | Console/programming UART transmit |
| 2 | 24 | BUZZ_PWM | Piezo MOSFET / J21 | Boot strap; external gate pulldown; ADC2 not used |
| 3 | 34 | U0_RX | USB bridge / J1 | Console/programming UART receive |
| 4 | 26 | US_TRIG | 5V buffered ultrasonic trigger / J20 | General output; not a 5V-tolerant ESP input |
| 5 | 29 | SPI_CS | SPI J17 / J21 | Boot strap; pullup; peripheral must not force low during reset |
| 12 | 14 | STRAP12 | Dedicated 10k pulldown; reserved | Selects flash voltage; not general GPIO; JTAG conflicts |
| 13 | 16 | US_ECHO | Buffered echo / J20 | 3V3 output of echo buffer; do not externally drive shared header |
| 14 | 13 | M_B2 | Motor bridge B input2 / J20 | PWM; JTAG alternate unavailable while motor active |
| 15 | 23 | SERVO_OE | Servo disable / J21 | Boot strap; external pullup; HIGH disables servo outputs |
| 16 | 27 | UART_RX | GPS/UART J18 | Can be TWAI RX only when UART/GPS disabled; N8 no PSRAM |
| 17 | 28 | UART_TX | GPS/UART J18 | Can be TWAI TX only when UART/GPS disabled |
| 18 | 30 | SPI_SCK | SPI J17 | 3V3 SPI clock |
| 19 | 31 | SPI_MISO | SPI J17 | 3V3 SPI receive |
| 21 | 33 | I2C_SDA | Onboard bus / J16 | 2.2k pullup; shared with all onboard I2C parts |
| 22 | 36 | I2C_SCL | Onboard bus / J16 | 2.2k pullup; initially 100kHz, validate 400kHz rise time |
| 23 | 37 | SPI_MOSI | SPI J17 | 3V3 SPI transmit |
| 25 | 10 | M_A1 | Motor bridge A input1 / J20 | PWM; ADC2 not used |
| 26 | 11 | M_A2 | Motor bridge A input2 / J20 | PWM; ADC2 not used |
| 27 | 12 | M_B1 | Motor bridge B input1 / J20 | PWM; ADC2 not used |
| 32 | 8 | IMU_INT | IMU INT1 / J20 | Direct interrupt; occupied, not free analog input |
| 33 | 9 | BAT_ADC | Battery divider / J20 | ADC1, WiFi-compatible; occupied by battery sensing |
| 34 | 6 | ENC_RA | Encoder right A / J21 | INPUT ONLY, no internal pullup; external buffer |
| 35 | 7 | ENC_RB | Encoder right B / J21 | INPUT ONLY, no internal pullup; external buffer |
| 36 | 4 | ENC_LA | Encoder left A / J21 | INPUT ONLY, SENSOR_VP, no internal pullup; external buffer |
| 39 | 5 | ENC_LB | Encoder left B / J21 | INPUT ONLY, SENSOR_VN, no internal pullup; external buffer |

Expansion headers expose allocated signals for probing and alternate firmware use. They do not create extra independent GPIO or disconnect onboard drivers. Do not configure a buffered encoder/echo net as an output or externally drive an IMU interrupt. GPIO12 is deliberately not presented as unrestricted expansion.

## Expander and PWM allocation

| Device pin | Function | Firmware rule |
|---|---|---|
| MCP GPA0 | Motor sleep | External pulldown; set HIGH only after safe motor controls |
| MCP GPA1 | Motor nFAULT | Input, active LOW; pullup fitted |
| MCP GPA2 | ToF XSHUT | Emulate open drain: LOW output / released input |
| MCP GPA3 | ToF interrupt | Input, pullup fitted |
| MCP GPA4 | User button | Input, active LOW |
| MCP GPA5/6/7 | Red/green/blue LEDs | LOW turns on; GPA7 output-only |
| MCP GPB0..2 | TP1..TP3 local service pads | 3V3 GPIO, accessible solder/probe pads |
| MCP GPB3..6 | J19 expansion | 3V3 GPIO; poll or arrange external interrupt support |
| MCP GPB7 | J19 / load MOSFET | OUTPUT ONLY; also turns load on when HIGH |
| PCA9685 LED0..3 | Servo1..4 | Shared nominal 50Hz, external 5V buffers |

The MCP23017 INTA/B outputs are intentionally unconnected; fast encoder counting and the IMU interrupt do not use the expander. Current manufacturer documentation specifies GPA7/GPB7 as output-only: [Microchip datasheet](https://ww1.microchip.com/downloads/aemDocuments/documents/APID/ProductDocuments/DataSheets/MCP23017-Data-Sheet-DS20001952.pdf).
