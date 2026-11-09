# LogicScope S3 — LS-S3-A0

Compact 8-channel USB digital logic analyzer hardware by Prashanna Tiwari.
Open `LogicScope_S3.kicad_pro` in KiCad 10. The project contains native
hierarchical schematics, verified library parts and an actual two-layer PCB.

**Engineering prototype; acquisition firmware and desktop software are not yet
implemented or bench validated.** 1 MS/s is an unmeasured finite-capture target,
not an advertised continuous rate. There is no analog voltage measurement.

## Design

- ESP32-S3-WROOM-1-N8R2, eight parallel LCD_CAM inputs and GDMA.
- SN74LVC245APW at 3.3 V with 5.5-V-tolerant inputs, 220-ohm series resistors
  and 100-kilohm input pull-downs. External signal range: 0–5 V.
- USB-C device port, native USB Full-Speed, ESD protection and 3.3-V buck supply.
- Two 2x5 input headers, BOOT/RESET, capture/power LEDs and UART/test access.
- 55 x 40 mm, two layers, 0.8-mm board; PCB antenna overhangs by 6.75 mm.
- **TIWARI** etched in front copper and printed on silkscreen.

Use a common ground with the target. J2 pin 7 is a current-limited reference
only; this instrument does not power the target.

## Files and limitations

Read [acquisition architecture](docs/Acquisition_Architecture.md),
[electrical/fabrication decisions](docs/Electrical_and_Fabrication.md) and the
[hardware validation plan](docs/Validation_Plan.md) before ordering or using
a prototype. Connector pinout and GPIO allocation are supplied as CSV files.
`BOM.csv` contains exact manufacturer part numbers and DNP status.

Final checks: ERC 0, DRC 0, unconnected nets 0, schematic parity findings 0.
Read the [engineering report](docs/Engineering_Report.md). Manufacturing files
are in `fabrication/`; the KiCad 3D render is in `previews/`.

Fabrication needs a stack-specific USB impedance review and the documented
USB connector hole-clearance capability. Sampling, USB throughput, power,
thermal and ESD behavior require physical prototype testing.

## Tool workflow

Connected KiCad MCP created the native project and initial components,
generated a netlist and ran electrical checks. Native pcbnew scripts perform
placement and routing because those editing operations are absent from the
connected MCP. Native KiCad CLI and MCP perform final validation and exports.
Scripts under `scripts/` record engineering operations; do not run placement
or initial-routing scripts over the completed board. `release.py`, when
available, validates the current design and exports without reconstructing it.

Copyright (c) 2026 Prashanna Tiwari. [CERN-OHL-P-2.0](LICENSE).
KiCad-derived library graphics retain their upstream licence in `libraries/`.
