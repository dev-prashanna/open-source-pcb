"""Reposition opposite-face passives that block necessary via escape cylinders."""
from cadlib import *
import pcbnew as p,sys
from shapely.geometry import Point,LineString,Polygon,box
from shapely.strtree import STRtree
path=ROOT/'RoveFlight_S3.kicad_pcb';b=p.LoadBoard(str(path));report=json.loads((ROOT/'reports'/sys.argv[1]).read_text());fps={f.GetReference():f for f in b.GetFootprints()};items={z.m_Uuid.AsString():z for f in fps.values() for z in f.Pads()}
def rect(fp):
 layer=p.F_CrtYd if fp.GetLayer()==p.F_Cu else p.B_CrtYd;rs=[z.GetBoundingBox() for z in fp.GraphicalItems() if z.GetLayer()==layer]
 if fp.GetReference()=='U1':return (12.725,-6.75,32.275,19.475)
 if not rs:return None
 return (min(p.ToMM(z.GetX()) for z in rs),min(p.ToMM(z.GetY()) for z in rs),max(p.ToMM(z.GetRight()) for z in rs),max(p.ToMM(z.GetBottom()) for z in rs))
def polys(pad,layer):
 out=[];ps=pad.GetEffectivePolygon(layer)
 for i in range(ps.OutlineCount()):
  a=ps.COutline(i);out.append(Polygon([(p.ToMM(a.CPoint(j).x),p.ToMM(a.CPoint(j).y)) for j in range(a.PointCount())]))
 return out
targets=[]
for v in report['unconnected_items']:
 for item in v['items']:
  pad=items.get(item['uuid'])
  if pad is None or pad.GetAttribute()!=p.PAD_ATTRIB_SMD:continue
  ref=pad.GetParentFootprint().GetReference()
  if not ref.startswith(('U','J')):continue
  a=pad.GetPosition();targets.append((p.ToMM(a.x),p.ToMM(a.y),pad.GetNetname(),p.F_Cu if pad.IsOnLayer(p.F_Cu) else p.B_Cu,ref))
blockers=set()
for x,y,net,side,ref in targets:
 opposite=p.B_Cu if side==p.F_Cu else p.F_Cu;g=Point(x,y).buffer(.39)
 for key,fp in fps.items():
  if fp.GetLayer()!=opposite or not key.startswith(('C','R','FB')) or key in ['C100','C101','C102','R100']:continue
  if any(pad.GetNetname()!=net and any(g.intersects(q) for q in polys(pad,opposite)) for pad in fp.Pads()):blockers.add(key)
for v in report['violations']:
 if v['type']=='courtyards_overlap':
  for item in v['items']:
   ref=item['description'].replace('Footprint ','')
   if ref.startswith(('R','TP')):blockers.add(ref)
print('Blocking passives',sorted(blockers),flush=True);log=[];remove_later={};alltracks=list(b.GetTracks())
for ref in sorted(blockers):
 fp=fps[ref];side=fp.GetLayer();old=fp.GetPosition();oldrot=fp.GetOrientationDegrees();oldpads=[]
 for pad in fp.Pads():oldpads += [(q,pad.GetNetname()) for q in polys(pad,side)]
 removable=[]
 for t in alltracks:
  if isinstance(t,p.PCB_VIA):continue
  if t.GetLayer()!=side:continue
  a=t.GetStart();z=t.GetEnd();line=LineString([(p.ToMM(a.x),p.ToMM(a.y)),(p.ToMM(z.x),p.ToMM(z.y))])
  if any(t.GetNetname()==net and line.distance(q)<.02 for q,net in oldpads):removable.append(t)
 omit={t.m_Uuid.AsString() for t in removable};geoms=[];owners=[]
 for key,other in fps.items():
  if key==ref:continue
  for pad in other.Pads():
   if not pad.IsOnLayer(side):continue
   for q in polys(pad,side):geoms.append(q);owners.append(pad.GetNetname())
 for t in alltracks:
  if t.m_Uuid.AsString() in omit or t.m_Uuid.AsString() in remove_later:continue
  a=t.GetStart();z=t.GetEnd()
  if isinstance(t,p.PCB_VIA):q=Point(p.ToMM(a.x),p.ToMM(a.y)).buffer(p.ToMM(t.GetWidth(p.F_Cu))/2)
  elif t.GetLayer()==side:q=LineString([(p.ToMM(a.x),p.ToMM(a.y)),(p.ToMM(z.x),p.ToMM(z.y))]).buffer(p.ToMM(t.GetWidth())/2)
  else:continue
  geoms.append(q);owners.append(t.GetNetname())
 tree=STRtree(geoms);bodies=[box(*rect(other)) for key,other in fps.items() if key!=ref and rect(other) and (other.GetLayer()==side or key.startswith('H'))];success=False
 offsets=[(ix*.25,iy*.25) for ix in range(-16,17) for iy in range(-16,17)];offsets.sort(key=lambda q:q[0]**2+q[1]**2)
 for dx,dy in offsets:
  for rot in [oldrot,oldrot+90,oldrot-90,oldrot+180]:
   fp.SetOrientationDegrees(rot);fp.SetPosition(p.VECTOR2I(old.x+p.FromMM(dx),old.y+p.FromMM(dy)));rr=rect(fp);r=box(*rr)
   if rr[0]<.5 or rr[1]<1 or rr[2]>44.5 or rr[3]>44.5 or any(r.buffer(.1).intersects(q) for q in bodies):continue
   okay=True
   for pad in fp.Pads():
    net=pad.GetNetname()
    for q in polys(pad,side):
     if any(owners[i]!=net and q.distance(geoms[i])<.16 for i in tree.query(q.buffer(.17))):okay=False;break
     if any(side!=targetside and net!=tn and q.distance(Point(x,y))<.4 for x,y,tn,targetside,tr in targets):okay=False;break
    if not okay:break
   if okay:success=True;break
  if success:break
 if success:
  for t in removable:remove_later[t.m_Uuid.AsString()]=t
  q=fp.GetPosition();log.append({'ref':ref,'old_xy':[p.ToMM(old.x),p.ToMM(old.y)],'new_xy':[p.ToMM(q.x),p.ToMM(q.y)],'rotation':fp.GetOrientationDegrees(),'removed_segments':len(removable)});print('Moved',log[-1],flush=True)
 else:fp.SetOrientationDegrees(oldrot);fp.SetPosition(old);print('No safe move',ref,flush=True)
for t in remove_later.values():b.Remove(t)
p.ZONE_FILLER(b).Fill(b.Zones());b.BuildConnectivity();p.SaveBoard(str(path),b);(ROOT/'reports/Placement_Adjustments.json').write_text(json.dumps(log,indent=2))
