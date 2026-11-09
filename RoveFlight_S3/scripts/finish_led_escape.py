"""Escape R130 inside the reviewed 0.39-mm corridor above its LED pad."""
from cadlib import *
from pathlib import Path
exec(compile(Path(__file__).with_name('power_drops.py').read_text().split('added=[];failed=[]')[0], 'geometry', 'exec'))
x,y=19.,31.1
g=Point(x,y).buffer(.225);h=Point(x,y).buffer(.1)
assert all(clear(g.buffer(.005),layer,'LED_A') for layer in layers)
assert all(h.distance(old) >= .26 for old in holes)
assert not any(h.intersects(smd[layer][i]) for layer in layers
               for i in smdtrees[layer].query(h))
assert clear(LineString([(19.,31.49),(x,y)]).buffer(.0675),p.F_Cu,'LED_A')
v=p.PCB_VIA(b);v.SetPosition(p.VECTOR2I(p.FromMM(x),p.FromMM(y)))
v.SetWidth(p.FromMM(.45));v.SetDrill(p.FromMM(.2))
v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetViaType(p.VIATYPE_THROUGH)
v.SetNet(b.FindNet('LED_A'));b.Add(v)
track((19.,31.49),(x,y),p.F_Cu,'LED_A',.125)
p.ZONE_FILLER(b).Fill(b.Zones())
p.SaveBoard(str(ROOT/'RoveFlight_S3.kicad_pcb'),b)
print('R130 LED escape added; drill remains outside the solder aperture')
