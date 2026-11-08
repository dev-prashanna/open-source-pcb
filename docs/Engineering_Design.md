# P-TIWARI — Integrated Robotics & IoT Platform

Revision A.0, 8 November 2026. Design identity: **PTW-ESP32-ROB-A0**.
Core philosophy: **Plug in, program, and build.**

This is an original electrical design implemented as editable KiCad schematics and a native PCB. KiCad MCP created the project and controller, and inspected the resulting hierarchy. Native KiCad library and pcbnew automation builds the remaining circuitry, placement and copper; an external router assists routing. The actual KiCad netlist and DRC, rather than the construction scripts, determine connectivity and clearance results. The saved reports describe validation achieved; no physical boards have been tested.

## Controller selection

Use **ESP32-WROOM-32E-N8**, 8 MB flash, no PSRAM. N4 and N16 offer different flash capacities; R2 variants have PSRAM and different GPIO restrictions and are not approved substitutions. The installed KiCad RF_Module symbol and footprint support the selected module. ESP32-S3 offers native USB and more resources but drops Bluetooth Classic; ESP32-C3 also lacks Classic and has fewer pins. Retaining Classic alongside BLE and 2.4 GHz Wi-Fi justifies the WROOM-32E and a CP2102N USB bridge. OTA is a firmware function; two application slots must be configured in the 8 MB flash. See [Espressif module datasheet](https://documentation.espressif.com/esp32-wroom-32e_esp32-wroom-32ue_datasheet_en.pdf).

The EN pin has a 10 kΩ / 1 µF reset network, IO0 a pullup and boot switch, and GPIO12 a pulldown to select the correct flash supply. The crossed two-transistor reset/boot circuit follows the [Espressif DevKitC reference](https://dl.espressif.com/dl/schematics/esp32_devkitc_v4-sch.pdf). GPIO6–11 and module NC pads are not offered as GPIO. The antenna projects beyond the board edge, with its library copper/component keepout retained on all layers; enclosure and chassis clearance still require review against [Espressif layout guidance](https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32/pcb-layout-design.html).

## Motor-driver choice

TB6612FNG offers a wider motor-voltage range but no adjustable winding-current regulation. DRV8833PWPR supplies two bridges with current chopping, sleep, fault output, overcurrent and thermal protection, with fewer control pins. The **PWP PowerPAD package** is essential: the uncooled PW variant has a much lower continuous-current capability. Selected 0.25 Ω shunts set approximately 0.8 A winding-current regulation. The recommended board load is **0.6 A continuous per motor**, subject to temperature testing; headline IC peak ratings are not a board rating. The design is aimed at small gearmotors, not large high-stall-current motors. See [TI DRV8833 datasheet](https://www.ti.com/lit/ds/symlink/drv8833.pdf).

VM enters through a dedicated reverse-protected fused connector. It is electrically separate from regulated logic and servo supplies, sharing the ground reference. Local charge-pump, VINT, ceramic and 470 µF bulk capacitors are included. A firmware command alone is not emergency-stop protection: disconnect VM for a hardware stop. Use a battery or other source that can absorb regenerated energy. The capacitor is not an active braking clamp.

## Integrated sensor selection

| Function | Selected part | Interface/address | Design decision |
|---|---|---|---|
| Accelerometer + gyro | LSM6DS3TR-C | I²C 0x6A; INT1 GPIO32 | Current ST family, integrated FIFO; existing KiCad LSM6DS3 pin map and LGA match |
| Compass | LIS3MDLTR | I²C 0x1C | Separate device permits placement away from power circuitry |
| Temperature / humidity / pressure | BME280 | I²C 0x76 | Direct 3.3 V operation; pressure opening must remain exposed |
| Ambient light | VEML7700-TT | I²C 0x10 | Distinct address, low power, top-view optical package |
| Distance | VL53L1CXV0FY1 | I²C 0x29 | Direct sensor, shutdown and interrupt accessible through expander |
| Analog expansion | ADS1115IDGSR | I²C 0x48 | Four analog inputs independent of ESP32 ADC2/Wi-Fi sharing |
| Servo PWM | PCA9685PW,118 | I²C 0x40 | Four servo channels, independent of ESP32 PWM timing |
| GPIO expander | MCP23017-E/SS | I²C 0x20 | Slow controls and eight expansion outputs/inputs |

PCA9685 also responds to default all-call address 0x70; disable that response when necessary. Other listed addresses are 7-bit addresses. No duplicated onboard address exists.

LSM6DS3TR-C is a deliberate alternative to BMI270: verified library support avoids a new MEMS land pattern and a BMI270 configuration-blob dependency. The LSM6DS3 symbol has the same 14-pin assignment; no auxiliary sensor bus is used. Compass reserved pins are grounded and its C1 capacitor is fitted. The VEML7700 is the only new symbol/footprint: the project-local library follows Vishay's top-view package, 1.27 mm pitch and 0.7 × 1.6 mm pads. Its pin map and assembly orientation need an independent library review before release.

Sensor sources: [ST IMU](https://www.st.com/resource/en/datasheet/lsm6ds3tr-c.pdf), [ST magnetometer](https://www.st.com/resource/en/datasheet/lis3mdl.pdf), [Bosch BME280](https://www.bosch-sensortec.com/media/boschsensortec/downloads/datasheets/bst-bme280-ds002.pdf), [Vishay light sensor](https://www.vishay.com/docs/84286/veml7700.pdf), [ST distance sensor](https://www.st.com/resource/en/datasheet/vl53l1x.pdf), [TI ADC](https://www.ti.com/lit/ds/symlink/ads1115.pdf).

The sensor branch uses a ferrite bead and local bypass capacitors rather than being wired directly to the high-current input domains. Firmware must select the VL53L1X's 2V8 I/O mode for this 3.3 V implementation, and use open-drain emulation on its XSHUT control. The optical aperture points normal to the PCB, not parallel to the board. Mount the board accordingly or use the ultrasonic connector for forward ranging on a horizontal chassis.

## Interface details

Encoder inputs have 10 kΩ pullups, 1 kΩ series resistance, 100 pF filtering and individual Schmitt buffers. The SN74LVC1G17 accepts signals up to 5.5 V while operating from 3.3 V; only these buffered inputs and ultrasonic ECHO have this level tolerance. Connector encoder power is still 3.3 V. See [TI input-buffer datasheet](https://www.ti.com/lit/ds/symlink/sn74lvc1g17.pdf).

The ultrasonic TRIG signal and four servo signals pass through AHCT buffers powered from BAT5, producing proper 5 V logic. Servo power is a different net, SERVO5. BAT5 requires battery power even when the servo power selector uses an external source. GPIO15's pullup holds servo outputs disabled at reset. Set valid PCA9685 pulse registers before enabling outputs; do not use its default waveform blindly. All PCA9685 PWM channels share one frequency. See [NXP PWM driver](https://www.nxp.com/docs/en/data-sheet/PCA9685.pdf) and [TI AHCT buffer](https://www.ti.com/lit/ds/symlink/sn74ahct1g125.pdf).

The USB-C connector has two independent CC pulldowns, USBLC6 data-line protection and a self-powered CP2102N. Its VBUS sense divider is 22.1 kΩ / 47.5 kΩ, and VREGIN/VDD/VIO connect to the regulated 3.3 V supply. UART transmit and receive cross correctly. The shield is bonded to digital ground for this prototype. USB full-speed signal integrity, inrush, suspend current and host current declaration require bench/USB compliance testing. See [Silicon Labs CP2102N](https://www.silabs.com/documents/public/data-sheets/cp2102n-datasheet.pdf) and [ST protection device](https://www.st.com/resource/en/datasheet/usblc6-2.pdf).

## Scope decisions

No gas heater, microphone, IR receiver or CAN transceiver is fitted. They add power, noise or connector/pin pressure without being essential to the platform. The IMU already supplies die-temperature diagnostics; the BME280 supplies environmental temperature. Battery sensing and motor current regulation are included. The current-sense nodes are not calibrated motor-current telemetry: they are small chopped shunt voltages. GPS uses the dedicated UART connector; LoRa uses SPI plus expansion control lines. An external 3.3 V CAN transceiver can reuse GPIO16/17 as TWAI RX/TX when the GPS/UART function is disabled. These are explicit alternate uses, not simultaneous GPIO assignments.

The user interface includes reset, boot and user buttons, power and programmable red/green/blue indicator LEDs, a piezo buzzer and a low-side MOSFET load connector. Discrete colored LEDs were chosen over an addressable RGB package for predictable supply/logic behavior.

## Application support

| Application | Onboard capabilities | User still supplies / implements |
|---|---|---|
| Obstacle avoidance | ToF, ultrasonic protected interface, dual bridges | Motors, chassis; optional ultrasonic transducer/module and navigation firmware |
| Line following | Four protected ADS1115 inputs, motor PWM | Reflectance sensor array; not an onboard line sensor |
| Differential drive | Two quadrature interfaces and dual bridges | Encoder-equipped gearmotors and PID/odometry software |
| Basic self-balancing | Central IMU, direct interrupt, direct motor control | Mechanically suitable robot, fast control firmware, tuning and failsafe; validate control-loop latency |
| Wi-Fi robot | Integrated radio and bridge control | Web/control firmware, authenticated transport and network |
| Bluetooth robot | Classic + BLE radio | Control application and firmware |
| Environmental monitor | BME280 + ambient light | Appropriate vented enclosure and logging/telemetry firmware |
| GPS mobile robot | 3.3 V UART expansion, IMU, compass, encoder inputs | Compatible GPS receiver/antenna and localization software |
| IoT node | Wi-Fi/BLE, sensors, GPIO, analog, MOSFET load | Application firmware and external controlled loads |

Sensors and motor/servo driver modules are integrated into the PCB. Motors, servos, batteries, GPS/LoRa modules, line-sensing optics and the external balance charger are application hardware rather than functions falsely claimed to be onboard.

## Procurement and cost

BOM.csv lists individual references, orderable manufacturer part numbers and footprints; BOM_Grouped.csv combines identical items. Manufacturer documents were reviewed on the design date and are cached in datasheets/. Availability is not a guaranteed purchase allocation: obtain live authorized-distributor quotations before releasing a build. Buy Bosch/ST sensors and the ESP module from traceable suppliers. The motor driver must retain its PowerPAD package, the light sensor must retain the **TT** package, and module R2/C3/S3 substitutions require redesign. The four-layer, two-sided assembly, several MEMS parts and many connectors make this materially more expensive than an ESP32 breakout; a verified unit-cost quotation has not been produced.
