# P-TIWARI connector reference

Pin numbers follow the KiCad footprint and the square/marked pin-1 pad, viewed from the component side. Cable drawings can mirror this view: verify mating orientation before making a harness. Never infer wire colors or JST motor polarity from unrelated breakout boards.

## J1 — SERVICE 3V3

3V3 service logic only

| Pin | Signal |
|---|---|
| 1 | GND |
| 2 | +3V3 |
| 3 | U0_TX |
| 4 | U0_RX |
| 5 | EN |
| 6 | BOOT |

## J2 — USB-C 5V DATA

USB 5V sink, full-speed data, no PD

| Pin | Signal |
|---|---|
| A1 | GND |
| A4 | USB_VBUS |
| A5 | CC1 |
| A6 | USB_DP |
| A7 | USB_DM |
| A9 | USB_VBUS |
| A12 | GND |
| B1 | GND |
| B4 | USB_VBUS |
| B5 | CC2 |
| B6 | USB_DP |
| B7 | USB_DM |
| B9 | USB_VBUS |
| B12 | GND |
| SH | GND |

## J3 — 2S BAT 6.4-8.4V

Protected 2S 6.4–8.4V; no onboard charging

| Pin | Signal |
|---|---|
| 1 | BAT_RAW |
| 2 | GND |

## J4 — EXT 5V LOGIC

Regulated external 5V logic input

| Pin | Signal |
|---|---|
| 1 | EXT5_RAW |
| 2 | GND |

## J5 — SERVO EXT 5-6V

External 5–6V servo input

| Pin | Signal |
|---|---|
| 1 | SERVO_EXT_RAW |
| 2 | GND |

## JP1 — SERVO SELECT 1-2 BAT / 2-3 EXT

ONE shunt:1-2 battery servo,2-3 external servo

| Pin | Signal |
|---|---|
| 1 | SERVO_BUCK |
| 2 | SERVO_SELECTED |
| 3 | SERVO_EXT |

## J6 — VM 3-8.4V

Separate motor input 3–8.4V

| Pin | Signal |
|---|---|
| 1 | MOTOR_RAW |
| 2 | GND |

## J7 — MOTOR A

Motor A, <=0.6A continuous target

| Pin | Signal |
|---|---|
| 1 | MOTOR_A_P |
| 2 | MOTOR_A_N |

## J8 — MOTOR B

Motor B, <=0.6A continuous target

| Pin | Signal |
|---|---|
| 1 | MOTOR_B_P |
| 2 | MOTOR_B_N |

## J9 — ULTRASONIC 5V

5V accessories require battery BAT5; ECHO input buffered

| Pin | Signal |
|---|---|
| 1 | BAT5 |
| 2 | US_TRIG5 |
| 3 | US_ECHO_RAW |
| 4 | GND |

## J10 — ENC LEFT

Encoder power 3V3; A/B buffer inputs accept <=5.5V

| Pin | Signal |
|---|---|
| 1 | +3V3 |
| 2 | GND |
| 3 | ENC_LA_RAW |
| 4 | ENC_LB_RAW |

## J11 — ENC RIGHT

Encoder power 3V3; A/B buffer inputs accept <=5.5V

| Pin | Signal |
|---|---|
| 1 | +3V3 |
| 2 | GND |
| 3 | ENC_RA_RAW |
| 4 | ENC_RB_RAW |

## J12 — SERVO 1

GND / servo supply / 5V signal; aggregate servo current limit applies

| Pin | Signal |
|---|---|
| 1 | GND |
| 2 | SERVO5 |
| 3 | SERVO_OUT0 |

## J13 — SERVO 2

GND / servo supply / 5V signal; aggregate servo current limit applies

| Pin | Signal |
|---|---|
| 1 | GND |
| 2 | SERVO5 |
| 3 | SERVO_OUT1 |

## J14 — SERVO 3

GND / servo supply / 5V signal; aggregate servo current limit applies

| Pin | Signal |
|---|---|
| 1 | GND |
| 2 | SERVO5 |
| 3 | SERVO_OUT2 |

## J15 — SERVO 4

GND / servo supply / 5V signal; aggregate servo current limit applies

| Pin | Signal |
|---|---|
| 1 | GND |
| 2 | SERVO5 |
| 3 | SERVO_OUT3 |

## J16 — I2C 3V3

3V3 I2C, shared pullups, short cable

| Pin | Signal |
|---|---|
| 1 | +3V3 |
| 2 | GND |
| 3 | I2C_SDA |
| 4 | I2C_SCL |

## J17 — SPI / LORA

3V3 SPI; CS boot strap must remain high at reset

| Pin | Signal |
|---|---|
| 1 | GND |
| 2 | +3V3 |
| 3 | SPI_SCK |
| 4 | SPI_MOSI |
| 5 | SPI_MISO |
| 6 | SPI_CS |

## J18 — GPS / UART

3V3 UART/GPS; alternate external CAN transceiver replaces UART

| Pin | Signal |
|---|---|
| 1 | GND |
| 2 | +3V3 |
| 3 | UART_TX |
| 4 | UART_RX |

## J19 — GPIO EXP 3V3

3V3 GPB3..7; pins3..5 are ground returns; B7 output-only/shared load

| Pin | Signal |
|---|---|
| 1 | GND |
| 2 | +3V3 |
| 3 | GND |
| 4 | GND |
| 5 | GND |
| 6 | EXP_B3 |
| 7 | EXP_B4 |
| 8 | EXP_B5 |
| 9 | EXP_B6 |
| 10 | EXP_B7 |

## TP1 — EXP_B0



| Pin | Signal |
|---|---|
| 1 | EXP_B0 |

## TP2 — EXP_B1



| Pin | Signal |
|---|---|
| 1 | EXP_B1 |

## TP3 — EXP_B2



| Pin | Signal |
|---|---|
| 1 | EXP_B2 |

## J20 — ESP GPIO SHARED

Shared controller signals; BAT_ADC and IMU_INT are inputs

| Pin | Signal |
|---|---|
| 1 | GND |
| 2 | +3V3 |
| 3 | M_A1 |
| 4 | M_A2 |
| 5 | M_B1 |
| 6 | M_B2 |
| 7 | IMU_INT |
| 8 | BAT_ADC |
| 9 | US_TRIG |
| 10 | US_ECHO |

## J21 — ESP GPIO INPUTS

Shared controller signals; encoder pins input-only

| Pin | Signal |
|---|---|
| 1 | GND |
| 2 | SERVO_OE |
| 3 | BUZZ_PWM |
| 4 | ENC_LA |
| 5 | ENC_LB |
| 6 | ENC_RA |
| 7 | ENC_RB |
| 8 | SPI_CS |

## J22 — ANALOG 0-3V3

0–3V3 analog, ADS1115 total <=860samples/s

| Pin | Signal |
|---|---|
| 1 | +3V3 |
| 2 | GND |
| 3 | AN_IN0 |
| 4 | AN_IN1 |
| 5 | AN_IN2 |
| 6 | AN_IN3 |

## J23 — LOAD 5V 0.25A

5V switched load, <=250mA, battery BAT5 required

| Pin | Signal |
|---|---|
| 1 | BAT5 |
| 2 | LOAD_LOW |

USB SBU pads A8/B8 are intentionally unused; shell is grounded. Connector signals containing RAW or FUSED are named before or after protection and are not regulated outputs. For each servo connector, pin1 is GND, pin2 is the selected servo supply, pin3 is PWM. Power domains are not interchangeable.
