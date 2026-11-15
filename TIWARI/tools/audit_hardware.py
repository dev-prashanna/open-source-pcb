#!/usr/bin/env python3
"""Validate final native PCB pins, layer count and routing against the manifest.
Run using a Python environment with pcbnew available after native KiCad DRC.
"""
from pathlib import Path
import json
import pcbnew as p
ROOT=Path(__file__).resolve().parents[1]
b=p.LoadBoard(str(ROOT/'hardware/TIWARI.kicad_pcb'))
parts=json.loads((ROOT/'hardware/design.json').read_text())
fps={f.GetReference():f for f in b.GetFootprints()}
assert b.GetCopperLayerCount()==4
assert abs(p.ToMM(b.GetDesignSettings().GetBoardThickness())-1)<.001
checks=0
for part in parts:
 fp=fps[part['ref']]
 for num,net in part['nets'].items():
  pad=next(q for q in fp.Pads()if q.GetNumber()==num)
  assert pad.GetNetname()==net,(part['ref'],num,net,pad.GetNetname())
  checks+=1
for tr in b.GetTracks():
 if not isinstance(tr,p.PCB_VIA):
  assert tr.GetLayer()!=p.In1_Cu,'Ground reference layer contains a signal track'
  assert tr.GetWidth()>=p.FromMM(.15),'Track is below fabrication minimum'
report={'parts':len(parts),'mapped_pins_checked':checks,'copper_layers':4,'board_thickness_mm':1.0,'ground_reference_signal_tracks':0,'result':'PASS'}
(ROOT/'reports/Hardware_Audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
