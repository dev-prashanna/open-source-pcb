"""Join front ground islands to the continuous rear ground plane."""
from route_utils import *

def polys(z,layer):
 ps=z.GetFilledPolysList(layer)
 def ring(r):return [(p.ToMM(r.CPoint(k).x),p.ToMM(r.CPoint(k).y)) for k in range(r.PointCount())]
 return [Polygon(ring(ps.COutline(i)),[ring(ps.CHole(i,j)) for j in range(ps.HoleCount(i))]).buffer(0) for i in range(ps.OutlineCount())]

def anchors():
 out=[]
 for fp in b.GetFootprints():
  for q in fp.Pads():
   if q.GetNetname()=='GND' and q.GetAttribute()==p.PAD_ATTRIB_PTH:out.append(Point(*xy(q)).buffer(.05))
 for q in b.GetTracks():
  if isinstance(q,p.PCB_VIA) and q.GetNetname()=='GND':out.append(Point(*xy(q)).buffer(.05))
 return out

added=[];failed=[]
for layer in [p.F_Cu]:
 zones=[z for z in b.Zones() if not z.GetIsRuleArea() and z.GetLayer()==layer and z.GetNetname()=='GND']
 for z in zones:
  shapes=polys(z,layer)
  for index,shape in enumerate(shapes):
   if any(shape.intersects(a) for a in anchors()):continue
   done=False
   for land,drill in [(.6,.3),(.5,.25)]:
    area=shape.buffer(-land/2-.03)
    if area.is_empty:continue
    rp=area.representative_point();x0,y0,x1,y1=area.bounds
    candidates=[(rp.x,rp.y)]+[(x,y) for x in np.arange(x0,x1,.15) for y in np.arange(y0,y1,.15) if area.contains(Point(x,y))]
    for vx,vy in candidates:
     g=Point(vx,vy).buffer(land/2);hole=Point(vx,vy).buffer(drill/2)
     if any(hole.distance(h)<.26 for h in holes):continue
     if any(g.distance(smd[l][i])<.06 for l in layers for i in smdtrees[l].query(g.buffer(.07))):continue
     if not all(clear(g,l,'GND') for l in layers):continue
     v=p.PCB_VIA(b);v.SetPosition(p.VECTOR2I(p.FromMM(float(vx)),p.FromMM(float(vy))));v.SetWidth(p.FromMM(land));v.SetDrill(p.FromMM(drill));v.SetViaType(p.VIATYPE_THROUGH);v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetNet(b.FindNet('GND'));b.Add(v)
     for l in layers:extra[l].append((g,'GND'))
     holes.append(hole);added.append({'x_mm':vx,'y_mm':vy,'land_mm':land,'drill_mm':drill,'island_area_mm2':shape.area});done=True;break
    if done:break
   if not done:failed.append({'island':index,'area_mm2':shape.area,'bounds':shape.bounds})
save()
(ROOT/'reports/Ground_Stitching.json').write_text(json.dumps({'added':added,'needs_review':failed},indent=2)+'\n')
print('Ground vias added',len(added),'islands need review',len(failed))
