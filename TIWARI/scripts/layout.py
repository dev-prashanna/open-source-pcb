"""Create a four-layer TIWARI board from the electrical netlist.
Regeneration destroys routing; release.py exports the final board without this step.
"""
from cadlib import *
import pcbnew as p
import xml.etree.ElementTree as ET
path=ROOT/'TIWARI.kicad_pcb'
b=p.BOARD();b.SetCopperLayerCount(4);b.GetDesignSettings().SetBoardThickness(p.FromMM(1.0))
parts=json.loads((ROOT/'design.json').read_text());meta={c['ref']:c for c in parts}
xml=ET.parse(ROOT.parent/'reports/netlist.xml').getroot()
components={c.attrib['ref']:c for c in xml.find('components')}
pinnets={(n.attrib['ref'],n.attrib['pin']):net.attrib['name'].lstrip('/') for net in xml.find('nets') for n in net.findall('node')}
nets={}
for name in sorted(set(pinnets.values())):
 net=p.NETINFO_ITEM(b,name);b.Add(net);nets[name]=net
fps={}
for part in parts:
 lib,name=part['fp'].split(':');fp=p.FootprintLoad(str(ROOT/'libraries/TIWARI.pretty') if lib=='TIWARI' else '/usr/share/kicad/footprints/'+lib+'.pretty',name)
 if not fp:raise ValueError(part['fp'])
 fp.SetReference(part['ref']);fp.SetValue(part['value']);fp.SetFPID(p.LIB_ID(lib,name))
 component=components[part['ref']]
 fp.SetPath(p.KIID_PATH(component.find('sheetpath').attrib['tstamps']+component.find('tstamps').text.split()[0]))
 for pad in fp.Pads():
  net=pinnets.get((part['ref'],pad.GetNumber()))
  if net:pad.SetNet(nets[net])
 fp.Reference().SetVisible(False);fp.Value().SetVisible(False)
 field=p.PCB_FIELD(fp,p.FIELD_T_USER,'MPN');field.SetText(part['mpn']);field.SetVisible(False);fp.Add(field)
 field=p.PCB_FIELD(fp,p.FIELD_T_USER,'Manufacturer');field.SetText(part['mfr']);field.SetVisible(False);fp.Add(field)
 fp.GetField(p.FIELD_T_DATASHEET).SetText(part['source'])
 b.Add(fp);fps[part['ref']]=fp
 if part['side']=='B':fp.Flip(p.VECTOR2I(0,0),False)
# Distinctive chamfered outline. No mounting holes to preserve compact header area.
outline=[(2,0),(48,0),(50,2),(50,33),(48,35),(2,35),(0,33),(0,2)]
for a,z in zip(outline,outline[1:]+outline[:1]):
 line=p.PCB_SHAPE();line.SetShape(p.SHAPE_T_SEGMENT);line.SetLayer(p.Edge_Cuts);line.SetWidth(p.FromMM(.05));line.SetStart(p.VECTOR2I(*[p.FromMM(q) for q in a]));line.SetEnd(p.VECTOR2I(*[p.FromMM(q) for q in z]));b.Add(line)
def box(fp):
 boxes=[v.GetBoundingBox() for v in fp.GraphicalItems() if v.GetLayer() in [p.F_CrtYd,p.B_CrtYd]]
 if not boxes:boxes=[fp.GetBoundingBox(False,False)]
 return min(p.ToMM(q.GetX()) for q in boxes),min(p.ToMM(q.GetY()) for q in boxes),max(p.ToMM(q.GetRight()) for q in boxes),max(p.ToMM(q.GetBottom()) for q in boxes)
def intersects(a,z):return min(a[2],z[2])-max(a[0],z[0])>-.05 and min(a[3],z[3])-max(a[1],z[1])>-.05
placed={}
def place(ref,fixed=False):
 part=meta[ref];fp=fps[ref];x,y=part['xy'];angle=part['rot']
 offsets=[(0,0)] if fixed else sorted([(i*.25,j*.25) for i in range(-40,41) for j in range(-40,41)],key=lambda v:v[0]**2+v[1]**2)
 for dx,dy in offsets:
  for rot in [angle] if fixed else [angle,(angle+90)%360]:
   fp.SetPosition(p.VECTOR2I(p.FromMM(x+dx),p.FromMM(y+dy)));fp.SetOrientationDegrees(rot);rect=box(fp)
   if rect[0]<.4 or rect[2]>49.6 or rect[1]<.4 or rect[3]>(37 if ref=='J1' else 34.6):continue
   if any(intersects(rect,old) for oldref,old in placed.items() if meta[oldref]['side']==part['side'] or any(q.GetDrillSize().x for q in fps[oldref].Pads()) or any(q.GetDrillSize().x for q in fp.Pads())):continue
   placed[ref]=rect;return
 if part['side']=='F' and ref.startswith(('C','R','FB','D')):
  fp.Flip(fp.GetPosition(),False);part['side']='B';place(ref);return
 raise RuntimeError(('blocked placement',ref,box(fp)))
for ref in ['U1','U2','J1','J2','J3','J4','Y1','Y2','U7','U8','U3','U4','U5','SW1','SW2','U6','F1']:
 place(ref,ref in ['U1','U2','J1','J2','J3','J4'])
for c in sorted(parts,key=lambda c:0 if c['side']=='B' else 1):
 if c['ref'] not in placed:place(c['ref'])
for layer,netname in [(p.In1_Cu,'GND'),(p.In2_Cu,'+3V3')]:
 zone=p.ZONE(b);zone.SetLayer(layer);zone.SetNet(nets[netname]);zone.SetLocalClearance(p.FromMM(.15));zone.SetMinThickness(p.FromMM(.15));zone.SetPadConnection(p.ZONE_CONNECTION_FULL);zone.SetIslandRemovalMode(p.ISLAND_REMOVAL_MODE_ALWAYS)
 poly=zone.Outline();poly.NewOutline()
 for x,y in [(2,.4),(48,.4),(49.6,2),(49.6,33),(48,34.6),(2,34.6),(.4,33),(.4,2)]:poly.Append(p.FromMM(x),p.FromMM(y))
 b.Add(zone)
tb=b.GetTitleBlock();tb.SetTitle('TIWARI | Original 8-bit CPU Development Board');tb.SetRevision('TW8-A0');tb.SetDate('2026-11-15');tb.SetCompany('Prashanna Tiwari');b.SetTitleBlock(tb)
p.SaveBoard(str(path),b)
proj=json.loads((ROOT/'TIWARI.kicad_pro').read_text());rules=proj['board']['design_settings']['rules'];rules.update(min_clearance=.15,min_track_width=.15,min_via_diameter=.5,min_through_hole_diameter=.25,min_hole_clearance=.18,min_copper_edge_clearance=.25,min_silk_clearance=.1,min_text_height=.7,min_text_thickness=.1)
default=proj['net_settings']['classes'][0];default.update(clearance=.15,track_width=.15,via_diameter=.5,via_drill=.25,diff_pair_width=.18,diff_pair_gap=.15)
usb=copy.deepcopy(default);usb.update(name='USB',track_width=.18)
power=copy.deepcopy(default);power.update(name='Power',track_width=.4)
proj['net_settings']['classes']=[default,usb,power];proj['net_settings']['netclass_patterns']=[{'pattern':n,'netclass':'USB'}for n in ['USB_DP','USB_DM']]+[{'pattern':n,'netclass':'Power'}for n in ['USB_5V','VUSB','+1V2','+3V3','FT_1V8']]
(ROOT/'TIWARI.kicad_pro').write_text(json.dumps(proj,indent=2)+'\n')
(ROOT/'placement.json').write_text(json.dumps([{'ref':ref,'x':p.ToMM(fp.GetPosition().x),'y':p.ToMM(fp.GetPosition().y),'rotation':fp.GetOrientationDegrees(),'side':meta[ref]['side'],'courtyard':placed[ref]}for ref,fp in fps.items()],indent=2))
print('Placed',len(parts),'parts, 50x35mm, four layers')
