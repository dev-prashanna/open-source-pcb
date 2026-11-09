# LogicScope S3 firmware v0.1.0

ESP32-S3 firmware for **LS-S3-A0**, using **ESP-IDF v5.5.2** exactly.
Firmware is implemented and intended for first-board bring-up. No physical
board capture or sampling-rate qualification has been performed.

## Build and flash

Install [ESP-IDF v5.5.2](https://docs.espressif.com/projects/esp-idf/en/v5.5.2/esp32s3/get-started/index.html)
with the ESP32-S3 tools and activate its environment. From this directory:

```sh
idf.py set-target esp32s3
idf.py build
idf.py -p /dev/ttyACM0 flash
```

On Windows use a port such as `COM3`. Select the port actually connected to
the board. For initial download, hold BOOT, press/release RESET, then release
BOOT. ROM USB download and the application can enumerate as different ports.
If USB download fails, use a **3.3-V UART adapter** on J4 (GPIO43 TX, GPIO44 RX,
and ground) with BOOT/RESET. Do not apply adapter power to the target headers.

`build/logicscope_s3.bin` is the application image; it is **not** a complete
factory image. Use `idf.py flash` and its generated flash arguments to write
the bootloader, partition table and app at the right offsets. Capture software
uses the application's USB port after resetting into normal boot.

Console output uses UART0 GPIO43/44. The native USB Serial/JTAG controller on
GPIO19/20 is reserved for binary capture traffic. It appears as the Espressif
USB serial device, normally VID `303a`, PID `1001`; it does not have a custom
TinyUSB product descriptor. USB CDC baud settings do not set the sample rate.

## Implemented operation

- Eight simultaneous bits, CH0..7 on GPIO4,5,6,7,15,16,17,18.
- XTAL-derived LEDC clock on GPIO12, through the PCB loopback into GPIO11.
- LCD_CAM RX at a 40-MHz peripheral clock; no software GPIO polling.
- Finite GDMA descriptor chain, internal SRAM only, 16–65,536 samples in
  multiples of four. Descriptor payloads are at most 4,092 bytes, not 4,096.
- Requested PCLK rates: 100 kS/s, 250 kS/s, 500 kS/s, 1 MS/s. These are
  configured rates, **not measured or qualified performance**.
- OE_N is high during reset/idle/upload; capture LED is on while collecting.
- DE/VSYNC on GPIO9/10 use input/output mode for GPIO-matrix loopback.
- Byte-count EOF stops camera reception. No circular chain or buffer reuse
  occurs while DMA is active. Samples upload only after capture stops.
- Descriptor errors, abnormal EOF, timeout, unexpected final descriptor,
  wrong descriptor byte count/ownership, and guard corruption reject a capture.
- RX FIFO full is configured to stop the camera. A resulting short/stalled
  capture fails byte-count/timeout checks; the S3 does not expose a complete
  diagnostic history for every possible lost-input condition. Qualify with a
  counter; passing software checks alone does not prove lossless sampling.
- USB responses contain sequence, exact length and CRC-32 covering header and
  payload. Host recomputes the trigger result from received samples.

At 1 MS/s the maximum capture is 65.536 ms; at 100 kS/s it is 655.36 ms. The
64-KiB limit deliberately fits the 16-bit LCD_CAM receive byte-count field.
The architecture document's 128-KiB allocation was a future design budget.

Trigger modes are **searches inside one finite capture**: immediate, rising,
falling, high, low, or a masked pattern. The first matching sample is returned,
or `-1` for no match/immediate. An edge requires two retained samples, so an
edge at sample zero is unknowable. Firmware does not wait for an external
trigger, retry windows, stream continuously, or maintain pre-trigger history.

Wi-Fi/Bluetooth and PSRAM are unused. Power management is disabled to keep the
sampling clock fixed. USB hardware suspend/current behavior and clock/startup
alignment still require physical validation.

## Verification and next bench steps

Run the portable firmware tests from the project root:

```sh
cc -std=c11 -Wall -Wextra -Werror -I firmware/main \
  firmware/tests/test_protocol.c firmware/main/protocol.c -o /tmp/ls-protocol-test
/tmp/ls-protocol-test
```

Follow [the hardware validation plan](../docs/Validation_Plan.md). In particular,
measure TP8 PCLK at every configured rate, verify channel/byte order with a
parallel counter, exercise descriptor boundaries and maximum captures, repeat
start/stop cycles, and test USB removal during upload. Validate FIFO-full stop
behavior and deliberately remove/interrupt the clock to verify timeout handling.
The first-sample phase relative to the target is unspecified.

Private LCD_CAM/GDMA interfaces are version-pinned by a compile-time check.
Review the peripheral code before upgrading ESP-IDF. Official references:
[S3 camera implementation](https://github.com/espressif/esp32-camera/blob/master/target/esp32s3/ll_cam.c),
[IDF v5.5.2 camera HAL](https://github.com/espressif/esp-idf/blob/v5.5.2/components/hal/esp32s3/include/hal/cam_ll.h),
[USB Serial/JTAG](https://docs.espressif.com/projects/esp-idf/en/v5.5.2/esp32s3/api-reference/peripherals/usb_serial_jtag.html).

Firmware is [MIT licensed](LICENSE); hardware remains CERN-OHL-P-2.0.
