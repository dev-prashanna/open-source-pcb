"""Stitch actual outer-layer ground islands to both inner reference planes."""
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

existing=[]
for fp in b.GetFootprints():
 for pad in fp.Pads():
  if pad.GetNetname()=='GND' and pad.GetDrillSize().x:
   q=pad.GetPosition();existing.append((p.ToMM(q.x),p.ToMM(q.y)))
for t in b.GetTracks():
 if isinstance(t,p.PCB_VIA) and t.GetNetname()=='GND':
  q=t.GetPosition();existing.append((p.ToMM(q.x),p.ToMM(q.y)))
added=[];failed=[]
for zone in b.Zones():
 if zone.GetNetname()!='GND' or zone.GetLayer() not in [p.F_Cu,p.B_Cu]:continue
 ps=zone.GetFilledPolysList(zone.GetLayer())
 for oi in range(ps.OutlineCount()):
  o=ps.COutline(oi);poly=Polygon([(p.ToMM(o.CPoint(i).x),p.ToMM(o.CPoint(i).y)) for i in range(o.PointCount())])
  if not poly.is_valid:poly=poly.buffer(0)
  if poly.is_empty or any(poly.covers(Point(x,y)) for x,y in existing):continue
  q=poly.representative_point();x0,y0,x1,y1=poly.bounds
  candidates=[(q.x,q.y)]+[(float(x),float(y)) for x in np.arange(x0+.1,x1,.2) for y in np.arange(y0+.1,y1,.2)]
  candidates.sort(key=lambda q:(q[0]-x0)**2+(q[1]-y0)**2)
  done=False
  for x,y in candidates:
   if not(.7<x<44.3 and .7<y<44.3):continue
   g=Point(x,y).buffer(.225)
   if not poly.covers(g) or any(g.distance(h)<.26 for h in holes):continue
   if not all(clear(g.buffer(.012),l,'GND') for l in layers):continue
   v=p.PCB_VIA(b);v.SetPosition(p.VECTOR2I(p.FromMM(x),p.FromMM(y)));v.SetWidth(p.FromMM(.45));v.SetDrill(p.FromMM(.2));v.SetViaType(p.VIATYPE_THROUGH);v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetNet(b.FindNet('GND'));b.Add(v)
   for l in layers:extra[l].append((g,'GND'))
   holes.append(Point(x,y).buffer(.1));existing.append((x,y));added.append([x,y]);done=True;break
  if not done:failed.append({'layer':b.GetLayerName(zone.GetLayer()),'area_mm2':poly.area,'bbox':list(poly.bounds)})
p.ZONE_FILLER(b).Fill(b.Zones());b.BuildConnectivity();p.SaveBoard(str(ROOT/'RoveFlight_S3.kicad_pcb'),b);(ROOT/'reports/Ground_Stitching.json').write_text(json.dumps({'added':added,'failed':failed},indent=2));print('Ground islands',len(added),'stitched;',len(failed),'need escapes')
