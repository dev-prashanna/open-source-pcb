PYTHON ?= python3
IVERILOG ?= iverilog
VVP ?= vvp
YOSYS ?= yosys
NEXTPNR ?= nextpnr-ice40
ICEPACK ?= icepack
ICEPROG ?= iceprog
PROGRAM ?= examples/blink.asm
RTL = rtl/tiwari8.v rtl/uart.v rtl/tiwari_soc.v
.PHONY: all test sim synth flash clean
all: test sim synth
build/blink.hex: $(PROGRAM) tools/assemble.py FORCE
	mkdir -p build
	$(PYTHON) tools/assemble.py $(PROGRAM) $@
test:
	$(PYTHON) -m unittest discover -s tests -v
sim:
	mkdir -p build
	$(PYTHON) tools/assemble.py examples/blink.asm build/blink.hex
	$(IVERILOG) -g2012 -Wall -s cpu_tb -o build/cpu_tb rtl/tiwari8.v tests/cpu_tb.sv
	$(VVP) build/cpu_tb
	$(IVERILOG) -g2012 -Wall -s soc_tb -o build/soc_tb $(RTL) tests/soc_tb.sv
	$(VVP) build/soc_tb
	$(IVERILOG) -g2012 -Wall -s uart_tb -o build/uart_tb rtl/uart.v tests/uart_tb.sv
	$(VVP) build/uart_tb
	$(IVERILOG) -g2012 -Wall -s blink_tb -o build/blink_tb $(RTL) tests/blink_tb.sv
	$(VVP) build/blink_tb
synth: build/blink.hex
	$(YOSYS) -Q -l build/synthesis.log -p 'read_verilog $(RTL) rtl/top.v; synth_ice40 -top top -json build/tiwari.json'
	$(NEXTPNR) --up5k --package sg48 --json build/tiwari.json --pcf hardware/TIWARI.pcf --freq 36 --seed 1 --asc build/tiwari.asc --report build/timing.json --log build/place_route.log
	$(ICEPACK) build/tiwari.asc build/tiwari.bin
flash: synth
	$(ICEPROG) build/tiwari.bin
clean:
	rm -rf build tools/__pycache__ tests/__pycache__
.PHONY: FORCE
FORCE:
