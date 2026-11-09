"""Open short obstructing track portions for clearance-tested escape vias."""
from cadlib import *
import pcbnew as p,sys
from shapely.geometry import Point,LineString,Polygon
from shapely.strtree import STRtree
path=ROOT/'RoveFlight_S3.kicad_pcb';b=p.LoadBoard(str(path));report=json.loads((ROOT/'reports'/sys.argv[1]).read_text());layers=[p.F_Cu,p.In1_Cu,p.In2_Cu,p.In3_Cu,p.In4_Cu,p.B_Cu]
objects={z.m_Uuid.AsString():z for z in b.GetTracks()};pads=[];padowners=[];padlayers=[];holes=[];viaobs=[]
for fp in b.GetFootprints():
 for pad in fp.Pads():
  objects[pad.m_Uuid.AsString()]=pad
  for l in layers:
   if not pad.IsOnLayer(l):continue
   ps=pad.GetEffectivePolygon(l)
   for i in range(ps.OutlineCount()):
    o=ps.COutline(i);pads.append(Polygon([(p.ToMM(o.CPoint(j).x),p.ToMM(o.CPoint(j).y)) for j in range(o.PointCount())]));padowners.append(pad.GetNetname());padlayers.append(l)
  if pad.GetDrillSize().x:
   q=pad.GetPosition();holes.append(Point(p.ToMM(q.x),p.ToMM(q.y)).buffer(max(p.ToMM(pad.GetDrillSize().x),p.ToMM(pad.GetDrillSize().y))/2))
tracks=[]
for t in b.GetTracks():
 q=t.GetStart();z=t.GetEnd();net=t.GetNetname()
 if isinstance(t,p.PCB_VIA):viaobs.append((Point(p.ToMM(q.x),p.ToMM(q.y)).buffer(p.ToMM(t.GetWidth(p.F_Cu))/2),net));holes.append(Point(p.ToMM(q.x),p.ToMM(q.y)).buffer(p.ToMM(t.GetDrill())/2))
 else:tracks.append((t,LineString([(p.ToMM(q.x),p.ToMM(q.y)),(p.ToMM(z.x),p.ToMM(z.y))]),p.ToMM(t.GetWidth()),net,t.GetLayer()))
ptree=STRtree(pads);seen=set();log=[];failed=[];remove={};newparts=[];protected=[]
for entry in report['unconnected_items']:
 for item in entry['items']:
  obj=objects.get(item['uuid'])
  if obj is None or isinstance(obj,p.PCB_VIA) or item['uuid'] in seen:continue
  seen.add(item['uuid']);net=obj.GetNetname()
  if net in ['GND','VM']:continue
  if isinstance(obj,p.PAD):
   if obj.GetAttribute()!=p.PAD_ATTRIB_SMD:continue
   ref=obj.GetParentFootprint().GetReference();q=obj.GetPosition();ls=[l for l in [p.F_Cu,p.B_Cu] if obj.IsOnLayer(l)];label=ref+'.'+obj.GetNumber()
  else:q=obj.GetStart();ls=[obj.GetLayer()];label='track'
  x,y=p.ToMM(q.x),p.ToMM(q.y);land=.45;dr=.2;width=.135;best=None
  for r in [0,.2,.4,.6,.8,1.,1.3]:
   for angle in range(0,360,30):
    vx,vy=round(x+r*math.cos(math.radians(angle)),4),round(y+r*math.sin(math.radians(angle)),4)
    if not(.7<vx<44.3 and .7<vy<44.3):continue
    g=Point(vx,vy).buffer(land/2);h=Point(vx,vy).buffer(dr/2)
    if any(h.distance(o)<.26 for o in holes) or any(on!=net and g.distance(o)<.16 for o,on in viaobs):continue
    if any(padowners[i]!=net and g.distance(pads[i])<.16 for i in ptree.query(g.buffer(.17))):continue
    for layer in ls:
     line=LineString([(x,y),(vx,vy)]) if r else Point(x,y)
     if any(padlayers[i]==layer and padowners[i]!=net and line.distance(pads[i])<width/2+.16 for i in ptree.query(line.buffer(width/2+.17))):continue
     if any(on!=net and line.distance(o)<width/2+.16 for o,on in viaobs):continue
     cuts=[];cost=r*.2
     for t,tl,tw,tn,l in tracks:
      if tn==net or t.m_Uuid.AsString() in remove:continue
      if tl.distance(g)<tw/2+.16 or (l==layer and tl.distance(line)<tw/2+width/2+.16):
       cuts.append((t,tl,tw,tn,l));cost+=.5 if tn=='GND' else 12 if tn in ['VM','BAT_FUSED','BAT_PROTECTED','REG_L1','REG_L2'] else 20 if tn in ['USB_DP','USB_DM','USB_DP_CONN','USB_DM_CONN'] else 1
     if any(tn!=net and (tl.distance(g)<tw/2+.16 or (l==layer and tl.distance(line)<tw/2+width/2+.16)) for tl,tw,tn,l in protected):continue
     if best is None or cost<best[0]:best=(cost,vx,vy,layer,line,cuts)
   if best and best[0]<.4:break
  if best is None:failed.append({'source':label,'net':net});continue
  cost,vx,vy,layer,line,cuts=best
  if not cuts:continue
  for t,tl,tw,tn,l in cuts:
   remove[t.m_Uuid.AsString()]=t;exclusion=Point(vx,vy).buffer(land/2+.17+tw/2)
   if l==layer:exclusion=exclusion.union(line.buffer(width/2+.17+tw/2))
   result=tl.difference(exclusion)
   for part in ([result] if result.geom_type=='LineString' else list(result.geoms)):
    if part.is_empty or part.length<.02:continue
    a,z=list(part.coords)[0],list(part.coords)[-1];newparts.append((a,z,tw,tn,l))
  v=p.PCB_VIA(b);v.SetPosition(p.VECTOR2I(p.FromMM(vx),p.FromMM(vy)));v.SetWidth(p.FromMM(land));v.SetDrill(p.FromMM(dr));v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetViaType(p.VIATYPE_THROUGH);v.SetNet(b.FindNet(net));b.Add(v);holes.append(Point(vx,vy).buffer(dr/2));viaobs.append((Point(vx,vy).buffer(land/2),net))
  if line.geom_type=='LineString' and line.length>.001:
   t=p.PCB_TRACK(b);t.SetStart(p.VECTOR2I(p.FromMM(x),p.FromMM(y)));t.SetEnd(p.VECTOR2I(p.FromMM(vx),p.FromMM(vy)));t.SetWidth(p.FromMM(width));t.SetLayer(layer);t.SetNet(b.FindNet(net));b.Add(t);protected.append((line,width,net,layer))
  log.append({'source':label,'net':net,'via':[vx,vy],'cut_nets':sorted(set(tn for t,tl,tw,tn,l in cuts))});print(log[-1],flush=True)
for t in remove.values():b.Remove(t)
for a,z,tw,tn,l in newparts:
 t=p.PCB_TRACK(b);t.SetStart(p.VECTOR2I(p.FromMM(a[0]),p.FromMM(a[1])));t.SetEnd(p.VECTOR2I(p.FromMM(z[0]),p.FromMM(z[1])));t.SetWidth(p.FromMM(tw));t.SetLayer(l);t.SetNet(b.FindNet(tn));b.Add(t)
p.ZONE_FILLER(b).Fill(b.Zones());b.BuildConnectivity();p.SaveBoard(str(path),b);(ROOT/'reports/Priority_Escapes.json').write_text(json.dumps({'added':log,'failed':failed},indent=2));print('Opened',len(log),'escapes; cut',len(remove),'segments')
