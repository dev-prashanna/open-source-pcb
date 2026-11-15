# Physical prototype validation

These steps require an assembled board and instruments. They are a planned
qualification procedure, not recorded results. Software checks cannot prove
power integrity, USB signal quality, assembly quality, or real execution speed.

1. Inspect polarity, regulator ordering codes, FPGA/FTDI orientation, solder
   bridges, QFN exposed-pad joints, and all USB-C pins under magnification.
2. With power disconnected, measure resistance from VUSB, +3V3, +1V2 and FT_1V8
   to ground. Investigate any unexpected short before powering the board.
3. Use a current-limited 5V supply through a USB breakout, initially without
   external loads. Check 1.2V first, then delayed 3.3V. Scope the sequencing:
   FPGA VCC/VCCPLL must reach at least 0.5V before SPI_VCCIO/VPP rise. Confirm
   the manufacturer's permitted rise times and supply tolerances.
4. Measure 1.2V at U1 pins 5/30 and VCCPLL pin 29, 3.3V on each I/O bank,
   FTDI VREGOUT/VCORE near 1.8V, and FTDI PHY/PLL supplies. Check current and
   regulator/FPGA temperatures. Stop if a rail is wrong or an IC heats rapidly.
5. Connect a USB data host and verify factory FTDI VID/PID and both interfaces.
   Provision EEPROM descriptors and current request as documented. Measure
   enumeration and suspend current; USB power compliance remains unqualified.
6. Read the flash JEDEC ID using `iceprog -t`. Confirm flash supply and SPI
   polarity. Program the tested blink image and verify its contents with the
   programmer. Confirm CDONE rises and the USER LED toggles around 250ms.
7. Measure the external 12MHz oscillator and confirm PWM frequencies from the
   programmed clock/divider. Use a dedicated FPGA test image to expose the
   internal clock on a spare pin if direct CPU-clock measurement is needed.
8. Exercise all 16 GPIO one at a time in both directions with 3.3V sources and
   suitable current limiting. Check reset high impedance. Test both PWM outputs.
9. Run serial echo at 115200 baud for all byte values; test overrun and framing
   error indication. Validate USB hot-plug, suspend/resume, cold boot, CPU reset,
   and FPGA reconfiguration. Test at the intended temperature and supply range.
10. Benchmark actual workloads against a stated Uno R3 program/compiler setup.
    Record cycles, instruction counts, wall time, and measurement method. Do
    not use clock ratio alone as an application performance result.

Capture photographs, instruments, firmware hashes, board revision and measured
values in a new report. Only then promote this engineering revision to a
physically validated release. Fabricator DFM and assembly review precede an order.
