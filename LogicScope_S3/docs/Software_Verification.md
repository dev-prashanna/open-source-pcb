# Firmware and host software verification — v0.1.0

Date: 2026-11-09. Hardware: LS-S3-A0. This report covers software compilation
and host-side tests. **No physical analyser was connected, flashed or sampled.**

## Implemented scope

Firmware uses the board's exact GPIO mapping, LCD_CAM eight-bit reception,
an XTAL-derived LEDC clock through the GPIO12/11 loopback, and a finite GDMA
chain in internal SRAM. It captures 16–65,536 samples at configured rates of
100,000, 250,000, 500,000 or 1,000,000 S/s, then uploads over native USB
Serial/JTAG. CRC covers response metadata and samples as well as the header.

Trigger search identifies the first retained edge/level/masked-pattern match.
It does not arm/wait, continuously stream, or supply a rolling pre-trigger
buffer. No protocol decoders are included in this version.

The host app has eight waveform lanes, zoom/pan, two timing cursors, trigger
markers, save/open, CSV/VCD exports, serial port discovery/handshake, and a
synthetic demo mode. Serial and file operations run outside the UI thread.

## Completed checks

- **ESP32-S3 firmware build passed** with ESP-IDF **v5.5.2**, commit
  `30aaf64524299d3bde422ca9a2848090d1bc5d0f`, and its installed Xtensa toolchain.
  Bootloader, partition table, ELF and application binary were produced. App
  image was 199,824 bytes (`0x30c90`), fitting the 1-MiB factory app partition.
  This is a compiler/linker result, not a hardware boot or capture result.
- **23 Python tests passed** on Python 3.12 / Linux. Cases cover fragmented
  frames, leading noise, stale sequences, CRC corruption, invalid/oversized
  lengths, timeout, configuration bounds, trigger modes and indices, captures
  at the 4,092-byte descriptor boundary, persistence, CSV mapping and VCD timing.
- Interoperability tests compiled the **actual C firmware protocol module**
  into a host shared library, checked its CRC against Python on a full capture,
  compared trigger results for all channel/mode combinations and masked
  patterns, and verified rejected request bounds.
- Portable C tests passed with `-Wall -Wextra -Werror` and address/undefined
  behavior sanitizers, including the standard CRC vector and incremental CRC.
- **Actual Tk GUI smoke test passed** on a display: maximum-size demo data,
  eight waveform lanes, zoom, horizontal pan, A/B cursor delta and fit-to-window.
- Installed the package into `software/.venv`; the `logicscope` entry point,
  demo capture/export and serial-port listing worked. No analyser USB serial
  port was available for hardware communication testing.

## Physical checks still required

Follow [the complete validation plan](Validation_Plan.md) and
[firmware bring-up instructions](../firmware/README.md). Establish:

1. Successful flashing, normal boot, UART diagnostics and USB request/response.
2. OE_N idle state, input-only probe behavior, and all eight channel mappings.
3. TP8 PCLK frequency/jitter for each requested rate; DE/VSYNC startup behavior.
4. Byte order, capture-start phase, exact sample counts, every descriptor
   boundary and repeated maximum captures using a known parallel counter.
5. FIFO-full stop behavior, interrupted/missing clock, DMA faults, timeouts,
   disconnect during capture/upload, repeated reconnects, and current/suspend.
6. Comparison with a reference analyser and measured USB throughput on
   representative Linux, Windows and macOS hosts. Only Linux host behavior
   has been exercised here.

The controller's observable error/count/guard checks cannot establish the
absence of every lost or aliased physical input pulse. The configured sample
rate and 64-KiB allocation remain subject to real-board qualification. Continue
to call the project an **engineering prototype** until those results exist.
