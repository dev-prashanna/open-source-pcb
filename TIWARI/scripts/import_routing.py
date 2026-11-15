"""Import a routed Specctra session and refill reference planes."""
from pathlib import Path
import sys
import pcbnew as p
ROOT=Path(__file__).resolve().parents[1]
path=ROOT/'hardware/TIWARI.kicad_pcb';b=p.LoadBoard(str(path))
assert p.ImportSpecctraSES(b,str(ROOT/'reports'/sys.argv[1]))
p.ZONE_FILLER(b).Fill(b.Zones());b.BuildConnectivity();p.SaveBoard(str(path),b)
print('Imported',sys.argv[1],len(list(b.GetTracks())),'copper items')
