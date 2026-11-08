from cadlib import *
import pcbnew as p
import xml.etree.ElementTree as ET
b=p.LoadBoard(str(ROOT/'RoveCore_One.kicad_pcb'));fps={f.GetReference():f for f in b.GetFootprints()};parts=json.loads((ROOT/'design.json').read_text());nets={n.GetNetname():n for n in b.GetNetInfo().NetsByNetcode().values()}
root=ET.parse(ROOT/'reports/RoveCore_One.xml').getroot()
for net in root.find('nets'):
 name=net.attrib['name'].lstrip('/').replace('/','{slash}')
 if not name.startswith('unconnected-'):continue
 if name not in nets:n=p.NETINFO_ITEM(b,name);b.Add(n);nets[name]=n
 for el in net.findall('node'):
  if el.attrib['ref'] not in fps:continue
  for pad in fps[el.attrib['ref']].Pads():
   if pad.GetNumber()==el.attrib['pin']:pad.SetNet(nets[name])
for c in parts:
 fp=fps[c['ref']]
 for key,val in [('MPN',c['mpn']),('Manufacturer',c['mfr']),('Datasheet',c['source'])]:
  if key=='Datasheet':f=fp.GetField(p.FIELD_T_DATASHEET);f.SetText(val)
  else:
   f=p.PCB_FIELD(fp,p.FIELD_T_USER,key);f.SetText(val);f.SetVisible(False);fp.Add(f)
for ref in ['H1','H2','H3','H4']:fps[ref].SetAttributes(fps[ref].GetAttributes()|p.FP_BOARD_ONLY)
for ref in ['J19','J20']:
 a=fps[ref].GetPosition();fps[ref].SetPosition(p.VECTOR2I(a.x,p.FromMM(8.25)))
fps['C3'].SetPosition(p.VECTOR2I(p.FromMM(10.9),p.FromMM(3.28)))
def bounds(fp):
 layer=p.B_CrtYd if fp.GetLayer()==p.B_Cu else p.F_CrtYd
 rs=[z.GetBoundingBox() for z in fp.GraphicalItems() if isinstance(z,p.PCB_SHAPE) and z.GetLayer()==layer]
 if not rs:return None
 return min(p.ToMM(r.GetX()) for r in rs),min(p.ToMM(r.GetY()) for r in rs),max(p.ToMM(r.GetRight()) for r in rs),max(p.ToMM(r.GetBottom()) for r in rs)
def ov(a,z,gap=.12):return min(a[2],z[2])-max(a[0],z[0])>-gap and min(a[3],z[3])-max(a[1],z[1])>-gap
c4=fps['C4'];candidates=[(dx*.25,dy*.25) for dx in range(-25,26) for dy in range(-25,26)];candidates.sort(key=lambda z:z[0]**2+z[1]**2)
for dx,dy in candidates:
 c4.SetPosition(p.VECTOR2I(p.FromMM(9.545+dx),p.FromMM(41.05+dy)));box=bounds(c4);bad=False
 if box[0]<.5 or box[1]<.5 or box[2]>79.5 or box[3]>64.5:continue
 for ref,other in fps.items():
  if ref=='C4':continue
  ob=bounds(other)
  if other.GetLayer()==c4.GetLayer() and ob and ov(box,ob):bad=True;break
  for pad in other.Pads():
   ds=pad.GetDrillSize()
   if not ds.x:continue
   a=pad.GetPosition();x,y=p.ToMM(a.x),p.ToMM(a.y);rr=max(p.ToMM(ds.x),p.ToMM(ds.y))/2+.3
   if ov(box,(x-rr,y-rr,x+rr,y+rr)):
    bad=True;break
  if bad:break
 if not bad:break
else:raise ValueError('Cannot legalize USB bypass capacitor')
# All back silkscreen must be mirrored; bulk bodies have their own polarity marks.
for z in b.GetDrawings():
 if isinstance(z,p.PCB_TEXT) and z.GetLayer()==p.B_SilkS:z.SetMirrored(True)
for fp in fps.values():
 for f in fp.GetFields():
  if f.GetLayer()==p.B_SilkS:f.SetMirrored(True)
p.SaveBoard(str(ROOT/'RoveCore_One.kicad_pcb'),b)
# DSN exporter does not preserve project net classes in the Python API; explicitly
# add them to the routing file in prepare_routing.py.
p.ExportSpecctraDSN(b,str(ROOT/'reports/RoveCore_One.dsn'))
print('Placed board updated with schematic fields and intentional unconnected-pad nets')
