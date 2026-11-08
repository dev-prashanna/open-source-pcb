"""Connect ground and quiet sensor power using clearance-tested short escapes.
No signal layer is routed on In1. Geometric checks include every pad and track.
"""
from cadlib import *
import pcbnew as p
from shapely.geometry import Point,LineString,Polygon
from shapely.strtree import STRtree
import numpy as np
b=p.LoadBoard(str(ROOT/'RoveCore_One.kicad_pcb'));layers=[p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu]
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
for net in ['GND','+3V3_SENS']:
 targets=[]
 for fp in b.GetFootprints():
  for pad in fp.Pads():
   if pad.GetNetname()==net and pad.GetAttribute()==p.PAD_ATTRIB_SMD:targets.append((fp.GetReference(),pad))
 for ref,pad in targets:
  a=pad.GetPosition();x,y=p.ToMM(a.x),p.ToMM(a.y);layer=p.F_Cu if pad.IsOnLayer(p.F_Cu) else p.B_Cu
  found=False
  offsets=[(r*math.cos(a),r*math.sin(a)) for r in [.8,1.,1.25,1.5,2.,2.5,3.] for a in [i*math.pi/12 for i in range(24)]]
  for dx,dy in offsets:
   vx,vy=round(x+dx,4),round(y+dy,4)
   if not(.85<vx<79.15 and .85<vy<64.15):continue
   if not drilling_clear(vx,vy):continue
   g=Point(vx,vy).buffer(.3);line=LineString([(x,y),(vx,vy)]).buffer(.0675)
   if not all(clear(g,l,net) for l in layers):continue
   if not clear(line,layer,net):continue
   via(vx,vy,net)
   if dx or dy:track((x,y),(vx,vy),layer,net)
   added.append({'ref':ref,'pad':pad.GetNumber(),'net':net,'via':[vx,vy],'escape_length':round(math.hypot(dx,dy),3)});found=True;break
  if not found:failed.append({'ref':ref,'pad':pad.GetNumber(),'net':net})
# Stitch remaining outer ground islands into the uninterrupted inner plane.
for x in np.arange(2.,79.,4.):
 for y in np.arange(2.,64.,4.):
  g=Point(x,y).buffer(.3)
  if drilling_clear(x,y) and all(clear(g,l,'GND') for l in layers):via(float(x),float(y),'GND')
# A quiet sensor-power plane on In2 connects the ferrite output and local sensor drops.
z=p.ZONE(b);z.SetLayer(p.In2_Cu);z.SetNet(b.FindNet('+3V3_SENS'));z.SetLocalClearance(p.FromMM(.18));z.SetMinThickness(p.FromMM(.15));z.SetPadConnection(p.ZONE_CONNECTION_FULL);poly=z.Outline();poly.NewOutline()
for x,y in [(.5,.5),(79.5,.5),(79.5,64.5),(.5,64.5)]:poly.Append(p.FromMM(x),p.FromMM(y))
b.Add(z)
for z in b.Zones():z.SetPadConnection(p.ZONE_CONNECTION_FULL)
p.ZONE_FILLER(b).Fill(b.Zones());b.BuildConnectivity();p.SaveBoard(str(ROOT/'RoveCore_One.kicad_pcb'),b)
(ROOT/'reports/Plane_Stitching.json').write_text(json.dumps({'added':added,'failed':failed},indent=2));print('Plane stitching:',len(added),'pad drops;',len(failed),'need further review')
