# Getting started, from zero

A development board is a small computer with accessible pins. A program tells
its CPU what to do. TIWARI's CPU is implemented in an FPGA, a chip containing
logic that can be rewired by a configuration file. The FPGA is not a second
microcontroller running an emulator: the processor and peripherals become logic
circuits inside it.

You can start without buying a board. Run the assembler and simulations first.
Manufacturing and assembly require the KiCad/fabrication files and the BOM;
you cannot build this board by uploading code to an ordinary Arduino.

## 1. Tools on Ubuntu 24.04

```sh
sudo apt update
sudo apt install python3 make iverilog yosys nextpnr-ice40 nextpnr-ice40-chipdb fpga-icestorm
```

Clone the source repository and enter this project:

```sh
git clone https://github.com/dev-prashanna/open-source-pcb.git
cd open-source-pcb/TIWARI
make test sim
```

The assembler uses only the Python standard library. `iverilog` and `vvp`
simulate the actual Verilog logic. Yosys converts the logic into FPGA cells;
nextpnr places and connects them; icepack creates the configuration image.
These tools must be on PATH. Windows/macOS users can use a compatible OSS CAD
Suite installation; the commands and USB permissions still need local setup.

## 2. Your first program

```asm
LDI 1       ; load the number 1 into accumulator A
OUT 0x40    ; send A to the built-in USER LED register
HLT         ; stop the CPU; peripherals keep running
```

Save this as `examples/my_led.asm` and build it:

```sh
make synth PROGRAM=examples/my_led.asm
```

The file `build/tiwari.bin` contains both the processor hardware and your program.
The default clock is 36 MHz. The build must pass its timing check before you
flash it. A different program can change FPGA placement and timing, so always
rebuild rather than editing a bitstream. The maximum program is 4096 words.

`make sim` checks the reference blink example as well as CPU/peripheral tests.
It always builds blink for the blink test; `make synth PROGRAM=...` selects the
program that will be built for hardware.

## 3. After a prototype has been assembled and checked

Follow [bring-up](Bringup.md) first. Use a USB-C data cable. The power LED should
light and the FTDI USB device should enumerate. A power-only cable cannot
program the board. Channel A is the programmer; channel B is the serial port.
Retain the FTDI factory VID/PID; provision its EEPROM as described in Hardware.md.

On Linux, install the documented IceStorm udev permissions for your device or
configure an appropriate `plugdev` rule. USB programming uses libusb rather
than the serial port. The serial console usually appears as the second
FTDI ttyUSB interface. Serial-port access commonly requires the `dialout` group.
Re-login after changing group membership. Avoid globally writable USB devices.

To program the blink example after checking the board:

```sh
make flash
```

CPU RESET restarts the application while preserving RAM. RECONFIGURE reloads
the FPGA hardware and program from external flash. USER is software-controlled;
FAULT indicates an illegal CPU instruction. Pressing reconfigure while
programming interrupts the operation; retry programming after releasing it.

## 4. Examples

```sh
make flash PROGRAM=examples/gpio.asm
make flash PROGRAM=examples/pwm.asm
make flash PROGRAM=examples/serial_echo.asm
```

For GPIO mirroring, connect stable 3.3V digital signals to D8..D15; the program
copies them to D0..D7. Inputs float without external pull resistors. Connect an
LED through a suitable resistor; use an external driver for a motor or relay.

For serial echo, open channel B at 115200, 8N1. Type slowly: the CPU has a
single-byte UART buffer and no flow control. The USB bridge may buffer several
bytes, but the CPU interface itself is one byte. Test sustained traffic before
using it in an application. Close applications using channel A before flashing.

## Electrical boundaries

GPIO and PWM are **3.3V only**. Do not connect 5V Uno outputs directly. The 3V3
header pins supply external circuits; they are not power inputs. Never feed
power back into them. Start with low-current LEDs or sensors; keep external
3.3V loads within the provisional 50mA aggregate bring-up budget until the
actual regulator temperatures and USB current are measured. There is no analog
input, battery charger, or motor driver in this revision.
