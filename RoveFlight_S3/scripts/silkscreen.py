"""Place readable legends without masking copper; retain full refs on F/B.Fab."""
from cadlib import *
import pcbnew as p
import re
path=ROOT/'RoveFlight_S3.kicad_pcb';doc=sx.loads(path.read_text())
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
   bad=rect(z)[1]<.2
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
  rs=[rect(z) for z in fp.GraphicalItems() if z.GetLayer()==cy]
  if rs:
   body=(min(r[0] for r in rs),min(r[1] for r in rs),max(r[2] for r in rs),max(r[3] for r in rs))
   if fp.GetReference()=='U1':body=(12.725,-6.75,32.275,19.475)
   bodies[silk].append(body)
def legend(txt,target,layer,size=.65,body_avoid=True,maxrad=15):
 t=p.PCB_TEXT(b);t.SetText(txt);t.SetLayer(layer);t.SetTextSize(p.VECTOR2I(p.FromMM(size),p.FromMM(size)));t.SetTextThickness(p.FromMM(.1));t.SetMirrored(layer==p.B_SilkS)
 offsets=[(x*.5,y*.5) for x in range(-maxrad*2,maxrad*2+1) for y in range(-maxrad*2,maxrad*2+1)];offsets.sort(key=lambda v:v[0]**2+v[1]**2)
 for dx,dy in offsets:
  for angle in [0,90]:
   t.SetTextAngle(p.EDA_ANGLE(angle,p.DEGREES_T));t.SetPosition(p.VECTOR2I(p.FromMM(target[0]+dx),p.FromMM(target[1]+dy)));r=rect(t)
   if r[0]<.4 or r[1]<.4 or r[2]>44.6 or r[3]>44.6:continue
   if any(ov(r,z) for z in pads[layer]+occupied[layer]):continue
   if body_avoid and any(ov(r,z,.05) for z in bodies[layer]):continue
   occupied[layer].append(r);b.Add(t);return True
 return False
names={'J1':'USB','J2':'1S BAT','J3':'M1','J4':'M2','J5':'M3','J6':'M4','J7':'RC 3V3','J8':'FLOW SPI','J9':'DEBUG','J10':'I2C','JP1':'ARM LINK','SW1':'RESET','SW2':'BOOT','SW3':'KILL','U8':'IMU','U9':'BARO','U10':'TOF DOWN'}
failed=[]
for fp in sorted(fps,key=lambda f:0 if f.GetReference() in names else 1):
 ref=fp.GetReference();pt=fp.GetPosition();target=p.ToMM(pt.x),p.ToMM(pt.y)
 layer=p.F_SilkS if fp.GetLayer()==p.F_Cu else p.B_SilkS
 label=ref+' '+names[ref] if ref in names else ref
 if not legend(label,target,layer,maxrad=8 if ref in names else 5):
  # Full assembly designators are retained in a separate Fab field.
  failed.append(ref)
  fp.GetField(p.FIELD_T_REFERENCE).SetLayer(p.F_Fab if fp.GetLayer()==p.F_Cu else p.B_Fab);fp.GetField(p.FIELD_T_REFERENCE).SetVisible(True)
legend('ROVEFLIGHT S3',(22.5,31),p.F_SilkS,.8,True,8)
legend('A.0 | 1S BRUSHED',(22.5,4),p.B_SilkS,.7,False,8)
legend('FWD ^',(22.5,20.5),p.F_SilkS,.7,True,3)
legend('REMOVE JP1 TO DISARM',(22.5,39),p.B_SilkS,.6,True,8)
legend('NO CHARGER',(22.5,41),p.B_SilkS,.6,True,8)
# Back-layer mirror changes only rendering, not coordinates or connector numbering.
p.SaveBoard(str(ROOT/'RoveFlight_S3.kicad_pcb'),b)
(ROOT/'reports/Silkscreen.json').write_text(json.dumps({'references_on_fab_only':failed,'connector_legends':names},indent=2))
print('Silkscreen placed;',len(failed),'dense assembly references moved to Fab layer')
