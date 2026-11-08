"""Short ground drops; record every deliberate via-in-pad for filled/capped fab."""
from pathlib import Path
source=Path(__file__).with_name('stitch_planes.py').read_text().split('added=[];failed=[]')[0]
exec(compile(source,str(Path(__file__).with_name('stitch_planes.py')),'exec'))
from shapely.geometry import box
failed_islands=json.loads((ROOT/'reports/Ground_Islands.json').read_text())['not_stitched'];added=[];failed=[];seen=set()
for island in failed_islands:
 poly=box(*island['bbox']);candidates=[(fp,pad) for fp in b.GetFootprints() for pad in fp.Pads() if pad.GetNetname()=='GND' and pad.IsOnLayer(island['layer']) and poly.buffer(.05).covers(Point(p.ToMM(pad.GetPosition().x),p.ToMM(pad.GetPosition().y)))]
 if not candidates:continue
 found=False
 for fp,pad in candidates:
  key=(fp.GetReference(),pad.GetNumber())
  if key in seen:found=True;break
  a=pad.GetPosition();x,y=p.ToMM(a.x),p.ToMM(a.y);layer=island['layer']
  for land,dr in [(.5,.25),(.4,.2)]:
   offsets=[(r*math.cos(i*math.pi/12),r*math.sin(i*math.pi/12)) for r in [0,.2,.4,.6,.8,1.,1.3,1.6,2.] for i in range(24)]
   for dx,dy in offsets:
    vx,vy=round(x+dx,4),round(y+dy,4);g=Point(vx,vy).buffer(land/2+.005);h=Point(vx,vy).buffer(dr/2)
    if not(.8<vx<79.2 and .8<vy<64.2):continue
    if any(h.distance(old)<.25 for old in holes):continue
    if not all(clear(g,l,'GND') for l in layers):continue
    if not clear(LineString([(x,y),(vx,vy)]).buffer(.075),layer,'GND'):continue
    v=p.PCB_VIA(b);v.SetPosition(p.VECTOR2I(p.FromMM(vx),p.FromMM(vy)));v.SetWidth(p.FromMM(land));v.SetDrill(p.FromMM(dr));v.SetViaType(p.VIATYPE_THROUGH);v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetNet(b.FindNet('GND'));b.Add(v)
    if dx or dy:track((x,y),(vx,vy),layer,'GND',.135)
    for l in layers:extra[l].append((g,'GND'))
    holes.append(h);inpad=any(g.intersects(smd[l][idx]) for l in layers for idx in smdtrees[l].query(g))
    added.append({'ref':fp.GetReference(),'pad':pad.GetNumber(),'via':[vx,vy],'land_mm':land,'drill_mm':dr,'via_in_pad':inpad});seen.add(key);found=True;break
   if found:break
  if found:break
 if not found:failed.append(island)
for z in b.Zones():z.SetIslandRemovalMode(p.ISLAND_REMOVAL_MODE_ALWAYS)
p.ZONE_FILLER(b).Fill(b.Zones());b.BuildConnectivity();p.SaveBoard(str(ROOT/'RoveCore_One.kicad_pcb'),b)
(ROOT/'reports/Ground_Drops.json').write_text(json.dumps({'added':added,'failed':failed},indent=2));print('Ground drops:',len(added),'added;',len(failed),'failed')
