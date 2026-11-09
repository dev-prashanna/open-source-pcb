"""Route exact-geometry straight and dogleg connections on available signal layers."""
from cadlib import *
from pathlib import Path
source=Path(__file__).with_name('power_drops.py').read_text().split('added=[];failed=[]')[0];exec(compile(source,'geometry','exec'))
import sys
from shapely.geometry import box
report=json.loads((ROOT/'reports'/sys.argv[1]).read_text());routing=[p.In3_Cu,p.In2_Cu,p.F_Cu,p.B_Cu];b.BuildConnectivity();conn=b.GetConnectivity();objects={x.m_Uuid.AsString():x for x in b.GetTracks()}
for fp in b.GetFootprints():
 for pad in fp.Pads():objects[pad.m_Uuid.AsString()]=pad
for zone in b.Zones():objects[zone.m_Uuid.AsString()]=zone
npth=[]
for fp in b.GetFootprints():
 for pad in fp.Pads():
  if pad.GetAttribute()==p.PAD_ATTRIB_NPTH:
   q=pad.GetPosition();npth.append(Point(p.ToMM(q.x),p.ToMM(q.y)).buffer(max(p.ToMM(pad.GetDrillSize().x),p.ToMM(pad.GetDrillSize().y))/2))
def options(desc):
 obj=objects.get(desc['uuid'])
 if obj is None or isinstance(obj,p.ZONE):return []
 todo=[obj];seen=set();vias=[];others=[]
 while todo and len(seen)<6000:
  o=todo.pop();key=o.m_Uuid.AsString();o=objects.get(key,o)
  if key in seen or isinstance(o,p.ZONE):continue
  seen.add(key)
  if isinstance(o,p.PCB_VIA):
   q=o.GetPosition();vias.append((p.ToMM(q.x),p.ToMM(q.y),routing))
  elif isinstance(o,p.PAD):
   q=o.GetPosition();others.append((p.ToMM(q.x),p.ToMM(q.y),[l for l in routing if o.IsOnLayer(l)]))
  elif isinstance(o,p.PCB_TRACK):
   for q in [o.GetStart(),o.GetEnd()]:others.append((p.ToMM(q.x),p.ToMM(q.y),[o.GetLayer()]))
  for n in conn.GetConnectedItems(o):
   if n.GetNetCode()==obj.GetNetCode() and n.m_Uuid.AsString() not in seen:todo.append(n)
 return vias + others if '--all-ends' in sys.argv else vias or others
added=[];failed=[]
for entry in report['unconnected_items']:
 es=entry['items'];obj=objects.get(es[0]['uuid']);net=obj.GetNetname() if obj else ''
 if net=='GND' or not net:continue
 aa,zz=options(es[0]),options(es[1])
 if not aa or not zz:continue
 pairs=sorted(((a,z) for a in aa for z in zz),key=lambda q:(q[0][0]-q[1][0])**2+(q[0][1]-q[1][1])**2)[:50];done=False
 widths=[1.2,.8,.5] if net in ['BAT_FUSED','BAT_PROTECTED','VM'] else [.5,.3,.18,.125] if net in ['+3V3','USB_VBUS','SYS_IN','REG_L1','REG_L2'] else [.16,.125]
 for width in widths:
  for a,z in pairs:
   axy,zxy=a[:2],z[:2];paths=[[axy,zxy],[axy,(axy[0],zxy[1]),zxy],[axy,(zxy[0],axy[1]),zxy]]
   for d in [.5,1.,1.5,2.,3.]:
    for dx,dy in [(d,0),(-d,0),(0,d),(0,-d)]:paths.append([axy,(axy[0]+dx,axy[1]+dy),zxy]);paths.append([axy,(zxy[0]+dx,zxy[1]+dy),zxy])
   for layer in [l for l in routing if l in a[2] and l in z[2]]:
    for points in paths:
     points=[q for i,q in enumerate(points) if i==0 or q!=points[i-1]]
     if len(points)<2:continue
     geom=LineString(points).buffer(width/2)
     if not box(.4,.4,44.6,44.6).covers(geom):continue
     if not clear(geom.buffer(.012),layer,net) or any(geom.distance(q)<.26 for q in npth):continue
     for first,last in zip(points,points[1:]):track(first,last,layer,net,width)
     added.append({'net':net,'layer':b.GetLayerName(layer),'width_mm':width,'points':points});print('Visibility connected',net,b.GetLayerName(layer),width,flush=True);done=True;break
    if done:break
   if done:break
  if done:break
 if not done:failed.append(net)
 else:
  b.BuildConnectivity()
  for x in b.GetTracks():objects[x.m_Uuid.AsString()]=x
  p.SaveBoard(str(ROOT/'RoveFlight_S3.kicad_pcb'),b)
p.ZONE_FILLER(b).Fill(b.Zones());b.BuildConnectivity();p.SaveBoard(str(ROOT/'RoveFlight_S3.kicad_pcb'),b);(ROOT/'reports/Visibility_Routing.json').write_text(json.dumps({'added':added,'failed':failed},indent=2));print('Visibility routes',len(added),'failed',failed)
