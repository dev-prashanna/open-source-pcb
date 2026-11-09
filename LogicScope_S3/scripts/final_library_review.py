from cadlib import *
import pcbnew as p
# Exact 1206 PPTC package filter instead of suppressing a generic library warning.
lib=ROOT/'libraries/LogicScope.kicad_sym';doc=sx.loads(lib.read_text());sym=symbol('Device','Polyfuse');sym[1]='Polyfuse_1206'
for item in nodes(sym,'symbol'):item[1]=str(item[1]).replace('Polyfuse_','Polyfuse_1206_',1)
for field in nodes(sym,'property'):
 if field[1]=='ki_fp_filters':field[2]='Fuse_1206*'
 if field[1]=='Footprint':field[2]='Fuse:Fuse_1206_3216Metric'
 if field[1]=='Datasheet':field[2]='https://www.littelfuse.com/products/polyswitch-resettable-pptcs/surface-mount/1206l'
doc.append(sym);lib.write_text(sx.dumps(doc)+'\n')
for file in ROOT.glob('*.kicad_sch'):
 d=sx.loads(file.read_text())
 for cached in nodes(node(d,'lib_symbols'),'symbol'):
  if cached[1]=='Device:Polyfuse':
   cached[:]=copy.deepcopy(sym);cached[1]='LogicScope:Polyfuse_1206'
 for instance in nodes(d,'symbol'):
  fields={f[1]:f for f in nodes(instance,'property')};ref=fields.get('Reference',[None,None,None])[2]
  if ref=='F1':node(instance,'lib_id')[1]='LogicScope:Polyfuse_1206'
  if ref in ['TP6','TP7']:fields['Footprint'][2]='LogicScope:TestPoint_D0.5mm'
 file.write_text(sx.dumps(d)+'\n')
b=p.LoadBoard(str(ROOT/'LogicScope_S3.kicad_pcb'));fps={f.GetReference():f for f in b.GetFootprints()}
for ref in ['TP6','TP7']:fps[ref].SetFPID(p.LIB_ID('LogicScope','TestPoint_D0.5mm'))
clone=p.Cast_to_FOOTPRINT(fps['TP6'].Duplicate(False));clone.SetPosition(p.VECTOR2I(0,0));clone.SetOrientationDegrees(0);clone.SetReference('REF**');clone.SetValue('TestPoint_D0.5mm')
for q in clone.Pads():q.SetNetCode(0)
p.FootprintSave(str(ROOT/'libraries/LogicScope.pretty'),clone)
for ref in ['TP3','D1','D2']:
 t=fps[ref].Reference();t.SetLayer(p.F_Fab);t.SetPosition(fps[ref].GetPosition())
for t in b.GetDrawings():
 if isinstance(t,p.PCB_TEXT) and t.GetLayer()==p.F_SilkS and t.GetText()=='CAP':t.SetPosition(p.VECTOR2I(p.FromMM(45),p.FromMM(24.5)))
p.SaveBoard(str(ROOT/'LogicScope_S3.kicad_pcb'),b)
parts=json.loads((ROOT/'design.json').read_text())
for part in parts:
 if part['ref']=='F1':part.update(lib='LogicScope',name='Polyfuse_1206')
 if part['ref'] in ['TP6','TP7']:part['fp']='LogicScope:TestPoint_D0.5mm'
 if part['ref']=='R25':part['xy']=[14.5,19.]
 if part['ref']=='R26':part['xy']=[14.5,21.]
(ROOT/'design.json').write_text(json.dumps(parts,indent=2)+'\n')
