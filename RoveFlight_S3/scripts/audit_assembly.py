"""Identify via drills intersecting SMD solder apertures for fabrication review."""
from cadlib import *
import pcbnew as p
from shapely.geometry import Point,Polygon

board=p.LoadBoard(str(ROOT/'RoveFlight_S3.kicad_pcb'))
pads=[]
for fp in board.GetFootprints():
    for pad in fp.Pads():
        if pad.GetAttribute()!=p.PAD_ATTRIB_SMD:continue
        for layer in (p.F_Cu,p.B_Cu):
            if not pad.IsOnLayer(layer):continue
            ps=pad.GetEffectivePolygon(layer)
            for i in range(ps.OutlineCount()):
                ring=ps.COutline(i)
                shape=Polygon([(p.ToMM(ring.CPoint(j).x),p.ToMM(ring.CPoint(j).y)) for j in range(ring.PointCount())])
                pads.append((shape,fp.GetReference(),pad.GetNumber(),board.GetLayerName(layer)))
findings=[]
for via in board.GetTracks():
    if not isinstance(via,p.PCB_VIA):continue
    q=via.GetPosition();x,y=p.ToMM(q.x),p.ToMM(q.y)
    hole=Point(x,y).buffer(p.ToMM(via.GetDrill())/2)
    touched=[{'reference':ref,'pad':pin,'layer':layer} for shape,ref,pin,layer in pads if hole.intersects(shape)]
    if touched:findings.append({'x_mm':x,'y_mm':y,'drill_mm':p.ToMM(via.GetDrill()),'net':via.GetNetname(),'apertures':touched})
report={'via_drills_intersecting_smd_pads':findings,'count':len(findings),
        'required_process':'Resin fill and copper cap intersecting vias; assembler must review stencil and thermal-pad vias. Tenting alone is insufficient.',
        'scope':'Board vias versus nominal SMD copper lands; mask expansion and footprint-integrated thermal drill pads require additional CAM review.'}
(ROOT/'reports/Assembly_Audit.json').write_text(json.dumps(report,indent=2)+'\n')
print('Assembly audit:',len(findings),'via drills intersect SMD lands; fill/cap required')
