// P-TIWARI A.0; pin contract only, not validated application firmware.
#pragma once
namespace p_tiwari {
constexpr int PIN_BOOT = 0;
constexpr int PIN_U0_TX = 1;
constexpr int PIN_BUZZ_PWM = 2;
constexpr int PIN_U0_RX = 3;
constexpr int PIN_US_TRIG = 4;
constexpr int PIN_SPI_CS = 5;
constexpr int PIN_STRAP12 = 12;
constexpr int PIN_US_ECHO = 13;
constexpr int PIN_M_B2 = 14;
constexpr int PIN_SERVO_OE = 15;
constexpr int PIN_UART_RX = 16;
constexpr int PIN_UART_TX = 17;
constexpr int PIN_SPI_SCK = 18;
constexpr int PIN_SPI_MISO = 19;
constexpr int PIN_I2C_SDA = 21;
constexpr int PIN_I2C_SCL = 22;
constexpr int PIN_SPI_MOSI = 23;
constexpr int PIN_M_A1 = 25;
constexpr int PIN_M_A2 = 26;
constexpr int PIN_M_B1 = 27;
constexpr int PIN_IMU_INT = 32;
constexpr int PIN_BAT_ADC = 33;
constexpr int PIN_ENC_RA = 34;
constexpr int PIN_ENC_RB = 35;
constexpr int PIN_ENC_LA = 36;
constexpr int PIN_ENC_LB = 39;
constexpr unsigned IMU_ADDR=0x6A, MAG_ADDR=0x1C, BME_ADDR=0x76, ALS_ADDR=0x10;
constexpr unsigned TOF_ADDR=0x29, PWM_ADDR=0x40, EXP_ADDR=0x20, ADC_ADDR=0x48;
}
