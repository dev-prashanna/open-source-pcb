# Extend existing silk with operating labels, retaining checked channel markings.
source=open('scripts/label_board.py').read().split('for i in range(5):')[0]
source=source.replace("r=fps[ref].GetBoundingBox(False,False);obstacles.append(box(p.ToMM(r.GetX()),p.ToMM(r.GetY()),p.ToMM(r.GetRight()),p.ToMM(r.GetBottom())))","r=fps[ref].GetBoundingBox(False,False);obstacles.append(box(27.225,-6.75,46.775,19.475) if ref=='U1' else box(p.ToMM(r.GetX()),p.ToMM(r.GetY()),p.ToMM(r.GetRight()),p.ToMM(r.GetBottom())))")
exec(source)
fps['R25'].Reference().SetLayer(p.F_Fab);fps['R25'].Reference().SetPosition(fps['R25'].GetPosition())
for d in b.GetDrawings():
 if isinstance(d,p.PCB_TEXT) and d.GetLayer()==p.F_Fab and d.GetText()=='R26':d.SetPosition(fps['R26'].GetPosition())
for fp in b.GetFootprints():
 if fp.Reference().GetLayer()==p.F_SilkS and fp.Reference().IsVisible():obstacles.append(bbox(fp.Reference()).buffer(.06))
# Rotate the button names into the free edge margin.
labels=[('GND',6.,18.,0),('REF ONLY',5.5,20.,0),('GND',5.5,35.7,0),('RESET',53.7,22.,90),('BOOT',53.7,27.,90),('PWR',50.5,35.6,0),('CAP',45.,24.4,0)]
for text,x,y,angle in labels:
 okay=False
 for dx,dy in [(0,0)]+sorted([(i*.1,j*.1) for i in range(-10,11) for j in range(-10,11)],key=lambda q:q[0]**2+q[1]**2):
  # no verbose log per fallback trial
  t=p.PCB_TEXT(b);t.SetText(text);t.SetLayer(p.F_SilkS);t.SetTextSize(p.VECTOR2I(p.FromMM(.7),p.FromMM(.7)));t.SetTextThickness(p.FromMM(.1));t.SetTextAngle(p.EDA_ANGLE(angle,p.DEGREES_T));t.SetPosition(p.VECTOR2I(p.FromMM(x+dx),p.FromMM(y+dy)))
  if fits(t):b.Add(t);obstacles.append(bbox(t).buffer(.06));print('Added',text,x+dx,y+dy);okay=True;break
 if not okay:print('No location for',text)
# Mark debug pin functions on rear where cable pinout remains readable.
for text,x,y in [('GND',51,5),('TX',51,7.54),('RX',51,10.08),('0-5V INPUTS',12,22),('COMMON GROUND',12,24),('REF ONLY - NO TARGET POWER',28,38)]:
 t=p.PCB_TEXT(b);t.SetText(text);t.SetLayer(p.B_SilkS);t.SetMirrored(True);t.SetPosition(p.VECTOR2I(p.FromMM(x),p.FromMM(y)));t.SetTextSize(p.VECTOR2I(p.FromMM(.8),p.FromMM(.8)));t.SetTextThickness(p.FromMM(.12));b.Add(t)
p.SaveBoard(str(ROOT/'LogicScope_S3.kicad_pcb'),b)
