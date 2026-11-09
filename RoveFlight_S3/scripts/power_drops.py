"""Connect accessible logic/sensor pads to local power copper."""
"""Connect ground and quiet sensor power using clearance-tested short escapes.
No signal layer is routed on In1. Geometric checks include every pad and track.
"""
from cadlib import *
import pcbnew as p
from shapely.geometry import Point,LineString,Polygon
from shapely.strtree import STRtree
import numpy as np
b=p.LoadBoard(str(ROOT/'RoveFlight_S3.kicad_pcb'));layers=[p.F_Cu,p.In1_Cu,p.In2_Cu,p.In3_Cu,p.In4_Cu,p.B_Cu]
geoms={l:[] for l in layers};owners={l:[] for l in layers};smd={l:[] for l in layers};holes=[]
def addgeom(g,l,n):geoms[l].append(g);owners[l].append(n)
for fp in b.GetFootprints():
 for pad in fp.Pads():
  for layer in layers:
   if not pad.IsOnLayer(layer):continue
   poly=pad.GetEffectivePolygon(layer)
   for oi in range(poly.OutlineCount()):
    a=poly.COutline(oi);g=Polygon([(p.ToMM(a.CPoint(i).x),p.ToMM(a.CPoint(i).y)) for i in range(a.PointCount())])
    if g.is_valid:
     addgeom(g,layer,pad.GetNetname())
     if pad.GetAttribute()==p.PAD_ATTRIB_SMD:smd[layer].append(g)
  drill=pad.GetDrillSize()
  if drill.x:
   pt=pad.GetPosition();holes.append(Point(p.ToMM(pt.x),p.ToMM(pt.y)).buffer(max(p.ToMM(drill.x),p.ToMM(drill.y))/2))
  if pad.GetAttribute()==p.PAD_ATTRIB_NPTH and drill.x:
   pt=pad.GetPosition();g=Point(p.ToMM(pt.x),p.ToMM(pt.y)).buffer(max(p.ToMM(drill.x),p.ToMM(drill.y))/2)
   for l in layers:addgeom(g,l,'__HOLE')
for tr in b.GetTracks():
 a=tr.GetStart();z=tr.GetEnd();n=tr.GetNetname()
 if isinstance(tr,p.PCB_VIA):
  g=Point(p.ToMM(a.x),p.ToMM(a.y)).buffer(p.ToMM(tr.GetWidth(p.F_Cu))/2)
  holes.append(Point(p.ToMM(a.x),p.ToMM(a.y)).buffer(p.ToMM(tr.GetDrill())/2))
  for l in layers:addgeom(g,l,n)
 else:addgeom(LineString([(p.ToMM(a.x),p.ToMM(a.y)),(p.ToMM(z.x),p.ToMM(z.y))]).buffer(p.ToMM(tr.GetWidth())/2),tr.GetLayer(),n)
trees={l:STRtree(geoms[l]) for l in layers}
smdtrees={l:STRtree(smd[l]) for l in layers}
extra={l:[] for l in layers}
def clear(g,l,net):
 for idx in trees[l].query(g.buffer(.16)):
  if owners[l][idx]!=net and g.distance(geoms[l][idx])<.149:return False
 for other,on in extra[l]:
  if on!=net and g.distance(other)<.149:return False
 return True
def via(x,y,net):
 v=p.PCB_VIA(b);v.SetPosition(p.VECTOR2I(p.FromMM(x),p.FromMM(y)));v.SetWidth(p.FromMM(.6));v.SetDrill(p.FromMM(.3));v.SetViaType(p.VIATYPE_THROUGH);v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetNet(b.FindNet(net));b.Add(v)
 g=Point(x,y).buffer(.3)
 for l in layers:extra[l].append((g,net))
 holes.append(Point(x,y).buffer(.15))
def drilling_clear(x,y):
 g=Point(x,y).buffer(.3);h=Point(x,y).buffer(.15)
 if any(h.distance(old)<.249 for old in holes):return False
 for l in layers:
  if any(g.distance(smd[l][idx])<.08 for idx in smdtrees[l].query(g.buffer(.09))):return False
 return True
def track(a,z,layer,net,width=.135):
 t=p.PCB_TRACK(b);t.SetStart(p.VECTOR2I(p.FromMM(a[0]),p.FromMM(a[1])));t.SetEnd(p.VECTOR2I(p.FromMM(z[0]),p.FromMM(z[1])));t.SetWidth(p.FromMM(width));t.SetLayer(layer);t.SetNet(b.FindNet(net));b.Add(t);extra[layer].append((LineString([a,z]).buffer(width/2),net))
added=[];failed=[]
for fp in b.GetFootprints():
 for pad in fp.Pads():
  net=pad.GetNetname()
  if net not in ['+3V3','+3V3_SENS'] or pad.GetAttribute()!=p.PAD_ATTRIB_SMD:continue
  a=pad.GetPosition();x,y=p.ToMM(a.x),p.ToMM(a.y);layer=p.F_Cu if pad.IsOnLayer(p.F_Cu) else p.B_Cu;found=False
  for r in [.6,.8,1.,1.3,1.6,2.,2.5,3.,4.]:
   for i in range(24):
    vx,vy=round(x+r*math.cos(i*math.pi/12),4),round(y+r*math.sin(i*math.pi/12),4)
    if not(10.5<vx<34.5 and 1.5<vy<42.5):continue
    if net=='+3V3_SENS' and not(10.5<vx<25.0 and 20.5<vy<30.5):continue
    if net=='+3V3' and 9.5<vx<26.0 and 19.5<vy<31.5:continue
    g=Point(vx,vy).buffer(.225);h=Point(vx,vy).buffer(.1)
    if any(h.distance(old)<.28 for old in holes):continue
    if any(g.distance(smd[l][idx])<.1 for l in layers for idx in smdtrees[l].query(g.buffer(.11))):continue
    if not all(clear(g.buffer(.04),l,net) for l in layers):continue
    line=LineString([(x,y),(vx,vy)]).buffer(.0675)
    if not clear(line.buffer(.04),layer,net):continue
    v=p.PCB_VIA(b);v.SetPosition(p.VECTOR2I(p.FromMM(vx),p.FromMM(vy)));v.SetWidth(p.FromMM(.45));v.SetDrill(p.FromMM(.2));v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetViaType(p.VIATYPE_THROUGH);v.SetNet(b.FindNet(net));b.Add(v);holes.append(h)
    for l in layers:extra[l].append((g,net))
    track((x,y),(vx,vy),layer,net,.135);added.append({'ref':fp.GetReference(),'pad':pad.GetNumber(),'net':net,'via':[vx,vy]});found=True;break
   if found:break
  if not found:failed.append([fp.GetReference(),pad.GetNumber(),net])
p.ZONE_FILLER(b).Fill(b.Zones());b.BuildConnectivity();p.SaveBoard(str(ROOT/'RoveFlight_S3.kicad_pcb'),b)
(ROOT/'reports/Logic_Power_Drops.json').write_text(json.dumps({'added':added,'not_dropped':failed},indent=2));print('Added',len(added),'logic drops;',len(failed),'require routed connections')
