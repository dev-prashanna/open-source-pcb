"""Use the motor power copper and fixed multi-via drops, not autorouter VM detours."""
from cadlib import *
import pcbnew as p
path=ROOT/'RoveFlight_S3.kicad_pcb';b=p.LoadBoard(str(path));original=p.LoadBoard(str(ROOT/'reports/placement_before_route.kicad_pcb'))
keep={(round(p.ToMM(t.GetPosition().x),4),round(p.ToMM(t.GetPosition().y),4)) for t in original.GetTracks() if isinstance(t,p.PCB_VIA) and t.GetNetname()=='VM'};segments=[(t.GetStart().x,t.GetStart().y,t.GetEnd().x,t.GetEnd().y,t.GetWidth(),t.GetLayer()) for t in original.GetTracks() if not isinstance(t,p.PCB_VIA) and t.GetNetname()=='VM'];removed=0
for t in list(b.GetTracks()):
 if t.GetNetname()!='VM':continue
 if isinstance(t,p.PCB_VIA):
  q=t.GetPosition()
  if (round(p.ToMM(q.x),4),round(p.ToMM(q.y),4)) in keep:continue
 b.Remove(t);removed+=1
restored=0
for ax,ay,zx,zy,width,layer in segments:
 z=p.PCB_TRACK(b);z.SetStart(p.VECTOR2I(ax,ay));z.SetEnd(p.VECTOR2I(zx,zy));z.SetWidth(width);z.SetLayer(layer);z.SetNet(b.FindNet('VM'));b.Add(z);restored+=1
p.ZONE_FILLER(b).Fill(b.Zones());b.BuildConnectivity();p.SaveBoard(str(path),b);print('Removed',removed,'VM detour items; restored',restored,'fixed plane-drop traces')
