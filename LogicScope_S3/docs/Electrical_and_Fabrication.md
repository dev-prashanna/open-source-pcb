# Electrical and fabrication decisions

The board targets 55 x 40 mm, two copper layers and 0.8-mm nominal finished
thickness. Parts are assembled on the front. The ESP32 PCB antenna overhangs
the forward edge by 6.75 mm; allow that additional assembled envelope and keep
the enclosure, wiring and nearby metal clear of the antenna. Its official
all-copper keepout remains in the native footprint.

## Input front end

[TI's SN74LVC245A datasheet](https://www.ti.com/lit/ds/symlink/sn74lvc245a.pdf)
specifies 5.5-V-tolerant inputs with 3.3-V supply and partial-power-down Ioff.
The selected SN74LVC245APW is the tube-packed PW/TSSOP-20 version. Its fixed
A-to-B direction is explicit in the schematic symbol and wiring; do not
substitute HC/HCT/LS logic. Each input has 220 ohms in series and 100 kilohms
to ground. There is no deliberate input-filter capacitor or analog front end.
The digital thresholds are fixed, rather than adjustable to an external VREF.

Optional U5/U6 [TPD4E05U06DQAR arrays](https://www.ti.com/lit/ds/symlink/tpd4e05u06.pdf)
are DNP in the baseline BOM. They have roughly 0.5-pF typical channel loading
and 5.5-V standoff. Their approximately 10-V transient clamping behavior is an
ESD-current diversion characteristic, not a precision 5-V voltage clamp.
Population requires prototype ESD verification; neither they nor the series
resistors provide industrial overvoltage, negative-voltage, mains or surge
protection. The specified measurement range remains ground-referenced 0–5 V.

Both input headers follow Connector_Pinouts.csv exactly. Connect ground before
signals. J2 pin 7 is a 3.3-V reference through 10 kilohms, limiting a shorted
reference to about 330 microamps; it is not a target-board supply. J2 pins 9
and 10 are intentionally unconnected. No header exports USB 5 V.

## USB

The GCT USB4105-GF-A pin numbering and lands were checked against the
[manufacturer drawing B3](https://www.mouser.com/datasheet/2/837/Global_Connector_Technology_usb4105-3106202.pdf).
Both D+/D- contact pairs and all supply/ground contacts are wired. Each CC pin
has its own 5.1-kilohm Rd. The shield is bonded to board ground.

U4 is [TPD2E2U06DCKR](https://www.ti.com/lit/ds/symlink/tpd2e2u06.pdf), SC70-3:
pin 1 IO1, pin 2 IO2, pin 3 GND. The two channels have 1.5-pF typical
capacitance and 5.5-V standoff. TI specifies 9.7-V clamping at 1-A TLP
and 12.4 V at 5 A; this is transient protection, not a 5-V precision clamp.
It requires no VBUS connection. Ground return
is short and tied to the reference plane. The 22-ohm damping resistors are
0402 parts close to the module. USB probe pads are inline original 0.5-mm PCB
features; they add no off-route test stubs and are excluded from the BOM.

The principal differential geometry uses 0.75-mm traces and 0.17-mm edge gap
over the bottom ground reference, with short necks at the contacts and device
pads. This is an approximately 90-ohm **design target**, not a measured or
field-solver-certified impedance. Obtain a stack-specific impedance check,
including actual dielectric thickness, copper and soldermask, from the
fabricator. Review enumeration and signal quality on a physical board.

The standard connector land pattern has 0.1944-mm nominal copper clearance to
its locating holes. A documented component-internal rule permits 0.18 mm
between J3's own pads/holes; unrelated routing retains 0.25-mm copper-to-hole
clearance. Confirm that capability with the fabricator. The rule is not an
exclusion of electrical shorts or missing connections.

## Supply and thermal budget

USB 5 V enters a 500-mA resettable fuse and the
[AP63203WU-7 synchronous buck](https://www.diodes.com/assets/Datasheets/AP63200-AP63201-AP63203-AP63205.pdf).
Its exact TSOT-23-6 pins are FB=1, EN=2, VIN=3, GND=4, SW=5 and BST=6.
The fixed-output FB senses 3.3 V. The network includes 10-uF input bypass,
100-nF local input and bootstrap capacitors, a 4.7-uH inductor and two 22-uF
output ceramics. These are component nominal capacitances; account for bias
derating in transient tests.

Budget 350 mA sustained and 500 mA transient on 3.3 V, subject to USB host
entitlement and measurements. At the 500-mA budget, output power is 1.65 W.
Assuming 85% efficiency, total converter loss is 0.291 W and input current is
0.446 A at a pessimistic 4.35-V fused input. Applying the datasheet 89 C/W
reference thermal figure to all of that loss gives a conservative calculated
26 C rise; the real PCB requires measurement. The converter's 2-A headline is
not a permitted USB load rating for this board.

[SRN4018-4R7M](https://www.bourns.com/docs/product-datasheets/srn4018.pdf) is
4.7 uH with 2.0-A saturation and 1.9-A RMS reference ratings, well above the
initial load budget. Its maximum DCR is 84 milliohms, corresponding to about
21 mW DC winding loss at 500 mA, before ripple loss. Inductor and converter
ratings still depend on temperature and layout.

Firmware must keep radios off during acquisition, respect USB pre-enumeration
and suspend current, and avoid current-heavy activity before configuration.
Verify startup inrush, fuse voltage drop/derating, rail transients and USB
suspend behavior with real hardware. The power LED uses 4.7 kilohms to keep
its static current small. There is no battery, charger or external target
power output.

## Ground and routing

The bottom layer is a connected ground plane with short local signal
bypasses. The USB differential pair and eight buffer-to-MCU data routes stay
on the front without vias. Rear bypasses are kept outside their return
corridors. Front ground islands are stitched to the rear plane. Review the
final physical audit for rear coverage, actual trace lengths and via count.

## Manufacturing process

Specify two-layer FR4, 0.8-mm nominal thickness, nominal 35-micrometre copper,
0.15-mm minimum track/copper spacing, and the stack-specific USB impedance
review. Routing vias use 0.60/0.30-mm and localized 0.50/0.25-mm lands/drills. The standard module
footprint additionally contains 0.20-mm thermal drills; the manufacturer and
assembler must review its windowed paste apertures, via tenting/filling and
module reflow process. Do not silently enlarge those thermal drills.

The two 2.2-mm mounting holes are nonplated. Check the USB stake protrusion,
header solder tails, cable access and antenna overhang in the enclosure.
TIWARI appears as etched front-copper lettering and readable silkscreen in a
reserved clear area; it does not cut the rear ground plane. Fabrication DFM,
electrical bring-up and acquisition/USB performance testing remain necessary
before a production order or performance claim.
