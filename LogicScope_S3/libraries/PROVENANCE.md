# Library provenance

The schematic uses installed KiCad 10 standard symbols and footprints, with
upstream CC-BY-SA-4.0 and KiCad library exception as reproduced in
`KiCad-LICENSE.md`.

- `LogicScope:SN74LVC245APW_A_TO_B`: graphics and pin placement derived from
  KiCad `74xx:74LS245`; fixed-direction electrical pin types and exact LVC part
  identification verified against TI SN74LVC245A PW/TSSOP-20 datasheet.
- `LogicScope:ESP32-S3-WROOM-1_Overhang`: identical copper, pads, courtyard,
  keepout and models to the installed `RF_Module:ESP32-S3-WROOM-1`; silk
  graphics that extend beyond the PCB edge moved to fabrication layer.
  ESP32-S3-WROOM-1-N8R2 pad map matches the manufacturer module drawing.
- `LogicScope:TestPoint_D0.5mm`: PCB-only circular 0.5-mm exposed copper probe
  feature, derived from KiCad's 1-mm test-point footprint; no solder paste,
  component purchase or assembly placement. USB probe features lie inline.

Other components use stock KiCad footprints, cross-checked against exact
manufacturer package drawings. Optional ESD arrays retain their verified
10-pin USON footprints and are DNP in the initial assembly.

- `LogicScope:Polyfuse_1206`: unchanged Device:Polyfuse pin geometry, with a
  package filter explicitly accepting the verified Littelfuse 1206 PPTC land.
  This resolves a generic symbol naming filter without disabling that check.
