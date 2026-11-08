"""Open small holes in crossing tracks for five essential local ground drops.
Only the short obstructing portion is removed; DRC drives subsequent repairs.
"""
from cadlib import *
from shapely.geometry import Point,LineString
targets=[(52.8625,45.95),(11.8625,43.),(30.,41.225),(26.8125,39.05),(50.925,30.)]
path=ROOT/'RoveCore_One.kicad_pcb';doc=sx.loads(path.read_text());out=[];cuts=[]
for n in doc:
 if isinstance(n,list) and n and str(n[0])=='segment' and atom(n,'net')!='GND':
  aa=node(n,'start');zz=node(n,'end');line=LineString([(float(aa[1]),float(aa[2])),(float(zz[1]),float(zz[2]))]);width=float(atom(n,'width'));pieces=[line]
  for x,y in targets:
   nextpieces=[]
   for g in pieces:
    clipped=g.difference(Point(x,y).buffer(.36+width/2+.1))
    if clipped.equals(g):nextpieces.append(g)
    else:
     cuts.append({'net':atom(n,'net'),'near':[x,y]})
     if clipped.geom_type=='LineString':nextpieces.append(clipped)
     elif clipped.geom_type=='MultiLineString':nextpieces+=list(clipped.geoms)
   pieces=nextpieces
  if len(pieces)!=1 or not pieces[0].equals(line):
   for g in pieces:
    if g.length<.03:continue
    nn=copy.deepcopy(n);a,z=list(g.coords)[0],list(g.coords)[-1];node(nn,'start')[1:]=[round(a[0],6),round(a[1],6)];node(nn,'end')[1:]=[round(z[0],6),round(z[1],6)];node(nn,'uuid')[1]=uid();out.append(nn)
   continue
 out.append(n)
path.write_text(sx.dumps(out));(ROOT/'reports/Ground_Priority_Cuts.json').write_text(json.dumps(cuts,indent=2));print('Opened',len(cuts),'short crossings for ground drops')
