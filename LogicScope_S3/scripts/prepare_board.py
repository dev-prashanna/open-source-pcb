"""Apply verified process requirements and orient the USB flow-through protector."""
from cadlib import *
import pcbnew as p
import shutil

path=ROOT/'LogicScope_S3.kicad_pcb';b=p.LoadBoard(str(path))
fps={f.GetReference():f for f in b.GetFootprints()}
fps['U4'].SetOrientationDegrees(90)
# Preserve the module antenna keepout and move only off-board silk to Fab.
fp=fps['U1']
for item in fp.GraphicalItems():
    if item.GetLayer()==p.F_SilkS and p.ToMM(item.GetBoundingBox().GetY())<.2:item.SetLayer(p.F_Fab)
name='ESP32-S3-WROOM-1_Overhang'
fp.SetFPID(p.LIB_ID('LogicScope',name))
clone=p.Cast_to_FOOTPRINT(fp.Duplicate(False));clone.SetPosition(p.VECTOR2I(0,0));clone.SetOrientationDegrees(0)
clone.SetReference('REF**');clone.SetValue(name)
for q in clone.Pads():q.SetNetCode(0)
shutil.copyfile('/usr/share/kicad/footprints/RF_Module.pretty/ESP32-S3-WROOM-1.kicad_mod',ROOT/'libraries/LogicScope.pretty/ESP32-S3-WROOM-1.kicad_mod')
p.FootprintSave(str(ROOT/'libraries/LogicScope.pretty'),clone)
# Physical, subtractively etched copper lettering; rear ground stays intact.
for layer,y,size in [(p.F_Cu,36.6,1.2),(p.F_SilkS,34.5,.9)]:
    text=p.PCB_TEXT(b);text.SetText('TIWARI');text.SetLayer(layer)
    text.SetPosition(p.VECTOR2I(p.FromMM(15),p.FromMM(y)))
    text.SetTextSize(p.VECTOR2I(p.FromMM(size),p.FromMM(size)));text.SetTextThickness(p.FromMM(.15))
    if layer==p.F_Cu:text.SetIsKnockout(True)
    b.Add(text)
area=p.ZONE(b);area.SetLayer(p.F_Cu);area.SetIsRuleArea(True)
area.SetDoNotAllowTracks(True);area.SetDoNotAllowVias(True);area.SetDoNotAllowZoneFills(False)
outline=area.Outline();outline.NewOutline()
for x,y in [(10.5,35.5),(19.5,35.5),(19.5,37.7),(10.5,37.7)]:outline.Append(p.FromMM(x),p.FromMM(y))
b.Add(area)
p.SaveBoard(str(path),b)
parts=json.loads((ROOT/'design.json').read_text())
for part in parts:
    if part['ref']=='U1':part['fp']='LogicScope:'+name
    if part['ref']=='U4':part['rot']=90
(ROOT/'design.json').write_text(json.dumps(parts,indent=2)+'\n')
for file in ROOT.glob('*.kicad_sch'):
    doc=sx.loads(file.read_text())
    for sym in nodes(doc,'symbol'):
        fields={f[1]:f for f in nodes(sym,'property')}
        if fields.get('Reference',[None,None,None])[2]=='U1':fields['Footprint'][2]='LogicScope:'+name
    file.write_text(sx.dumps(doc)+'\n')
project=json.loads((ROOT/'LogicScope_S3.kicad_pro').read_text())
# The native module includes 0.2-mm thermal drills; routing vias stay 0.6/0.3 mm.
project['board']['design_settings']['rules']['min_through_hole_diameter']=.2
(ROOT/'LogicScope_S3.kicad_pro').write_text(json.dumps(project,indent=2)+'\n')
(ROOT/'LogicScope_S3.kicad_dru').write_text('''(version 1)
# GCT USB4105 recommended land pattern, drawing B3, component-side view.
# Internal peg-to-GND-land clearance is 0.1944mm. Requires fab >=0.18mm capability.
# Unrelated routing keeps the global 0.25mm copper-to-hole rule.
(rule "USB4105 manufacturer internal peg land spacing"
  (condition "A.memberOfFootprint('J3') && B.memberOfFootprint('J3')")
  (constraint hole_clearance (min 0.18mm)))
''')
print('Recorded module thermal drills and connector manufacturer geometry; other routing rules unchanged')
