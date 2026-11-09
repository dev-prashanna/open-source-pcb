"""Localized two-layer bypasses, protecting USB/acquisition ground returns.

Penalizes rear routing heavily; vias must sit outside SMD solder lands.
The completed rear GND fill must still be checked for continuity and coverage.
"""
from route_utils import *
import heapq,sys
from scipy.ndimage import distance_transform_edt
from shapely import contains_xy
from shapely.ops import unary_union

STEP=.05;NX=1101;NY=801;SIZE=NX*NY
SMALL='--small-vias' in sys.argv
LAND=.5 if SMALL else .6
DRILL=.25 if SMALL else .3
owner=np.zeros((2,NY,NX),dtype=np.int16);drills=np.zeros((NY,NX),dtype=bool);solder=np.zeros((NY,NX),dtype=bool)
codes={net.GetNetname():net.GetNetCode() for net in b.GetNetInfo().NetsByNetcode().values()}
def paint(shape,array,value):
    if shape.is_empty:return
    x0,y0,x1,y1=shape.bounds
    ix0=max(0,int(x0/STEP)-1);ix1=min(NX,int(x1/STEP)+2);iy0=max(0,int(y0/STEP)-1);iy1=min(NY,int(y1/STEP)+2)
    if ix0>=ix1 or iy0>=iy1:return
    xx,yy=np.meshgrid(np.arange(ix0,ix1)*STEP,np.arange(iy0,iy1)*STEP)
    array[iy0:iy1,ix0:ix1][contains_xy(shape,xx,yy)]=value
for li,layer in enumerate(layers):
    for shape,net in zip(geoms[layer],owners[layer]):paint(shape.buffer(.01),owner[li],codes.get(net,-1))
    for shape in smd[layer]:paint(shape,solder,True)
for hole in holes:paint(hole,drills,True)
npth=[]
for fp in b.GetFootprints():
    for q in fp.Pads():
        if q.GetAttribute()==p.PAD_ATTRIB_NPTH:
            ds=q.GetDrillSize();shape=Point(*xy(q)).buffer(max(p.ToMM(ds.x),p.ToMM(ds.y))/2);npth.append(shape)
            for li in range(2):paint(shape.buffer(.075),owner[li],-1)
critical=[]
for shape,net in zip(geoms[p.F_Cu],owners[p.F_Cu]):
    if net.startswith('USB_D') or net in {f'D{i}' for i in range(8)} or net=='__KEEP_OUT':critical.append(shape.buffer(.35))
protected=unary_union(critical)
paint(protected,owner[1],-1)
owner[:,:7,:]=-1;owner[:,-7:,:]=-1;owner[:,:,:7]=-1;owner[:,:,-7:]=-1
hole_distance=distance_transform_edt(~drills)*STEP;solder_distance=distance_transform_edt(~solder)*STEP
objects={q.m_Uuid.AsString():q for q in b.GetTracks()}
for fp in b.GetFootprints():
    for q in fp.Pads():objects[q.m_Uuid.AsString()]=q
for zone in b.Zones():objects[zone.m_Uuid.AsString()]=zone
def options(item):
    obj=objects.get(item['uuid'])
    if obj is None or isinstance(obj,p.ZONE):return [],set()
    todo=[obj];seen=set();result=[];conn=b.GetConnectivity()
    while todo and len(seen)<10000:
        q=todo.pop();key=q.m_Uuid.AsString();q=objects.get(key,q)
        if key in seen or isinstance(q,p.ZONE):continue
        seen.add(key)
        if isinstance(q,p.PAD):
            result.append((*xy(q),[i for i,l in enumerate(layers) if q.IsOnLayer(l)]))
        elif isinstance(q,p.PCB_VIA):result.append((*xy(q),[0,1]))
        elif isinstance(q,p.PCB_TRACK):
            a,z=q.GetStart(),q.GetEnd();ls=[layers.index(q.GetLayer())]
            result += [(p.ToMM(a.x),p.ToMM(a.y),ls),(p.ToMM(z.x),p.ToMM(z.y),ls)]
        for other in conn.GetConnectedItems(q):
            if other.GetNetCode()==obj.GetNetCode() and not isinstance(other,p.ZONE):todo.append(other)
    return [q for q in result if q[2]],seen
def search(a,z,net,width):
    distances=np.stack([distance_transform_edt(~((o!=0)&(o!=codes[net])))*STEP for o in owner])
    okay=distances>=width/2+.17
    viaok=(distances.min(axis=0)>=LAND/2+.21)&(hole_distance>=DRILL/2+.3)&(solder_distance>=LAND/2+.1)
    sx,sy=round(a[0]/STEP),round(a[1]/STEP);gx,gy=round(z[0]/STEP),round(z[1]/STEP)
    starts=[l*SIZE+sy*NX+sx for l in a[2] if okay[l,sy,sx]]
    goals={l*SIZE+gy*NX+gx for l in z[2] if okay[l,gy,gx]}
    if not starts or not goals:return None
    valid=okay.ravel();vok=viaok.ravel();scores=np.full(2*SIZE,np.inf,dtype=np.float32);prev=np.full(2*SIZE,-1,dtype=np.int32)
    def h(x,y):
        dx,dy=abs(x-gx),abs(y-gy);return (max(dx,dy)+.41421356*min(dx,dy))*1.5
    heap=[]
    for u in starts:scores[u]=0;heapq.heappush(heap,(h(sx,sy),0.,u))
    count=0;found=None
    while heap:
        _,cost,u=heapq.heappop(heap)
        if cost>float(scores[u])+.001:continue
        if u in goals:found=u;break
        count+=1
        if count>2400000:return None
        li=u//SIZE;idx=u%SIZE;y,x=divmod(idx,NX)
        for dx,dy,weight in [(1,0,1),(-1,0,1),(0,1,1),(0,-1,1),(1,1,1.41421356),(1,-1,1.41421356),(-1,1,1.41421356),(-1,-1,1.41421356)]:
            xx,yy=x+dx,y+dy
            if not (0<xx<NX-1 and 0<yy<NY-1):continue
            v=u+dy*NX+dx
            if not valid[v] or (dx and dy and (not valid[u+dx] or not valid[u+dy*NX])):continue
            new=cost+weight*(15. if li else .4 if owner[li,yy,xx]==codes[net] else 1.)
            if new+.001<float(scores[v]):scores[v]=new;prev[v]=u;heapq.heappush(heap,(new+h(xx,yy),new,v))
        if vok[idx]:
            v=(1-li)*SIZE+idx;new=cost+50
            if valid[v] and new+.001<float(scores[v]):scores[v]=new;prev[v]=u;heapq.heappush(heap,(new+h(x,y),new,v))
    if found is None:return None
    points=[];u=found
    while u>=0:
        li=u//SIZE;y,x=divmod(u%SIZE,NX);points.append((x*STEP,y*STEP,li))
        u=int(prev[u])
    points.reverse();points=[(*a[:2],points[0][2])]+points+[(*z[:2],points[-1][2])]
    compact=[points[0]];last=points[0];direction=None
    for q in points[1:]:
        if q==last:continue
        direction_now=(round((q[0]-last[0])/STEP,3),round((q[1]-last[1])/STEP,3),q[2]-last[2])
        if direction is not None and direction_now!=direction and last!=compact[-1]:compact.append(last)
        direction=direction_now;last=q
    if last!=compact[-1]:compact.append(last)
    return compact
def validate(points,net,width):
    rear=0
    for a,z in zip(points,points[1:]):
        if a[2]!=z[2]:
            g=Point(z[0],z[1]).buffer(LAND/2)
            if any(not clear(g,l,net) for l in layers) or g.intersects(protected):return False
        elif math.dist(a[:2],z[:2])>.000001:
            g=LineString([a[:2],z[:2]]).buffer(width/2)
            if not clear(g,layers[a[2]],net) or any(g.distance(h)<.255 for h in npth):return False
            if a[2]:
                if g.intersects(protected):return False
                rear+=math.dist(a[:2],z[:2])
    return rear<=20.
def add(points,net,width):
    rear=0;nv=0
    for a,z in zip(points,points[1:]):
        if a[2]!=z[2]:
            via=p.PCB_VIA(b);via.SetPosition(p.VECTOR2I(p.FromMM(z[0]),p.FromMM(z[1])))
            via.SetWidth(p.FromMM(LAND));via.SetDrill(p.FromMM(DRILL));via.SetViaType(p.VIATYPE_THROUGH)
            via.SetLayerPair(p.F_Cu,p.B_Cu);via.SetNet(b.FindNet(net));b.Add(via);nv+=1
            g=Point(z[0],z[1]).buffer(LAND/2)
            for i,l in enumerate(layers):extra[l].append((g,net));paint(g.buffer(.01),owner[i],codes[net])
            hole=Point(z[0],z[1]).buffer(DRILL/2);holes.append(hole);paint(hole,drills,True)
        else:
            track(a[:2],z[:2],net,width,layers[a[2]])
            paint(LineString([a[:2],z[:2]]).buffer(width/2+.01),owner[a[2]],codes[net])
            if a[2]:rear+=math.dist(a[:2],z[:2])
    return rear,nv

report=json.loads((ROOT/'reports'/sys.argv[1]).read_text());done=[];failed=[]
b.BuildConnectivity()
for entry in sorted(report['unconnected_items'],key=lambda e: 1 if any(any('['+n+']' in q['description'] for n in ('EN',)) for q in e['items']) else 0):
    es=entry['items'];obj=objects.get(es[0]['uuid'])
    if obj is None:continue
    net=obj.GetNetname()
    if net=='GND' or net.startswith('unconnected-'):continue
    if net.startswith('USB_D') or net in {f'D{i}' for i in range(8)}:continue
    aa,sa=options(es[0]);zz,sz=options(es[1])
    if sa&sz:continue
    pairs=sorted(((a,z) for a in aa for z in zz),key=lambda q:math.dist(q[0][:2],q[1][:2]))[:20]
    found=None
    for width in ([.4,.3] if net in ('VUSB','USB_5V','+3V3') else [.2,.15]):
        for a,z in pairs:
            if math.dist(a[:2],z[:2])<.001:continue
            points=search(a,z,net,width)
            if points and validate(points,net,width):found=(points,width);break
        if found:break
    if not found:failed.append(net);print('Needs review',net,flush=True);continue
    points,width=found;rear,nv=add(points,net,width);b.BuildConnectivity()
    for q in b.GetTracks():objects[q.m_Uuid.AsString()]=q
    p.SaveBoard(str(ROOT/'LogicScope_S3.kicad_pcb'),b)
    done.append({'net':net,'width_mm':width,'rear_length_mm':rear,'vias':nv,'points':points})
    print('Bypass',net,round(rear,2),'mm rear,',nv,'vias',flush=True)
    hole_distance=distance_transform_edt(~drills)*STEP
save()
(ROOT/'reports/Local_Bypasses.json').write_text(json.dumps({'connections':done,'remaining':failed,'protected_returns':'USB data and eight acquisition lines; front copper TIWARI marking'},indent=2)+'\n')
print('Bypasses:',len(done),'completed;',len(failed),'remaining')
