"""Remove rerouting remnants with no component pad or useful power-plane role."""
from cadlib import *
import pcbnew as p
path=ROOT/'RoveFlight_S3.kicad_pcb';b=p.LoadBoard(str(path));b.BuildConnectivity();c=b.GetConnectivity();tracks=list(b.GetTracks());objs={z.m_Uuid.AsString():z for z in tracks};padids=set()
for fp in b.GetFootprints():
 for pad in fp.Pads():objs[pad.m_Uuid.AsString()]=pad;padids.add(pad.m_Uuid.AsString())
parent={key:key for key in objs}
def find(x):
 while parent[x]!=x:parent[x]=parent[parent[x]];x=parent[x]
 return x
def union(a,z):
 a,z=find(a),find(z)
 if a!=z:parent[z]=a
for key,obj in objs.items():
 for neighbor in c.GetConnectedItems(obj):
  other=neighbor.m_Uuid.AsString()
  if other in objs and neighbor.GetNetCode()==obj.GetNetCode():union(key,other)
padgroups={find(x) for x in padids};planenets={'GND'};remove=set();counts={}
for t in tracks:
 key=t.m_Uuid.AsString();net=t.GetNetname()
 if net not in planenets and find(key) not in padgroups:remove.add(key);counts[net]=counts.get(net,0)+1
# Edit the native S-expression to avoid deleting shared SWIG wrappers in a loop.
doc=sx.loads(path.read_text());doc=[z for z in doc if not(isinstance(z,list) and z and str(z[0]) in ['segment','via'] and atom(z,'uuid') in remove)];path.write_text(sx.dumps(doc))
print('Removed',len(remove),'padless routing remnants',counts)
