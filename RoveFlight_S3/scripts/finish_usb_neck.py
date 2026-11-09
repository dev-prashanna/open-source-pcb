"""Center the USB branch between CC2 copper and the connector locating hole."""
from cadlib import *
from pathlib import Path
exec(compile(Path(__file__).with_name('power_drops.py').read_text().split('added=[];failed=[]')[0], 'geometry', 'exec'))
for t in b.GetTracks():
    if isinstance(t,p.PCB_VIA):continue
    if t.GetNetname()=='USB_VBUS' and t.GetLayer()==p.In3_Cu:
        a,z=t.GetStart(),t.GetEnd()
        for endpoint in ('start','end'):
            q=a if endpoint=='start' else z
            if abs(p.ToMM(q.y)-27.3)<.00001 and p.ToMM(q.x) in (6.,8.5):
                q=p.VECTOR2I(q.x,p.FromMM(27.22))
                if endpoint=='start':t.SetStart(q)
                else:t.SetEnd(q)
        if {round(p.ToMM(t.GetStart().x),3),round(p.ToMM(t.GetEnd().x),3)}=={6.,8.5}:
            t.SetWidth(p.FromMM(.125))
    if t.GetNetname()=='VM' and t.GetLayer()==p.In3_Cu:
        a,z=t.GetStart(),t.GetEnd()
        line=LineString([(p.ToMM(a.x),p.ToMM(a.y)),(p.ToMM(z.x),p.ToMM(z.y))])
        distance=line.distance(Point(35.1893,18.0207))
        old_width=p.ToMM(t.GetWidth())
        width=2*(distance-.3-.16)
        if distance-.3-old_width/2<.15:
            assert width>=.45, 'VM neck would fall below the reviewed 0.45-mm limit'
            t.SetWidth(p.FromMM(width))
p.ZONE_FILLER(b).Fill(b.Zones())
p.SaveBoard(str(ROOT/'RoveFlight_S3.kicad_pcb'),b)
print('Centered USB locating-hole neck and restored margin at VM ground-via clearance')
