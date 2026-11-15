# Open Source PCB

Open hardware designs for a custom 8-bit CPU development board, ESP32 robotics, a brushed-motor flight controller, and a USB logic analyser.

## TIWARI

[TIWARI](TIWARI/) is a 50 × 35-mm, four-layer development board with an original
36MHz 8-bit CPU implemented in an iCE40UP5K FPGA, USB-C programming/serial,
16 digital GPIO, two hardware PWM outputs and a millisecond timer.

- [Beginner guide and project overview](TIWARI/README.md)
- [KiCad project](TIWARI/hardware/TIWARI.kicad_pro)
- [Fabrication and assembly package](TIWARI/fabrication/)
- [CPU architecture](TIWARI/docs/Architecture.md)
- [Verification evidence](TIWARI/docs/Verification.md)
- [Open-source licenses](TIWARI/LICENSE)

TW8-A0 passes ERC, DRC, schematic/PCB parity, CPU/peripheral HDL simulation,
and 36MHz FPGA timing checks for all four example images. This is an engineering
prototype; fabrication, assembly, USB/power qualification and real performance
measurements remain to be done. It uses its own instruction set and does not
run Arduino sketches.

![TIWARI PCB CAD preview](TIWARI/previews/TIWARI_isometric.png)

## LogicScope S3

[LogicScope S3](LogicScope_S3/) is a compact 8-channel USB digital logic analyser hardware prototype built around the ESP32-S3, with a 55 x 40-mm, two-layer PCB.

- [Project documentation](LogicScope_S3/README.md)
- [KiCad project](LogicScope_S3/LogicScope_S3.kicad_pro)
- [Fabrication and assembly package](LogicScope_S3/fabrication/)
- [Engineering report](LogicScope_S3/docs/Engineering_Report.md)
- [Hardware validation plan](LogicScope_S3/docs/Validation_Plan.md)
- [License](LogicScope_S3/LICENSE)

LS-S3-A0 has recorded passing ERC, DRC, connectivity and schematic/PCB parity checks. Firmware and a simple desktop app v0.1.0 are implemented, with finite DMA captures, an eight-channel viewer, timing cursors and CSV/VCD export. Sampling performance and electrical behavior require physical prototype validation.

- [Firmware: build and flash](LogicScope_S3/firmware/README.md)
- [Desktop app: install and demo](LogicScope_S3/software/README.md)
- [Software verification](LogicScope_S3/docs/Software_Verification.md)

![LogicScope S3 PCB](LogicScope_S3/previews/PCB_3D_isometric.png)

## RoveFlight S3

[RoveFlight S3](RoveFlight_S3/) is a 45 x 45-mm, six-layer ESP32-S3 controller for a 1S brushed quadcopter, with hardware motor interlocks, IMU, barometer, ToF and expansion interfaces.

- [Project documentation](RoveFlight_S3/README.md)
- [KiCad project](RoveFlight_S3/RoveFlight_S3.kicad_pro)
- [Fabrication and assembly package](RoveFlight_S3/fabrication/)
- [Manufacturing readiness and validation](RoveFlight_S3/docs/Manufacturing_Readiness.md)
- [License](RoveFlight_S3/LICENSE)

RF-S3-A0 passes ERC, DRC, connectivity and schematic/PCB parity checks. Via filling/capping and fabricator DFM are required; bench and flight qualification remain open.

![RoveFlight S3 PCB](RoveFlight_S3/previews/PCB_top.png)

## RoveCore One

The complete ESP32 robotics PCB project is in [RoveCore](RoveCore/).

- [Project documentation](RoveCore/README.md)
- [KiCad project](RoveCore/RoveCore_One.kicad_pro)
- [Fabrication files](RoveCore/fabrication/)
- [Manufacturing readiness](RoveCore/docs/Manufacturing_Readiness.md)
- [License](RoveCore/LICENSE)

![RoveCore PCB](RoveCore/previews/PCB_top.png)
