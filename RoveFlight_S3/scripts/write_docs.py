"""Generate pin contracts and engineering notes from the electrical manifest."""
from cadlib import *
from collections import defaultdict
parts=json.loads((ROOT/'design.json').read_text());u=next(c for c in parts if c['ref']=='U1');names=pinmap('RF_Module','ESP32-S3-WROOM-1');groups=defaultdict(list)
for c in parts:groups[(c['mpn'],c['value'],c['fp'],c['mfr'])].append(c['ref'])
with (ROOT/'BOM_Grouped.csv').open('w') as f:
 w=csv.writer(f);w.writerow(['Quantity','References','Value','MPN','Manufacturer','Footprint'])
 for (mpn,val,fp,mfr),refs in groups.items():w.writerow([len(refs),','.join(refs),val,mpn,mfr,fp])
rows=[]
for pin,net in u['nets'].items():
 name=names[pin]
 if name.startswith('IO'):gpio=int(name[2:])
 elif name=='USB_D-':gpio=19
 elif name=='USB_D+':gpio=20
 elif name=='RXD0':gpio=44
 elif name=='TXD0':gpio=43
 else:continue
 rows.append((gpio,pin,net))
rows.sort()
with (ROOT/'GPIO_Allocation.csv').open('w') as f:w=csv.writer(f);w.writerow(['GPIO','Module_pad','Net']);w.writerows(rows)
text='# GPIO allocation\n\nExact module: ESP32-S3-WROOM-1-N8R2. USB is GPIO19/20. ADC monitoring uses ADC1 GPIO1/2. GPIO0 is BOOT; GPIO3/45/46 are unused strapping pins. GPIO35/36/37 are unused, allowing a conservative allocation around memory variants. Module flash/PSRAM pins not exposed as general-purpose signals are never assigned. Do not substitute a module variant without repeating the memory and pin review.\n\n| GPIO | Module pad | Net |\n|---:|---:|---|\n'
text+=''.join(f'| {g} | {p} | {n} |\n' for g,p,n in rows)
text+='\nGPIO38 receives a low-to-high arm pulse only after health checks; GPIO39 sends falling watchdog edges from the healthy control task. GPIO40 is configured OPEN DRAIN and LOW before any PWM setup, then released only for deliberate arming. GPIO4–7 PWM and their buffer inputs have external pulldowns. RC UART on GPIO41/42 is separate from debug UART GPIO43/44. The single external SPI expansion shares the IMU/barometer bus; bound its transaction latency.\n'
(ROOT/'docs/GPIO_Allocation.md').write_text(text)
with (ROOT/'Connector_Pinouts.csv').open('w') as f:
 w=csv.writer(f);w.writerow(['Reference','Function','Pin','Signal'])
 for c in parts:
  if c['ref'].startswith(('J','TP')):
   for pin,net in c['nets'].items():w.writerow([c['ref'],c['value'],pin,net])
(ROOT/'docs/Motors_and_Safety.md').write_text('''# Brushed motor mapping and hardware shutdown

Board forward is toward the ESP32 antenna, the top edge in the front view. Motor directions below are viewed from above. Reverse the two motor wires to change rotation; this low-side circuit cannot reverse electrically. Use matched CW/CCW motors and appropriate propellers.

| Motor | Position | Pads | Rotation viewed from above | PWM GPIO |
|---|---|---|---|---:|
| M1 | Front left | J3: 1 VM+, 2 switched negative | CCW | 4 |
| M2 | Front right | J4: 1 VM+, 2 switched negative | CW | 5 |
| M3 | Rear right | J5: 1 VM+, 2 switched negative | CCW | 6 |
| M4 | Rear left | J6: 1 VM+, 2 switched negative | CW | 7 |

These are four independent brushed stages, not brushless ESCs. Each uses AO3400A, 100-ohm gate resistor, 10-kohm gate-source pulldown, input pulldown and SS24 flyback diode (cathode VM). Add a 100-nF capacitor directly across each motor's terminals and twist the motor leads; board capacitors cannot replace suppression at the brushes.

## Operating envelope and thermal calculation

No motor/propeller was specified. The design envelope is a 1S motor rated for 4.2 V maximum battery voltage, no more than 1 A running per channel, 4 A aggregate running, and no more than 2 A single-channel stall for 100 ms. These are engineering limits to qualify, not verified ratings for an unspecified motor. Simultaneous stalled motors and static high-duty operation require shutdown; a fuse alone is too slow to protect a small motor. Measure running and locked-rotor current with the actual propeller, battery, wiring and cooling before fitting flight propellers.

AO3400A has 48-milliohm maximum RDS(on) at 2.5-V gate drive, rather than relying on its headline current rating. Taking 1.7 times that resistance as a hot-device estimate gives 81.6 mW at 1 A and 326 mW at 2 A. With a conservative 125 C/W junction-to-ambient estimate, those imply about 10 C and 41 C rise at full duty, before board heating and switching loss. This is a calculation, not a thermal measurement. A 6-nC gate-charge scale gives 96 uA average gate charge current per channel at 16 kHz. Initial PWM is 16 kHz; scope switching loss and drain overshoot before raising it. At 1-A motor current and 50% off time, a 0.5-V flyback estimate gives 0.25 W diode dissipation per channel. Diode and common-board heating can dominate MOSFET conduction loss.

## Interlock behavior

U7 SN74LVC125A only connects PWM to motor gates when MOTOR_OE_N is low. The removable JP1 shunt connects that enable to the inverted output of U6's arming latch; removing JP1 leaves the enables pulled high. Gate and PWM-input pulldowns hold motors off during reset and unpowered/disabled-buffer states.

SAFE_CLR_N asynchronously clears U6 and is pulled low by U4 watchdog timeout, U5 VM undervoltage/reset supervisor, USB VBUS through Q2, SW3 KILL, or firmware's open-drain KILL_OD. U5 manual reset is tied to ESP EN. USB insertion therefore prevents arming even if a battery is attached. A new rising ARM_CLK is needed after any detected clear condition. Do not automatically rearm after heartbeat recovery or undervoltage recovery.

The TPS3431 uses 1 nF on CWD: approximately 132.4 ms nominal timeout (119.82–144.98 ms before capacitor tolerance), followed by its reset pulse. Heartbeat falling edges should be supplied at most 20 ms apart only by a control task that has completed valid sensing, command-age and control checks. A peripheral-generated heartbeat could continue after a software failure and is prohibited. VM undervoltage trips at approximately 0.405*(1+665k/100k) = 3.098 V, before component tolerances, with roughly 50 ms release delay from 10-nF CT. Instantaneous load dips can deliberately latch disarmed. SW3 provides an independent physical kill; it is not a radio emergency-stop system.

Internal ESP software/brownout resets do not necessarily pull external EN low. PWM pulldowns provide the reset default; firmware must assert KILL_OD as its very first GPIO action on every boot and never restore an old armed state. Wireless command loss still requires firmware to assert KILL_OD immediately; the external watchdog independently bounds a stopped control task. Neither mechanism substitutes for fault-injection testing.

For an initial X mixer in forward/right/down coordinates: M1=T+R+P+Y, M2=T-R+P-Y, M3=T-R-P+Y, M4=T+R-P-Y. Here positive yaw is clockwise viewed from above and CCW rotor reaction torque produces positive yaw. Verify each sign, motor number and thrust response without propellers, then on a restrained thrust stand. Saturation handling, filtering and controller stability are firmware work.
''')
(ROOT/'docs/Power_Architecture.md').write_text('''# Battery, motor and logic power

J2 uses solder pads: pin 1 BAT_RAW positive, pin 2 GND. Fit a keyed, externally insulated harness and a protected 1S LiPo, 3.1–4.2 V operating target. There is no charger, cell protector, balancer or fuel gauge. Use a suitable external 1S charger with the pack disconnected. F1 is a 5-A catastrophic-fault backup, not a precision current limiter or deep-discharge protector.

Power path: BAT_RAW -> F1 -> reverse-connected Q1 DMP2008UFG -> BAT_PROTECTED -> R100 5-milliohm shunt -> VM. VM feeds all motor positive pads, flyback cathodes and the logic-input Schottky diode D1. USB VBUS feeds SYS_IN through D2. The diode cathodes meet at SYS_IN; USB cannot feed VM or charge the battery. Q1 drain is on the raw/fused side and source on the protected side so its body diode starts conduction only for correct polarity. Its 9.8-milliohm maximum at -2.5-V gate drive gives 157 mW at 4 A before hot-resistance increase; 1.7 times resistance gives 267 mW. Review copper area and measured temperature.

R100 produces 20 mV and dissipates 80 mW at 4 A; its 0.25-W rating is not the claimed 1-W rating of some other 1206 shunts. INA180A2 gain 50 yields 0.25 V/A, giving 1.0 V at 4 A, 1.5 V at 6 A and 2.0 V at 8 A. Use Kelvin sense pickoff at the shunt pads. ADC1 GPIO1 receives the filtered current output. ADC1 GPIO2 sees VM divided by two (2.1 V at 4.2-V battery), plus a 1-kohm/100-nF filter. ADC calibration and sense-amplifier offsets must be measured; this is not a calibrated coulomb counter.

TPS63001DRCR makes fixed 3.3 V using a 2.2-uH IFSC1515AHER2R2M01 inductor, rated 3.1 A for the manufacturer's stated saturation/thermal definitions. It is a buck-boost, allowing operation across the 3.3-V crossing of a 1S pack. PS/SYNC is high for forced PWM. VINA is separately filtered through 100 ohms and 100 nF. Input/output ceramics follow the TI reference network, with extra local MCU bulk. A ferrite and local capacitance filter +3V3_SENS; ground remains common.

Budget a maximum 650-mA 3.3-V load, including module, sensors and external interfaces, rather than equating the converter's 1.8-A switch limit with output current. At 650 mA the load is 2.145 W. Assuming 85% efficiency gives 0.379 W converter loss and about 0.953 A input at 2.65 V after the battery diode. These efficiency and thermal values are assumptions to verify. At 500 mA, loss is about 0.291 W under the same assumption. TI specifies up to 800 mA in boost for input above 2.4 V; this sets useful but conditional margin. Diode drop, battery sag and switching peaks must be measured together. Keep total external accessory draw below 50 mA until characterized.

The logic rail has two 22-uF output ceramics, MCU-local ceramic bypassing and a 100-uF polymer bulk capacitor. For an idealized 400-mA step over 20 us, 100 uF alone gives 80 mV droop, plus ESR and distribution impedance; ceramic bias derating and control-loop response matter. This calculation does not establish transient compliance. Measure rail minimum at the ESP supply pads with simultaneous Wi-Fi transmission and motor steps. USB firmware must respect host current entitlement and keep wireless/current-heavy accessories disabled before configuration or use an appropriate powered host.

## Copper and return paths

Six copper layers: F.Cu components/signals and local motor copper; In1.Cu continuous GND; In2.Cu perimeter VM distribution, central 3.3-V/filtered-sensor copper and local signal routes; In3.Cu additional signals; In4.Cu ground reference; B.Cu components/signals and GND fill. No signal tracks are allowed on In1.Cu or In4.Cu; In2.Cu is shared with local signal routes. Final filled-zone connectivity must preserve every motor supply connection. Multiple through-vias connect motor positive pads, MOSFET sources, battery return and bulk capacitors to their respective planes. High-current motor loops remain around the perimeter, with the IMU and filtered sensor supply nearer the center. A common plane avoids an impedance-producing split beneath sensor signals, but common-impedance motor noise still needs bench measurement.

For 35-um copper, a 20-mm-long, 1-mm-wide trace has about 9.8 milliohms resistance at 20 C (copper resistivity 1.72e-8 ohm-m). At 1 A this is 9.8 mV/9.8 mW; at 2 A, 19.6 mV/39 mW. The VM plane carries aggregate current; do not replace it with a single 1-mm track. Trace temperature rise depends on copper spreading, stack, air flow and nearby heat, so resistance estimates do not certify ampacity. Check actual routed necks and via counts in the physical audit.
''')
(ROOT/'docs/Sensors_and_Mechanics.md').write_text('''# Sensor and mechanical integration

The board is 45 x 45 mm with chamfered corners, four M2 clearance holes at (9.75,9.75), (35.25,9.75), (9.75,35.25), (35.25,35.25) mm: a 25.5-mm square pattern. Nominal finished thickness is 1.0 mm. The ESP antenna overhangs the forward edge by 6.75 mm, so the assembled envelope extends beyond 45 mm. Confirm frame, propeller arcs, USB cable and standoff clearances before fabrication. This mounting pattern is a choice for the prototype, not a claim of compatibility with every 25.5-mm frame.

BMI270 U8 is fixed near board center at (22.5,23) mm on the front, 0-degree rotation, pin 1 toward forward-left. Its native +X points forward (toward decreasing KiCad Y), +Y points left (decreasing KiCad X), and +Z points out of the front face. For forward/right/down flight coordinates, apply (x,y,z)=(sensor_x,-sensor_y,-sensor_z) to both accelerometer and gyro; bench-verify all six static faces and signed rotations. A flat face-up accelerometer should report approximately -g on the body-down axis. Use compliant mounting grommets and restrained motor wires; MEMS isolation cannot be solved by schematic choice alone.

BMI270 was selected for a compact 3 x 2.5-mm, 14-pad package, 10-MHz SPI, FIFO, interrupt and Bosch's maintained configuration/driver interface. Its accelerometer ODR tops out at 1.6 kHz while gyro supports 6.4 kHz; begin at a 1-kHz control loop, not an assumed 8-kHz loop. Initialization requires the correct Bosch configuration image. ICM-42688-P was evaluated as a stronger high-rate alternative (up to 32-kHz ODR and 2.8-mdps/sqrt(Hz) gyro-noise figure), at the cost of a different driver/footprint qualification. LSM6DSR offers an extended 4000-dps gyro range, but its different package and driver do not provide an immediate advantage for this first bounded-rate prototype. These parts are not drop-in substitutions.

BMP390 U9 is on the underside, away from the main switching converter and exposed motor terminals; actual placement is in Placement.csv. Use a vented enclosure pocket with a small protected atmospheric opening and breathable open-cell foam over, but not sealing, its pressure port. Keep the foam clear of the component lid port and ToF optical windows. Do not drill through the sensor, coat the port, wash it with unapproved processes or place hot batteries directly below it. Propeller airflow and PCB self-heating can still bias altitude; characterize offsets under motor load. Pressure-derived altitude needs firmware calibration and filtering.

VL53L1X U10 faces downward on B.Cu. Reserve a clear optical cone around its transmitter and receiver and a matte separation baffle in any cover; follow ST cover-glass calibration guidance. It is near-ground ranging for landing experiments, not reliable obstacle avoidance. Enable the required 2V8 I/O setting when supplied at 3.3 V. TSOP75438TT U11 also faces the underside for 38-kHz remote-protocol experiments. Its TT top-view mounting and single pad row must not be replaced with a TR side-view part without a mechanical review. A separate reflectance emitter/detector was omitted because the ToF already provides the useful short-range experiment without extra emitter current or board area.

An onboard compass is deliberately omitted. Four nearby motor supply/return paths and ferrous motor cans make heading calibration load-dependent. The I2C connector permits an external, physically separated 3.3-V magnetometer if required. J8 accepts an external PMW3901-based optical-flow module with the correct supply conversion, SPI-level compatibility, downward lens and working-distance specification; the raw sensor requires its own optical/mechanical design. There is no claim of onboard optical-flow measurement.
''')
(ROOT/'docs/Firmware_Architecture.md').write_text('''# Recommended ESP-IDF architecture

This deliverable is hardware. Attitude estimation, PID, motor mixing, altitude estimation, calibration, logging, OTA, telemetry, configuration and failsafe policy require firmware and validation. It is not compatible with arbitrary existing flight-controller firmware without a board port.

Use ESP-IDF for the exact ESP32-S3 N8R2 memory configuration. Keep the control stack, ISR buffers and time-critical data in internal RAM; use PSRAM for noncritical logs and telemetry. Native USB Serial/JTAG handles programming/debugging; UART0 on J9 is an independent recovery route. Reserve flash partitions for NVS configuration, two OTA application slots and optional bounded logging. Never perform OTA, flash erase or PID parameter persistence while armed.

Suggested modules: board_pins, motor_interlock, motor_pwm, bmi270_spi, bmp390_spi, vl53l1x_i2c, battery_adc, receiver_uart, optical_flow_spi, ir_receiver, attitude_estimator, rate_pid, attitude_pid, mixer, safety_state, telemetry, configuration and flight_log. Use vendor sensor drivers under their licences; verify SPI dummy bytes, configuration blob, FIFO timestamps and sensor identity at startup.

Startup order: assert GPIO40 KILL_OD open-drain LOW first; set ARM_CLK LOW; set all PWM inputs LOW; initialize motor timers with zero duty; initialize/calibrate sensors; validate supply and command input; test watchdog and interlock feedback; release KILL only while disarmed. Require an explicit user arm action plus all health checks before a single ARM_CLK rising edge. Read the ARMED test point during commissioning; no GPIO feedback is assigned for it in this revision. After any reset or fault, discard old commands and require manual rearm.

A high-priority local task on one core waits for IMU data-ready, reads timestamped SPI data, checks sample age, runs an attitude estimator and cascaded angle/rate control, bounds the mixer, updates four hardware PWM duties, validates control input age and supply limits, then toggles heartbeat. Begin at 1 kHz and 16-kHz PWM; measure worst-case execution time and jitter before changing rates. Do not feed the watchdog from an independent timer ISR. Wi-Fi/BLE/ESP-NOW telemetry and configuration run at lower priority on the other core. Attitude stabilization never depends on a smartphone or wireless packet arrival.

Use a state machine: BOOT -> SENSOR_CHECK -> DISARMED -> ARMED -> FAULT_LATCHED. On invalid IMU, stale command (>100 ms initial target), brownout warning, current violation, task deadline miss or user kill, assert KILL_OD immediately, set all PWM duties zero and stop watchdog edges. Do not use the 132-ms external watchdog as the normal radio-loss response. Recovery goes through DISARMED with deliberate rearm. Abrupt motor shutdown is a containment policy for an experimental aircraft; safe behavior in free flight needs a broader system safety review and restrained testing.

Store validated PID gains, calibration matrices, battery/current thresholds, radio settings, maximum duty, sample rates and failsafe timeouts with versioning and range checks. Change safety-critical parameters only while disarmed. Calibrate ADC against external meters, gyro bias at rest, accelerometer six-face alignment, barometer pressure/temperature drift and ToF offset/crosstalk. No untested PID gains are supplied.

RC interface J7 is 3.3-V UART with a 3.3-V accessory rail. Suitable CRSF/iBUS receivers must meet those electrical limits; receivers needing 5 V need a separate supply, and SBUS needs suitable inversion/level handling. Do not attach a 5-V UART directly. Bound external optical-flow SPI transactions so they cannot stall the IMU task.
''')
print('Wrote BOM grouping, pin contracts and engineering documents')
