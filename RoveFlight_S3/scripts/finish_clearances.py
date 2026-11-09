"""Repair measured residual clearances without changing design-rule limits."""
from cadlib import *
from pathlib import Path
exec(compile(Path(__file__).with_name('power_drops.py').read_text().split('added=[];failed=[]')[0], 'geometry', 'exec'))

items = {track.m_Uuid.AsString(): track for track in b.GetTracks()}
for item in b.GetTracks():
    if not isinstance(item,p.PCB_VIA) and item.GetNetname()=='LED_A':
        item.SetWidth(p.FromMM(.125))
changes = {
    'cbcb1011-f5b1-467c-80a4-795457baab72': .125,
    '1240bcd5-a9c7-409f-9794-991c50d6ebc0': .52,
}
for key, width in changes.items():
    if key in items:
        items[key].SetWidth(p.FromMM(width))
key = '4d99d2fc-3656-4113-83ef-f5c8a2c9f938'
if key in items:
    old = items[key]
    points = [(33.775, 18.525), (33.70, 18.45),
              (33.70, 18.10), (33.775, 18.025)]
    shape = LineString(points).buffer(.125 / 2)
    assert clear(shape.buffer(.005), p.In2_Cu, 'DEBUG_RX')
    for a, z in zip(points, points[1:]):
        track(a, z, p.In2_Cu, 'DEBUG_RX', .125)
    b.Remove(old)
p.ZONE_FILLER(b).Fill(b.Zones())
p.SaveBoard(str(ROOT / 'RoveFlight_S3.kicad_pcb'), b)
print('Repaired DEBUG_RX dogleg and two local width transitions')
