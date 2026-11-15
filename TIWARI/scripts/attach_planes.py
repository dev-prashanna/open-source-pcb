"""Connect local supply/ground pads to inner planes after signal routing.
Uses exact existing copper geometry and checks every new via on all layers.
"""
from pathlib import Path
import json,math
import pcbnew as p
from shapely.geometry import Polygon,Point,LineString,box
from shapely.strtree import STRtree
ROOT=Path(__file__).resolve().parents[1];path=ROOT/'hardware/TIWARI.kicad_pcb'
b=p.LoadBoard(str(path));layers=[p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu]
# Signal routing is complete; this pass uses the two inner reference planes.
assert all(z.GetLayer() not in [p.F_Cu,p.B_Cu] for z in b.Zones())
g={l:[]for l in layers};nets={l:[]for l in layers};holes=[];extra={l:[]for l in layers}
def xy(q):return p.ToMM(q.x),p.ToMM(q.y)
for fp in b.GetFootprints():
 for pad in fp.Pads():
  for layer in layers:
   if not pad.IsOnLayer(layer):continue
   ps=pad.GetEffectivePolygon(layer)
   for i in range(ps.OutlineCount()):
    ring=ps.COutline(i);poly=Polygon([xy(ring.CPoint(j))for j in range(ring.PointCount())])
    if poly.is_valid:g[layer].append(poly);nets[layer].append(pad.GetNetname())
  ds=pad.GetDrillSize()
  if ds.x:holes.append(Point(*xy(pad.GetPosition())).buffer(max(xy(ds))/2))
existing_vias=[]
for tr in b.GetTracks():
 net=tr.GetNetname()
 if isinstance(tr,p.PCB_VIA):
  pt=xy(tr.GetPosition());geom=Point(*pt).buffer(p.ToMM(tr.GetWidth(p.F_Cu))/2)
  for l in layers:g[l].append(geom);nets[l].append(net)
  holes.append(Point(*pt).buffer(p.ToMM(tr.GetDrill())/2));existing_vias.append((pt,net))
 elif tr.GetLayer()in layers:
  l=tr.GetLayer();geom=LineString([xy(tr.GetStart()),xy(tr.GetEnd())]).buffer(p.ToMM(tr.GetWidth())/2);g[l].append(geom);nets[l].append(net)
trees={l:STRtree(g[l])for l in layers}
def clear(geom,l,net):
 if not box(.3,.3,49.7,34.7).covers(geom):return False
 for i in trees[l].query(geom.buffer(.151)):
  if nets[l][i]!=net and geom.distance(g[l][i])<.151:return False
 return all(n==net or geom.distance(q)>=.151 for q,n in extra[l])
added=[];failed=[]
for fp in b.GetFootprints():
 for pad in fp.Pads():
  net=pad.GetNetname()
  if net not in['GND','+3V3']or pad.GetDrillSize().x or not pad.GetNumber():continue
  if fp.GetReference()=='U1' and pad.GetNumber()=='49':continue
  x,y=xy(pad.GetPosition());layer=p.F_Cu if pad.IsOnLayer(p.F_Cu)else p.B_Cu
  # Reuse a nearby reachable via before drilling another one.
  candidates=sorted(((math.dist((x,y),pt),pt)for pt,n in existing_vias if n==net))
  done=False
  for distance,pt in candidates:
   if distance>1.5:break
   if clear(LineString([(x,y),pt]).buffer(.075),layer,net):
    tr=p.PCB_TRACK(b);tr.SetStart(pad.GetPosition());tr.SetEnd(p.VECTOR2I(*[p.FromMM(v)for v in pt]));tr.SetWidth(p.FromMM(.15));tr.SetLayer(layer);tr.SetNet(pad.GetNet());b.Add(tr);extra[layer].append((LineString([(x,y),pt]).buffer(.075),net));done=True;break
  if done:continue
  for radius in [.65,.8,1.,1.2,1.5,1.8,2.2,2.8,3.5]:
   for angle in range(0,360,15):
    vx=round(x+radius*math.cos(math.radians(angle)),4);vy=round(y+radius*math.sin(math.radians(angle)),4);geom=Point(vx,vy).buffer(.25);hole=Point(vx,vy).buffer(.125)
    if any(hole.distance(q)<.181 for q in holes):continue
    if not all(clear(geom,l,net)for l in layers):continue
    line=LineString([(x,y),(vx,vy)]).buffer(.075)
    if not clear(line,layer,net):continue
    via=p.PCB_VIA(b);via.SetPosition(p.VECTOR2I(p.FromMM(vx),p.FromMM(vy)));via.SetWidth(p.FromMM(.5));via.SetDrill(p.FromMM(.25));via.SetViaType(p.VIATYPE_THROUGH);via.SetLayerPair(p.F_Cu,p.B_Cu);via.SetNet(pad.GetNet());b.Add(via)
    tr=p.PCB_TRACK(b);tr.SetStart(pad.GetPosition());tr.SetEnd(via.GetPosition());tr.SetWidth(p.FromMM(.15));tr.SetLayer(layer);tr.SetNet(pad.GetNet());b.Add(tr)
    for l in layers:extra[l].append((geom,net))
    extra[layer].append((line,net));holes.append(hole);existing_vias.append(((vx,vy),net));added.append({'ref':fp.GetReference(),'pin':pad.GetNumber(),'net':net,'via':[vx,vy]});done=True;break
   if done:break
  if not done:failed.append({'ref':fp.GetReference(),'pin':pad.GetNumber(),'net':net})
p.ZONE_FILLER(b).Fill(b.Zones());b.BuildConnectivity();p.SaveBoard(str(path),b)
(ROOT/'reports/final_plane_drops.json').write_text(json.dumps({'added':added,'no_new_drop':failed},indent=2));print('Added',len(added),'local plane drops;',len(failed),'pads had no legal new drop; DRC determines connectivity')
