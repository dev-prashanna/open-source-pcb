from cadlib import *
import pcbnew as p
b=p.LoadBoard(str(ROOT/'LogicScope_S3.kicad_pcb'))
f=next(f for f in b.GetFootprints() if f.GetReference()=='R25');f.SetPosition(p.VECTOR2I(p.FromMM(14.5),p.FromMM(19.0)));p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(ROOT/'LogicScope_S3.kicad_pcb'),b)
d=json.loads((ROOT/'placement.json').read_text())
for c in d:
 if c['ref']=='R25':c['y']=19.;c['courtyard']=[13.3,18.3,15.7,19.7]
(ROOT/'placement.json').write_text(json.dumps(d,indent=2)+'\n')
