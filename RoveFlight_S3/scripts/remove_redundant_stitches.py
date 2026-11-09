"""Keep motor and MCU return drops; remove excess stitching that fences routing."""
from cadlib import *
import pcbnew as p
path=ROOT/'RoveFlight_S3.kicad_pcb';b=p.LoadBoard(str(path));r=json.loads((ROOT/'reports/Plane_Drops.json').read_text());preserve={'J2','Q3','Q4','Q5','Q6','C100','C101','C102','C1','C2','C3'};keep={(round(z['via'][0],4),round(z['via'][1],4)) for z in r['added'] if z['net']=='GND' and z['ref'] in preserve};remove=set();n=0
for t in b.GetTracks():
 if not isinstance(t,p.PCB_VIA) or t.GetNetname()!='GND':continue
 q=t.GetPosition()
 if (round(p.ToMM(q.x),4),round(p.ToMM(q.y),4)) not in keep:remove.add(t.m_Uuid.AsString());n+=1
# Native footprint thermal holes stay: they are pads, not board track-vias.
doc=sx.loads(path.read_text());doc=[z for z in doc if not(isinstance(z,list) and z and str(z[0])=='via' and atom(z,'uuid') in remove)];path.write_text(sx.dumps(doc));print('Removed',n,'redundant stitch vias; retained',len(keep),'motor/MCU return drops and all footprint thermal holes')
