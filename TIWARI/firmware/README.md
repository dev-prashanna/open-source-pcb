# Programs and FPGA images

The CPU and hardware peripherals are in `../rtl/`; programs are in `../examples/`.
Build and program from the TIWARI project directory with `make flash`.

`prebuilt/` holds bitstreams and ROM images for TW8-A0, 36MHz. All four were
synthesized and placed/routed with passing timing checks; none has been flashed
to physical hardware yet. `blink.bin` is the default image. After following the
bring-up procedure you may write it with `iceprog firmware/prebuilt/blink.bin`.

These files contain the entire FPGA configuration plus initialized program
memory. They are not AVR HEX files or files for an Arduino bootloader. Keep
hardware revision, RTL, pin constraints, ROM image and bitstream together.
