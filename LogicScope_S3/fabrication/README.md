# LS-S3-A0 engineering fabrication package

This is an unbuilt prototype. Firmware and host software v0.1.0 are implemented
but have not been validated on physical hardware; see `../firmware/README.md`
and `../software/README.md`.
Read `../docs/Engineering_Report.md` and `../docs/Electrical_and_Fabrication.md`.

- `gerbers/`: TWO copper layers, masks, silkscreens, outline, separate PTH/NPTH
  drills, Gerber job and PDF drill maps. Use the complete set for bare-board CAM.
- `assembly/`: baseline BOM (54 populated parts; U5/U6 DNP), grouped BOM,
  native KiCad placement CSV, assembly PDF and baseline F.Paste stencil Gerber.
- Baseline paste excludes U5/U6. Module thermal-pad windowing is retained;
  assembler must approve thermal-via tenting/filling and paste process.
- `Schematic.pdf`: six native KiCad schematic pages.
- `Drill_Report.txt`: drill tools and plating classification.
- `SHA256SUMS`: integrity of source and output files, paths relative to project.

Specify 55x40 mm, TWO layers, 0.8-mm FR4, nominal 35-um copper and the documented
USB stack/impedance review. Routing vias are 0.6/0.3 and 0.5/0.25 mm; the module
has stock 0.2-mm thermal drills. The GCT connector requires 0.18-mm internal
copper-to-locating-hole capability. DFM signoff remains required.

J2 reference is output-only through 10 kilohms. Never power the target from it.
TIWARI is physically etched in front copper and appears on front silkscreen.
