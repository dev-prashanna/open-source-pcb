"""Synchronous device API; the GUI runs it in a worker thread."""
import json
import time

from .capture import Capture
from .protocol import (CAPTURE, ERROR, INFO, METADATA, Config, ProtocolError,
                       StreamDecoder, encode_frame, find_trigger)


def list_ports():
    from serial.tools import list_ports as ports
    return list(ports.comports())


class Device:
    def __init__(self, port, timeout=5.0):
        import serial
        self.timeout = timeout
        # Set control lines before open: avoid requesting an S3 boot/reset.
        self.serial = serial.Serial(port=None, baudrate=115200, timeout=0.05, write_timeout=1)
        self.serial.dtr = False
        self.serial.rts = False
        self.serial.port = port
        self.serial.open()
        self.serial.reset_input_buffer()
        self.sequence = 0
        self.broken = False

    def close(self):
        self.serial.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def _exchange(self, kind, payload=b""):
        if self.broken:
            raise ProtocolError("Connection lost synchronization; disconnect and reconnect")
        self.sequence = (self.sequence + 1) & 65535
        raw = encode_frame(kind, self.sequence, payload)
        decoder = StreamDecoder()
        deadline = time.monotonic() + self.timeout
        try:
            if self.serial.write(raw) != len(raw):
                raise ProtocolError("Incomplete command write")
            while time.monotonic() < deadline:
                for frame in decoder.feed(self.serial.read(4096)):
                    if frame.sequence != self.sequence:
                        continue  # delayed frame from a previous connection/request
                    if frame.type == ERROR:
                        raise ProtocolError(frame.payload.decode("utf-8", errors="replace"))
                    if frame.type != kind | 0x80:
                        raise ProtocolError("Unexpected response type")
                    return frame.payload
            raise TimeoutError("No complete response. Reconnect; check firmware, cable and clock loopback.")
        except Exception:
            self.broken = True
            raise

    def info(self):
        doc = json.loads(self._exchange(INFO).decode("utf-8"))
        if not isinstance(doc, dict) or doc.get("device") != "LogicScope S3" or doc.get("protocol") != 1:
            raise ProtocolError("Port is not a supported LogicScope S3")
        return doc

    def capture(self, config=Config()):
        payload = self._exchange(CAPTURE, config.pack())
        if len(payload) < METADATA.size:
            raise ProtocolError("Truncated capture metadata")
        rate, count, trigger, flags = METADATA.unpack_from(payload)
        samples = payload[METADATA.size:]
        if rate != config.rate or count != config.count or len(samples) != count:
            raise ProtocolError("Capture rate/count does not match request")
        if trigger != find_trigger(samples, config):
            raise ProtocolError("Device trigger index does not match received samples")
        return Capture(rate, samples, trigger, flags)
