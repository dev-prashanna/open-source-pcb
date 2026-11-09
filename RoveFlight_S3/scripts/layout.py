"""Reproducible six-layer placement. Running this clears routing."""
from cadlib import *
import pcbnew as p
import xml.etree.ElementTree as ET
W=H=45;path=ROOT/'RoveFlight_S3.kicad_pcb';b=p.BOARD()
# Populate the MCP-initialized project with a reproducible native board.
b.SetCopperLayerCount(6);b.GetDesignSettings().SetBoardThickness(p.FromMM(1.0))
parts=json.loads((ROOT/'design.json').read_text());meta={c['ref']:c for c in parts};xml=ET.parse(ROOT/'reports/RoveFlight_S3.xml').getroot();comps={c.attrib['ref']:c for c in xml.find('components')};pin_nets={}
for n in xml.find('nets'):
 for a in n.findall('node'):pin_nets[(a.attrib['ref'],a.attrib['pin'])]=n.attrib['name'].lstrip('/')
nets={}
for name in sorted(set(pin_nets.values())):
 n=p.NETINFO_ITEM(b,name);b.Add(n);nets[name]=n
fps={}
for c in parts:
 lib,name=c['fp'].split(':');libpath=ROOT/'libraries'/f'{lib}.pretty' if lib=='RoveFlight' else Path('/usr/share/kicad/footprints')/f'{lib}.pretty';fp=p.FootprintLoad(str(libpath),name);assert fp,c['fp']
 fp.SetReference(c['ref']);fp.SetValue(c['value']);fp.SetFPID(p.LIB_ID(lib,name));el=comps[c['ref']];fp.SetPath(p.KIID_PATH(el.find('sheetpath').attrib['tstamps']+el.find('tstamps').text.split()[0]))
 for pad in fp.Pads():
  name=pin_nets.get((c['ref'],pad.GetNumber()))
  if name:pad.SetNet(nets[name])
 fp.Reference().SetVisible(False);fp.Value().SetVisible(False);b.Add(fp);fps[c['ref']]=fp
holes=[(9.75,9.75),(35.25,9.75),(9.75,35.25),(35.25,35.25)]
def pos(fp,x,y,rot=0,side='F'):
 if (side=='B')!=(fp.GetLayer()==p.B_Cu):fp.Flip(fp.GetPosition(),False)
 fp.SetOrientationDegrees(rot);fp.SetPosition(p.VECTOR2I(p.FromMM(x),p.FromMM(y)))
def bbox(fp):
 if fp.GetReference()=='U1':
  q=fp.GetPosition();x,y=p.ToMM(q.x),p.ToMM(q.y);return x-9.775,y-12.75,x+9.775,y+13.475
 layer=p.F_CrtYd if fp.GetLayer()==p.F_Cu else p.B_CrtYd;rs=[z.GetBoundingBox() for z in fp.GraphicalItems() if z.GetLayer()==layer]
 if not rs:r=fp.GetBoundingBox(False,False);return p.ToMM(r.GetX()),p.ToMM(r.GetY()),p.ToMM(r.GetRight()),p.ToMM(r.GetBottom())
 return min(p.ToMM(r.GetX()) for r in rs),min(p.ToMM(r.GetY()) for r in rs),max(p.ToMM(r.GetRight()) for r in rs),max(p.ToMM(r.GetBottom()) for r in rs)
def overlap(a,z,m=.12):return min(a[2],z[2])-max(a[0],z[0])>-m and min(a[3],z[3])-max(a[1],z[1])>-m
placed=[];boxes={}
def legal(fp):
 ref=fp.GetReference();q=bbox(fp)
 if q[0]<.4 or q[2]>W-.4 or q[3]>H-.4:return False
 if q[1]<.4 and ref!='U1':return False
 # Antenna overhang occupies all sides; keep top edge free of other components.
 if ref!='U1' and q[1]<1:return False
 for x,y in holes:
  if overlap(q,(x-2.5,y-2.5,x+2.5,y+2.5)):return False
 for old in placed:
  if old.GetLayer()==fp.GetLayer() and overlap(q,boxes[old.GetReference()]):return False
  for pad in old.Pads():
   if old.GetLayer()!=fp.GetLayer() and pad.GetDrillSize().x>0:
    bb=pad.GetBoundingBox();r=(p.ToMM(bb.GetX()),p.ToMM(bb.GetY()),p.ToMM(bb.GetRight()),p.ToMM(bb.GetBottom()))
    if overlap(q,r):return False
 return True
def place(ref,xy,rot=0,sides=('F',),radius=8):
 fp=fps[ref];tiny=len(list(fp.Pads()))<=3 and not ref.startswith(('J','SW'))
 choices=[(dx*.25,dy*.25) for dx in range(-int(radius*4),int(radius*4)+1) for dy in range(-int(radius*4),int(radius*4)+1)];choices.sort(key=lambda v:v[0]**2+v[1]**2)
 for dx,dy in choices:
  for side in sides:
   for r in ([rot,(rot+90)%360,(rot+180)%360,(rot+270)%360] if ref in ['J7','J8','J9','J10'] else [rot,(rot+90)%360] if tiny else [rot]):
    pos(fp,xy[0]+dx,xy[1]+dy,r,side)
    if legal(fp):placed.append(fp);boxes[ref]=bbox(fp);return
 raise ValueError(('No legal placement',ref,xy,bbox(fp)))
# Mechanical anchors, main sensors, and switching devices take precedence.
for ref in ['U1','J2','J3','J4','J5','J6','J1','U2','SW1','SW2','U8','U9','U10','U11','U3','L1','Q1','R100','F1','Q3','Q4','Q5','Q6','D3','D4','D5','D6','U7','U4','U5','U6','U12','JP1','J7','J8','J9','J10','SW3','C100','C101','C102','D1','D2','FB1']:
 c=meta[ref];place(ref,c['xy'],c['rot'],(c['side'],),radius=0 if ref in ['U1','U8','J2','J3','J4','J5','J6'] else 12)
for c in sorted((c for c in parts if c['ref'] not in boxes),key=lambda c:0 if c['name']=='C' else 2 if c['ref'].startswith('TP') else 1):
 ref=c['ref'];parent=fps.get(c['parent']);target=c['xy']
 if target is None:
  if parent:
   pads=[z for z in parent.Pads() if z.GetNetname()==c['nets'].get('1')]
   q=pads[0].GetPosition() if pads else parent.GetPosition();target=(p.ToMM(q.x),p.ToMM(q.y))
  else:target=(22.5,30)
 sides=(c['side'],) if c['xy'] else (('B','F') if parent and parent.GetLayer()==p.B_Cu else ('F','B'))
 place(ref,target,c['rot'],sides,10)
# Native mounting holes, excluded from schematic/BOM.
for i,(x,y) in enumerate(holes,1):
 fp=p.FootprintLoad('/usr/share/kicad/footprints/MountingHole.pretty','MountingHole_2.2mm_M2');fp.SetReference('H'+str(i));fp.SetAttributes(fp.GetAttributes()|p.FP_BOARD_ONLY);pos(fp,x,y);fp.Reference().SetVisible(False);fp.Value().SetVisible(False);b.Add(fp)
pts=[(1,0),(44,0),(45,1),(45,44),(44,45),(1,45),(0,44),(0,1)]
for a,z in zip(pts,pts[1:]+pts[:1]):
 o=p.PCB_SHAPE();o.SetShape(p.SHAPE_T_SEGMENT);o.SetStart(p.VECTOR2I(p.FromMM(a[0]),p.FromMM(a[1])));o.SetEnd(p.VECTOR2I(p.FromMM(z[0]),p.FromMM(z[1])));o.SetLayer(p.Edge_Cuts);o.SetWidth(p.FromMM(.05));b.Add(o)
# Ground/reference plane In1; motor supply plane In2. Neither is used for signals.
for layer,net in [(p.In1_Cu,'GND'),(p.In4_Cu,'GND'),(p.In2_Cu,'VM'),(p.F_Cu,'GND'),(p.B_Cu,'GND')]:
 z=p.ZONE(b);z.SetLayer(layer);z.SetNet(nets[net]);z.SetLocalClearance(p.FromMM(.18));z.SetMinThickness(p.FromMM(.15));z.SetPadConnection(p.ZONE_CONNECTION_FULL);z.SetIslandRemovalMode(p.ISLAND_REMOVAL_MODE_ALWAYS);poly=z.Outline();poly.NewOutline()
 for x,y in [(.5,.5),(44.5,.5),(44.5,44.5),(.5,44.5)]:poly.Append(p.FromMM(x),p.FromMM(y))
 b.Add(z)
# Board title and physical orientation.
tb=b.GetTitleBlock();tb.SetTitle('RoveFlight S3 | 1S brushed quad');tb.SetRevision('A.0 ENGINEERING PROTOTYPE');tb.SetDate('2026-11-08');tb.SetComment(0,'45x45mm | 4 layers | 25.5mm M2 mounting');b.SetTitleBlock(tb)
p.SaveBoard(str(path),b)
# Explicit process rules, not relaxed to mask a violation.
pro=json.loads((ROOT/'RoveFlight_S3.kicad_pro').read_text());nc=pro.setdefault('net_settings',{});nc['classes']=[]
classes={'Default':(.15,.16,.5,.25),'Power':(.15,.5,.6,.3),'Motor':(.15,1.,.7,.3),'Battery':(.15,2.,.8,.4)}
for name,(cl,tw,vd,dr) in classes.items():nc['classes'].append(dict(name=name,clearance=cl,track_width=tw,via_diameter=vd,via_drill=dr,microvia_diameter=.3,microvia_drill=.1,diff_pair_width=.18,diff_pair_gap=.15,diff_pair_via_gap=.2,wire_width=6,bus_width=12,line_style=0,pcb_color='rgba(0,0,0,0.000)',schematic_color='rgba(0,0,0,0.000)'))
assign={}
for name in nets:
 if name in ['BAT_RAW','BAT_FUSED','BAT_PROTECTED','VM']:assign[name]='Battery'
 elif name.endswith('_NEG'):assign[name]='Motor'
 elif name in ['+3V3','+3V3_SENS','SYS_IN','REG_L1','REG_L2','USB_VBUS']:assign[name]='Power'
nc['netclass_assignments']={};nc['netclass_patterns']=[{'pattern':n,'netclass':v} for n,v in assign.items()]
rules=pro.setdefault('board',{}).setdefault('design_settings',{}).setdefault('rules',{});rules.update(min_clearance=.15,min_track_width=.125,min_via_diameter=.45,min_through_hole_diameter=.2,min_hole_clearance=.25,min_copper_edge_clearance=.25,min_silk_clearance=.1,min_text_height=.6,min_text_thickness=.1)
(ROOT/'RoveFlight_S3.kicad_pro').write_text(json.dumps(pro,indent=2));placement=[]
for c in parts:
 fp=fps[c['ref']];q=fp.GetPosition();placement.append(dict(ref=c['ref'],x=p.ToMM(q.x),y=p.ToMM(q.y),rotation=fp.GetOrientationDegrees(),side='F' if fp.GetLayer()==p.F_Cu else 'B',courtyard=boxes[c['ref']],parent=c['parent']))
(ROOT/'placement.json').write_text(json.dumps(placement,indent=2));print('Placed',len(parts),'electrical entries plus 4 mounting holes')
