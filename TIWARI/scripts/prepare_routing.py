"""Add short plane drops, fill reference planes and export outer-layer routing."""
from pathlib import Path
import json,math,re
import pcbnew as p
from shapely.geometry import Point,LineString,box
from shapely.affinity import rotate,translate
ROOT=Path(__file__).resolve().parents[1];path=ROOT/'hardware/TIWARI.kicad_pcb'
b=p.LoadBoard(str(path));layers=[p.F_Cu,p.B_Cu,p.In1_Cu,p.In2_Cu]
obstacles={layer:[]for layer in layers};holes=[]
def xy(pos):return p.ToMM(pos.x),p.ToMM(pos.y)
for fp in b.GetFootprints():
 for pad in fp.Pads():
  x,y=xy(pad.GetPosition());sx,sy=xy(pad.GetSize());geom=translate(rotate(box(-sx/2,-sy/2,sx/2,sy/2),pad.GetOrientationDegrees(),origin=(0,0)),x,y)
  for layer in layers:
   if pad.IsOnLayer(layer):obstacles[layer].append((geom,pad.GetNetname()))
  dx,dy=xy(pad.GetDrillSize())
  if dx:holes.append(Point(x,y).buffer(max(dx,dy)/2))
def clear(geom,layer,net):return all(net==n or geom.distance(g)>=.151 for g,n in obstacles[layer])
def track(start,end,layer,net,width=.15):
 t=p.PCB_TRACK(b);t.SetStart(p.VECTOR2I(*[p.FromMM(v)for v in start]));t.SetEnd(p.VECTOR2I(*[p.FromMM(v)for v in end]));t.SetLayer(layer);t.SetWidth(p.FromMM(width));t.SetNet(b.FindNet(net));b.Add(t);obstacles[layer].append((LineString([start,end]).buffer(width/2),net))
def via(x,y,net):
 v=p.PCB_VIA(b);v.SetPosition(p.VECTOR2I(p.FromMM(x),p.FromMM(y)));v.SetWidth(p.FromMM(.5));v.SetDrill(p.FromMM(.25));v.SetViaType(p.VIATYPE_THROUGH);v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetNet(b.FindNet(net));b.Add(v)
 g=Point(x,y).buffer(.25)
 for layer in layers:obstacles[layer].append((g,net))
 holes.append(Point(x,y).buffer(.125))
added=[];failed=[]
for fp in b.GetFootprints():
 for pad in fp.Pads():
  net=pad.GetNetname()
  if net not in ['GND','+3V3'] or pad.GetDrillSize().x:continue
  x,y=xy(pad.GetPosition());layer=p.F_Cu if pad.IsOnLayer(p.F_Cu)else p.B_Cu
  # Large exposed ground paddle: four filled/capped thermal vias.
  if fp.GetReference()=='U1' and pad.GetNumber()=='49':
   for dx,dy in [(-1,-1),(1,-1),(-1,1),(1,1)]:via(x+dx,y+dy,net)
   added.append({'ref':'U1','pin':'49','thermal_vias':4});continue
  found=False
  for radius in [.65,.8,1.,1.2,1.5,1.8,2.2,2.8]:
   for angle in range(0,360,15):
    vx=round(x+radius*math.cos(math.radians(angle)),4);vy=round(y+radius*math.sin(math.radians(angle)),4)
    if not(.6<vx<49.4 and .6<vy<34.4):continue
    geom=Point(vx,vy).buffer(.25);hole=Point(vx,vy).buffer(.125)
    if any(hole.distance(g)<.251 for g in holes):continue
    if not all(clear(geom,l,net)for l in layers):continue
    line=LineString([(x,y),(vx,vy)]).buffer(.075)
    if not clear(line,layer,net):continue
    via(vx,vy,net);track((x,y),(vx,vy),layer,net)
    added.append({'ref':fp.GetReference(),'pin':pad.GetNumber(),'net':net,'via':[vx,vy]});found=True;break
   if found:break
  if not found:failed.append({'ref':fp.GetReference(),'pin':pad.GetNumber(),'net':net})
# Sparse additional stitching joins the ground reference and outer ground drops.
for x in range(2,49,5):
 for y in range(2,34,5):
  geom=Point(x,y).buffer(.25);hole=Point(x,y).buffer(.125)
  if all(clear(geom,l,'GND')for l in layers)and all(hole.distance(g)>.251 for g in holes):via(x,y,'GND')
p.ZONE_FILLER(b).Fill(b.Zones());b.BuildConnectivity();p.SaveBoard(str(path),b)
(ROOT/'reports/plane_drops.json').write_text(json.dumps({'added':added,'incomplete':failed},indent=2))
print('Plane drops',len(added),'unresolved',failed,flush=True)
# Export planes as real DSN planes, retaining plane-net connectivity.
dsn=ROOT/'reports/TIWARI.dsn';assert p.ExportSpecctraDSN(b,str(dsn));s=dsn.read_text()
for name in ['In1.Cu','In2.Cu']:s=s.replace(f'(layer {name}\n      (type signal)',f'(layer {name}\n      (type power)')
s=s.replace('(clearance 37.5 (type smd_smd))','(clearance 150 (type smd_smd))')
dsn.write_text(s)
