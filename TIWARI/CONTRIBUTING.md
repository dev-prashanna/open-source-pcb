# Contributing

Run `make test sim` and `python3 tools/check_pins.py` before submitting a CPU,
assembler, firmware or pin-assignment change. Run `make synth` for every
example program after changing RTL; each image must meet the 36MHz target.
Describe instruction semantics and peripheral register changes in docs.

For hardware changes use KiCad 10, preserve component UUIDs where possible,
update the BOM/manifest/PCF together, and run ERC and DRC with schematic parity.
Attach rule-check reports and rendered front/back views. Fabrication exports
must be regenerated from the exact reviewed board. Do not mark a hardware
issue physically verified without measurements and a board revision.

The scripts under `scripts/` are construction and release utilities. Running
build_hardware.py/layout.py regenerates schematic/placement and destroys manual
layout progress. The release exporter never regenerates placement or routing.
Use a separate working copy when changing the construction design.

Contributions retain the file's applicable license; see LICENSE. Include
upstream attribution for any third-party library modifications.
