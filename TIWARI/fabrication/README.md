# TIWARI TW8-A0 fabrication package

This is a manufacturing-data package for an engineering prototype, not a
physically qualified production release. Review `../docs/Hardware.md` and
`../docs/Bringup.md` with your fabricator and assembler before ordering.

- `gerbers/`: all four copper layers, masks, silkscreen, outline and drill data.
- `TIWARI-TW8-A0-Gerbers.zip`: the same board/drill files in one archive.
- `assembly/BOM.csv`: components to populate; rear service pads are not parts.
- `assembly/*-positions.csv`: component placement, with front/back sides.
- `SHA256SUMS`: hashes binding this package to the reviewed design and firmware.

Nominal board: 50 × 35mm, four layers, 1.0mm FR4. Confirm actual outer prepreg,
USB impedance geometry, solder-mask slivers, drill/annular ring limits and via
fill/capping under the FPGA exposed pad. See the hardware document for details.
Two-sided reflow and QFN inspection are required. Do not treat DRC as DFM approval.
