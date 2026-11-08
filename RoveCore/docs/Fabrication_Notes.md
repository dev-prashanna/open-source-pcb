# P-TIWARI fabrication and assembly notes

Engineering prototype A.0. Do not interpret Gerber availability as production approval.

- Outline: 80 × 65 mm with 1.5 mm corner chamfers; four 2.7 mm nonplated M2.5 holes, centers (3.5,3.5), (76.5,3.5), (3.5,61.5), (76.5,61.5), in board coordinates.
- Nominal finished thickness: 1.6 mm. Four copper layers: F.Cu components/signals/power, In1.Cu ground reference, In2.Cu sensor power plus routed signals, B.Cu components/signals/power/ground fill.
- Use a fabricator-qualified four-layer stack with 1 oz nominal copper. Request an outer-layer-to-reference spacing near 0.10 mm where practical, with the central core adjusted for total thickness; final impedance geometry must be confirmed with that fabricator. A nominal stack is not an impedance measurement.
- Minimum process capabilities: 0.125 mm traces, 0.15 mm copper spacing, 0.20 mm plated thermal holes; ordinary routing vias 0.30 mm drill / 0.60 mm land, except two 0.59 mm lands preserving clearance. Minimum copper-to-edge clearance is 0.25 mm, needed at module edge pads near the antenna overhang.
- Keep the ESP32 antenna outside the PCB/chassis ground plane and retain the all-layer library keepout. No metal enclosure, battery, cabling, mounting bracket or copper extension may be added near the antenna without RF review.
- The ESP32 and motor-driver library thermal-via structures must be reviewed with the assembler for solder wicking, stencil apertures and any required plugging. Most new stitching vias are outside ordinary SMD solder pads. Two deliberate 0.50 mm land / 0.25 mm drill via-in-pad escapes are at U7 pad6 (63.1375, 52.975 mm) and U19 pad27 (52.8625, 34.425 mm). These two vias must be resin-filled and copper-capped for reliable solder assembly; quote this process explicitly. Footprint-specified thermal vias remain. Do not silently remove thermal vias or enlarge the thermal paste area.
- Components occur on both faces, including tall polarized capacitors. Confirm underside mechanical clearance and support during reflow and chassis assembly. Inspect Place­ment.csv rather than assuming a single-sided assembly.
- Suggested finish: ENIG. A dark-blue or black solder mask and white silkscreen suit the P-TIWARI identity; color choice does not alter the electrical design.
- Standard lead-free reflow must respect the most restrictive sensor and module handling requirements. Optical/MEMS parts require moisture and contamination control. Do not coat or obstruct the BME280 pressure port, ToF windows, ambient-light aperture or RF antenna.
- Verify VEML7700-**TT** orientation against the Vishay top-view drawing; the TR side-view package is not approved as an assembly substitution.
- Check pin-1, diode polarity, capacitor polarity, module antenna orientation, MOSFET pin mapping and connector cable orientation on an assembly sample.
- Choose mating servo headers/shunts for the aggregate current, and appropriately rated power terminals and wire gauge. Reverse-polarity protection on inputs does not protect incorrectly wired servo or motor-output harnesses.

The manufacturing assessment lists outstanding review and physical-validation gates. First build should be a small engineering lot with current-limited bring-up, not a production order.
