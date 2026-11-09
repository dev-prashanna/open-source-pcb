"""Clearance-tested local escape vias, recording every potential via-in-pad."""
from pathlib import Path
from cadlib import *
source=Path(__file__).with_name('power_drops.py').read_text().split('added=[];failed=[]')[0]
exec(compile(source,str(Path(__file__).with_name('power_drops.py')),'exec'))
import sys
report=json.loads((ROOT/'reports'/sys.argv[1]).read_text());items={z.m_Uuid.AsString():z for z in b.GetTracks()}
for fp in b.GetFootprints():
 for pad in fp.Pads():items[pad.m_Uuid.AsString()]=pad
added=[];failed=[];seen=set()
for entry in report['unconnected_items']:
 for desc in entry['items']:
  obj=items.get(desc['uuid'])
  if obj is None or isinstance(obj,p.PCB_VIA) or desc['uuid'] in seen:continue
  seen.add(desc['uuid']);net=obj.GetNetname()
  if isinstance(obj,p.PAD):
   if obj.GetAttribute()!=p.PAD_ATTRIB_SMD:continue
   pt=obj.GetPosition();ls=[l for l in [p.F_Cu,p.B_Cu] if obj.IsOnLayer(l)];label=obj.GetParentFootprint().GetReference()+'.'+obj.GetNumber()
  else:pt=obj.GetStart();ls=[obj.GetLayer()];label='track'
  x,y=p.ToMM(pt.x),p.ToMM(pt.y);high=net in ['VM','BAT_RAW','BAT_FUSED','BAT_PROTECTED'];land,drill=(.6,.3) if high else (.45,.2);width=.8 if high else .135;found=False
  for r in [0,.15,.25,.4,.6,.8,1.,1.3,1.6,2.]:
   for angle in range(0,360,15):
    vx,vy=round(x+r*math.cos(math.radians(angle)),4),round(y+r*math.sin(math.radians(angle)),4)
    if not(.7<vx<44.3 and .7<vy<44.3):continue
    g=Point(vx,vy).buffer(land/2);h=Point(vx,vy).buffer(drill/2)
    if any(h.distance(old)<.26 for old in holes):continue
    if not all(clear(g.buffer(.012),l,net) for l in layers):continue
    line=LineString([(x,y),(vx,vy)]).buffer(width/2) if r else Point(x,y).buffer(width/2)
    if not any(clear(line.buffer(.012),l,net) for l in ls):continue
    layer=next(l for l in ls if clear(line.buffer(.012),l,net))
    v=p.PCB_VIA(b);v.SetPosition(p.VECTOR2I(p.FromMM(vx),p.FromMM(vy)));v.SetWidth(p.FromMM(land));v.SetDrill(p.FromMM(drill));v.SetViaType(p.VIATYPE_THROUGH);v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetNet(b.FindNet(net));b.Add(v)
    if r:track((x,y),(vx,vy),layer,net,width)
    for l in layers:extra[l].append((g,net))
    holes.append(h);inpad=any(h.intersects(smd[l][idx]) for l in layers for idx in smdtrees[l].query(h))
    added.append({'source':label,'net':net,'via':[vx,vy],'land_mm':land,'drill_mm':drill,'via_in_pad':inpad});found=True;break
   if found:break
  if not found:failed.append({'source':label,'net':net,'xy':[x,y]})
p.ZONE_FILLER(b).Fill(b.Zones());b.BuildConnectivity();p.SaveBoard(str(ROOT/'RoveFlight_S3.kicad_pcb'),b)
(ROOT/'reports/Local_Escapes.json').write_text(json.dumps({'added':added,'failed':failed},indent=2));print('Local escapes',len(added),'added;',len(failed),'failed')
