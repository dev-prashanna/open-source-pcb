# RF-S3-A0 manufacturing readiness

Hardware engineering release completed on 2026-11-09 using KiCad 10.0.6.
The native project and fabrication exports are complete for engineering review.
Fabricator DFM, assembly process approval and physical qualification remain open.

| Check | Final result |
|---|---|
| Schematic ERC | 0 violations |
| PCB DRC, with zones refilled | 0 violations |
| Unconnected PCB items | 0 |
| Schematic/PCB parity | 0 issues |
| Independent connectivity audit | 15/15 checks passed; 396 mapped pins |
| Electrical manifest | 138 entries, 71 connected nets |
| Physical board | 142 footprints, six copper layers, 45 x 45 mm |
| Signal tracks on ground reference layers | 0 |
| Tracks beyond the antenna-side audit boundary | 0 |

Authoritative evidence is in [ERC](../reports/ERC.json),
[DRC](../reports/DRC.json), [connectivity](../reports/Connectivity_Audit.json),
[physical audit](../reports/Physical_Audit.json), and
[assembly audit](../reports/Assembly_Audit.json). These results use the project
rule configuration; the JSON reports explicitly list ignored check categories.
No clearance, missing-connection, or parity findings were waived for release.

## Fabrication handoff

- [Gerbers and Excellon drills](../fabrication/gerbers/) include all six copper layers, both masks, both legends and Edge.Cuts.
- [Schematic PDF](../fabrication/Schematic.pdf), [assembly drawing](../fabrication/assembly/Assembly.pdf), [placement export](../fabrication/assembly/Placement.csv), [BOM](../BOM.csv), and [grouped BOM](../BOM_Grouped.csv) accompany the native files.
- [SHA256SUMS](../fabrication/SHA256SUMS) identifies the source files, validation reports and manufacturing outputs used for this handoff. Paths are relative to the project directory.
- The BOM excludes PCB-only mounting holes and probe pads. Check the assembly placement export against the BOM before machine import; it also contains PCB-only footprints.

**Via filling and capping is a required process for this layout.** The assembly
audit identifies 54 board-via drills intersecting nominal SMD copper lands.
Have the fabricator resin-fill, planarize and copper-cap these vias, and review
the module/regulator footprint-integrated thermal vias and stencil apertures
with the assembler. Tenting alone does not address solder loss into these
holes. The audit uses copper lands; the assembler must also inspect the actual
soldermask openings and nearby via annuli. Connector plated holes and the four
NPTH mounting holes must retain their intended functions.

Obtain a qualified six-layer 1.0-mm stack with 0.125-mm tracks, 0.15-mm copper
spacing, 0.20-mm routing drills and 0.45-mm minimum via lands. Confirm these
minima, annular rings, fill/cap capability, stack tolerances and USB impedance
with the chosen fabricator before ordering. See [fabrication notes](Fabrication_Notes.md).

## Layout completion

The remaining signal, arming-latch, USB supply, sensor-supply and ground-island
connections were completed. Dangling routing remnants were removed, measured
clearances repaired, and the planes refilled. In1.Cu and In4.Cu remain ground
reference layers without signal tracks. The regulator PGND pad and the isolated
underside capacitor return now have explicit plane drops.

Silkscreen names the motor ports, battery, USB, arming link, KILL and expansion
interfaces. Dense references remain on Fab layers. The antenna overhang and
local silkscreen edits are explicit project-library assets; upstream pad
numbering and copper geometry are preserved. See
[footprint variant provenance](../libraries/Footprint_Variants.json).

The physical audit reports actual route lengths and neck widths. Mixed power
planes supplement routed supply copper; minimum track width alone does not
describe the complete current path. The USB VBUS contact branch includes a
2.5-mm-long 0.125-mm neck between CC2 copper and a locating hole; the lower
VBUS contacts also feed the main supply route. Validate connector current
sharing, voltage drop and temperature with the specified host load. USB data
impedance, routing discontinuities and enumeration require stack-specific
review and measurement.

## Qualification still required

No board has been fabricated or flown. Validate power-up, interlock fault
injection, converter transients, motor stall/thermal behavior, sensor axes and
noise, USB signal quality and radio performance using the
[bring-up procedure](Bringup_and_Validation.md). Proposed motor/load ratings
remain conditional on those measurements. The included firmware is an
unbuilt disarmed bring-up skeleton; flight control and its validation are
separate work described in [firmware architecture](Firmware_Architecture.md).

## Reproduce the release

Use a Python environment with KiCad 10 system bindings and requirements.txt:

```sh
python3 -m venv --system-site-packages .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/release.py
sha256sum -c fabrication/SHA256SUMS
```

The release script validates and exports the existing design. It stops before
export if ERC, DRC, parity or connectivity checks fail. Construction/routing
scripts are separate engineering tools and can overwrite the native design;
they are not prerequisites for checking or exporting this release.
