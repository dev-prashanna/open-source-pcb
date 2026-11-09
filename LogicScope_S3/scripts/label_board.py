"""Readable channel labels and collision-checked native reference designators."""
from route_utils import *
obstacles=[]
def bbox(item):
 r=item.GetBoundingBox();return box(p.ToMM(r.GetX()),p.ToMM(r.GetY()),p.ToMM(r.GetRight()),p.ToMM(r.GetBottom()))
for f in b.GetFootprints():
 for q in f.Pads():
  if q.IsOnLayer(p.F_Cu):obstacles.append(bbox(q).buffer(.13))
 for d in f.GraphicalItems():
  if d.GetLayer()==p.F_SilkS:obstacles.append(bbox(d).buffer(.06))
for d in b.GetDrawings():
 if d.GetLayer()==p.F_SilkS:obstacles.append(bbox(d).buffer(.06))
# Do not put visible text under module shield, connector body or button caps.
for ref in ['U1','J1','J2','J3','J4','SW1','SW2','L1']:
 r=fps[ref].GetBoundingBox(False,False);obstacles.append(box(p.ToMM(r.GetX()),p.ToMM(r.GetY()),p.ToMM(r.GetRight()),p.ToMM(r.GetBottom())))

def fits(t):
 r=bbox(t).buffer(.04)
 return box(.3,.3,54.7,39.7).covers(r) and not any(r.intersects(g) for g in obstacles)
def add(text,x,y,size=.7,angle=0):
 t=p.PCB_TEXT(b);t.SetText(text);t.SetLayer(p.F_SilkS);t.SetTextSize(p.VECTOR2I(p.FromMM(size),p.FromMM(size)));t.SetTextThickness(p.FromMM(.1));t.SetTextAngle(p.EDA_ANGLE(angle,p.DEGREES_T));t.SetPosition(p.VECTOR2I(p.FromMM(x),p.FromMM(y)))
 if not fits(t):print('Label needs review',text,x,y,bbox(t).bounds,[g.bounds for g in obstacles if bbox(t).buffer(.04).intersects(g)],flush=True);return False
 b.Add(t);obstacles.append(bbox(t).buffer(.06));return True
for i in range(5):assert add('CH'+str(i),1.0,5+2.54*i,angle=90)
for i in range(3):assert add('CH'+str(5+i),1.0,23+2.54*i,angle=90)
assert add('REF',1.0,30.62,angle=90)
assert add('NC',1.0,33.16,angle=90)
for label,x,y,size in [('GND',6,17.4,.7),('REF ONLY',5.5,20.9,.7),('GND',5.5,35.3,.7),('RESET',50,24.7,.7),('BOOT',50,29.2,.7),('PWR',51.5,35,.7),('CAP',48.2,19.7,.7),('LOGICSCOPE S3',14.8,38.8,.8)]:
 add(label,x,y,size)
placed=[];fab=[]
for ref,fp in sorted(fps.items(),key=lambda kv:(0 if kv[0].startswith('TP') else 1,kv[0])):
 t=fp.Reference();t.SetLayer(p.F_SilkS);t.SetTextSize(p.VECTOR2I(p.FromMM(.7),p.FromMM(.7)));t.SetTextThickness(p.FromMM(.1));t.SetTextAngle(p.EDA_ANGLE(0,p.DEGREES_T));t.SetVisible(True)
 x,y=xy(fp);good=False
 # Perimeter-first candidates keep references near the corresponding body.
 offsets=sorted([(i*.25,j*.25) for i in range(-12,13) for j in range(-12,13) if abs(i)>2 or abs(j)>2],key=lambda q: q[0]**2+q[1]**2)
 for dx,dy in offsets:
  t.SetPosition(p.VECTOR2I(p.FromMM(x+dx),p.FromMM(y+dy)))
  if fits(t):obstacles.append(bbox(t).buffer(.06));placed.append(ref);good=True;break
 if not good:
  t.SetLayer(p.F_Fab);t.SetPosition(fp.GetPosition());fab.append(ref)
# Add assembly reference text for all parts, including ones whose silk is omitted.
for ref,fp in fps.items():
 if ref in fab:continue
 t=p.PCB_TEXT(b);t.SetText(ref);t.SetLayer(p.F_Fab);t.SetTextSize(p.VECTOR2I(p.FromMM(.7),p.FromMM(.7)));t.SetTextThickness(p.FromMM(.1));t.SetPosition(fp.GetPosition());b.Add(t)
p.SaveBoard(str(ROOT/'LogicScope_S3.kicad_pcb'),b)
(ROOT/'reports/Silkscreen.json').write_text(json.dumps({'silk_references':placed,'assembly_only_references':fab},indent=2)+'\n')
print('References:',len(placed),'silk,',len(fab),'Fab only; all references in assembly drawing')
