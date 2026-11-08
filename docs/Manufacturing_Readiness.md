# Manufacturing readiness — A.0 engineering prototype

The editable board is fully routed and checked against its schematic. This is an unbuilt engineering prototype. The checked-in ERC, DRC, connectivity and physical audit reports describe the delivered files; they do not establish tested hardware performance.

## Recorded checks

- KiCad 10 DRC includes schematic parity. No remaining unconnected copper or schematic-to-board differences are accepted by the export script.
- The independent manifest audit checks 220 electrical entries (217 fitted parts and three service pads), 682 connected pins and 186 nets against the exported schematic and board pad nets.
- The physical audit records routed widths and lengths, decoupling distances, layer use and placement. In1.Cu has no signal traces; the RF keepout has no routed traces.
- ERC retains three warnings: U8 SDO/SA0, U9 SDO/SA1 and U10 SDO are bidirectional library pins strapped to ground for I2C address selection. Their SPI-output function is unused in this I2C design. The warning arises from the ground power flag. These warnings are not excluded or hidden.
- Project-local footprints preserve the existing assembly geometry and layout-specific silkscreen adjustments. The ESP32 footprint also retains the antenna keepout. Original manufacturer geometry and upstream model references remain reviewable in the local libraries.

## Fabrication and assembly review

Use the four-layer stack, process minima, antenna clearance, two-sided assembly and filled/capped via requirements in [Fabrication_Notes.md](Fabrication_Notes.md). The final added ground stitch is at (52.2, 28.6) mm with a 0.50 mm land and 0.25 mm drill; review nearby B.Cu capacitor solder-mask geometry with the assembler. Gerbers are engineering build outputs, not a tested production release.

Before ordering, review the actual supplier stack and trace impedance, current capacity of power-route necks and connectors, regulator switching loops, motor transient paths, thermal-via/stencil treatment and component availability. Netclass preferred widths do not guarantee that every local escape uses that width; inspect Physical_Audit.json.

## Physical validation still required

Follow [Bringup_and_Calibration.md](Bringup_and_Calibration.md) on a small engineering lot. Measure rail startup/ripple and source switching, USB enumeration/programming, battery ADC calibration, motor and servo load steps, driver/regulator temperatures, sensor readings and I2C rise times. Verify RF performance with the intended enclosure and cabling. Validate ESD/EMC behavior and applicable compliance before production. No fabricated-board, thermal, transient, RF or compliance test results are claimed.
