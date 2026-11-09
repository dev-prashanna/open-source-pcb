# Brushed motor mapping and hardware shutdown

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
