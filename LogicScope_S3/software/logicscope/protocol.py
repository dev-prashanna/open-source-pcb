"""Version 1 framing, shared with firmware/main/protocol.c."""
from dataclasses import dataclass
from enum import IntEnum
import struct
import zlib

MAGIC = b"LSA1"
HEADER = struct.Struct("<4sBBHII")
REQUEST = struct.Struct("<IIBBBB")
METADATA = struct.Struct("<IIiI")
RATES = (100_000, 250_000, 500_000, 1_000_000)
MAX_SAMPLES = 65_536
MAX_PAYLOAD = MAX_SAMPLES + METADATA.size
UNVALIDATED = 1
INFO, CAPTURE, ERROR = 1, 2, 255


class ProtocolError(ValueError):
    pass


class Trigger(IntEnum):
    IMMEDIATE = 0
    RISING = 1
    FALLING = 2
    HIGH = 3
    LOW = 4
    PATTERN = 5


@dataclass(frozen=True)
class Config:
    rate: int = 1_000_000
    count: int = 16_384
    trigger: Trigger = Trigger.IMMEDIATE
    mask: int = 1
    value: int = 0

    def validate(self):
        if self.rate not in RATES:
            raise ValueError(f"Sample rate must be one of {RATES}")
        if not 16 <= self.count <= MAX_SAMPLES or self.count % 4:
            raise ValueError("Samples must be 16–65536 and a multiple of four")
        try:
            kind = Trigger(self.trigger)
        except ValueError as exc:
            raise ValueError("Unknown trigger search") from exc
        if not 0 <= self.mask <= 255 or not 0 <= self.value <= 255:
            raise ValueError("Mask and pattern must be bytes (0–255)")
        if kind and not self.mask:
            raise ValueError("Trigger search needs a nonzero mask")
        if kind not in (Trigger.IMMEDIATE, Trigger.PATTERN) and self.mask & (self.mask - 1):
            raise ValueError("Edge/level searches require exactly one channel")
        if self.value & ~self.mask:
            raise ValueError("Pattern has bits outside the mask")

    def pack(self):
        self.validate()
        return REQUEST.pack(self.rate, self.count, self.trigger, self.mask, self.value, 0)


@dataclass(frozen=True)
class Frame:
    type: int
    sequence: int
    payload: bytes


def encode_frame(kind, sequence, payload=b""):
    if not 0 <= sequence <= 65535 or len(payload) > MAX_PAYLOAD:
        raise ProtocolError("Invalid sequence or oversized payload")
    prefix = HEADER.pack(MAGIC, kind, 0, sequence, len(payload), 0)[:12]
    crc = zlib.crc32(payload, zlib.crc32(prefix))
    return prefix + struct.pack("<I", crc) + payload


def decode_frame(data):
    if len(data) < HEADER.size:
        raise ProtocolError("Truncated header")
    magic, kind, flags, seq, size, crc = HEADER.unpack_from(data)
    if magic != MAGIC or flags:
        raise ProtocolError("Invalid magic or reserved flags")
    if size > MAX_PAYLOAD or len(data) != HEADER.size + size:
        raise ProtocolError("Invalid frame length")
    payload = data[HEADER.size:]
    if zlib.crc32(payload, zlib.crc32(data[:12])) != crc:
        raise ProtocolError("CRC mismatch; capture discarded")
    return Frame(kind, seq, payload)


class StreamDecoder:
    """Bounded stream parser. CRC failures fail loudly; leading noise is skipped."""
    def __init__(self):
        self.buffer = bytearray()

    def feed(self, data):
        if len(data) > MAX_PAYLOAD + HEADER.size:
            raise ProtocolError("Input chunk too large")
        self.buffer.extend(data)
        frames = []
        while True:
            start = self.buffer.find(MAGIC)
            if start < 0:
                self.buffer[:] = self.buffer[-3:]
                return frames
            del self.buffer[:start]
            if len(self.buffer) < HEADER.size:
                return frames
            _, _, flags, _, size, _ = HEADER.unpack_from(self.buffer)
            if flags or size > MAX_PAYLOAD:
                self.buffer.clear()
                raise ProtocolError("Invalid response flags or length")
            total = HEADER.size + size
            if len(self.buffer) < total:
                return frames
            raw = bytes(self.buffer[:total])
            del self.buffer[:total]
            frames.append(decode_frame(raw))


def find_trigger(samples, config):
    config.validate()
    kind = config.trigger
    if kind == Trigger.IMMEDIATE:
        return -1
    for i, sample in enumerate(samples):
        now = sample & config.mask
        previous = samples[i - 1] & config.mask if i else 0
        if ((kind == Trigger.RISING and i > 0 and not previous and now)
                or (kind == Trigger.FALLING and i > 0 and previous and not now)
                or (kind == Trigger.HIGH and now)
                or (kind == Trigger.LOW and not now)
                or (kind == Trigger.PATTERN and now == config.value)):
            return i
    return -1
