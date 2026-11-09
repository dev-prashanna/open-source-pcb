"""Front-only clearance-tested routing of KiCad-reported missing connections.

The rear copper layer is reserved for ground, including under the USB pair.
USB routes are pre-routed by route_usb.py and never synthesized here.
"""
from route_utils import *
import sys,heapq
from scipy.ndimage import distance_transform_edt
from shapely import contains_xy

STEP=.025 if '--fine' in sys.argv else .05
NX=round(55/STEP)+1;NY=round(40/STEP)+1;SIZE=NX*NY
MARGIN=.18 if '--fine' in sys.argv else .205
owner=np.zeros((NY,NX),dtype=np.int16)
codes={net.GetNetname():net.GetNetCode() for net in b.GetNetInfo().NetsByNetcode().values()}
def paint(shape,net):
    if shape.is_empty:return
    x0,y0,x1,y1=shape.bounds
    ix0=max(0,int(x0/STEP)-1);ix1=min(NX,int(x1/STEP)+2)
    iy0=max(0,int(y0/STEP)-1);iy1=min(NY,int(y1/STEP)+2)
    if ix0>=ix1 or iy0>=iy1:return
    xx,yy=np.meshgrid(np.arange(ix0,ix1)*STEP,np.arange(iy0,iy1)*STEP)
    mask=contains_xy(shape,xx,yy)
    owner[iy0:iy1,ix0:ix1][mask]=codes.get(net,-1)
for shape,net in zip(geoms[p.F_Cu],owners[p.F_Cu]):paint(shape.buffer(.01),net)
npth=[]
for fp in b.GetFootprints():
    for q in fp.Pads():
        if q.GetAttribute()==p.PAD_ATTRIB_NPTH:
            point=xy(q);drill=q.GetDrillSize()
            shape=Point(*point).buffer(max(p.ToMM(drill.x),p.ToMM(drill.y))/2)
            npth.append(shape);paint(shape.buffer(.075),'__MECHANICAL')
border=math.ceil(.35/STEP)
owner[:border,:]=-1;owner[-border:,:]=-1;owner[:,:border]=-1;owner[:,-border:]=-1
objects={x.m_Uuid.AsString():x for x in b.GetTracks()}
for fp in b.GetFootprints():
    for q in fp.Pads():objects[q.m_Uuid.AsString()]=q
for zone in b.Zones():objects[zone.m_Uuid.AsString()]=zone
def options(item):
    obj=objects.get(item['uuid'])
    if obj is None or isinstance(obj,p.ZONE):return [],set()
    todo=[obj];seen=set();points=[];connect=b.GetConnectivity()
    while todo and len(seen)<10000:
        q=todo.pop();key=q.m_Uuid.AsString();q=objects.get(key,q)
        if key in seen or isinstance(q,p.ZONE):continue
        seen.add(key)
        if isinstance(q,p.PAD):
            if q.IsOnLayer(p.F_Cu):points.append(xy(q))
        elif isinstance(q,p.PCB_VIA):points.append(xy(q))
        elif isinstance(q,p.PCB_TRACK) and q.GetLayer()==p.F_Cu:
            a,z=q.GetStart(),q.GetEnd()
            points += [(p.ToMM(a.x),p.ToMM(a.y)),(p.ToMM(z.x),p.ToMM(z.y))]
        for neighbor in connect.GetConnectedItems(q):
            if neighbor.GetNetCode()==obj.GetNetCode() and not isinstance(neighbor,p.ZONE):todo.append(neighbor)
    return list(dict.fromkeys(points)),seen
def good(points,net,width):
    if len(points)<2 or math.dist(points[0],points[-1])<.00001:return False
    g=LineString(points).buffer(width/2)
    return clear(g,p.F_Cu,net) and all(g.distance(h)>=.255 for h in npth)
def maze(a,z,net,width):
    occupied=(owner!=0)&(owner!=codes[net])
    distance=distance_transform_edt(~occupied)*STEP
    okay=distance>=width/2+MARGIN
    sx,sy=round(a[0]/STEP),round(a[1]/STEP);gx,gy=round(z[0]/STEP),round(z[1]/STEP)
    start=sy*NX+sx;goal=gy*NX+gx
    if not okay[sy,sx] or not okay[gy,gx]:return None
    valid=okay.ravel();scores=np.full(SIZE,np.inf,dtype=np.float32);prev=np.full(SIZE,-1,dtype=np.int32)
    scores[start]=0
    def heuristic(x,y):
        dx,dy=abs(x-gx),abs(y-gy)
        return (max(dx,dy)+.41421356*min(dx,dy))*1.5
    heap=[(heuristic(sx,sy),0.,start)];expanded=0
    while heap:
        _,cost,u=heapq.heappop(heap)
        if cost>float(scores[u])+.001:continue
        if u==goal:break
        expanded+=1
        if expanded>(4000000 if '--fine' in sys.argv else 1200000):return None
        y,x=divmod(u,NX)
        for dx,dy,weight in [(1,0,1),(-1,0,1),(0,1,1),(0,-1,1),(1,1,1.41421356),(1,-1,1.41421356),(-1,1,1.41421356),(-1,-1,1.41421356)]:
            xx,yy=x+dx,y+dy
            if not (0<xx<NX-1 and 0<yy<NY-1):continue
            v=yy*NX+xx
            if not valid[v] or (dx and dy and (not valid[u+dx] or not valid[u+dy*NX])):continue
            new=cost+weight*(.4 if owner[yy,xx]==codes[net] else 1.)
            if new+.001<float(scores[v]):
                scores[v]=new;prev[v]=u;heapq.heappush(heap,(new+heuristic(xx,yy),new,v))
    else:return None
    points=[];u=goal
    while u>=0:
        y,x=divmod(u,NX);points.append((x*STEP,y*STEP))
        if u==start:break
        u=int(prev[u])
    points.reverse();simplified=[a];last=points[0];direction=None
    if math.dist(a,last)>.00001:simplified.append(last)
    for q in points[1:]:
        d=(round((q[0]-last[0])/STEP),round((q[1]-last[1])/STEP))
        if direction is not None and d!=direction and last!=simplified[-1]:simplified.append(last)
        direction=d;last=q
    if last!=simplified[-1]:simplified.append(last)
    if z!=simplified[-1]:simplified.append(z)
    return simplified if good(simplified,net,width) else None

report=json.loads((ROOT/'reports'/sys.argv[1]).read_text())
done=[];failed=[]
def priority(entry):
    description=' '.join(x['description'] for x in entry['items'])
    if '[SW]' in description or '[BST]' in description:return 0
    for i in range(8):
        if '[D'+str(i)+']' in description:return 1+i*.01
        if '[IN'+str(i)+']' in description:return 2+i*.01
        if '[CH'+str(i)+']' in description:return 3+i*.01
    if any('['+n+']' in description for n in ('+3V3','VUSB','USB_5V')):return 4
    return 4
b.BuildConnectivity()
for entry in sorted(report['unconnected_items'],key=priority):
    items=entry['items'];obj=objects.get(items[0]['uuid'])
    if obj is None:continue
    net=obj.GetNetname()
    if net=='GND' or net.startswith('unconnected-'):continue
    if net.startswith('USB_D'):failed.append({'net':net,'reason':'USB must be repaired as a pair'});continue
    aa,seen_a=options(items[0]);zz,seen_z=options(items[1])
    if seen_a & seen_z:continue
    if not aa or not zz:failed.append({'net':net,'reason':'zone endpoint'});continue
    pairs=sorted(((a,z) for a in aa for z in zz),key=lambda q:math.dist(*q))[:5]
    widths=[.6,.4,.25] if net in ('SW','VUSB','USB_5V','+3V3') else [.2,.15]
    found=None
    for width in widths:
        for a,z in pairs:
            if math.dist(a,z)<.000001:continue
            for points in [[a,z],[a,(a[0],z[1]),z],[a,(z[0],a[1]),z]]:
                points=[q for i,q in enumerate(points) if i==0 or q!=points[i-1]]
                if good(points,net,width):found=(points,width);break
            if found:break
        if found:break
        for a,z in pairs[:3]:
            points=maze(a,z,net,width)
            if points:found=(points,width);break
        if found:break
    if found:
        points,width=found;route(points,net,width)
        for a,z in zip(points,points[1:]):paint(LineString([a,z]).buffer(width/2+.01),net)
        b.BuildConnectivity()
        for q in b.GetTracks():objects[q.m_Uuid.AsString()]=q
        done.append({'net':net,'width_mm':width,'points':points})
        p.SaveBoard(str(ROOT/'LogicScope_S3.kicad_pcb'),b)
        print('Connected',net,'on F.Cu,',width,'mm,',len(points),'vertices',flush=True)
    else:
        failed.append({'net':net,'reason':'no clear front-layer path'});print('Needs routing',net,flush=True)
save()
(ROOT/'reports/Front_Routing.json').write_text(json.dumps({'routed':done,'remaining':failed},indent=2)+'\n')
print('Completed',len(done),'connections;',len(failed),'need review; rear plane preserved')
