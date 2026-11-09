# Acquisition architecture review

Decision: the ESP32-S3 LCD_CAM architecture is viable for an eight-bit parallel
capture instrument. Proceed with a 1 MS/s **buffered-capture design target**.
No sampling rate has been measured on this PCB. The 2 MS/s stretch target is
not a released capability. This review establishes peripheral compatibility,
not a substitute for hardware and firmware qualification.

## Evidence reviewed before schematic construction

Espressif's [ESP32-S3 TRM, version 1.8](https://documentation.espressif.com/esp32-s3_technical_reference_manual_en.pdf),
chapter 29, documents eight-/sixteen-bit camera RX through GDMA and GPIO-matrix
signal assignment. Section 29.4.3 requires the camera module clock to run at
least twice the incoming pixel clock in slave mode. Its internal-memory limit
for the eight-bit mode is below 80 MHz. That upper bound is not an achievable
logic-analyzer product rating. Configure the peripheral clock well above the
1-MHz incoming sampling clock and bypass all image conversion.

Espressif's [ESP32-S3 camera implementation](https://github.com/espressif/esp32-camera/blob/master/target/esp32s3/ll_cam.c)
provides implementation evidence for eight-bit mode, one DMA byte per item,
byte-count EOF and RX GDMA descriptor chains. It is a camera driver, not a
drop-in logic-analyzer firmware. Reuse or adapt it only under its own licence
and pin a tested ESP-IDF/component revision.

The [module datasheet](https://documentation.espressif.com/esp32-s3-wroom-1_wroom-1u_datasheet_en.pdf)
confirms module GPIOs, native USB, internal SRAM, and the N8/N8R2 variants.
N8R2 retains 8-MB Quad SPI flash and adds 2-MB Quad PSRAM. The chosen capture
signals avoid strapping pins, USB pins, and memory-reserved signals. PSRAM is
not required by the first capture mode.

## Exact hardware mapping

| Sample bit | Probe | Buffer A input | Buffer B output | ESP GPIO | Module pad |
|---:|---|---:|---:|---:|---:|
| 0 | CH0 | 2 | 18 | 4 | 4 |
| 1 | CH1 | 3 | 17 | 5 | 5 |
| 2 | CH2 | 4 | 16 | 6 | 6 |
| 3 | CH3 | 5 | 15 | 7 | 7 |
| 4 | CH4 | 6 | 14 | 15 | 8 |
| 5 | CH5 | 7 | 13 | 16 | 9 |
| 6 | CH6 | 8 | 12 | 17 | 10 |
| 7 | CH7 | 9 | 11 | 18 | 11 |

GPIO12 generates a hardware clock through R4, 33 ohms, into GPIO11/CAM_PCLK.
This is an actual PCB loopback. GPIO9 and GPIO10 generate DE and VSYNC;
configure their pads for simultaneous input/output and route the input side to
the camera control signals through the GPIO matrix. Test points expose all
three camera control inputs. No camera sensor, external clock module or CPLD
is required.

GPIO13 controls buffer OE_N; its pull-up disables outputs during reset. DIR is
permanently high, so external signals always enter A and the MCU always
receives B. GPIO14 drives the capture LED. GPIO19/20 are USB D-/D+; GPIO43/44
are the independent debug UART. GPIO0 is BOOT and EN is RESET.

## Required capture implementation

Use LCD_CAM slave RX with eight-bit data, direct byte packing, DE/VSYNC gating,
and one allocated RX GDMA channel. Feed the camera PCLK from the hardware
clock output. Set deterministic GPIO-matrix routing, lock the clock source,
and keep radio activity off while sampling. Eight independently polled GPIO
loops are not an acquisition implementation for this board.

Allocate aligned internal DMA-capable SRAM and descriptors at runtime. A
proposed 128-KiB capture allocation holds 131,072 eight-channel samples:
131.072 ms at 1,000,000 samples/s. The chip's total 512-KB SRAM is shared with
code, stacks and runtime state; it is not all free sample memory. Treat 128 KiB
as an allocation budget to validate, not a guaranteed available heap. Reject
oversized captures cleanly. Keep PSRAM off the critical path initially.

Use descriptor-sized blocks, for example 4-KiB multiples with valid hardware
descriptor lengths/alignment. A finite chain and guarded stop sequence must
prevent overwriting completed samples. Validate byte order, first-sample
alignment, EOF counts and FIFO-overflow handling against an external counter.
Capture completion must not silently discard an overflow or missing block.

Rising/falling/level/pattern triggers can scan the DMA-produced sample bytes;
they do not require extra hardware comparators. A circular descriptor ring can
retain pre-trigger history, provided completed blocks are protected from DMA
overwrite while the trigger task inspects them. Preserve the actual triggering
sample index and account for block-processing latency. None of those firmware
features has been exercised on this hardware yet.

## USB bandwidth and realistic modes

The [Espressif USB device stack](https://docs.espressif.com/projects/esp-usb/en/latest/esp32s3/usb_device.html)
uses the S3 native Full-Speed peripheral. The 12-Mbit/s link has a raw ceiling
of 1.5 MB/s **before** packet framing, handshakes, host scheduling and firmware
overhead. Eight channels are packed into one byte per sample, not one byte per
channel:

| Sampling rate | Raw payload | 128-KiB buffer duration | Release status |
|---:|---:|---:|---|
| 100 kS/s | 100 kB/s | 1.31072 s | Candidate; unmeasured |
| 250 kS/s | 250 kB/s | 524.288 ms | Candidate; unmeasured |
| 1 MS/s | 1 MB/s | 131.072 ms | Finite-capture target; unmeasured |
| 2 MS/s | 2 MB/s | 65.536 ms | Stretch only; not enabled/validated |

Capture to SRAM and then upload is the baseline mode. Continuous 1-MS/s
streaming has insufficient assured margin to promise across hosts/stacks.
Uncompressed continuous 2-MS/s operation exceeds even the raw USB ceiling.
After implementation, benchmark sustained bulk transfers with actual framing,
CRC/sequence counters and the Python client. Advertise a continuous rate only
below the measured worst-case payload throughput, with explicit margin and
overflow detection. Do not equate a nominal CDC baud setting with USB speed.

At 1 MS/s, timing quantization is 1 microsecond; narrow asynchronous pulses can
be missed. A useful initial decoding envelope is UART at 115200 baud and
I2C/SPI around 100 kHz, subject to validation. Fast STM32/Raspberry Pi SPI
clocks at multiple MHz are outside this initial capture target. This device
records digital states, not analog amplitude, rise time or voltage waveforms.
