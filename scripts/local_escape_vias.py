"""Use 0.50/0.25mm routing vias outside solder pads for two enclosed escapes."""
from pathlib import Path
source=Path(__file__).with_name('stitch_planes.py').read_text().split('added=[];failed=[]')[0]
exec(compile(source,str(Path(__file__).with_name('stitch_planes.py')),'exec'))
b.BuildConnectivity();cn=b.GetConnectivity();results=[]
for ref,num in [('U7','6'),('U19','27')]:
 fp=next(f for f in b.GetFootprints() if f.GetReference()==ref);pad=next(q for q in fp.Pads() if q.GetNumber()==num);net=pad.GetNetname();objects=list(cn.GetConnectedItems(pad))+[pad];points=[]
 for obj in objects:
  if isinstance(obj,p.PAD):
   a=obj.GetPosition();points.append((p.ToMM(a.x),p.ToMM(a.y),p.F_Cu if obj.IsOnLayer(p.F_Cu) else p.B_Cu))
  elif isinstance(obj,p.PCB_TRACK) and not isinstance(obj,p.PCB_VIA):
   for a in [obj.GetStart(),obj.GetEnd()]:points.append((p.ToMM(a.x),p.ToMM(a.y),obj.GetLayer()))
 offsets=[(r*math.cos(i*math.pi/12),r*math.sin(i*math.pi/12)) for r in [0,.3,.5,.7,1.,1.3,1.6,2.] for i in range(24)]
 found=False
 for dx,dy in offsets:
  for x,y,layer in points:
   vx,vy=round(x+dx,4),round(y+dy,4);g=Point(vx,vy).buffer(.255);h=Point(vx,vy).buffer(.125)
   if not(.8<vx<79.2 and .8<vy<64.2):continue
   if any(h.distance(old)<.25 for old in holes):continue
   if '--allow-via-in-pad' not in __import__('sys').argv and any(g.distance(smd[l][idx])<.08 for l in layers for idx in smdtrees[l].query(g.buffer(.09))):continue
   if not all(clear(g,l,net) for l in layers):continue
   line=LineString([(x,y),(vx,vy)]).buffer(.075)
   if not clear(line,layer,net):continue
   v=p.PCB_VIA(b);v.SetPosition(p.VECTOR2I(p.FromMM(vx),p.FromMM(vy)));v.SetWidth(p.FromMM(.5));v.SetDrill(p.FromMM(.25));v.SetViaType(p.VIATYPE_THROUGH);v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetNet(b.FindNet(net));b.Add(v)
   if dx or dy:track((x,y),(vx,vy),layer,net,.135)
   for l in layers:extra[l].append((g,net))
   holes.append(h);results.append({'ref':ref,'pin':num,'via':[vx,vy],'stub':[x,y],'net':net});found=True;break
  if found:break
 if not found:results.append({'ref':ref,'pin':num,'failed':True})
for z in b.Zones():z.SetIslandRemovalMode(p.ISLAND_REMOVAL_MODE_ALWAYS)
p.ZONE_FILLER(b).Fill(b.Zones());b.BuildConnectivity();p.SaveBoard(str(ROOT/'RoveCore_One.kicad_pcb'),b)
(ROOT/'reports/Local_Escape_Vias.json').write_text(json.dumps(results,indent=2));print(results)
