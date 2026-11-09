"""Import an assisted routing session and refill the actual KiCad copper."""
from cadlib import *
import pcbnew as p,sys
path=ROOT/'RoveFlight_S3.kicad_pcb';b=p.LoadBoard(str(path));session=ROOT/'reports'/sys.argv[1]
import shutil
shutil.copy2(path,ROOT/'reports/placement_before_route.kicad_pcb')
assert p.ImportSpecctraSES(b,str(session))
p.ZONE_FILLER(b).Fill(b.Zones());b.BuildConnectivity();p.SaveBoard(str(path),b)
print('Imported',session.name,'tracks',len(list(b.GetTracks())))
