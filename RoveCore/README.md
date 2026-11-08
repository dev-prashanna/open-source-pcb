# P-TIWARI

**Integrated ESP32 robotics & IoT platform — PTW-ESP32-ROB-A0**

Plug in, program, and build.

This project contains a real, editable KiCad design: ESP32-WROOM-32E-N8, USB-C/CP2102N programming, two current-regulated motor bridges, IMU, compass, environmental and light sensors, ToF ranging, two buffered quadrature encoders, four servo connectors with dedicated PWM and power, four ADC inputs, GPIO expansion and protected power inputs.

The PCB is 80 × 65 mm, four layers, with components on both sides and an antenna overhang. Its electrical bill contains 217 fitted parts and three copper service pads, plus four PCB-only mounting holes. The design is an **engineering prototype**, with no fabricated-board test results. Read the manufacturing assessment before ordering boards; ERC/DRC alone cannot establish thermal, RF, transient or USB compliance.

![Board top view](previews/PCB_top.png)

## Open the design

- Open **RoveCore_One.kicad_pro** in KiCad 10.
- **RoveCore_One.kicad_sch** is the root schematic; functional sheets are linked from it.
- **RoveCore_One.kicad_pcb** contains placement and actual copper routing.
- **previews/** contains the schematic PDF and board exports.

## Engineering references

- [Design decisions and application coverage](docs/Engineering_Design.md)
- [Power architecture, limits and calculations](docs/Power_Architecture.md)
- [GPIO mapping](docs/GPIO_Mapping.md)
- [Connector pinouts](docs/Connector_Pinouts.md)
- [Bring-up and calibration procedure](docs/Bringup_and_Calibration.md)
- [Manufacturing readiness](docs/Manufacturing_Readiness.md)

Machine-readable references are **BOM.csv**, **BOM_Grouped.csv**, **GPIO_Mapping.csv**, **Connector_Pinouts.csv** and **Placement.csv**. Every electrical component has a footprint assignment and manufacturer part number. Verify procurement and mating connectors against manufacturer drawings before ordering.

**reports/ERC.json**, **reports/DRC.json**, **reports/Connectivity_Audit.json** and **reports/Physical_Audit.json** are the final validation records. Intermediate reports and routing sessions are retained as engineering evidence; they are not fabrication releases.

## Power and connection essentials

- All unrestricted logic is 3.3 V. Only the explicitly buffered encoder inputs and ultrasonic echo accept 5 V signals.
- J3 takes an externally protected 2S battery. **There is no onboard charger or cell balancer.** Use an external proper 2S balance charger with the pack disconnected.
- J6 powers motors independently. Motor recommendation is 3–8.4 V, ≤0.6 A continuous per bridge, with approximately 0.8 A current chopping.
- JP1 selects one servo supply. Fit exactly one shunt. Servo power never comes from the 3.3 V rail.
- USB powers logic; the battery-derived 5 V accessory and servo-signal-buffer rail requires battery power.
- Read shared-GPIO restrictions before repurposing headers. GPB7 expansion is output-only and also controls the load MOSFET.

## Source and regeneration

The scripts in **scripts/** preserve an explicit electrical manifest (**design.json**), construct native KiCad files from installed libraries, audit the exported netlist, and document the implementation. They require KiCad's system Python bindings and the packages listed in **requirements.txt**. The installed KiCad version used for this project was 10.0.6. Assisted routing used Freerouting 2.5.0 with Java 25; native KiCad DRC is the independent verification step.

These are engineering construction tools, not a single unattended release pipeline. `build_design.py` regenerates the schematic, `layout.py` regenerates placement and clears routing, and subsequent routing/import/repair steps operate on that layout. Running placement on the finished project will replace its copper; work on a copy when experimenting. The delivered native files and final reports are the reviewable result. `firmware/board_pins.h` is a framework-independent pin contract, not tested robot firmware.

## Open source and fabrication exports

Copyright 2026 dev-prashanna. Original project sources are licensed under **CERN-OHL-P-2.0**; see [LICENSE](LICENSE). Third-party KiCad library content retains its upstream licensing, including the KiCad library exception where applicable. Manufacturer datasheets are referenced by URL in `datasheets/sources.json`.

`fabrication/gerbers/` contains four copper layers, solder mask, silkscreen, board outline and plated/nonplated drill files. `fabrication/assembly/` contains KiCad placement exports for both faces. `fabrication/RoveCore_One-Gerbers.zip` is the corresponding fabrication archive. Consult [fabrication notes](docs/Fabrication_Notes.md) and [manufacturing readiness](docs/Manufacturing_Readiness.md) before ordering.

Regenerate checks and manufacturing outputs from the delivered board with:

```sh
python3 scripts/export_release.py
```

This requires KiCad 10's `kicad-cli` on PATH. It checks DRC and schematic parity before exporting, and rejects ERC errors. Three ERC warnings are retained for sensor address straps tied to ground; their rationale is recorded in the manufacturing assessment. To repeat the manifest and physical audits, use a Python environment with system KiCad bindings and `requirements.txt`, then run `scripts/verify_design.py` and `scripts/physical_audit.py`.
