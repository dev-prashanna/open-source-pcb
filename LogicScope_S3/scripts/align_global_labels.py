from cadlib import *
for f in ROOT.glob('*.kicad_sch'):
 d=sx.loads(f.read_text())
 for q in nodes(d,'global_label'):
  angle=float(node(q,'at')[3]);ef=node(q,'effects');old=node(ef,'justify')
  if old:ef.remove(old)
  ef.append([S('justify'),S('left' if angle==180 else 'right')])
 f.write_text(sx.dumps(d)+'\n')
