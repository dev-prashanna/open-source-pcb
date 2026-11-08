"""Bounded grid routing for specific KiCad-reported remaining connections.
Uses three routing layers; the In1 ground plane is never used for traces.
"""
from cadlib import *
import pcbnew as p, numpy as np, heapq,sys
from scipy.ndimage import distance_transform_edt
from shapely.geometry import Point,LineString,Polygon
from shapely import contains_xy
b=p.LoadBoard(str(ROOT/'RoveCore_One.kicad_pcb'));STEP=.025 if '--fine' in sys.argv else .05;NX=round(80/STEP)+1;NY=round(65/STEP)+1;SZ=NX*NY
layers=[p.F_Cu,p.In2_Cu,p.B_Cu];owner=np.zeros((3,NY,NX),dtype=np.int16);holes=np.zeros((NY,NX),dtype=bool);bridges=set()
def paint(g,net,ls):
 x0,y0,x1,y1=g.bounds;ix0=max(0,int(x0/STEP)-1);ix1=min(NX,int(x1/STEP)+2);iy0=max(0,int(y0/STEP)-1);iy1=min(NY,int(y1/STEP)+2)
 if ix1<=ix0 or iy1<=iy0:return
 xx,yy=np.meshgrid(np.arange(ix0,ix1)*STEP,np.arange(iy0,iy1)*STEP);mask=contains_xy(g,xx,yy)
 for l in ls:owner[l,iy0:iy1,ix0:ix1][mask]=net
def drill(x,y,r):
 x0=max(0,int((x-r)/STEP)-1);x1=min(NX,int((x+r)/STEP)+2);y0=max(0,int((y-r)/STEP)-1);y1=min(NY,int((y+r)/STEP)+2)
 xx,yy=np.meshgrid(np.arange(x0,x1)*STEP,np.arange(y0,y1)*STEP);holes[y0:y1,x0:x1]|=(xx-x)**2+(yy-y)**2<r*r
for l in range(3):owner[l,:10,:]=-1;owner[l,-10:,:]=-1;owner[l,:,:10]=-1;owner[l,:,-10:]=-1
for fp in b.GetFootprints():
 for pad in fp.Pads():
  for li,layer in enumerate(layers):
   if not pad.IsOnLayer(layer):continue
   ps=pad.GetEffectivePolygon(layer)
   for oi in range(ps.OutlineCount()):
    a=ps.COutline(oi);g=Polygon([(p.ToMM(a.CPoint(i).x),p.ToMM(a.CPoint(i).y)) for i in range(a.PointCount())])
    if g.is_valid:paint(g.buffer(.02),pad.GetNetCode() or -1,[li])
  ds=pad.GetDrillSize();pt=pad.GetPosition()
  if ds.x:
   r=max(p.ToMM(ds.x),p.ToMM(ds.y))/2;drill(p.ToMM(pt.x),p.ToMM(pt.y),r)
   if pad.GetAttribute()==p.PAD_ATTRIB_PTH:bridges.add((round(p.ToMM(pt.x)/STEP),round(p.ToMM(pt.y)/STEP),pad.GetNetCode()))
   if pad.GetAttribute()==p.PAD_ATTRIB_NPTH:paint(Point(p.ToMM(pt.x),p.ToMM(pt.y)).buffer(r+.02),-1,[0,1,2])
for tr in b.GetTracks():
 a=tr.GetStart();z=tr.GetEnd();pt=(p.ToMM(a.x),p.ToMM(a.y))
 if isinstance(tr,p.PCB_VIA):
  paint(Point(*pt).buffer(p.ToMM(tr.GetWidth(p.F_Cu))/2+.02),tr.GetNetCode(),[0,1,2]);drill(*pt,p.ToMM(tr.GetDrill())/2)
  bridges.add((round(pt[0]/STEP),round(pt[1]/STEP),tr.GetNetCode()))
 elif tr.GetLayer() in layers:paint(LineString([pt,(p.ToMM(z.x),p.ToMM(z.y))]).buffer(p.ToMM(tr.GetWidth())/2+.02),tr.GetNetCode(),[layers.index(tr.GetLayer())])
items={str(z.m_Uuid.AsString()):z for z in b.GetTracks()}
for fp in b.GetFootprints():
 for pad in fp.Pads():items[str(pad.m_Uuid.AsString())]=pad
def info(el):
 obj=items.get(el['uuid']);x=el['pos']['x'];y=el['pos']['y']
 if obj is None:return None
 if isinstance(obj,p.PAD):ls=[i for i,l in enumerate(layers) if obj.IsOnLayer(l)]
 elif isinstance(obj,p.PCB_VIA):ls=[0,1,2]
 else:ls=[layers.index(obj.GetLayer())] if obj.GetLayer() in layers else []
 return x,y,ls,obj.GetNetCode()
def maze(a,z,net,width):
 obs=(owner!=0)&(owner!=net);dist=np.stack([distance_transform_edt(~o)*STEP for o in obs]);dholes=distance_transform_edt(~holes)*STEP
 sx,sy=round(a[0]/STEP),round(a[1]/STEP);gx,gy=round(z[0]/STEP),round(z[1]/STEP)
 # Power necks are confined to 1.5mm around the selected endpoints.
 yy,xx=np.ogrid[:NY,:NX];neck=((xx*STEP-a[0])**2+(yy*STEP-a[1])**2<1.5**2)|((xx*STEP-z[0])**2+(yy*STEP-z[1])**2<1.5**2)
 okay=dist>=(.225 if STEP==.025 else .25)
 okay|=owner==net
 viaok=(dist.min(axis=0)>=.48)&(dholes>=.43)
 for bx,by,bn in bridges:
  if bn==net:viaok[by,bx]=True;okay[:,by,bx]=True
 valid=okay.ravel();vok=viaok.ravel();scores=np.full(3*SZ,np.inf,dtype=np.float32);par=np.full(3*SZ,-1,dtype=np.int32)
 starts=[l*SZ+sy*NX+sx for l in a[2]];goals={l*SZ+gy*NX+gx for l in z[2]}
 for u in starts|goals if False else starts:valid[u]=True
 for u in goals:valid[u]=True
 def h(x,y):
  dx,dy=abs(gx-x),abs(gy-y);return (max(dx,dy)+.414214*min(dx,dy))*(3.0 if '--fast' in sys.argv else 1.04)
 heap=[]
 for u in starts:scores[u]=0;heapq.heappush(heap,(h(sx,sy),0.,u))
 count=0;found=None
 while heap:
  _,cost,u=heapq.heappop(heap)
  if cost>scores[u]+.001:continue
  if u in goals:found=u;break
  count+=1
  if count>(4000000 if '--fast' in sys.argv else 900000):break
  layer=u//SZ;idx=u%SZ;y=idx//NX;x=idx%NX
  for dx,dy,extra in [(1,0,1),(-1,0,1),(0,1,1),(0,-1,1),(1,1,1.414214),(1,-1,1.414214),(-1,1,1.414214),(-1,-1,1.414214)]:
   nx,ny=x+dx,y+dy
   if nx<1 or ny<1 or nx>=NX-1 or ny>=NY-1:continue
   v=u+dy*NX+dx
   if not valid[v] or (dx and dy and (not valid[u+dx] or not valid[u+dy*NX])):continue
   local_width=max(.135,min(width,2*(float(dist[layer,ny,nx])-.18)))
   nc=cost+extra*(.3 if owner[layer,ny,nx]==net else 1+max(0,width/local_width-1)*.7)
   if nc+.001<scores[v]:scores[v]=nc;par[v]=u;heapq.heappush(heap,(nc+h(nx,ny),nc,v))
  if vok[idx]:
   for ll in range(3):
    if ll==layer:continue
    v=ll*SZ+idx;nc=cost+18
    if valid[v] and nc+.001<scores[v]:scores[v]=nc;par[v]=u;heapq.heappush(heap,(nc+h(x,y),nc,v))
 if found is None:
  print('Search failed after',count,'states; start',a,'goal',z,'start owners',[int(owner[l,sy,sx]) for l in a[2]],'goal owners',[int(owner[l,gy,gx]) for l in z[2]],'adjacent start',[int(okay[l,sy-1:sy+2,sx-1:sx+2].sum()) for l in a[2]],'adjacent goal',[int(okay[l,gy-1:gy+2,gx-1:gx+2].sum()) for l in z[2]],flush=True)
  return None
 path=[];u=found
 while u>=0:
  li=u//SZ;idx=u%SZ;x=(idx%NX)*STEP;y=(idx//NX)*STEP;w=min(width,max(.135,math.floor((dist[li,idx//NX,idx%NX]-.18)*2*40)/40));path.append((x,y,li,w));u=int(par[u])
 return path[::-1]
def track(a,z,layer,net,width):
 if math.hypot(a[0]-z[0],a[1]-z[1])<.00001:return
 length=math.hypot(a[0]-z[0],a[1]-z[1])
 samples=np.linspace(0,1,max(3,int(length/.04)))
 if all(owner[layer,min(NY-1,max(0,round((a[1]+(z[1]-a[1])*t)/STEP))),min(NX-1,max(0,round((a[0]+(z[0]-a[0])*t)/STEP)))]==net for t in samples):return
 t=p.PCB_TRACK(b);t.SetStart(p.VECTOR2I(p.FromMM(a[0]),p.FromMM(a[1])));t.SetEnd(p.VECTOR2I(p.FromMM(z[0]),p.FromMM(z[1])));t.SetWidth(p.FromMM(width));t.SetLayer(layers[layer]);t.SetNetCode(net);b.Add(t);paint(LineString([a[:2],z[:2]]).buffer(width/2+.02),net,[layer])
def addpath(path,a,z,net):
 track(a,path[0],path[0][2],net,path[0][3]);track(path[-1],z,path[-1][2],net,path[-1][3]);start=last=path[0];direction=None
 for q in path[1:]:
  if q[2]!=last[2]:
   track(start,last,last[2],net,min(start[3],last[3]))
   key=(round(q[0]/STEP),round(q[1]/STEP),net)
   if key not in bridges:
    v=p.PCB_VIA(b);v.SetPosition(p.VECTOR2I(p.FromMM(q[0]),p.FromMM(q[1])));v.SetWidth(p.FromMM(.6));v.SetDrill(p.FromMM(.3));v.SetViaType(p.VIATYPE_THROUGH);v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetNetCode(net);b.Add(v);paint(Point(q[0],q[1]).buffer(.32),net,[0,1,2]);drill(q[0],q[1],.15);bridges.add(key)
   start=q;direction=None
  else:
   dr=(round((q[0]-last[0])/STEP),round((q[1]-last[1])/STEP))
   if direction is not None and (dr!=direction or q[3]!=last[3]):track(start,last,last[2],net,min(start[3],last[3]));start=last
   direction=dr
  last=q
 track(start,last,last[2],net,min(start[3],last[3]))
report=json.loads((ROOT/'reports'/sys.argv[1]).read_text());done=[];failed=[]
def priority(v):
 desc=' '.join(i['description'] for i in v['items'])
 return 0 if '[USB_VBUS]' in desc else 1 if '[MOTOR_B_P]' in desc else 2 if any(x in desc for x in ['[SW_','[VM]','[SERVO','[ISENSE']) else 3
for v in sorted(report['unconnected_items'],key=priority):
 es=v['items'];a=info(es[0]);z=info(es[1])
 if a is None and z is None:continue
 if a is None:a,z=z,a
 net=a[3];name=b.FindNet(net).GetNetname()
 if '--no-ground' in sys.argv and name=='GND':continue
 if z is None:
  if name not in ['GND','+3V3_SENS']:continue
  if name=='+3V3_SENS':
   target=next(pad for fp in b.GetFootprints() if fp.GetReference()=='FB1' for pad in fp.Pads() if pad.GetNumber()=='2');pt=target.GetPosition();z=(p.ToMM(pt.x),p.ToMM(pt.y),[i for i,l in enumerate(layers) if target.IsOnLayer(l)],net)
  else:
   candidates=[v for v in b.GetTracks() if isinstance(v,p.PCB_VIA) and v.GetNetCode()==net]
   v=min(candidates,key=lambda v:(p.ToMM(v.GetPosition().x)-a[0])**2+(p.ToMM(v.GetPosition().y)-a[1])**2);pt=v.GetPosition();z=(p.ToMM(pt.x),p.ToMM(pt.y),[0,1,2],net)
 width=.8 if name in ['SERVO5','SERVO_BUCK','VBAT','VM','SW_SERVO'] else .6 if name.startswith('MOTOR_') or name in ['SW_3V3','USB_VBUS'] else .18
 path=maze(a,z,net,width)
 if path is None:failed.append(name);print('FAILED',name,flush=True);continue
 addpath(path,a,z,net);done.append(name);print('Connected',name,len(path),'steps',flush=True)
for z in b.Zones():z.SetIslandRemovalMode(p.ISLAND_REMOVAL_MODE_ALWAYS)
p.ZONE_FILLER(b).Fill(b.Zones());b.BuildConnectivity();p.SaveBoard(str(ROOT/'RoveCore_One.kicad_pcb'),b)
(ROOT/'reports/Repair_Log.json').write_text(json.dumps({'connected':done,'failed':failed},indent=2));print('Completed',len(done),'connections; failed',failed)
