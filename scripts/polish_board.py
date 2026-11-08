from cadlib import *
import pcbnew as p
path=ROOT/'RoveCore_One.kicad_pcb';doc=sx.loads(path.read_text())
report=json.loads((ROOT/'reports'/__import__('sys').argv[1]).read_text())
# Dangling vias have no completed connection; removing them does not disconnect a net.
remove={i['uuid'] for v in report['violations'] if v['type'] in ['via_dangling','track_dangling'] for i in v['items'] if i['description'].startswith(('Via ','Track '))}
doc=[n for n in doc if not(isinstance(n,list) and n and str(n[0]) in ['via','segment'] and atom(n,'uuid') in remove)]
path.write_text(sx.dumps(doc))
b=p.LoadBoard(str(path));fps={f.GetReference():f for f in b.GetFootprints()}
for ref in ['U20','U7','U1']:
 for z in fps[ref].GraphicalItems():
  if isinstance(z,p.PCB_SHAPE) and z.GetLayer()==p.F_SilkS and z.GetShape()==p.SHAPE_T_POLY:z.SetLayer(p.F_Fab)
# Two geometric circle-approximation differences under 1um: reduce only those via
# diameters by 10um, retaining 0.145mm annular ring and 0.30mm drill.
for tr in b.GetTracks():
 if not isinstance(tr,p.PCB_VIA) and p.ToMM(tr.GetWidth())<.125:tr.SetWidth(p.FromMM(.125))
 if isinstance(tr,p.PCB_VIA):
  a=tr.GetPosition();x,y=p.ToMM(a.x),p.ToMM(a.y)
  if (abs(x-59.075)<.0001 and abs(y-11.7178)<.0001) or (abs(x-61.625)<.0001 and abs(y-8.148999)<.0001):tr.SetWidth(p.FromMM(.59))
tb=b.GetTitleBlock();tb.SetTitle('P-TIWARI | Integrated Robotics & IoT');tb.SetRevision('A.0 ENGINEERING PROTOTYPE');tb.SetDate('2026-11-08');tb.SetComment(0,'PTW-ESP32-ROB-A0 | 80x65mm | four layers');b.SetTitleBlock(tb)
for z in b.Zones():z.SetIslandRemovalMode(p.ISLAND_REMOVAL_MODE_ALWAYS)
p.ZONE_FILLER(b).Fill(b.Zones());b.BuildConnectivity();p.SaveBoard(str(path),b)
print('Removed',len(remove),'dangling vias; polished markings and sub-micron clearance edge cases')
