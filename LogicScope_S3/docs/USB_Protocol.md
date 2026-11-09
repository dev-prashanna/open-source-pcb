# LogicScope USB protocol v1

Transport: ESP32-S3 native USB Serial/JTAG CDC byte stream. There is one
outstanding request at a time. Baud rate is irrelevant to capture rate. Boot
logs and diagnostics use the separate UART, not this stream.

All integers are **little endian**. Each frame has a 16-byte header:

| Offset | Size | Field |
| --- | --- | --- |
| 0 | 4 | ASCII `LSA1` |
| 4 | 1 | Command/response type |
| 5 | 1 | Reserved flags, must be zero |
| 6 | 2 | Host sequence, echoed in response |
| 8 | 4 | Payload byte length |
| 12 | 4 | CRC-32 of header bytes 0..11 followed by payload |

CRC is standard reflected CRC-32/ISO-HDLC, polynomial `0xEDB88320`, initial
internal register `0xFFFFFFFF`, final XOR `0xFFFFFFFF`. Equivalently:
`zlib.crc32(payload, zlib.crc32(header[:12]))`. The reference vector
`123456789` is `0xCBF43926`. Never trust the length for allocation before checking
the maximum. Firmware requests are at most 12 bytes; responses at most 65,552.

## Commands

`0x01 INFO`: empty request. `0x81` response is UTF-8 JSON with `device`, `board`,
`firmware`, `protocol`, `channels`, `rates`, `max_samples`, `alignment`,
`hardware_validated`, and `trigger_mode`. This firmware always reports
`hardware_validated=false` and `trigger_mode="search_in_capture"`.

`0x02 CAPTURE`: 12-byte request (`<IIBBBB` in Python):

| Offset | Size | Field |
| --- | --- | --- |
| 0 | 4 | Sample rate: 100000, 250000, 500000, 1000000 |
| 4 | 4 | Sample count: 16..65536, multiple of 4 |
| 8 | 1 | Search: 0 immediate, 1 rising, 2 falling, 3 high, 4 low, 5 pattern |
| 9 | 1 | Channel mask; nonzero for searches; single bit for modes 1..4 |
| 10 | 1 | Pattern value; bits outside mask must be zero |
| 11 | 1 | Reserved zero |

`0x82` response: 16-byte metadata followed by exactly `count` packed bytes.
Sample byte bit 0 is CH0, bit 7 is CH7; one byte represents eight simultaneous
digital inputs, in chronological order. Metadata is `<IIiI`:

| Offset | Size | Field |
| --- | --- | --- |
| 0 | 4 | Configured sample rate |
| 4 | 4 | Exact returned sample count |
| 8 | 4 | Signed first matching sample index, `-1` if none/immediate |
| 12 | 4 | Status: bit 0 = hardware/rates unvalidated; other bits reserved |

An edge search compares adjacent retained samples starting at index 1. Level
and pattern searches can match index 0. Samples before a match remain in the
returned capture; a search does not change capture start/end or block waiting
for the trigger. Times are `index / configured_rate` relative to sample zero;
there is no absolute device/host clock synchronization.

`0xFF ERROR`: UTF-8 diagnostic beginning with an `E_...` code. No samples are
returned on an acquisition failure. Defined diagnostics include `E_LENGTH`,
`E_TIMEOUT`, `E_CRC`, `E_FLAGS`, `E_CONFIG`, `E_INIT`, `E_CAPTURE_TIMEOUT`,
`E_CAPTURE`, and `E_COMMAND`.

## Framing and failure behavior

Firmware scans for magic after noise, waits at most 500 ms for the remainder
of a request header/payload, and rejects unsupported flags/configurations.
Capture timeout is the requested window duration plus 250 ms. A disconnected
host cannot leave capture running indefinitely. Upload attempts have bounded
timeouts; no partially uploaded frame is a valid capture.

The host deadline is 5 seconds, ignores complete stale-sequence responses,
and rejects CRC/length/type errors. After a timeout/protocol fault, reconnect
to discard pending bytes before another command. Device request processing is
serial; concurrent/pipelined commands and cancellation are unsupported.

This protocol provides transfer integrity, not an assurance that asynchronous
inputs were sampled without aliasing or physical capture faults. Qualify the
board and acquisition engine against known counter/pulse signals.
