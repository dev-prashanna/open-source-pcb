from cadlib import *
import pcbnew as p
b=p.LoadBoard(str(ROOT/'LogicScope_S3.kicad_pcb'))
for fp in b.GetFootprints():
 if fp.GetReference().startswith('TP'):fp.SetAttributes(fp.GetAttributes()|p.FP_EXCLUDE_FROM_POS_FILES)
p.SaveBoard(str(ROOT/'LogicScope_S3.kicad_pcb'),b)
for f in ROOT.glob('*.kicad_sch'):
 d=sx.loads(f.read_text());changed=False
 for q in nodes(d,'symbol'):
  fields={v[1]:v for v in nodes(q,'property')}
  if fields.get('Reference',[None,None,''])[2].startswith('TP'):
   v=node(q,'in_pos_files')
   if v:v[1]=S('no')
   else:q.append([S('in_pos_files'),S('no')])
   changed=True
 if changed:f.write_text(sx.dumps(d)+'\n')
