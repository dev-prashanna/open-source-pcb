"""Place readable legends without masking copper; retain full refs on F/B.Fab."""
from cadlib import *
import pcbnew as p
import re
path=ROOT/'RoveCore_One.kicad_pcb';doc=sx.loads(path.read_text())
doc=[n for n in doc if not(isinstance(n,list) and n and str(n[0])=='gr_text' and atom(n,'layer') in ['F.SilkS','B.SilkS'])]
path.write_text(sx.dumps(doc))
b=p.LoadBoard(str(path));fps=list(b.GetFootprints());occupied={p.F_SilkS:[],p.B_SilkS:[]}
def rect(z):
 r=z.GetBoundingBox();return p.ToMM(r.GetX()),p.ToMM(r.GetY()),p.ToMM(r.GetRight()),p.ToMM(r.GetBottom())
def ov(a,z,m=.13):return min(a[2],z[2])-max(a[0],z[0])>-m and min(a[3],z[3])-max(a[1],z[1])>-m
# Delete only generated free legends from previous runs; keep copper and board outline.
for fp in fps:
 fp.GetField(p.FIELD_T_REFERENCE).SetVisible(False)
 for z in list(fp.GraphicalItems()):
  if z.GetLayer() in [p.F_SilkS,p.B_SilkS]:
   # Existing outline marks are valid unless covered by an exposed pad on this layer.
   bad=False
   for of in fps:
    for pad in of.Pads():
     mask=p.F_Mask if z.GetLayer()==p.F_SilkS else p.B_Mask
     if pad.IsOnLayer(mask) and ov(rect(z),rect(pad),.08):bad=True;break
    if bad:break
   if bad:z.SetLayer(p.F_Fab if z.GetLayer()==p.F_SilkS else p.B_Fab)
   else:occupied[z.GetLayer()].append(rect(z))
# Text must avoid exposed pads and component body courtyards (assembled visibility).
pads={p.F_SilkS:[],p.B_SilkS:[]};bodies={p.F_SilkS:[],p.B_SilkS:[]}
for fp in fps:
 for pad in fp.Pads():
  for silk,mask in [(p.F_SilkS,p.F_Mask),(p.B_SilkS,p.B_Mask)]:
   if pad.IsOnLayer(mask):pads[silk].append(rect(pad))
 for silk,cy in [(p.F_SilkS,p.F_CrtYd),(p.B_SilkS,p.B_CrtYd)]:
  for z in fp.GraphicalItems():
   if z.GetLayer()==cy:bodies[silk].append(rect(z))
def legend(txt,target,layer,size=.65,body_avoid=True,maxrad=15):
 t=p.PCB_TEXT(b);t.SetText(txt);t.SetLayer(layer);t.SetTextSize(p.VECTOR2I(p.FromMM(size),p.FromMM(size)));t.SetTextThickness(p.FromMM(.1));t.SetMirrored(layer==p.B_SilkS)
 offsets=[(x*.5,y*.5) for x in range(-maxrad*2,maxrad*2+1) for y in range(-maxrad*2,maxrad*2+1)];offsets.sort(key=lambda v:v[0]**2+v[1]**2)
 for dx,dy in offsets:
  for angle in [0,90]:
   t.SetTextAngle(p.EDA_ANGLE(angle,p.DEGREES_T));t.SetPosition(p.VECTOR2I(p.FromMM(target[0]+dx),p.FromMM(target[1]+dy)));r=rect(t)
   if r[0]<.4 or r[1]<.4 or r[2]>79.6 or r[3]>64.6:continue
   if any(ov(r,z) for z in pads[layer]+occupied[layer]):continue
   if body_avoid and any(ov(r,z,.05) for z in bodies[layer]):continue
   occupied[layer].append(r);b.Add(t);return True
 return False
names={'J1':'PROG','J2':'USB-C','J3':'2S BAT','J4':'5V IN','J5':'SV EXT','J6':'VM IN','J7':'MOTOR A','J8':'MOTOR B','J9':'SONAR','J10':'ENC L','J11':'ENC R','J12':'S1','J13':'S2','J14':'S3','J15':'S4','J16':'I2C','J17':'SPI','J18':'GPS UART','J19':'EXP 3V3','J20':'GPIO SHARED','J21':'GPIO INPUTS','J22':'ADC 3V3','J23':'LOAD 5V','JP1':'SV SELECT','SW1':'RESET','SW2':'BOOT','SW3':'USER'}
failed=[]
for fp in sorted(fps,key=lambda f:0 if f.GetReference() in names else 1):
 ref=fp.GetReference();pt=fp.GetPosition();target=p.ToMM(pt.x),p.ToMM(pt.y)
 layer=p.F_SilkS if fp.GetLayer()==p.F_Cu else p.B_SilkS
 label=ref+' '+names[ref] if ref in names else ref
 if not legend(label,target,layer,maxrad=8 if ref in names else 5):
  # Full assembly designators are retained in a separate Fab field.
  failed.append(ref)
  fp.GetField(p.FIELD_T_REFERENCE).SetLayer(p.F_Fab if fp.GetLayer()==p.F_Cu else p.B_Fab);fp.GetField(p.FIELD_T_REFERENCE).SetVisible(True)
legend('P-TIWARI', (22,21.5),p.F_SilkS,1.1,True,5)
legend('P-TIWARI', (23,11),p.B_SilkS,1.1,False,15)
for ref in ['J20','J21','J23']:
 if ref in failed:
  pt=next(f.GetPosition() for f in fps if f.GetReference()==ref)
  legend(ref+' '+names[ref],(p.ToMM(pt.x),p.ToMM(pt.y)),p.B_SilkS,.65,False,12)
legend('A.0  |  3V3 LOGIC', (23,14),p.B_SilkS,.8,False,15)
legend('NO ONBOARD CHARGER', (20,59),p.B_SilkS,.65,False,10)
legend('1:G 2:+ 3:S', (60,19),p.B_SilkS,.65,False,10)
# Back-layer mirror changes only rendering, not coordinates or connector numbering.
p.SaveBoard(str(ROOT/'RoveCore_One.kicad_pcb'),b)
(ROOT/'reports/Silkscreen.json').write_text(json.dumps({'references_on_fab_only':failed,'connector_legends':names},indent=2))
print('Silkscreen placed;',len(failed),'dense assembly references moved to Fab layer')
