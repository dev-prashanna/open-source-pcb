"""Rotate two small passives about an anchored pad to clear ground via sites."""
from cadlib import *
import pcbnew as p
from shapely.geometry import box,Point
b=p.LoadBoard(str(ROOT/'RoveCore_One.kicad_pcb'));fps={f.GetReference():f for f in b.GetFootprints()}
def bbox(fp):
 layer=p.B_CrtYd if fp.GetLayer()==p.B_Cu else p.F_CrtYd;rs=[z.GetBoundingBox() for z in fp.GraphicalItems() if z.GetLayer()==layer and isinstance(z,p.PCB_SHAPE)]
 return min(p.ToMM(r.GetX()) for r in rs),min(p.ToMM(r.GetY()) for r in rs),max(p.ToMM(r.GetRight()) for r in rs),max(p.ToMM(r.GetBottom()) for r in rs)
report=[]
for ref,anchor,clearpoint in [('R50','2',(52.8625,45.95)),('FB1','2',(26.8125,39.05))]:
 fp=fps[ref];pads={z.GetNumber():z for z in fp.Pads()};pt=pads[anchor].GetPosition();oldxy=fp.GetPosition();oldrot=fp.GetOrientationDegrees();old=(p.ToMM(oldxy.x),p.ToMM(oldxy.y));target=(pt.x,pt.y);success=False
 for angle in [oldrot+90,oldrot-90,oldrot+180]:
  fp.SetOrientationDegrees(angle);q=pads[anchor].GetPosition();c=fp.GetPosition();fp.SetPosition(p.VECTOR2I(c.x+target[0]-q.x,c.y+target[1]-q.y));r=box(*bbox(fp))
  if r.intersects(Point(*clearpoint).buffer(.4)):continue
  if any(r.buffer(.05).intersects(box(*bbox(other))) for key,other in fps.items() if key!=ref and other.GetLayer()==fp.GetLayer()):continue
  # Ground-hole position must no longer lie under any copper pad of this part.
  if any(Point(p.ToMM(pad.GetPosition().x),p.ToMM(pad.GetPosition().y)).distance(Point(*clearpoint))<.7 for pad in fp.Pads()):continue
  success=True;break
 if not success:
  fp.SetOrientationDegrees(oldrot);fp.SetPosition(oldxy)
  if ref=='R50':
   offsets=[(dx*.5,dy*.5) for dx in range(-10,11) for dy in range(-10,11)];offsets.sort(key=lambda v:v[0]**2+v[1]**2)
   for dx,dy in offsets:
    fp.SetPosition(p.VECTOR2I(oldxy.x+p.FromMM(dx),oldxy.y+p.FromMM(dy)));r=box(*bbox(fp))
    if r.intersects(Point(*clearpoint).buffer(.5)):continue
    if any(r.buffer(.05).intersects(box(*bbox(other))) for key,other in fps.items() if key!=ref and other.GetLayer()==fp.GetLayer()):continue
    success=True;break
   if not success:fp.SetPosition(oldxy)
 report.append({'ref':ref,'old_xy':old,'new_xy':[p.ToMM(fp.GetPosition().x),p.ToMM(fp.GetPosition().y)],'rotation':fp.GetOrientationDegrees(),'success':success,'anchored_pad':anchor})
b.BuildConnectivity();p.SaveBoard(str(ROOT/'RoveCore_One.kicad_pcb'),b);(ROOT/'reports/Passive_Rotation.json').write_text(json.dumps(report,indent=2));print(report)
