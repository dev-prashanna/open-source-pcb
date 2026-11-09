"""Open regulator switch-pin and arming-latch access without changing the pinout."""
from cadlib import *
import pcbnew as p
path=ROOT/'RoveFlight_S3.kicad_pcb';b=p.LoadBoard(str(path));fps={f.GetReference():f for f in b.GetFootprints()};drops=json.loads((ROOT/'reports/Plane_Drops.json').read_text())['added'];target=next(z['via'] for z in drops if z['ref']=='U3' and z['pad']=='3');remove=[];tracks=list(b.GetTracks())
for t in tracks:
 if t.GetNetname()!='GND':continue
 a=t.GetStart();z=t.GetEnd()
 if isinstance(t,p.PCB_VIA):
  if abs(p.ToMM(a.x)-target[0])<.0001 and abs(p.ToMM(a.y)-target[1])<.0001:remove.append(t)
 elif any(abs(p.ToMM(q.x)-target[0])<.0001 and abs(p.ToMM(q.y)-target[1])<.0001 for q in [a,z]):remove.append(t)
fp=fps['J9'];old=fp.GetPosition();fp.SetPosition(p.VECTOR2I(old.x,old.y-p.FromMM(1.0)))
for t in remove:b.Remove(t)
p.ZONE_FILLER(b).Fill(b.Zones());b.BuildConnectivity();p.SaveBoard(str(path),b);print('Removed redundant U3 PGND escape (EP thermal vias retained); moved J9 north 1mm')
