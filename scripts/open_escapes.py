"""Rip up obstructing copper in specific fine-pitch escape corridors.
The next KiCad DRC exposes every affected net for reconnection.
"""
from cadlib import *
import pcbnew as p
from shapely.geometry import Point,LineString
b=p.LoadBoard(str(ROOT/'RoveCore_One.kicad_pcb'));remove=set();slots=[]
targets={'U3':['5'],'U7':['7'],'U19':['27']}
for fp in b.GetFootprints():
 if fp.GetReference() not in targets:continue
 center=fp.GetPosition();cx,cy=p.ToMM(center.x),p.ToMM(center.y)
 for pad in fp.Pads():
  if pad.GetNumber() not in targets[fp.GetReference()]:continue
  pt=pad.GetPosition();x,y=p.ToMM(pt.x),p.ToMM(pt.y);size=pad.GetSize();padw,padh=p.ToMM(size.x),p.ToMM(size.y)
  # SOT/HTSSOP/QFN pins in these target parts lie on the left/right edges.
  direction=1 if x>cx else -1;end=(x+direction*(padw/2+1.5),y);slot=LineString([(x,y),end]).buffer(.22)
  slots.append({'ref':fp.GetReference(),'pin':pad.GetNumber(),'from':[x,y],'to':end})
  for tr in b.GetTracks():
   if tr.GetNetCode()==pad.GetNetCode():continue
   if not isinstance(tr,p.PCB_VIA) and tr.GetLayer()!=fp.GetLayer():continue
   a=tr.GetStart();z=tr.GetEnd()
   if isinstance(tr,p.PCB_VIA):g=Point(p.ToMM(a.x),p.ToMM(a.y)).buffer(p.ToMM(tr.GetWidth(p.F_Cu))/2)
   else:g=LineString([(p.ToMM(a.x),p.ToMM(a.y)),(p.ToMM(z.x),p.ToMM(z.y))]).buffer(p.ToMM(tr.GetWidth())/2)
   if slot.intersects(g):remove.add(str(tr.m_Uuid.AsString()))
path=ROOT/'RoveCore_One.kicad_pcb';doc=sx.loads(path.read_text());doc=[n for n in doc if not(isinstance(n,list) and n and str(n[0]) in ['segment','via'] and atom(n,'uuid') in remove)];path.write_text(sx.dumps(doc))
(ROOT/'reports/Escape_Ripup.json').write_text(json.dumps({'slots':slots,'removed_tracks':sorted(remove)},indent=2));print('Opened fine-pitch escapes by removing',len(remove),'obstructing tracks/vias')
