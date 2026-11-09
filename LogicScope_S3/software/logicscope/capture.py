"""Capture persistence, simulation and interoperable exports (no GUI dependency)."""
import base64
import csv
from dataclasses import dataclass
import json
from pathlib import Path
import zlib

from .protocol import Config, MAX_SAMPLES, RATES, UNVALIDATED, find_trigger


@dataclass(frozen=True)
class Capture:
    rate: int
    samples: bytes
    trigger_index: int = -1
    flags: int = UNVALIDATED
    source: str = "hardware"

    def __post_init__(self):
        if self.rate not in RATES or not 1 <= len(self.samples) <= MAX_SAMPLES:
            raise ValueError("Invalid capture rate or sample count")
        if not -1 <= self.trigger_index < len(self.samples):
            raise ValueError("Trigger index is outside the capture")
        if self.source not in ("hardware", "demo"):
            raise ValueError("Unknown capture source")
        if self.flags != UNVALIDATED:
            raise ValueError("Unsupported capture status flags")

    @property
    def duration(self):
        return len(self.samples) / self.rate

    def save(self, path):
        document = {
            "format": "logicscope", "version": 1, "rate": self.rate,
            "count": len(self.samples), "trigger_index": self.trigger_index,
            "flags": self.flags, "source": self.source,
            "crc32": zlib.crc32(self.samples),
            "samples_base64": base64.b64encode(self.samples).decode("ascii"),
        }
        Path(path).write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")

    @classmethod
    def load(cls, path):
        if Path(path).stat().st_size > 200_000:
            raise ValueError("Capture file too large")
        doc = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(doc, dict) or doc.get("format") != "logicscope" or doc.get("version") != 1:
            raise ValueError("Unsupported capture file")
        samples = base64.b64decode(doc["samples_base64"], validate=True)
        if doc["count"] != len(samples) or doc["crc32"] != zlib.crc32(samples):
            raise ValueError("Capture sample count or checksum mismatch")
        return cls(doc["rate"], samples, doc["trigger_index"], doc["flags"], doc["source"])

    def export_csv(self, path):
        with Path(path).open("w", newline="", encoding="utf-8") as stream:
            writer = csv.writer(stream)
            writer.writerow(["sample", "time_s"] + [f"CH{i}" for i in range(8)])
            for i, byte in enumerate(self.samples):
                writer.writerow([i, f"{i / self.rate:.9f}"] + [(byte >> ch) & 1 for ch in range(8)])

    def export_vcd(self, path):
        with Path(path).open("w", encoding="ascii", newline="\n") as stream:
            stream.write("$version LogicScope S3 0.1 $end\n$timescale 1 ns $end\n")
            stream.write(f"$comment source={self.source}; hardware unvalidated $end\n")
            stream.write("$scope module LogicScope $end\n")
            for ch in range(8):
                stream.write(f"$var wire 1 {chr(33 + ch)} CH{ch} $end\n")
            stream.write("$upscope $end\n$enddefinitions $end\n#0\n$dumpvars\n")
            for ch in range(8):
                stream.write(f"{(self.samples[0] >> ch) & 1}{chr(33 + ch)}\n")
            stream.write("$end\n")
            previous = self.samples[0]
            for i, sample in enumerate(self.samples[1:], 1):
                changed = previous ^ sample
                if changed:
                    stream.write(f"#{i * 1_000_000_000 // self.rate}\n")
                    for ch in range(8):
                        if changed & (1 << ch):
                            stream.write(f"{(sample >> ch) & 1}{chr(33 + ch)}\n")
                previous = sample
            stream.write(f"#{len(self.samples) * 1_000_000_000 // self.rate}\n")


def demo_capture(config=Config()):
    """Repeatable divided-clock/counter signals, explicitly marked synthetic."""
    config.validate()
    samples = bytes((i // 8) & 255 for i in range(config.count))
    return Capture(config.rate, samples, find_trigger(samples, config), source="demo")
