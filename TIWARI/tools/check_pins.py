#!/usr/bin/env python3
"""Check FPGA constraint pins against the published schematic manifest."""
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
parts=json.loads((ROOT/'hardware/design.json').read_text())
fpga=next(part for part in parts if part['ref']=='U1')
expected={'clk_12m':'CLK12','reset_n':'CPU_RESET_N','uart_rx':'UART_TO_CPU','uart_tx':'UART_FROM_CPU','user_led':'USER_LED','fault_led':'FAULT_LED','pwm[0]':'PWM0','pwm[1]':'PWM1'}
expected.update({f'gpio[{i}]':f'D{i}'for i in range(16)})
actual={}
for line in (ROOT/'hardware/TIWARI.pcf').read_text().splitlines():
 if line.startswith('set_io '):
  _,name,pin=line.split()
  assert name not in actual,f'duplicate signal {name}'
  actual[name]=pin
assert actual.keys()==expected.keys(),'top-level signal set differs'
assert len(set(actual.values()))==len(actual),'physical pin reused'
for name,pin in actual.items():
 assert fpga['nets'].get(pin)==expected[name],f'{name}: pin {pin} is {fpga["nets"].get(pin)}'
print(f'PASS: {len(actual)} FPGA pin constraints match schematic net manifest')
