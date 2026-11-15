"""Readable TIWARI branding, reviewed FPGA footprint and assembly models."""
from pathlib import Path
import pcbnew as p
ROOT=Path(__file__).resolve().parents[1];H=ROOT/'hardware';path=H/'TIWARI.kicad_pcb'
b=p.LoadBoard(str(path))
for t in b.GetDrawings():
 if not isinstance(t,p.PCB_TEXT):continue
 s=t.GetText();x,y=p.ToMM(t.GetPosition().x),p.ToMM(t.GetPosition().y)
 if t.GetLayer()==p.F_SilkS:
  if abs(y-5.3)<.1:y=.8
  if s=='TIWARI':x,y=34.6,9.2;t.SetTextSize(p.VECTOR2I(p.FromMM(1.6),p.FromMM(1.6)))
  elif s=='8-BIT / OPEN CPU':x,y=34.6,11;t.SetTextSize(p.VECTOR2I(p.FromMM(.7),p.FromMM(.7)))
  elif s=='PWR':x,y=3,26.5;t.SetLayer(p.B_SilkS);t.SetMirrored(True)
  elif s=='RELOAD':x,y=44,21.8
  elif s=='USER':x,y=46.5,24
  elif s=='FAULT':x,y=46.5,27.5
 elif s in ['YOUR CPU. YOUR BOARD.','YOUR CPU.\nYOUR BOARD.']:
  x,y=42,12.8;t.SetText('YOUR CPU.\nYOUR BOARD.');t.SetTextSize(p.VECTOR2I(p.FromMM(.8),p.FromMM(.8)))
 t.SetPosition(p.VECTOR2I(p.FromMM(x),p.FromMM(y)))
fp=next(f for f in b.GetFootprints()if f.GetReference()=='U1')
fp.SetFPID(p.LIB_ID('TIWARI','UP5K_SG48_Reviewed'))
fp.Models().clear();model=p.FP_3DMODEL();model.m_Filename='${KIPRJMOD}/libraries/3d/QFN48_7mm_visual.step';fp.Add3DModel(model)
p.FootprintSave(str(H/'libraries/TIWARI.pretty'),fp)
p.SaveBoard(str(path),b)
print('Updated labels and localized reviewed FPGA footprint')
