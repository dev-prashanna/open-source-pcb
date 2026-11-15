# Library provenance

TIWARI uses the installed KiCad 10 symbol/footprint libraries. The schematic
embeds all symbols and the PCB embeds all land patterns, so both can be opened
without this construction environment. Standard library names remain attached
for normal KiCad maintenance. KiCad libraries are licensed CC-BY-SA-4.0 with the
KiCad Libraries Exception allowing their use in electronic designs without
forcing the entire design under that license.

Upstream: https://gitlab.com/kicad/libraries/kicad-symbols and
https://gitlab.com/kicad/libraries/kicad-footprints
License: https://www.kicad.org/libraries/license/

`TIWARI.kicad_sym` contains one adapted KiCad symbol:
`FPGA_Lattice:ICE40UP5K-SG48ITR`, renamed with `_REVIEWED`. Pin 29 VCCPLL was
changed from power output to power input to match the Lattice datasheet.
This derived symbol retains the upstream library license/exception. Its use
here does not change the original board's CERN-OHL-P-2.0 license.

The generic AP2112 family symbols are instantiated with fixed 1.2V and 3.3V MPNs.
The generic TPS3808DBV symbol uses the fixed-threshold TPS3808G12DBVR ordering
code, and the generic x16 EEPROM symbol uses 93LC46BT-I/SN. Datasheet review and
BOM ordering codes matter; a generic symbol value is not a substitute part.

Datasheets are linked rather than redistributed. See `docs/Hardware.md` for
primary technical sources and assembly-specific requirements.

The included KiCad STEP models retain the same upstream library license and
exception. The generic QFN48 7mm visual model has a 5.15mm underside paddle;
it is used only for a visible package-body preview. The electrical land pattern
is the unaltered 5.6mm-paddle SG48 footprint selected by KiCad for this device.
Use the footprint/datasheet rather than the preview model for stencil or
assembly design. The 1x10 header STEP is the matching upstream library model.

`UP5K_SG48_Reviewed.kicad_mod` is the selected upstream SG48 footprint with
unchanged copper and paste geometry, the crowded silkscreen marker moved to
F.Fab, and the visual model reference localized. It retains the KiCad library
license and exception. These local adaptations do not change pin numbering.
