"""Apply final manufacturing widths, useful silkscreen, and outer ground pours."""
from pathlib import Path
import pcbnew as p
ROOT=Path(__file__).resolve().parents[1];path=ROOT/'hardware/TIWARI.kicad_pcb'
b=p.LoadBoard(str(path))
# Autorouter neckdowns must obey the same fabrication minimum as other traces.
for tr in b.GetTracks():
 if not isinstance(tr,p.PCB_VIA)and tr.GetWidth()<p.FromMM(.15):tr.SetWidth(p.FromMM(.15))
# Continuous inner ground/power planes are retained.
# Remove one library marker that overlaps an adjacent decoupler's mask opening.
for fp in b.GetFootprints():
 if fp.GetReference()=='U1':
  for shape in list(fp.GraphicalItems()):
   if shape.GetLayer()==p.F_SilkS:shape.SetLayer(p.F_Fab)
# Own labels will be regenerated without duplicating older copies.
for item in list(b.GetDrawings()):
 if isinstance(item,p.PCB_TEXT) and item.GetLayer()in[p.F_SilkS,p.B_SilkS]:b.Remove(item)
def text(s,x,y,size=.8,layer=p.F_SilkS,angle=0):
 t=p.PCB_TEXT(b);t.SetText(s);t.SetPosition(p.VECTOR2I(p.FromMM(x),p.FromMM(y)));t.SetTextSize(p.VECTOR2I(p.FromMM(size),p.FromMM(size)));t.SetTextThickness(p.FromMM(.12 if size<1.5 else .2));t.SetLayer(layer);t.SetTextAngle(p.EDA_ANGLE(angle,p.DEGREES_T));t.SetMirrored(layer==p.B_SilkS);b.Add(t)
text('TIWARI',36.5,7.8,2.0)
text('8-BIT / OPEN CPU',36.5,10.1,.8)
text('TIWARI',37,7.0,3,p.B_SilkS)
text('YOUR CPU. YOUR BOARD.',37,10,.85,p.B_SilkS)
text('TW8-A0  |  36MHz  |  3V3 I/O',36,28.5,.8,p.B_SilkS)
text('OPEN HARDWARE',36,30,.8,p.B_SilkS)
for x,y,labels in [(22,5.3,['G','3V3']+[str(i)for i in range(8,16)]),(22,29.7,['G','3V3']+[str(i)for i in range(8)])]:
 for i,label in enumerate(labels):text(label,x+i*2.54,y,.7)
text('RESET',44,6.0,.7);text('RELOAD',44,21,.7)
text('PWR',2.5,26.2,.7);text('USER',44,22.3,.7);text('FAULT',44,28.8,.7)
text('USB-C',7,33,.8,p.B_SilkS)
p.ZONE_FILLER(b).Fill(b.Zones());b.BuildConnectivity();p.SaveBoard(str(path),b)
print('Finished board widths, ground pours and TIWARI branding')
