from route_utils import *
report=json.loads((ROOT/'reports/Ground_Stitching.json').read_text())
targets=[]
for entry in report['needs_review']:
 region=box(*entry['bounds'])
 for fp in b.GetFootprints():
  for q in fp.Pads():
   if fp.GetReference()=='R25' and q.GetNetname()=='GND' and region.contains(Point(*xy(q))):targets.append((fp.GetReference(),q))
for ref,q in targets:
 a=xy(q);done=False
 for land,drill in [(.45,.2)]:
  for r in np.arange(.5,3.01,.1):
   for ang in range(0,360,5):
    v=(round(a[0]+r*math.cos(math.radians(ang)),5),round(a[1]+r*math.sin(math.radians(ang)),5));g=Point(*v).buffer(land/2);h=Point(*v).buffer(drill/2)
    if not all(clear(g,l,'GND') for l in layers):continue
    if not clear(LineString([a,v]).buffer(.075),p.F_Cu,'GND'):continue
    if any(h.distance(old)<.26 for old in holes):continue
    if any(g.distance(smd[l][i])<.06 for l in layers for i in smdtrees[l].query(g.buffer(.07))):continue
    track(a,v,'GND',.15);via=p.PCB_VIA(b);via.SetPosition(p.VECTOR2I(p.FromMM(float(v[0])),p.FromMM(float(v[1]))));via.SetWidth(p.FromMM(land));via.SetDrill(p.FromMM(drill));via.SetViaType(p.VIATYPE_THROUGH);via.SetLayerPair(p.F_Cu,p.B_Cu);via.SetNet(b.FindNet('GND'));b.Add(via)
    for l in layers:extra[l].append((g,'GND'))
    holes.append(h);print(ref,q.GetNumber(),'ground via',v,flush=True);done=True;break
   if done:break
  if done:break
 if not done:print('Unresolved',ref,q.GetNumber(),a,flush=True)
save()
