# LogicScope S3 — LS-S3-A0 engineering report

2026-11-09 · Prashanna Tiwari · KiCad 10.0.6

The native hardware design is routed and passes electrical, layout and
schematic-parity checks. It is an **unbuilt engineering prototype**, not a
bench-qualified instrument. Acquisition firmware and the Python desktop
application remain to be implemented. There is no measured achievable sampling
rate yet. The design target is 1 MS/s for eight-channel finite captures;
2 MS/s and continuous 1 MS/s are not released specifications.

## Components

| Function | Exact selected component | Notes |
|---|---|---|
| MCU/module | ESP32-S3-WROOM-1-N8R2 | Verified N8 equivalent, 8-MB flash; extra 2-MB PSRAM unused by baseline DMA plan |
| Input buffer | SN74LVC245APW | 3.3-V supply, eight 5.5-V-tolerant A inputs, fixed A-to-B direction |
| USB connector | GCT USB4105-GF-A | USB-C device; independent 5.1-kilohm CC pull-downs |
| USB ESD | TPD2E2U06DCKR | SC70-3, 1.5-pF typical; exact pad map verified |
| Optional input ESD | 2 × TPD4E05U06DQAR | DNP baseline; four channels each, 0.5-pF typical |
| Regulator | AP63203WU-7 | Fixed 3.3-V synchronous buck |
| Inductor | SRN4018-4R7M | 4.7 uH, 2.0-A saturation reference rating |
| USB input fuse | 1206L050YR | 500-mA hold PPTC; temperature and voltage-drop qualification needed |
| Probe headers | 2 × Wurth 61301021121 | 2x5, 2.54-mm vertical |
| UART header | Wurth 61300311121 | GND, MCU TX, MCU RX; 3.3-V logic |
| Buttons | 2 × KMR221GLFS | RESET and BOOT |
| LEDs | 2 × LTST-C190KGKT | Power and capture/status |
| Input passives | 8 × 220 ohms, 8 × 100 kilohms | Series protection and input pull-downs, no filter capacitors |
| Other passives | See BOM | Required bypass/bulk/boot/clock/USB/power networks |

[BOM.csv](../BOM.csv) lists all 56 orderable entries and manufacturer numbers:
54 populated and two optional DNP arrays. Eleven PCB probe features and two
mounting holes are not purchased parts. Package and pin verification derives
from the manufacturer references in the BOM and
[design decisions](../docs/Electrical_and_Fabrication.md). N8R2 and APW packaging were
selected after the original N8/APWR listings were unavailable. Stock snapshots
are unreserved and must be rechecked before procurement.

## Final pin mapping

| Channel | Header pin | Buffer input/output pads | MCU GPIO | Module pad |
|---|---|---|---:|---:|
| CH0 | J1.1 | U2.2 / U2.18 | 4 | 4 |
| CH1 | J1.3 | U2.3 / U2.17 | 5 | 5 |
| CH2 | J1.5 | U2.4 / U2.16 | 6 | 6 |
| CH3 | J1.7 | U2.5 / U2.15 | 7 | 7 |
| CH4 | J1.9 | U2.6 / U2.14 | 15 | 8 |
| CH5 | J2.1 | U2.7 / U2.13 | 16 | 9 |
| CH6 | J2.3 | U2.8 / U2.12 | 17 | 10 |
| CH7 | J2.5 | U2.9 / U2.11 | 18 | 11 |

J1 even pins are ground. J2 pins 2/4/6/8 are ground; pin 7 is a 3.3-V
reference through 10 kilohms; pins 9/10 are intentionally NC. The reference
must not power the target. All targets require a common ground.

| Function | GPIO / module pad |
|---|---|
| Hardware clock output | GPIO12 / pad20 → R4 33 ohms |
| Camera PCLK input | GPIO11 / pad19 ← R4 |
| Camera DE control and input loopback | GPIO9 / pad17 |
| Camera VSYNC control and input loopback | GPIO10 / pad18 |
| Buffer OE_N | GPIO13 / pad21, 10-kilohm pull-up |
| Status LED | GPIO14 / pad22 |
| Native USB D− / D+ | GPIO19 / pad13; GPIO20 / pad14 |
| BOOT | GPIO0 / pad27 |
| UART TX / RX | GPIO43 / pad37; GPIO44 / pad36 |
| EN | Module pad3, 10-kilohm/1-uF reset network |

## Acquisition and USB limits

Espressif's LCD_CAM camera RX supports an eight-bit parallel bus and GDMA.
The [architecture review](../docs/Acquisition_Architecture.md) cites the TRM and
Espressif's actual ESP32-S3 camera driver. It documents raw-byte configuration,
clock/framing requirements and the firmware qualification steps. The hardware
avoids strapping, USB and memory-reserved pins for the eight data bits.

At 1 MS/s, each sample is one byte containing all eight channels: 1,000,000
bytes/s. A proposed 128-KiB internal-DMA buffer stores 131,072 samples, or
131.072 ms at that rate. This allocation is a firmware budget, not an observed
allocation result; the chip's full 512-KiB SRAM is not all available to DMA.
Initial operation captures to memory, stops and uploads. Trigger detection,
pre-trigger buffering, clock accuracy, sample ordering and absence of lost
samples must be demonstrated on the prototype.

USB Full-Speed is 12 Mbit/s, or 1.5 MB/s before protocol overhead. A 1-MB/s
sample stream consumes most practical payload capacity; sustained operation
requires measured host/device throughput and overflow detection. A raw 2-MS/s
eight-channel stream is 2 MB/s and exceeds even that physical upper bound.
Faster finite captures would require separate acquisition validation and
upload after capture. No 2-MS/s capability is claimed.

The eventual application should display, measure and decode digital waveforms,
and export CSV/VCD. None of those software features is supplied as a working
application in this hardware release. At the initial 1-us sampling interval,
narrow pulses can be missed; high-speed SPI and precise short-pulse timing
are outside the baseline qualification target.

## Layout and manufacturing

55 × 40 mm, two copper layers, 0.8-mm nominal FR4 and nominal 35-um copper.
The module antenna overhang adds 6.75 mm to the assembled envelope. Two M2
nonplated mounting holes are provided. **TIWARI is etched out of front copper
and also printed on front silkscreen**, without cutting the rear ground plane.

The eight buffer-to-MCU routes are 5.00–6.06 mm long, all on the front with no
vias. USB data also stays on the front with no vias; module-side D+/D− routes
are both 2.740 mm. Connector-side totals, including duplicate-contact branches,
are 23.575 mm D− and 22.970 mm D+. The principal pair is 0.75-mm wide with a
0.17-mm edge gap. Approximately 90-ohm differential impedance is a design
target requiring the fabricator's stack-specific calculation and prototype
signal-quality checks.

The rear GND zone is one connected polygon covering 2,035.38 mm², about 92.52%
of the board. Local signal bypasses total about 43.60 mm on the rear. The
geometry audit finds ground beneath all USB/data trace centerlines, no rear
routing or vias on those critical nets, no antenna copper overlaps, and no
board-via drills intersecting SMD lands. Module footprint thermal drills are
separate and require assembly-process review.

Fabrication rules are 0.15-mm minimum track/clearance, 0.60/0.30-mm and
0.50/0.25-mm routing via lands/drills, plus the stock module's 0.20-mm thermal
drills. GCT's verified internal locating-hole geometry requires the documented
0.18-mm component-internal hole-clearance capability. Other copper-to-hole
clearance remains 0.25 mm. Obtain DFM signoff for that connector, module paste
and thermal-via process, 0.8-mm stack, USB impedance and mechanical overhang.

The 3.3-V load budget is 350 mA sustained / 500 mA transient with radios off,
subject to USB configuration/suspend limits. At 500 mA output, an assumed 85%
efficiency gives 0.291 W converter loss and about 0.446 A at 4.35-V input.
Using 89 C/W gives a calculated 26 C rise; it is not a thermal measurement.
See the electrical report for input protection and power limitations.

## Validation results

Final native KiCad CLI checks and connected KiCad MCP checks were run and
inspected. Reports are included under `reports/`.

| Check | Result |
|---|---|
| ERC | 0 violations |
| DRC | 0 violations |
| Unconnected PCB items | 0 |
| Schematic-to-PCB parity | 0 findings |
| Independent manifest/XML/pad mapping | All checks passed |
| Critical routing/ground/antenna audit | Passed; details in Physical_Audit.json |
| Hardware sampling/USB/thermal/ESD tests | Not performed; PCB unbuilt |

No blanket clearance or connection exclusion was added. The GCT rule records
verified manufacturer geometry. Exact local symbol/footprint filters resolve
package-name warnings. Intentional NC markers correspond to unused MCU pins,
manufacturer NC pads and J2 pins 9/10. Optional input ESD remains DNP.

Before treating this as a working instrument, implement firmware and the host
application and complete the [prototype validation plan](../docs/Validation_Plan.md).
