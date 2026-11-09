"""Restore manufacturing geometry after SES import and add local power copper."""
from cadlib import *
import pcbnew as p
path=ROOT/'RoveFlight_S3.kicad_pcb';b=p.LoadBoard(str(path));parts=json.loads((ROOT/'design.json').read_text());meta={c['ref']:c for c in parts}
original=p.LoadBoard(str(ROOT/'reports/placement_before_route.kicad_pcb'))
via_sizes={ (round(p.ToMM(v.GetPosition().x),4),round(p.ToMM(v.GetPosition().y),4),v.GetNetname()):(v.GetWidth(p.F_Cu),v.GetDrill()) for v in original.GetTracks() if isinstance(v,p.PCB_VIA)}
for tr in b.GetTracks():
 if isinstance(tr,p.PCB_VIA):
  key=(round(p.ToMM(tr.GetPosition().x),4),round(p.ToMM(tr.GetPosition().y),4),tr.GetNetname())
  if key in via_sizes:tr.SetWidth(via_sizes[key][0]);tr.SetDrill(via_sizes[key][1])
  else:tr.SetWidth(p.FromMM(.5));tr.SetDrill(p.FromMM(.25))
 elif tr.GetWidth()<p.FromMM(.125):tr.SetWidth(p.FromMM(.125))
for fp in b.GetFootprints():
 c=meta.get(fp.GetReference())
 if not c:continue
 for key,value in [('MPN',c['mpn']),('Manufacturer',c['mfr'])]:
  f=p.PCB_FIELD(fp,p.FIELD_T_USER,key);f.SetText(value);f.SetVisible(False);fp.Add(f)
 fp.GetField(p.FIELD_T_DATASHEET).SetText(c['source'])
 if c['name']=='TestPoint':fp.SetAttributes(fp.GetAttributes()|p.FP_EXCLUDE_FROM_BOM)
# The perimeter VM copper is kept for the motor loop; central logic/sensor copper
# supplements routed power. In1 remains unbroken ground.
for net,priority,rect in [('+3V3',1,(10,1,35,43)),('+3V3_SENS',2,(10,20,25.5,31))]:
 z=p.ZONE(b);z.SetLayer(p.In2_Cu);z.SetNet(b.FindNet(net));z.SetAssignedPriority(priority);z.SetLocalClearance(p.FromMM(.18));z.SetMinThickness(p.FromMM(.15));z.SetPadConnection(p.ZONE_CONNECTION_FULL);z.SetIslandRemovalMode(p.ISLAND_REMOVAL_MODE_ALWAYS);poly=z.Outline();poly.NewOutline();x0,y0,x1,y1=rect
 for x,y in [(x0,y0),(x1,y0),(x1,y1),(x0,y1)]:poly.Append(p.FromMM(x),p.FromMM(y))
 b.Add(z)
p.ZONE_FILLER(b).Fill(b.Zones());b.BuildConnectivity();p.SaveBoard(str(path),b);print('Restored via drills/lands, widened narrow necks, added central power copper, synchronized symbol fields')
