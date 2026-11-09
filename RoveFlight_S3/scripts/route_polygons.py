"""Exact-copper polygon navigation for residual routed components."""
from pathlib import Path
source=Path(__file__).with_name('route_visibility.py').read_text().split('\nadded=[];failed=[]\n')[0];exec(compile(source,'visibility','exec'))
from scipy.spatial import Delaunay
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra
from shapely.ops import unary_union
from shapely.geometry import MultiPolygon
import numpy as np
added=[];failed=[]
for entry in report['unconnected_items']:
 es=entry['items'];obj=objects.get(es[0]['uuid']);net=obj.GetNetname() if obj else ''
 if not net or net=='GND':continue
 aa,zz=options(es[0]),options(es[1])
 if not aa or not zz:continue
 pairs=sorted(((a,z) for a in aa for z in zz if set(a[2]) & set(z[2])),key=lambda q:(q[0][0]-q[1][0])**2+(q[0][1]-q[1][1])**2)[:(20 if '--all-ends' in sys.argv else 4)];done=False
 width=.3 if net in ['+3V3','USB_VBUS','SYS_IN','VM','BAT_PROTECTED','BAT_FUSED','REG_L1','REG_L2'] else .125
 for a,z in pairs:
  for layer in [l for l in routing if l in a[2] and l in z[2]]:
   if abs(a[0]-z[0])+abs(a[1]-z[1])<.001:continue
   region=box(max(.4,min(a[0],z[0])-5),max(.4,min(a[1],z[1])-5),min(44.6,max(a[0],z[0])+5),min(44.6,max(a[1],z[1])+5))
   obs=[q.buffer(width/2+.19).intersection(region) for q,on in zip(geoms[layer],owners[layer]) if on!=net and q.intersects(region)]
   obs += [q.buffer(width/2+.19).intersection(region) for q,on in extra[layer] if on!=net and q.intersects(region)]
   obstacle=unary_union(obs).simplify(.015,preserve_topology=True);polygons=list(obstacle.geoms) if hasattr(obstacle,'geoms') else [obstacle];points=[a[:2],z[:2]]
   for poly in polygons:
    if poly.geom_type!='Polygon':continue
    points+=list(poly.exterior.coords)[:-1]
    for ring in poly.interiors:points+=list(ring.coords)[:-1]
   x0,y0,x1,y1=region.bounds;points += [(x0,y0),(x0,y1),(x1,y0),(x1,y1)]
   points=list(dict.fromkeys((round(x,5),round(y,5)) for x,y in points));arr=np.array(points)
   if len(arr)<3:continue
   try:tri=Delaunay(arr)
   except Exception:continue
   edges=set()
   for cell in tri.simplices:
    for i,j in [(cell[0],cell[1]),(cell[1],cell[2]),(cell[2],cell[0])]:edges.add((min(i,j),max(i,j)))
   edges.add((0,1))
   for endpoint in [0,1]:
    for idx in np.argsort(np.sum((arr-arr[endpoint])**2,axis=1))[1:81]:edges.add((min(endpoint,int(idx)),max(endpoint,int(idx))))
   row=[];col=[];data=[]
   for i,j in edges:
    line=LineString([points[i],points[j]]);g=line.buffer(width/2)
    if not region.buffer(.001).covers(g) or not clear(g.buffer(.008),layer,net) or any(g.distance(h)<.26 for h in npth):continue
    length=line.length;row += [i,j];col += [j,i];data += [length,length]
   graph=csr_matrix((data,(row,col)),shape=(len(points),len(points)));distance,pred=dijkstra(graph,indices=0,return_predecessors=True)
   if not np.isfinite(distance[1]):continue
   route=[];idx=1
   while idx>=0:
    route.append(points[idx])
    if idx==0:break
    idx=int(pred[idx])
   route=route[::-1]
   for first,last in zip(route,route[1:]):track(first,last,layer,net,width)
   print('Polygon connected',net,b.GetLayerName(layer),len(route),round(float(distance[1]),3),flush=True);added.append({'net':net,'layer':b.GetLayerName(layer),'width_mm':width,'points':route});done=True;break
  if done:break
 if not done:failed.append(net);print('Polygon FAILED',net,flush=True)
 else:
  b.BuildConnectivity()
  for x in b.GetTracks():objects[x.m_Uuid.AsString()]=x
  p.SaveBoard(str(ROOT/'RoveFlight_S3.kicad_pcb'),b)
p.ZONE_FILLER(b).Fill(b.Zones());b.BuildConnectivity();p.SaveBoard(str(ROOT/'RoveFlight_S3.kicad_pcb'),b);(ROOT/'reports/Polygon_Routing.json').write_text(json.dumps({'added':added,'failed':failed},indent=2));print('Polygon routes',len(added),'failed',failed)
