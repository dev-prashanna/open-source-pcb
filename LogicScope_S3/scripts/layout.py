"""Populate the MCP-created board from the exported schematic netlist.

Two copper layers, all parts on the front, rear ground reference reserved.
Running this script resets placement/routing; release.py never invokes it.
"""
from cadlib import *
import pcbnew as p
import xml.etree.ElementTree as ET

path=ROOT/'LogicScope_S3.kicad_pcb'
board=p.LoadBoard(str(path))
assert not list(board.GetFootprints()) and not list(board.GetTracks()), 'Work on a fresh MCP outline; do not discard completed routing'
board.SetCopperLayerCount(2)
board.GetDesignSettings().SetBoardThickness(p.FromMM(.8))
parts=json.loads((ROOT/'design.json').read_text());meta={z['ref']:z for z in parts}
xml=ET.parse(ROOT/'reports/LogicScope_S3.xml').getroot()
components={c.attrib['ref']:c for c in xml.find('components')}
pin_nets={(n.attrib['ref'],n.attrib['pin']):net.attrib['name'].lstrip('/') for net in xml.find('nets') for n in net.findall('node')}
nets={}
for name in sorted(set(pin_nets.values())):
    item=p.NETINFO_ITEM(board,name);board.Add(item);nets[name]=item
fps={}
for part in parts:
    lib,name=part['fp'].split(':')
    library=ROOT/'libraries/LogicScope.pretty' if lib=='LogicScope' else Path('/usr/share/kicad/footprints')/(lib+'.pretty')
    fp=p.FootprintLoad(str(library),name);assert fp,part['fp']
    fp.SetReference(part['ref']);fp.SetValue(part['value']);fp.SetFPID(p.LIB_ID(lib,name))
    component=components[part['ref']]
    fp.SetPath(p.KIID_PATH(component.find('sheetpath').attrib['tstamps']+component.find('tstamps').text.split()[0]))
    if part.get('dnp'):fp.SetAttributes(fp.GetAttributes()|p.FP_DNP)
    if part['ref'].startswith('TP'):fp.SetAttributes(fp.GetAttributes()|p.FP_EXCLUDE_FROM_BOM)
    for pad in fp.Pads():
        name=pin_nets.get((part['ref'],pad.GetNumber()))
        if name:pad.SetNet(nets[name])
    for key,value in [('MPN',part['mpn']),('Manufacturer',part['mfr'])]:
        field=p.PCB_FIELD(fp,p.FIELD_T_USER,key);field.SetText(value);field.SetVisible(False);fp.Add(field)
    fp.GetField(p.FIELD_T_DATASHEET).SetText(part['source'])
    fp.Reference().SetVisible(False);fp.Value().SetVisible(False)
    board.Add(fp);fps[part['ref']]=fp
holes=[(3.,37.5),(52.,37.5)]
def rect(fp):
    if fp.GetReference()=='U1':
        q=fp.GetPosition();x,y=p.ToMM(q.x),p.ToMM(q.y)
        # Antenna clearance extends outside the PCB; use the body for packing.
        # The unmodified native courtyard and all-layer rule area remain in DRC.
        return x-9.775,y-12.75,x+9.775,y+13.475
    drawings=[x.GetBoundingBox() for x in fp.GraphicalItems() if x.GetLayer()==p.F_CrtYd]
    if not drawings:drawings=[fp.GetBoundingBox(False,False)]
    return min(p.ToMM(x.GetX()) for x in drawings),min(p.ToMM(x.GetY()) for x in drawings),max(p.ToMM(x.GetRight()) for x in drawings),max(p.ToMM(x.GetBottom()) for x in drawings)
def overlap(a,z,margin=.1):
    return min(a[2],z[2])-max(a[0],z[0])>-margin and min(a[3],z[3])-max(a[1],z[1])>-margin
placed=[];boxes={}
def legal(fp):
    ref=fp.GetReference();r=rect(fp)
    if r[0]<.4 or r[2]>54.6:return False
    if r[1]<.4 and ref!='U1':return False
    if r[3]>39.6 and ref!='J3':return False
    if any(overlap(r,(x-2.2,y-2.2,x+2.2,y+2.2)) for x,y in holes):return False
    return not any(overlap(r,boxes[old]) for old in placed)
def place(ref):
    part=meta[ref];fp=fps[ref];xy=part['xy'];rot=part['rot']
    fixed=ref in ('U1','U2','U3','U4','J1','J2','J3','J4','L1')
    offsets=[(0,0)] if fixed else sorted([(i*.25,j*.25) for i in range(-24,25) for j in range(-24,25)],key=lambda q:q[0]**2+q[1]**2)
    for dx,dy in offsets:
        for angle in [rot] if fixed else [rot,(rot+90)%360]:
            fp.SetOrientationDegrees(angle);fp.SetPosition(p.VECTOR2I(p.FromMM(xy[0]+dx),p.FromMM(xy[1]+dy)))
            if legal(fp):placed.append(ref);boxes[ref]=rect(fp);return
    raise RuntimeError(('Placement blocked',ref,xy,rect(fp)))
for ref in ('U1','J1','J2','J3','J4','U2','U3','L1','U4','U5','U6','SW1','SW2','F1'):
    place(ref)
for part in sorted((z for z in parts if z['ref'] not in placed),key=lambda z:0 if z['ref'].startswith('C') else 2 if z['ref'].startswith('TP') else 1):place(part['ref'])
for i,(x,y) in enumerate(holes,1):
    fp=p.FootprintLoad('/usr/share/kicad/footprints/MountingHole.pretty','MountingHole_2.2mm_M2')
    fp.SetReference('H'+str(i));fp.SetAttributes(fp.GetAttributes()|p.FP_BOARD_ONLY|p.FP_EXCLUDE_FROM_BOM|p.FP_EXCLUDE_FROM_POS_FILES)
    fp.SetPosition(p.VECTOR2I(p.FromMM(x),p.FromMM(y)));fp.Reference().SetVisible(False);fp.Value().SetVisible(False);board.Add(fp)
for layer in (p.F_Cu,p.B_Cu):
    zone=p.ZONE(board);zone.SetLayer(layer);zone.SetNet(nets['GND'])
    zone.SetLocalClearance(p.FromMM(.2));zone.SetMinThickness(p.FromMM(.2));zone.SetPadConnection(p.ZONE_CONNECTION_FULL)
    zone.SetIslandRemovalMode(p.ISLAND_REMOVAL_MODE_ALWAYS)
    poly=zone.Outline();poly.NewOutline()
    for x,y in [(.3,.3),(54.7,.3),(54.7,39.7),(.3,39.7)]:poly.Append(p.FromMM(x),p.FromMM(y))
    board.Add(zone)
tb=board.GetTitleBlock();tb.SetTitle('LogicScope S3 | Eight digital channels');tb.SetRevision('LS-S3-A0 ENGINEERING PROTOTYPE');tb.SetDate('2026-11-09');tb.SetCompany('Prashanna Tiwari');tb.SetComment(0,'55x40mm | 2 copper layers | 0.8mm nominal');board.SetTitleBlock(tb)
p.SaveBoard(str(path),board)
project=json.loads((ROOT/'LogicScope_S3.kicad_pro').read_text())
rules=project['board']['design_settings']['rules']
rules.update(min_clearance=.15,min_track_width=.15,min_via_diameter=.6,min_through_hole_diameter=.3,min_hole_clearance=.25,min_copper_edge_clearance=.25,min_silk_clearance=.1,min_text_height=.7,min_text_thickness=.1)
default=project['net_settings']['classes'][0]
default.update(clearance=.15,track_width=.2,via_diameter=.6,via_drill=.3,diff_pair_width=.75,diff_pair_gap=.15,diff_pair_via_gap=.25)
usb=copy.deepcopy(default);usb.update(name='USB',track_width=.25,diff_pair_width=.75,diff_pair_gap=.15)
power=copy.deepcopy(default);power.update(name='Power',track_width=.6)
project['net_settings']['classes']=[default,usb,power]
project['net_settings']['netclass_patterns']=[{'pattern':n,'netclass':'USB'} for n in ['USB_DP','USB_DM','USB_DP_CONN','USB_DM_CONN']]+[{'pattern':n,'netclass':'Power'} for n in ['+3V3','VUSB','USB_5V','SW']]
(ROOT/'LogicScope_S3.kicad_pro').write_text(json.dumps(project,indent=2)+'\n')
report=[]
for ref,fp in fps.items():
    q=fp.GetPosition();report.append({'ref':ref,'x':p.ToMM(q.x),'y':p.ToMM(q.y),'rotation':fp.GetOrientationDegrees(),'side':'F','courtyard':boxes[ref]})
(ROOT/'placement.json').write_text(json.dumps(report,indent=2)+'\n')
print('Placed',len(parts),'electrical footprints and 2 M2 holes on two-layer MCP board')
