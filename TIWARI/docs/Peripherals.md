# Peripheral register map

IN reads and OUT writes an 8-bit port number. Unsupported reads return zero;
unsupported writes do nothing. Output latches and PWM start at zero; GPIO
starts as input/high impedance. All headers use 3.3V logic.

| Port | IN | OUT |
| --- | --- | --- |
| 00 | Synchronized D0..D7 inputs | D0..D7 output latch |
| 01 | Synchronized D8..D15 inputs | D8..D15 output latch |
| 02 | Low GPIO direction | Low GPIO direction; 1 = output |
| 03 | High GPIO direction | High GPIO direction; 1 = output |
| 04 | Low output latch | ignored |
| 05 | High output latch | ignored |
| 10 | UART received byte | UART transmit byte, ignored while busy |
| 11 | UART status | ignored |
| 12 | zero | Acknowledge received byte; clear ready/error flags |
| 20 | PWM0 duty byte | PWM0 duty byte |
| 21 | PWM1 duty byte | PWM1 duty byte |
| 22 | PWM prescaler | PWM prescaler |
| 30 | Latched milliseconds, low byte | Snapshot current milliseconds |
| 31 | Latched milliseconds, high byte | ignored |
| 40 | Built-in USER LED state | USER LED = A bit 0 |
| 7F | Revision identifier 81 hex | ignored |

UART status bit 0 is TX busy, bit 1 RX ready, bit 2 RX overrun, bit 3 RX framing
error; higher bits are zero. It has a single-byte receive buffer. An overrun
retains the older unread byte and drops the newer one. A framing error drops
the invalid byte. IN 10 does not acknowledge; OUT 12 acknowledges explicitly.
Poll RX ready before reading, and TX busy before transmitting. The registered
UART command takes effect one clock after OUT. The serial echo example follows
these rules. There is no FIFO or hardware flow control.

PWM outputs compare an 8-bit free-running counter with the duty register. Duty
0 is always low; duty 255 is 255/256 rather than exactly 100%. The shared divider
makes frequency `CPU_CLOCK / ((prescaler + 1) * 256)`. Duty updates are immediate
and may shorten the current pulse. These are logic outputs, not motor drivers.

Snapshot the millisecond timer with OUT 30, then read IN 30 and IN 31 to obtain a
coherent 16-bit value. It wraps after 65.536 seconds. Timer and PWM continue
independently of CPU instruction execution.
