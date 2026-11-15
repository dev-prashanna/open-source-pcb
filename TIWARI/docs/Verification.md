# Verification record — TW8-A0

This is an engineering design release, not a physically tested product.
The checks below exercise the actual HDL and software tools; no instruction-set
emulator result is substituted for an HDL simulation.

## Processor and firmware

`make test sim` passed with Icarus Verilog 12.0 and Python 3.12:

- Assembler instruction encoding, constants, forward labels, invalid input,
  operand limits, capacity limits, and all example sources.
- All 65,536 operand pairs for ADD and all 65,536 for SUB, including Z and C.
- Directed logic, shift, register transfer, conditional/direct branch, PC wrap,
  RAM, input/output, reset, pause, halt and illegal-encoding checks.
- SoC GPIO input/direction/output, LED, autonomous PWM duty and millisecond timer.
- UART loopback for every byte value, RX acknowledgement and overrun retention.
- The actual assembled blink program: three LED transitions with 250ms intervals
  in a scaled-clock SoC simulation, including timer low-byte wrap.

The CPU and peripherals are not formally proved. Uninitialized RAM, asynchronous
input timing, electrical metastability MTBF, and every possible program sequence
are not covered by these tests. UART framing-error behavior is implemented but
not included in the current directed test.

## FPGA implementation

Yosys 0.33 and nextpnr-ice40 0.6, iCE40UP5K / SG48, seed 1, 36MHz target:

| Example | Post-route estimated maximum | Target result |
| --- | --- | --- |
| Blink | 37.91 MHz | PASS at 36 MHz |
| Serial echo | 47.14 MHz | PASS at 36 MHz |
| GPIO mirror | 37.91 MHz | PASS at 36 MHz |
| PWM | 46.08 MHz | PASS at 36 MHz |

These are static timing estimates, not oscilloscope measurements. The default
blink image uses 803 of 5,280 logic cells and 13 of 30 block RAMs. Program ROM
constant optimization means usage and timing can change with the application.
Rebuild and check timing for every changed program. Do not raise the default
clock to the estimated maximum. Peripheral clock/divider constants and PLL
settings must change together if you intentionally change the clock.

The 36MHz setting is 2.25 times the classic Uno R3's 16MHz clock. TIWARI uses
2–3 clocks per instruction; nominal instruction throughput is 12–18 million per
second depending on instruction mix. This is not a measured speedup over AVR.
Parallel hardware peripherals may improve particular tasks; use a workload
benchmark before making an application-performance claim.

`reports/fpga/` contains the per-image timing/utilization evidence. The four
built images and initialized ROM files are in `firmware/prebuilt/`. They are
for TW8-A0 and remain untested on an assembled board.

## Hardware design checks

KiCad 10 is used for schematic/PCB checks and manufacturing exports. The
schematic has been checked with both the KiCad CLI and the connected KiCad
MCP server. Final ERC and DRC have zero violations, with zero unconnected nets and zero
schematic/PCB parity issues. All 274 mapped physical pins and all 24 FPGA
constraints match the manifest. These checks and pin-constraint reports are
provided under `reports/`. The release exporter stops when its required
checks fail; it does not regenerate or replace the reviewed routing.

## Physical work still required

No PCB fabrication, assembly, flash programming, USB signal/compliance test,
power/thermal measurement, GPIO load qualification, or real workload benchmark
has been performed. Follow [bring-up](Bringup.md). Fabricator DFM must confirm
the stackup, USB trace impedance, via filling/capping, and assembly process.
A zero-violation EDA report does not establish those physical properties.
