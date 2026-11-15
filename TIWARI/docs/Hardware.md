# Hardware design and fabrication

TW8-A0 is a 50 × 35 mm, four-layer, 1.0mm engineering prototype. Copper layers
are F.Cu signals/components, In1.Cu ground reference, In2.Cu 3.3V plane, B.Cu
signals/components. The outer copper target is 35um. Use 0.10mm nominal outer
prepreg as the starting point for controlled-impedance review. The fabricator
must confirm the exact finished stackup; USB geometry is not certified merely
because the design uses four layers.

## Electrical architecture

USB-C is a USB 2.0 device connection with independent 5.1k CC resistors and a
500mA resettable input fuse. U6 protects D+/D-. USB5V is not a general GPIO
voltage. An AP2112K-1.2 produces the FPGA core rail directly from fused USB5V.
A TPS3808G12 monitors it at its fixed 1.12V threshold and delays enabling the
AP2112K-3.3, so the FPGA core rises before its I/O/configuration supplies. The
10nF supervisor timing capacitor provides a nominal delay of about 40ms; measure
its actual behavior. A 100-ohm/1uF filter supplies VCCPLL. VPP_2V5 is tied to
3.3V for SPI flash boot, within the specified operating range; NVCM programming
is unsupported. All three I/O banks use 3.3V.

The FT2232HL uses its internal 1.8V regulator for VCORE; the required bulk and
local decoupling are present. VPHY and VPLL use separate ferrite filters. A
12MHz crystal clocks the USB bridge. A separate 12MHz CMOS oscillator clocks
the FPGA PLL, which produces the 36MHz system clock. Local decoupling is placed
on the rear below the FTDI supply pins, reducing loop length in the compact
layout. The QFN paddle and local plane drops provide the FPGA ground return.

The W25Q32JV 32Mbit flash stores the FPGA configuration and initialized program.
Flash CS, HOLD and WP pull high. ADBUS0/1/2 are SCK/MOSI/MISO, ADBUS4 drives
flash CS open drain, ADBUS7 drives CRESET open drain, and ADBUS6 senses CDONE,
matching IceStorm iceprog. FTDI channel B TX connects to FPGA RX and vice versa.
CPU RESET is separate from CRESET, so a program can restart without reloading
the FPGA. The USER and FAULT LEDs use 1k series resistors.

## Header pinout

The board is not pin-compatible with Uno shields. Consult the numbered pad-1
marker and actual KiCad layout; headers on opposite edges are independent.

| Connector | Pin order from pin 1 |
| --- | --- |
| J2 | GND, 3V3, D0, D1, D2, D3, D4, D5, D6, D7 |
| J3 | GND, 3V3, D8, D9, D10, D11, D12, D13, D14, D15 |
| J4 | GND, PWM0, PWM1, 3V3 |
| J5 rear service pads | GND, flash SCK, flash MOSI, flash MISO, flash CS, CRESET |

J5 is an original 0.85mm round test-pad array at 1.27mm pitch. It is not a
component to buy or populate. Attach a pogo fixture or temporary wires; do not
connect a second powered SPI programmer while the USB programmer is active.
The GPIO/FPGA physical pin mapping is in `hardware/TIWARI.pcf`; the release
check compares it to the U1 schematic pin manifest.

## Assembly and power limits

Use the exact BOM ordering codes or review substitutions against datasheets.
In particular, do not replace the fixed-threshold supervisor with the
adjustable variant. The EEPROM is permanently organized as x16. The FPGA is a
7 × 7mm QFN48 with exposed ground paddle; it requires stencil/reflow assembly
and inspection, rather than beginner breadboard assembly.

The exposed paddle contains four thermal ground vias. Require resin-filled,
copper-capped vias under U1 to prevent solder wicking, or have the assembler
approve a controlled alternative before fabrication. Use 0.25mm finished via
drills, 0.50mm via lands, minimum 0.15mm trace/clearance, and the documented
USB connector land pattern. Confirm all finished annular rings and solder-mask
slivers with the fabricator. The board uses parts on both sides and requires
an assembly sequence that retains rear decouplers during the second reflow.
No mechanical mounting holes are provided; use an insulating edge support.

The 600mA LDO rating is not the usable board current budget. LDO loss is
`(Vin - Vout) * Iout`; a 5V-to-1.2V regulator dissipates 0.19W at 50mA.
Use measured core consumption, junction-temperature estimates, USB current
allocation and ambient temperature to set the final budget. Until verified,
limit external 3.3V loads to 50mA aggregate and keep GPIO loads near 1mA per pin.
This is a conservative bring-up limit, not a qualified operating specification.

## USB provisioning

A blank/missing FTDI EEPROM uses default USB descriptors and should allow
initial enumeration and provisioning. Use FTDI FT_PROG to configure the
93LC46B for the actual design: retain VID 0403 / PID 6010, channel A/B as normal
interfaces, channel B VCP enabled, bus powered, an appropriate declared current
request (up to 500mA only if required and permitted), and a unique serial number.
Do not invent a private USB VID. Save and read back the provisioning template.

The board does not gate the complete FPGA supply off with PWREN/SUSPEND. USB
suspend current and pre-enumeration current have not been qualified. A 500mA
fuse or a changed descriptor does not establish USB compliance. Measure both
states before treating the board as a compliant product. Use a suitable
powered host/hub during bring-up and do not advertise certification.

## Primary references

- [Lattice UltraPlus datasheet](https://www.latticesemi.com/api/document/download?id=51968): pinout, supplies, sequencing, configuration and FPGA limits.
- [Lattice hardware checklist](https://www.latticesemi.com/api/document/download?id=47779): decoupling, PLL filtering, configuration connections.
- [FT2232H datasheet](https://www.ftdichip.cn/Support/Documents/DataSheets/ICs/DS_FT2232H.pdf): power, USB, crystal, EEPROM and channel pinout.
- [FTDI EEPROM organization guidance](https://ftdichip.com/faq/what-should-i-do-when-i-cannot-program-eeprom-using-the-ft_prog-utility/): x16 EEPROM requirement.
- [AP2112 datasheet](https://www.diodes.com/datasheet/download/AP2112.pdf): regulator pins, enable threshold, thermal limits and decoupling.
- [TPS3808 datasheet](https://www.ti.com/lit/ds/symlink/tps3808.pdf): fixed threshold, delay and open-drain reset.
- [IceStorm iceprog source](https://github.com/YosysHQ/icestorm/blob/main/iceprog/iceprog.c): programmer pin assignments and flash workflow.
- [Arduino Uno R3 documentation](https://docs.arduino.cc/hardware/uno-rev3): the comparison baseline is the classic 16MHz board, not every Arduino model.
