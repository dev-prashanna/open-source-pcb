import argparse
import sys
from pathlib import Path

from .capture import demo_capture
from .device import Device, list_ports
from .protocol import Config, RATES


def main(argv=None):
    parser = argparse.ArgumentParser(description="LogicScope S3 desktop viewer and capture CLI")
    parser.add_argument("--demo", action="store_true", help="Use synthetic signals, no device")
    parser.add_argument("--list", action="store_true", help="List serial ports and exit")
    parser.add_argument("--port", help="USB serial port, e.g. /dev/ttyACM0 or COM3")
    parser.add_argument("--rate", type=int, choices=RATES, default=1_000_000)
    parser.add_argument("--samples", type=int, default=16_384)
    parser.add_argument("--output", type=Path, help="Capture once to .lscope, .csv or .vcd without the GUI")
    args = parser.parse_args(argv)
    try:
        if args.list:
            for port in list_ports():
                print(f"{port.device}\t{port.description}")
            return 0
        config = Config(args.rate, args.samples)
        config.validate()
        if args.output:
            if args.output.suffix.lower() not in (".lscope", ".csv", ".vcd"):
                parser.error("Output extension must be .lscope, .csv or .vcd")
            if args.demo:
                capture = demo_capture(config)
            elif args.port:
                with Device(args.port) as device:
                    device.info()
                    capture = device.capture(config)
            else:
                parser.error("Use --port PORT or --demo with --output")
            method = {".lscope": capture.save, ".csv": capture.export_csv, ".vcd": capture.export_vcd}
            method[args.output.suffix.lower()](args.output)
            print(f"Saved {len(capture.samples)} samples at {capture.rate} S/s ({capture.source}) to {args.output}")
        else:
            from .gui import run
            run(demo=args.demo, port=args.port, config=config)
        return 0
    except (OSError, ValueError, TimeoutError, RuntimeError) as exc:
        print(f"LogicScope: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
