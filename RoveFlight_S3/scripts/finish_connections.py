"""Finish the reviewed USB branch and search longer, pad-safe plane escapes."""
from cadlib import *
from pathlib import Path
exec(compile(Path(__file__).with_name('power_drops.py').read_text().split('added=[];failed=[]')[0], 'geometry', 'exec'))

log = []
points = [(8.4086,22.6535), (8.4086,25.3), (6.,25.3),
          (6.,27.3), (8.5,27.3), (9.2,27.5), (11.6028,27.3005)]
for a,z in zip(points,points[1:]):
    width = next(w for w in [.5,.4,.3,.25,.2,.18]
                 if clear(LineString([a,z]).buffer(w/2+.005),p.In3_Cu,'USB_VBUS'))
    track(a,z,p.In3_Cu,'USB_VBUS',width)
    log.append({'net':'USB_VBUS','points':[a,z],'width_mm':width})

fps = {fp.GetReference():fp for fp in b.GetFootprints()}
for ref,pin,width in [('R130','2',.125), ('U3','3',.25), ('C123','2',.135)]:
    pad = next(z for z in fps[ref].Pads() if z.GetNumber()==pin)
    net = pad.GetNetname()
    q=pad.GetPosition();x,y=p.ToMM(q.x),p.ToMM(q.y)
    layer = p.F_Cu if pad.IsOnLayer(p.F_Cu) else p.B_Cu
    found=False
    for radius in np.arange(.5,8.01,.1):
        for angle in range(0,360,5):
            vx=round(x+float(radius)*math.cos(math.radians(angle)),4)
            vy=round(y+float(radius)*math.sin(math.radians(angle)),4)
            if not(.7<vx<44.3 and .7<vy<44.3):continue
            g=Point(vx,vy).buffer(.225);h=Point(vx,vy).buffer(.1)
            if any(h.distance(old)<.26 for old in holes):continue
            if any(g.distance(smd[l][idx])<.08 for l in layers
                   for idx in smdtrees[l].query(g.buffer(.09))):continue
            if not all(clear(g.buffer(.005),l,net) for l in layers):continue
            line=LineString([(x,y),(vx,vy)]).buffer(width/2+.005)
            if not clear(line,layer,net):continue
            v=p.PCB_VIA(b);v.SetPosition(p.VECTOR2I(p.FromMM(vx),p.FromMM(vy)))
            v.SetWidth(p.FromMM(.45));v.SetDrill(p.FromMM(.2))
            v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetViaType(p.VIATYPE_THROUGH)
            v.SetNet(b.FindNet(net));b.Add(v)
            for l in layers:extra[l].append((g,net))
            holes.append(h)
            track((x,y),(vx,vy),layer,net,width)
            log.append({'ref':ref,'pin':pin,'net':net,'via':[vx,vy],
                        'width_mm':width,'via_in_pad':False})
            print('Escaped',ref,pin,net,vx,vy,flush=True)
            found=True;break
        if found:break
    if not found:print('No straight escape',ref,pin,flush=True)
p.ZONE_FILLER(b).Fill(b.Zones())
p.SaveBoard(str(ROOT/'RoveFlight_S3.kicad_pcb'),b)
(ROOT/'reports/Final_Connections.json').write_text(json.dumps(log,indent=2))
