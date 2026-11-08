"""Place RoveCore One using real courtyards; export native board and DSN.
Physical placement is reproducible, with closest-pad decoupler placement priorities.
"""
from cadlib import *
import pcbnew as p
import xml.etree.ElementTree as ET
W,H=80,65
b=p.BOARD();b.SetCopperLayerCount(4);b.GetDesignSettings().SetBoardThickness(p.FromMM(1.6))
parts=json.loads((ROOT/'design.json').read_text())
# Get schematic paths from the actual netlist, not manufactured PCB identities.
netroot=ET.parse(ROOT/'reports/RoveCore_One.xml').getroot()
compxml={c.attrib['ref']:c for c in netroot.find('components')}
allnets=sorted({n for c in parts for n in c['nets'].values() if n});nets={}
for n in allnets:z=p.NETINFO_ITEM(b,n);b.Add(z);nets[n]=z
fps={};meta={c['ref']:c for c in parts}
for c in parts:
 lib,name=c['fp'].split(':');libpath=ROOT/'libraries'/f'{lib}.pretty' if lib=='RoveCore' else Path('/usr/share/kicad/footprints')/f'{lib}.pretty'
 fp=p.FootprintLoad(str(libpath),name)
 if fp is None:raise ValueError('Missing footprint '+c['fp'])
 fp.SetReference(c['ref']);fp.SetValue(c['value']);fp.SetFPID(p.LIB_ID(lib,name))
 el=compxml.get(c['ref'])
 if el is not None:
  path=el.find('sheetpath').attrib['tstamps']+el.find('tstamps').text.split()[0]
  fp.SetPath(p.KIID_PATH(path))
 for pad in fp.Pads():
  nn=c['nets'].get(pad.GetNumber())
  if not nn:nn=next((v for k,v in c['nets'].items() if k.startswith('[') and pad.GetNumber() in k.strip('[]').split(',')),None)
  if nn:pad.SetNet(nets[nn])
 fp.Reference().SetTextSize(p.VECTOR2I(p.FromMM(.65),p.FromMM(.65)));fp.Reference().SetTextThickness(p.FromMM(.1));fp.Value().SetVisible(False)
 b.Add(fp);fps[c['ref']]=fp
def pos(fp,x,y,rot=0,side='F'):
 if side=='B' and fp.GetLayer()!=p.B_Cu:fp.Flip(fp.GetPosition(),False)
 if side=='F' and fp.GetLayer()!=p.F_Cu:fp.Flip(fp.GetPosition(),False)
 fp.SetOrientationDegrees(rot);fp.SetPosition(p.VECTOR2I(p.FromMM(x),p.FromMM(y)))
def bbox(fp):
 if fp.GetReference()=='U1':
  a=fp.GetPosition();x,y=p.ToMM(a.x),p.ToMM(a.y)
  return x-9.3,y-13.1,x+9.3,y+13.6
 layer=p.B_CrtYd if fp.GetLayer()==p.B_Cu else p.F_CrtYd
 rects=[z.GetBoundingBox() for z in fp.GraphicalItems() if z.GetLayer()==layer and isinstance(z,p.PCB_SHAPE)]
 if not rects:rects=[z.GetBoundingBox() for z in fp.Pads()]
 return min(p.ToMM(r.GetX()) for r in rects),min(p.ToMM(r.GetY()) for r in rects),max(p.ToMM(r.GetRight()) for r in rects),max(p.ToMM(r.GetBottom()) for r in rects)
def overlap(a,z,margin=.12):return min(a[2],z[2])-max(a[0],z[0])>-margin and min(a[3],z[3])-max(a[1],z[1])>-margin
placed=[];bboxes={}
holes=[(3.5,3.5),(76.5,3.5),(3.5,61.5),(76.5,61.5)]
def legal(fp):
 box=bbox(fp);ref=fp.GetReference()
 if box[0]<.35 or box[2]>W-.35 or box[3]>H-.35:return False
 if box[1]<.35 and ref!='U1':return False
 if ref=='U1' and box[1]<-7.5:return False
 for x,y in holes:
  if overlap(box,(x-2,y-2,x+2,y+2),.2):return False
 for q in placed:
  # Through-hole pads reserve both sides; body courtyard is side-specific.
  if q.GetLayer()==fp.GetLayer() and overlap(box,bboxes[q.GetReference()]):return False
  if q.GetLayer()!=fp.GetLayer():
   for pad in q.Pads():
    if pad.GetAttribute()==p.PAD_ATTRIB_PTH and overlap(box,(p.ToMM(pad.GetPosition().x)-1,p.ToMM(pad.GetPosition().y)-1,p.ToMM(pad.GetPosition().x)+1,p.ToMM(pad.GetPosition().y)+1),.2):return False
 return True
def reserve(fp):placed.append(fp);bboxes[fp.GetReference()]=bbox(fp)
def place(fp,target,rot=0,sides=['F'],maxdist=15):
 # Closest feasible courtyard on 0.5mm grid. Rotate passives for a useful fit.
 tiny=len(list(fp.Pads()))<=3 and not fp.GetReference().startswith(('J','SW','BZ'))
 choices=[(0,0)]
 for dy in range(-int(maxdist*2),int(maxdist*2)+1):
  for dx in range(-int(maxdist*2),int(maxdist*2)+1):
   if dx or dy:choices.append((dx*.5,dy*.5))
 choices.sort(key=lambda z:z[0]**2+z[1]**2)
 for dx,dy in choices:
  for side in sides:
   for r in [rot,(rot+90)%360] if tiny else [rot]:
    pos(fp,target[0]+dx,target[1]+dy,r,side)
    if legal(fp):reserve(fp);return
 print('Placement failed:',fp.GetReference(),target,flush=True)
 raise ValueError('No place for '+fp.GetReference())

# Mechanical anchor locations. Origins follow library footprints, not body centers.
anchors={'U1':(22,6,0),'J2':(5.5,43,270),'J3':(10,60,0),'J4':(22,60,0),'J5':(35,60,0),'J6':(59,60,0),'J7':(76,43,90),'J8':(76,54,90),'J19':(77,7,0),'J20':(2.5,7,0),'J21':(35,8,0),'J1':(14,23,0),'SW1':(7.5,25,0),'SW2':(7.5,31,0),'SW3':(7.5,19,0),'J9':(73,24,90),'J10':(73,32,90),'J11':(73,38,90),'J12':(51.5,16,0),'J13':(57,16,0),'J14':(62.5,16,0),'J15':(68,16,0),'J16':(43,14,180),'J17':(39,22,0),'J18':(57,25,0),'J22':(59,5,180),'J23':(63,40,0),'JP1':(48,59,90),'BZ1':(25,30,0)}
for ref,(x,y,r) in anchors.items():place(fps[ref],(x,y),r,maxdist=9 if ref.startswith('J') else 6)
# Sensors fixed near front edge, IMU at center. Switching regulators on lower half.
for ref in ['U9','U10','U11','U12','U8','U2','U3','U4','U5','U6','U7','U19','U21','U22','U14','U20','U13','U15','U16','U17','U18']:
 c=meta[ref];place(fps[ref],c['xy'],c['rot'],maxdist=9)
# High-energy components first; electrical parent gives the local placement region.
remaining=[c for c in parts if c['ref'] not in bboxes]
def rank(c):
 return 0 if c['name']=='C' and c['parent'] in ['U4','U5','U6','U7'] else 1 if c['name'] in ['L','C_Polarized'] else 2 if c['ref'].startswith(('F','Q')) else 3 if c['name']=='C' else 4
remaining.sort(key=rank)
fallback={'Power Inputs':(17,52),'User Interface':(19,29),'Controller':(18,22),'Servo Power':(44,51),'Motor Driver':(65,48)}
for c in remaining:
 target=None
 if c['parent'] in fps and c['parent'] in bboxes:
  pt=fps[c['parent']].GetPosition();target=(p.ToMM(pt.x),p.ToMM(pt.y))
 if target is None:target=fallback.get(c['section'],(40,37))
 # Place bypass caps closest to the corresponding parent's supply pad.
 if c['name']=='C' and c['parent'] in fps:
  choices=[pad for pad in fps[c['parent']].Pads() if pad.GetNetname()==c['nets'].get('1')]
  if choices:
   a=choices[0].GetPosition();target=(p.ToMM(a.x),p.ToMM(a.y))
 sides=['F','B']
 place(fps[c['ref']],target,c['rot'],sides,maxdist=19)

for i,(x,y) in enumerate(holes):
 fp=p.FootprintLoad('/usr/share/kicad/footprints/MountingHole.pretty','MountingHole_2.7mm_M2.5');fp.SetReference('H'+str(i+1));fp.SetPosition(p.VECTOR2I(p.FromMM(x),p.FromMM(y)));fp.Value().SetVisible(False);b.Add(fp)
# Chamfered corners give a distinctive, fabricator-friendly outline.
pts=[(1.5,0),(78.5,0),(80,1.5),(80,63.5),(78.5,65),(1.5,65),(0,63.5),(0,1.5)]
for a,z in zip(pts,pts[1:]+pts[:1]):
 s=p.PCB_SHAPE();s.SetShape(p.SHAPE_T_SEGMENT);s.SetStart(p.VECTOR2I(p.FromMM(a[0]),p.FromMM(a[1])));s.SetEnd(p.VECTOR2I(p.FromMM(z[0]),p.FromMM(z[1])));s.SetLayer(p.Edge_Cuts);s.SetWidth(p.FromMM(.05));b.Add(s)
def text(txt,x,y,size=.8,layer=p.F_SilkS):
 t=p.PCB_TEXT(b);t.SetText(txt);t.SetPosition(p.VECTOR2I(p.FromMM(x),p.FromMM(y)));t.SetTextSize(p.VECTOR2I(p.FromMM(size),p.FromMM(size)));t.SetTextThickness(p.FromMM(.12));t.SetLayer(layer);b.Add(t)
text('ROVECORE ONE',40,33,1.3,p.B_SilkS);text('A.0 | 3V3 LOGIC | PROTOTYPE',40,35,.9,p.B_SilkS)
text('PLUG IN. PROGRAM. BUILD.',40,37,.8,p.B_SilkS)
# Reference labels are moved off the component body; functional labels go to the back
# so they remain legible on a tightly populated front assembly.
for c in parts:
 fp=fps[c['ref']];q=fp.GetPosition();x,y=p.ToMM(q.x),p.ToMM(q.y);box=bbox(fp)
 fp.Reference().SetPosition(p.VECTOR2I(p.FromMM(x),p.FromMM(box[1]-.5)));fp.Reference().SetTextAngle(p.EDA_ANGLE(0,p.DEGREES_T))
 if c['ref'].startswith('J'):
  text(c['ref']+' '+c['value'],x,y,.65,p.B_SilkS)
# Rules and net classes are written in the project so the router and DRC agree.
pro=json.loads((ROOT/'RoveCore_One.kicad_pro').read_text());nc=pro.setdefault('net_settings',{});nc['classes']=[]
classes={'Default':(.18,.18,.55,.25),'LogicPower':(.18,.65,.7,.3),'Motor':(.2,.8,.8,.4),'Servo':(.2,1.2,.9,.4),'Battery':(.2,1.2,.9,.4)}
for name,(cl,tw,vd,dr) in classes.items():nc['classes'].append({'name':name,'clearance':cl,'track_width':tw,'via_diameter':vd,'via_drill':dr,'microvia_diameter':.3,'microvia_drill':.1,'diff_pair_width':.18,'diff_pair_gap':.18,'diff_pair_via_gap':.2,'wire_width':6,'bus_width':12,'line_style':0,'pcb_color':'rgba(0, 0, 0, 0.000)','schematic_color':'rgba(0, 0, 0, 0.000)'})
assign={}
for name in allnets:
 if name in ['VM','MOTOR_RAW','MOTOR_FUSED','MOTOR_A_P','MOTOR_A_N','MOTOR_B_P','MOTOR_B_N','ISENSE_A','ISENSE_B']:assign[name]='Motor'
 elif name.startswith('SERVO_') and name in ['SERVO_BUCK','SERVO5','SERVO_EXT','SERVO_EXT_RAW','SERVO_SELECTED','SW_SERVO']:assign[name]='Servo'
 elif name in ['BAT_RAW','BAT_FUSED','VBAT']:assign[name]='Battery'
 elif name in ['+3V3','+3V3_SENS','BAT5','LOGIC5','SW_3V3','SW_BAT','USB_VBUS','EXT5_RAW','EXT5_FUSED','USB_FUSED']:assign[name]='LogicPower'
nc['netclass_assignments']={};nc['netclass_patterns']=[{'pattern':n,'netclass':v} for n,v in assign.items()]
rules=pro.setdefault('board',{}).setdefault('design_settings',{}).setdefault('rules',{})
rules.update({'min_clearance':.15,'min_track_width':.15,'min_via_diameter':.5,'min_through_hole_diameter':.25,'min_hole_clearance':.25,'min_copper_edge_clearance':.3,'min_silk_clearance':.1,'min_silk_text_height':.6,'min_silk_text_thickness':.1})
(ROOT/'RoveCore_One.kicad_pro').write_text(json.dumps(pro,indent=2))
b.GetDesignSettings().SetCopperEdgeClearance(p.FromMM(.3)) if hasattr(b.GetDesignSettings(),'SetCopperEdgeClearance') else None
p.SaveBoard(str(ROOT/'RoveCore_One.kicad_pcb'),b)
placement=[]
for c in parts:
 fp=fps[c['ref']];q=fp.GetPosition();placement.append({'ref':c['ref'],'x':p.ToMM(q.x),'y':p.ToMM(q.y),'rotation':fp.GetOrientationDegrees(),'side':'F' if fp.GetLayer()==p.F_Cu else 'B','courtyard':bbox(fp),'parent':c['parent']})
(ROOT/'placement.json').write_text(json.dumps(placement,indent=2))
with (ROOT/'Placement.csv').open('w') as f:
 w=csv.writer(f);w.writerow(['Reference','X_mm','Y_mm','Rotation_deg','Side'])
 for c in placement:w.writerow([c['ref'],c['x'],c['y'],c['rotation'],c['side']])
# Reload project settings before export.
b=p.LoadBoard(str(ROOT/'RoveCore_One.kicad_pcb'))
ok=p.ExportSpecctraDSN(b,str(ROOT/'reports/RoveCore_One.dsn'));print('DSN exported',ok)
print('Placed',len(parts),'electrical parts on',W,'x',H,'mm, 4 copper layers')
