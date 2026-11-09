import ctypes
import csv
import json
from pathlib import Path
import random
import shutil
import struct
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import zlib

from logicscope.capture import Capture, demo_capture
from logicscope.device import Device
from logicscope.protocol import (CAPTURE, ERROR, HEADER, INFO, MAX_SAMPLES, METADATA,
                                Config, ProtocolError, StreamDecoder, Trigger,
                                decode_frame, encode_frame, find_trigger)


class ProtocolTests(unittest.TestCase):
    def test_crc_vector_and_incremental_chunks(self):
        raw = encode_frame(CAPTURE, 42, b"123456789")
        expected = zlib.crc32(raw[:12] + b"123456789")
        self.assertEqual(struct.unpack_from("<I", raw, 12)[0], expected)
        for stride in (1, 3, 16, 50):
            decoder = StreamDecoder()
            frames = []
            stream = b"boot noise\n" + raw + raw
            for i in range(0, len(stream), stride):
                frames.extend(decoder.feed(stream[i:i + stride]))
            self.assertEqual([f.sequence for f in frames], [42, 42])

    def test_every_header_and_payload_bit_is_protected(self):
        raw = encode_frame(CAPTURE, 1, b"abc")
        for index in range(len(raw)):
            altered = bytearray(raw)
            altered[index] ^= 1
            with self.assertRaises(ProtocolError):
                decode_frame(altered)

    def test_bad_length_is_rejected_without_allocating_payload(self):
        decoder = StreamDecoder()
        header = HEADER.pack(b"LSA1", CAPTURE, 0, 1, 0xffffffff, 0)
        with self.assertRaises(ProtocolError):
            decoder.feed(header)

    def test_truncated_frame_waits_for_completion(self):
        raw = encode_frame(INFO, 12)
        parser = StreamDecoder()
        self.assertEqual(parser.feed(raw[:-1]), [])
        self.assertEqual(parser.feed(raw[-1:])[0].sequence, 12)

    def test_leading_garbage_buffer_is_bounded(self):
        parser = StreamDecoder()
        for _ in range(100):
            parser.feed(b"?" * 4096)
        self.assertLessEqual(len(parser.buffer), 3)

    def test_maximum_capture_frame(self):
        payload = bytes(MAX_SAMPLES + METADATA.size)
        self.assertEqual(decode_frame(encode_frame(0x82, 65535, payload)).payload, payload)

    def test_config_rejects_invalid_inputs(self):
        for config in (Config(rate=2_000_000), Config(count=15), Config(count=17),
                       Config(count=65540), Config(trigger=Trigger.RISING, mask=0),
                       Config(trigger=Trigger.RISING, mask=3), Config(trigger=6),
                       Config(trigger=Trigger.PATTERN, mask=1, value=2), Config(mask=256)):
            with self.assertRaises(ValueError):
                config.pack()

    def test_trigger_edges_levels_patterns_and_no_match(self):
        data = b"\0\0\x01\x01\x00\x02\x03"
        for kind, mask, value, expected in (
                (Trigger.IMMEDIATE, 1, 0, -1), (Trigger.RISING, 1, 0, 2),
                (Trigger.FALLING, 1, 0, 4), (Trigger.HIGH, 2, 0, 5),
                (Trigger.LOW, 1, 0, 0), (Trigger.PATTERN, 3, 3, 6),
                (Trigger.PATTERN, 255, 8, -1)):
            self.assertEqual(find_trigger(data, Config(trigger=kind, mask=mask, value=value)), expected)

    def test_edge_at_first_sample_is_not_invented(self):
        self.assertEqual(find_trigger(b"\1\1", Config(trigger=Trigger.RISING)), -1)

    def test_descriptor_boundary_trigger(self):
        samples = bytes(4092) + b"\x80" + bytes(100)
        self.assertEqual(find_trigger(samples, Config(trigger=Trigger.RISING, mask=128)), 4092)


class CaptureTests(unittest.TestCase):
    def test_save_roundtrip_and_detect_corruption(self):
        cap = demo_capture(Config(trigger=Trigger.RISING))
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "capture.lscope"
            cap.save(path)
            self.assertEqual(Capture.load(path), cap)
            doc = json.loads(path.read_text())
            doc["crc32"] ^= 1
            path.write_text(json.dumps(doc))
            with self.assertRaises(ValueError):
                Capture.load(path)

    def test_csv_bit_mapping_and_time(self):
        cap = Capture(1_000_000, b"\x01\x80")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "capture.csv"
            cap.export_csv(path)
            with path.open() as stream:
                rows = list(csv.reader(stream))
            self.assertEqual(rows[1], ["0", "0.000000000", "1", "0", "0", "0", "0", "0", "0", "0"])
            self.assertEqual(rows[2], ["1", "0.000001000", "0", "0", "0", "0", "0", "0", "0", "1"])

    def test_vcd_timestamps_and_transition_only_output(self):
        cap = Capture(250_000, b"\0\0\1\1")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "capture.vcd"
            cap.export_vcd(path)
            text = path.read_text()
            self.assertIn("$timescale 1 ns $end", text)
            self.assertIn("#8000\n1!\n", text)
            self.assertNotIn("#4000", text)
            self.assertTrue(text.endswith("#16000\n"))

    def test_invalid_capture_metadata(self):
        for args in ((1_000_000, b""), (1, b"a"), (1_000_000, b"a", 1),
                     (1_000_000, b"a", -2), (1_000_000, b"a", -1, 0)):
            with self.assertRaises(ValueError):
                Capture(*args)

    def test_demo_source_is_persistent(self):
        cap = demo_capture(Config(count=65536))
        self.assertEqual(cap.source, "demo")
        self.assertEqual(len(cap.samples), 65536)
        self.assertEqual(cap.samples[:16], bytes(8) + b"\1" * 8)


class FakeSerial:
    """Emulate short USB reads and stale sequence frames at the real serial API."""
    mode = "good"

    def __init__(self, **kwargs):
        self.port = None
        self.pending = bytearray()
        self.opened = False

    def open(self):
        self.opened = True

    def close(self):
        self.opened = False

    def reset_input_buffer(self):
        self.pending.clear()

    def write(self, raw):
        frame = decode_frame(raw)
        if frame.type == INFO:
            payload = json.dumps({"device": "LogicScope S3", "protocol": 1, "firmware": "0.1.0"}).encode()
        else:
            rate, count, kind, mask, value, _ = struct.unpack("<IIBBBB", frame.payload)
            config = Config(rate, count, Trigger(kind), mask, value)
            cap = demo_capture(config)
            trigger = cap.trigger_index + (1 if self.mode == "bad_trigger" else 0)
            payload = METADATA.pack(rate, count, trigger, 1) + cap.samples
        response = encode_frame(frame.type | 0x80, frame.sequence, payload)
        if self.mode == "crc":
            response = response[:-1] + bytes([response[-1] ^ 1])
        elif self.mode == "error":
            response = encode_frame(ERROR, frame.sequence, b"E_CAPTURE: DMA fault")
        elif self.mode == "truncated":
            response = response[:10]
        # An otherwise valid stale response must never satisfy the request.
        self.pending.extend(encode_frame(0x81, (frame.sequence - 1) & 65535, b"stale") + response)
        return len(raw)

    def read(self, count):
        result = bytes(self.pending[:7])
        del self.pending[:7]
        return result


class DeviceTests(unittest.TestCase):
    def setUp(self):
        FakeSerial.mode = "good"
        self.patch = patch("serial.Serial", FakeSerial)
        self.patch.start()

    def tearDown(self):
        self.patch.stop()

    def test_handshake_capture_fragmented_and_stale_frames(self):
        with Device("fake") as device:
            self.assertEqual(device.info()["protocol"], 1)
            cap = device.capture(Config(count=1024, trigger=Trigger.RISING))
            self.assertEqual(len(cap.samples), 1024)
            self.assertEqual(cap.trigger_index, 8)
            self.assertFalse(device.serial.dtr)
            self.assertFalse(device.serial.rts)
        self.assertFalse(device.serial.opened)

    def test_bad_crc_poisoned_connection_requires_reconnect(self):
        FakeSerial.mode = "crc"
        with Device("fake") as device:
            with self.assertRaisesRegex(ProtocolError, "CRC"):
                device.info()
            with self.assertRaisesRegex(ProtocolError, "reconnect"):
                device.info()

    def test_device_fault_is_not_accepted_as_samples(self):
        FakeSerial.mode = "error"
        with Device("fake") as device:
            with self.assertRaisesRegex(ProtocolError, "DMA fault"):
                device.capture()

    def test_incorrect_trigger_index_is_rejected(self):
        FakeSerial.mode = "bad_trigger"
        with Device("fake") as device:
            with self.assertRaisesRegex(ProtocolError, "trigger index"):
                device.capture(Config(count=16, trigger=Trigger.RISING))

    def test_incomplete_frame_times_out(self):
        FakeSerial.mode = "truncated"
        with Device("fake", timeout=0.01) as device:
            with self.assertRaises(TimeoutError):
                device.info()


@unittest.skipUnless(shutil.which("cc"), "Host C compiler required for firmware interoperability tests")
class FirmwareInteropTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        firmware = Path(__file__).resolve().parents[2] / "firmware" / "main"
        library = Path(cls.temp.name) / "protocol.so"
        subprocess.run(["cc", "-std=c11", "-Wall", "-Wextra", "-Werror", "-shared", "-fPIC",
                        str(firmware / "protocol.c"), "-o", str(library)], check=True)
        cls.lib = ctypes.CDLL(str(library))
        cls.lib.ls_crc32.argtypes = [ctypes.c_uint32, ctypes.c_void_p, ctypes.c_size_t]
        cls.lib.ls_crc32.restype = ctypes.c_uint32
        cls.lib.ls_parse_request.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p]
        cls.lib.ls_parse_request.restype = ctypes.c_bool
        cls.lib.ls_find_trigger.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_void_p]
        cls.lib.ls_find_trigger.restype = ctypes.c_int32

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_firmware_crc_matches_host_on_wire(self):
        raw = encode_frame(CAPTURE, 0xfffe, demo_capture().samples)
        crc = self.lib.ls_crc32(0, raw[:12], 12)
        crc = self.lib.ls_crc32(crc, raw[16:], len(raw) - 16)
        self.assertEqual(crc, struct.unpack_from("<I", raw, 12)[0])

    def test_firmware_and_python_find_identical_triggers(self):
        rng = random.Random(32)
        samples = bytes(rng.randrange(256) for _ in range(65536))
        for kind in Trigger:
            for ch in range(8):
                config = Config(trigger=kind, mask=1 << ch)
                c_request = ctypes.create_string_buffer(16)
                self.assertTrue(self.lib.ls_parse_request(config.pack(), 12, c_request))
                self.assertEqual(self.lib.ls_find_trigger(samples, len(samples), c_request),
                                 find_trigger(samples, config))
        for value in range(0, 256, 7):
            config = Config(trigger=Trigger.PATTERN, mask=255, value=value)
            c_request = ctypes.create_string_buffer(16)
            self.assertTrue(self.lib.ls_parse_request(config.pack(), 12, c_request))
            self.assertEqual(self.lib.ls_find_trigger(samples, len(samples), c_request),
                             find_trigger(samples, config))

    def test_firmware_rejects_oversized_and_unaligned_requests(self):
        out = ctypes.create_string_buffer(16)
        for count in (0, 15, 17, 65540, 0xffffffff):
            payload = struct.pack("<IIBBBB", 1000000, count, 0, 1, 0, 0)
            self.assertFalse(self.lib.ls_parse_request(payload, len(payload), out))


if __name__ == "__main__":
    unittest.main()
