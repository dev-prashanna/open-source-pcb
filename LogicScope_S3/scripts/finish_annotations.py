from cadlib import *
import pcbnew as p
b=p.LoadBoard(str(ROOT/'LogicScope_S3.kicad_pcb'))
for t in b.GetDrawings():
 if not isinstance(t,p.PCB_TEXT) or t.GetLayer()!=p.B_SilkS:continue
 if t.GetText() in ['GND','TX','RX'] and p.ToMM(t.GetPosition().x)==51:t.SetPosition(p.VECTOR2I(p.FromMM(48.2),t.GetPosition().y))
 if t.GetText()=='REF ONLY - NO TARGET POWER':t.SetPosition(p.VECTOR2I(p.FromMM(29),p.FromMM(3)))
for text,x,y in [('REF ONLY',12.5,30.5),('PWR',52.7,35.5),('CAP',45,24)]:
 t=p.PCB_TEXT(b);t.SetText(text);t.SetLayer(p.F_SilkS);t.SetPosition(p.VECTOR2I(p.FromMM(x),p.FromMM(y)));t.SetTextSize(p.VECTOR2I(p.FromMM(.7),p.FromMM(.7)));t.SetTextThickness(p.FromMM(.1));b.Add(t)
p.SaveBoard(str(ROOT/'LogicScope_S3.kicad_pcb'),b)
