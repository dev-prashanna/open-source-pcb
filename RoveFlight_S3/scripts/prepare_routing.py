"""Add clearance-checked plane drops, then export three routing layers with an uninterrupted ground plane."""
from cadlib import *
import pcbnew as p
import numpy as np,re
from shapely.geometry import Point,LineString,Polygon
from shapely.strtree import STRtree
path=ROOT/'RoveFlight_S3.kicad_pcb';b=p.LoadBoard(str(path));layers=[p.F_Cu,p.In1_Cu,p.In2_Cu,p.In3_Cu,p.In4_Cu,p.B_Cu];geoms={l:[] for l in layers};owners={l:[] for l in layers};smd={l:[] for l in layers};holes=[]
for fp in b.GetFootprints():
 for pad in fp.Pads():
  for l in layers:
   if not pad.IsOnLayer(l):continue
   ps=pad.GetEffectivePolygon(l)
   for i in range(ps.OutlineCount()):
    o=ps.COutline(i);g=Polygon([(p.ToMM(o.CPoint(j).x),p.ToMM(o.CPoint(j).y)) for j in range(o.PointCount())]);geoms[l].append(g);owners[l].append(pad.GetNetname())
    if pad.GetAttribute()==p.PAD_ATTRIB_SMD:smd[l].append(g)
  if pad.GetDrillSize().x:
   pt=pad.GetPosition();holes.append(Point(p.ToMM(pt.x),p.ToMM(pt.y)).buffer(max(p.ToMM(pad.GetDrillSize().x),p.ToMM(pad.GetDrillSize().y))/2))
  if pad.GetAttribute()==p.PAD_ATTRIB_NPTH:
   pt=pad.GetPosition();g=Point(p.ToMM(pt.x),p.ToMM(pt.y)).buffer(p.ToMM(pad.GetDrillSize().x)/2)
   for l in layers:geoms[l].append(g);owners[l].append('__HOLE')
trees={l:STRtree(geoms[l]) for l in layers};smdtrees={l:STRtree(smd[l]) for l in layers};extra={l:[] for l in layers}
def clear(g,l,net):
 return not any(owners[l][i]!=net and g.distance(geoms[l][i])<.19 for i in trees[l].query(g.buffer(.20))) and not any(on!=net and g.distance(q)<.19 for q,on in extra[l])
def via(x,y,net,land=.5,drill=.25):
 v=p.PCB_VIA(b);v.SetPosition(p.VECTOR2I(p.FromMM(x),p.FromMM(y)));v.SetWidth(p.FromMM(land));v.SetDrill(p.FromMM(drill));v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetViaType(p.VIATYPE_THROUGH);v.SetNet(b.FindNet(net));b.Add(v);g=Point(x,y).buffer(land/2)
 for l in layers:extra[l].append((g,net))
 holes.append(Point(x,y).buffer(drill/2))
def track(a,z,l,net,w):
 t=p.PCB_TRACK(b);t.SetStart(p.VECTOR2I(p.FromMM(a[0]),p.FromMM(a[1])));t.SetEnd(p.VECTOR2I(p.FromMM(z[0]),p.FromMM(z[1])));t.SetLayer(l);t.SetWidth(p.FromMM(w));t.SetNet(b.FindNet(net));b.Add(t);extra[l].append((LineString([a,z]).buffer(w/2),net))
added=[];failed=[]
for fp in b.GetFootprints():
 for pad in fp.Pads():
  net=pad.GetNetname();ref=fp.GetReference()
  if net not in ['GND','VM'] or pad.GetAttribute()!=p.PAD_ATTRIB_SMD or pad.GetDrillSize().x:continue
  if any(other.GetNumber()==pad.GetNumber() and other.GetDrillSize().x for other in fp.Pads()):continue
  pt=pad.GetPosition();x,y=p.ToMM(pt.x),p.ToMM(pt.y);layer=p.F_Cu if pad.IsOnLayer(p.F_Cu) else p.B_Cu
  high=(ref in ['Q3','Q4','Q5','Q6','J2','J3','J4','J5','J6','R100','C100','C101'] or (ref in ['D3','D4','D5','D6'] and net=='VM'));number=6 if ref=='J2' else 3 if high else 1;found=0
  land,drill=(.6,.3) if high else (.5,.25);width=.8 if high else .135
  for r in [.6,.8,1.,1.2,1.5,1.8,2.2,2.6]:
   for angle in range(0,360,15):
    vx,vy=round(x+r*math.cos(math.radians(angle)),4),round(y+r*math.sin(math.radians(angle)),4)
    if not(.8<vx<44.2 and 1.<vy<44.2):continue
    g=Point(vx,vy).buffer(land/2);h=Point(vx,vy).buffer(drill/2)
    if any(h.distance(q)<.28 for q in holes):continue
    if any(g.distance(q)<.1 for ls in smd.values() for q in ls):continue
    if not all(clear(g,l,net) for l in layers):continue
    line=LineString([(x,y),(vx,vy)]).buffer(width/2)
    if not clear(line,layer,net):continue
    via(vx,vy,net,land,drill);track((x,y),(vx,vy),layer,net,width);added.append({'ref':ref,'pad':pad.GetNumber(),'net':net,'via':[vx,vy],'width_mm':width});found+=1
    if found==number:break
   if found==number:break
  if found<number:failed.append({'ref':ref,'pad':pad.GetNumber(),'net':net,'required_vias':number,'added_vias':found})
# Ground stitching in free space, motor-plane supply through multiple drops above.
for x in np.arange(2,44,5):
 for y in np.arange(2,44,5):
  g=Point(x,y).buffer(.25);h=Point(x,y).buffer(.125)
  if any(h.distance(q)<.28 for q in holes) or any(g.distance(q)<.1 for ls in smd.values() for q in ls):continue
  if all(clear(g,l,'GND') for l in layers):via(float(x),float(y),'GND')
p.ZONE_FILLER(b).Fill(b.Zones());b.BuildConnectivity();p.SaveBoard(str(path),b)
(ROOT/'reports/Plane_Drops.json').write_text(json.dumps({'added':added,'incomplete':failed},indent=2));print('Plane drops',len(added),'incomplete',failed,flush=True)
# Reload actual project rules before DSN export.
b=p.LoadBoard(str(path))
for zone in list(b.Zones()):
 if zone.GetLayer() in [p.F_Cu,p.B_Cu,p.In2_Cu]:b.Remove(zone)
dsn=ROOT/'reports/RoveFlight_S3.dsn';assert p.ExportSpecctraDSN(b,str(dsn));s=dsn.read_text()
for name in ['In1.Cu','In4.Cu']:s=s.replace(f'(layer {name}\n      (type signal)',f'(layer {name}\n      (type power)')
s=s.replace('(clearance 200)','(clearance 150)').replace('(clearance 50 (type smd_smd))','(clearance 150 (type smd_smd))')
# Set class widths from project assignments and use the exported default via.
start=s.index('    (class kicad_default ');end=s.index('\n  (wiring',start);names=set(re.findall(r'\(net\s+([^\s()]+)',s[s.index('  (network'):start]));groups={'Default':[],'Power':[],'Motor':[],'Battery':[]};j=json.loads((ROOT/'RoveFlight_S3.kicad_pro').read_text());mapping={a['pattern']:a['netclass'] for a in j['net_settings']['netclass_patterns']}
for n in sorted(names):groups[mapping.get(n,'Default')].append(n)
viaid=re.search(r'\(via\s+([^\s()]+)',s).group(1);classes=''
for name,ns in groups.items():
 if ns:classes+='    (class '+name+' '+' '.join(ns)+'\n      (circuit (use_via '+viaid+'))\n      (rule (width '+str({'Default':160,'Power':500,'Motor':1000,'Battery':2000}[name])+') (clearance 150))\n    )\n'
s=s[:start]+classes+'  )'+s[end:]
# VM is implemented by its final zone, not by autorouter traces. Its fixed drops
# remain obstacles; final filled-board DRC verifies every resulting VM island.
start=s.index('    (net VM\n');depth=0;end=start
for i in range(start,len(s)):
 if s[i]=='(':depth+=1
 elif s[i]==')':
  depth-=1
  if depth==0:end=i+1;break
s=s[:start]+'    (net VM)'+s[end:];dsn.write_text(s);print('Prepared DSN',viaid)
