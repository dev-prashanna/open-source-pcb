# LogicScope desktop v0.1.0

A small Python/Tk desktop app for the LogicScope S3. It runs on Linux,
Windows and macOS where Python 3.10+ includes Tk. Only `pyserial` is required
outside the Python standard library. Hardware operation requires the matching
[v0.1.0 firmware](../firmware/README.md).

## Install and launch

From this directory:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e .
logicscope --demo
```

On Windows activate with `.venv\Scripts\activate` and use `python` instead of
`python3`. On Debian/Ubuntu, install `python3-tk` if Tk is missing. Demo mode
generates synthetic divided-clock signals and needs no board. To open the
application without demo data, run `logicscope`.

## Capture signals

1. Flash the firmware and reset the analyser into normal boot.
2. Connect a common ground, then attach the channel probes. Inputs record
   digital levels only; respect the hardware's documented 0–5 V input range.
3. Refresh/select the analyser's USB serial port and click **Connect**. The
   app checks the device identity and protocol version.
4. Select rate, sample count, and optional trigger search, then **Capture once**.
5. Scroll over the waveform to zoom, use the horizontal scrollbar to pan, or
   click **Fit**. Click for cursor A and Shift-click for B; the readout shows
   sample positions, packed byte values, and the time difference.
6. Save a `.lscope` capture to reopen later, or export CSV/VCD. Exports contain
   every sample/transition, independent of the displayed zoom.

Requested rates range from 100 kS/s to 1 MS/s, with at most 65,536 eight-channel
samples. The board and rates remain **physically unqualified**. This version
captures into SRAM and then uploads; it does not continuously stream.

Trigger search marks the first rising/falling/high/low/pattern match **inside
the captured buffer**. Edge/level modes use the selected channel. Pattern mode
uses a hexadecimal mask/value, e.g. mask `0x0F`, value `0x05`; masked-out bits
in the value must be zero. It does not arm and wait for a future trigger or
retain rolling pre-trigger history. `T` marks a match; `A`/`B` are user cursors.

The zoomed-out display shows both levels when a pixel covers a transition,
so a narrow retained pulse stays visible. Signals narrower than the physical
sampling period can still be missed at acquisition.

USB, file I/O and capture work run outside the Tk UI thread. CRC, sequence,
length, rate/count, flags and trigger-index checks protect received captures.
After a timeout or protocol error, **Disconnect** and **Connect** before retrying.
Close any other serial monitor using the same port. On Linux your account
needs access to the serial device (commonly through the `dialout` group).

## Command line

```sh
logicscope --list
logicscope --port /dev/ttyACM0
logicscope --port /dev/ttyACM0 --rate 250000 --samples 32768 --output capture.lscope
logicscope --demo --samples 1024 --output example.csv
logicscope --demo --output example.vcd
```

CSV columns are `sample,time_s,CH0,...,CH7`; sample zero defines time zero.
VCD uses a 1-ns timescale and can be opened in GTKWave. `.lscope` files contain
versioned JSON, sample rate/count, trigger index, source, status flags, packed
base64 sample bytes and their CRC-32. Demo captures preserve their demo label.

## Tests

```sh
python -m unittest discover -s tests -v
python tests/smoke_gui.py
```

The second command needs a display; on headless Linux use
`xvfb-run -a python tests/smoke_gui.py`. Interoperability tests compile the real
firmware protocol code with a host C compiler when available. See the project
[software verification report](../docs/Software_Verification.md).

Desktop code is [MIT licensed](LICENSE).
