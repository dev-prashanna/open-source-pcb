# Bring-up and acquisition qualification

Software update: firmware and desktop app v0.1.0 are implemented. The first
release uses finite captures up to 64 KiB and trigger search **within a captured
window**; it does not implement trigger wait, rolling pre-trigger history or
continuous streaming. Apply the relevant checks below to this implementation;
steps for future modes remain qualification requirements before enabling them.
See [firmware setup](../firmware/README.md) and
[software verification](Software_Verification.md).

1. Inspect the module variant, pin 1, buffer orientation, ESD part package and
   connector pin numbering against the BOM and native assembly drawing. Check
   resistance between 5 V, 3.3 V and ground before powering.
2. Apply current-limited USB 5 V without a target connected. Measure fused input,
   regulator output and module supply. Check converter startup and load steps,
   fuse drop, ripple and component temperature. Repeat at supply/cable limits.
3. Confirm BOOT/RESET and ROM download, then UART recovery. Implement and test
   native USB enumeration, descriptor current limits and suspend behavior.
   An unimplemented firmware/application cannot be treated as a working instrument.
4. Keep OE_N high at boot. Configure all eight acquisition GPIOs as inputs, then
   configure the parallel peripheral before asserting OE_N low. Verify no probe
   terminal ever drives the target. Check the reference output under a 10-Mohm
   meter and a deliberate short; never use it to power a target.
5. Drive each channel separately at 0/3.3 V, then 0/5 V. Verify sample-bit mapping
   and MCU-side amplitude, including board-off input injection. Check that all
   disconnected channels resolve according to their pulldowns.
6. Loop a known parallel counter into CH0..CH7, with a synchronous external test
   clock and deliberately asynchronous phase sweeps. At candidate rates from
   100 kS/s to 1 MS/s, verify every retained byte against the expected pattern.
   Measure PCLK at TP8 with a reference instrument. Verify clock divisor, jitter,
   start alignment, byte order, descriptor boundaries and exact sample count.
7. Repeat long sequences and finite captures with USB transfer activity, CPU
   load and repeated start/stop. Detect and report GDMA/FIFO/ring overflow;
   never silently accept a truncated or reordered capture. Validate runtime
   memory allocation bounds and guard regions.
8. Test rising, falling, high, low and pattern triggers on each channel. Check
   triggering sample indices, pre-trigger history and post-trigger retention,
   including triggers at block/ring boundaries. Document software trigger
   latency and the sample-time quantization.
9. Benchmark USB payload throughput with the actual Python host on multiple
   ports/hosts. Use sequence numbers, lengths and CRCs. Measure sustained minimum
   throughput and pauses before enabling a continuous mode, and keep margin.
   Uncompressed continuous 2-MS/s output is not a Full-Speed capability.
10. Compare UART, I2C and SPI captures against a reference logic analyzer at
    conservative rates. Check probe loading, ground-lead length and aliased
    narrow pulses. Validate CSV/VCD exports and any future protocol decoders
    against known captures, not screenshots alone.

Record hardware revision, exact MPNs, firmware/SDK revisions, host software,
measured sampling clocks, supply/current/temperature, sample-count errors,
USB throughput and fault outcomes. Only then publish a measured sampling
rate or describe a board as a working, qualified instrument. No fabricated
board, physical acquisition or USB performance test has been performed here.
