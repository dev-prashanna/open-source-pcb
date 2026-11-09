"""Correct measured imported trace clearances without changing fabrication minima."""
from cadlib import *
import pcbnew as p
path=ROOT/'RoveFlight_S3.kicad_pcb';b=p.LoadBoard(str(path));tracks=list(b.GetTracks());remove=[]
widths={'c6d7c4d5-c33f-4ea4-813a-a045c6b3fedc':.14,'3a2283ab-cb66-43b1-b4d5-e3d58bf28dc5':.15,'40f546ec-35f3-4b83-9104-df701c9d7d3e':.15}
old=p.VECTOR2I(p.FromMM(7.995),p.FromMM(22.55));new=p.VECTOR2I(p.FromMM(8.04),p.FromMM(22.58))
for t in tracks:
 key=t.m_Uuid.AsString()
 if key in widths:t.SetWidth(p.FromMM(widths[key]))
 if key=='39bed2a6-4d77-4ffa-8b31-532aff88e198':t.SetWidth(p.FromMM(.49))
 if key=='6657f2fe-cb7d-4a1a-85de-6d2d23732abc':t.SetPosition(new)
 if key=='4a0d3baf-0e6a-45e6-b2cd-01acbd3d4f33':remove.append(t)
 if not isinstance(t,p.PCB_VIA) and t.GetNetname()=='USB_VBUS':
  if t.GetStart()==old:t.SetStart(new)
  if t.GetEnd()==old:t.SetEnd(new)
for t in remove:b.Remove(t)
p.ZONE_FILLER(b).Fill(b.Zones());b.BuildConnectivity();p.SaveBoard(str(path),b)
print('Corrected four imported clearances and one NPTH escape; opened one obstructing fault-signal segment')
