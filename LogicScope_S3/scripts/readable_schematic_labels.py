"""Make vertical pin-net labels horizontal and clear of component values."""
from cadlib import *
for file in ROOT.glob('[0-9]*.kicad_sch'):
 d=sx.loads(file.read_text());added=[]
 for label in nodes(d,'global_label'):
  at=node(label,'at');x,y,angle=map(float,at[1:4])
  if angle not in [90.,270.]:continue
  at[1]=round(x+5.08,4);at[3]=180
  added.append([S('wire'),[S('pts'),[S('xy'),x,y],[S('xy'),at[1],y]],[S('stroke'),[S('width'),0],[S('type'),S('default')]],[S('uuid'),uid()]])
 d.extend(added);file.write_text(sx.dumps(d)+'\n')
 print(file.name,len(added),'horizontal labels')
