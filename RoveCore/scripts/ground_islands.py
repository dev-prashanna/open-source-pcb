"""Stitch each actual outer ground island to In1, after signal routing."""
from pathlib import Path
source=Path(__file__).with_name('stitch_planes.py').read_text().split('added=[];failed=[]')[0]
exec(compile(source,str(Path(__file__).with_name('stitch_planes.py')),'exec'))
existing=[]
for fp in b.GetFootprints():
 for pad in fp.Pads():
  if pad.GetNetname()=='GND' and pad.GetAttribute()==p.PAD_ATTRIB_PTH:
   a=pad.GetPosition();existing.append((p.ToMM(a.x),p.ToMM(a.y)))
for tr in b.GetTracks():
 if isinstance(tr,p.PCB_VIA) and tr.GetNetname()=='GND':
  a=tr.GetPosition();existing.append((p.ToMM(a.x),p.ToMM(a.y)))
added=[];failed=[]
for zone in list(b.Zones()):
 if zone.GetNetname()!='GND' or zone.GetLayer() not in [p.F_Cu,p.B_Cu]:continue
 ps=zone.GetFilledPolysList(zone.GetLayer())
 for oi in range(ps.OutlineCount()):
  out=ps.COutline(oi);poly=Polygon([(p.ToMM(out.CPoint(i).x),p.ToMM(out.CPoint(i).y)) for i in range(out.PointCount())])
  if not poly.is_valid:poly=poly.buffer(0)
  if poly.is_empty:continue
  if any(poly.covers(Point(x,y)) for x,y in existing):continue
  center=poly.representative_point();x0,y0,x1,y1=poly.bounds
  candidates=[(center.x,center.y)]+[(float(x),float(y)) for y in np.arange(y0+.2,y1,.4) for x in np.arange(x0+.2,x1,.4)]
  candidates.sort(key=lambda z:(z[0]-center.x)**2+(z[1]-center.y)**2)
  for x,y in candidates:
   if not(.8<x<79.2 and .8<y<64.2):continue
   g=Point(x,y).buffer(.3)
   if not poly.covers(g) or not drilling_clear(x,y):continue
   if not all(clear(g,l,'GND') for l in layers):continue
   via(x,y,'GND');existing.append((x,y));added.append([x,y]);break
  else:failed.append({'layer':zone.GetLayer(),'area_mm2':poly.area,'bbox':list(poly.bounds)})
p.ZONE_FILLER(b).Fill(b.Zones());b.BuildConnectivity();p.SaveBoard(str(ROOT/'RoveCore_One.kicad_pcb'),b)
(ROOT/'reports/Ground_Islands.json').write_text(json.dumps({'added_vias':added,'not_stitched':failed},indent=2));print('Ground islands:',len(added),'stitched;',len(failed),'need review')
