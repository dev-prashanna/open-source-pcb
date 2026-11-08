"""Import a Specctra session and fill actual KiCad ground copper."""
from cadlib import *
import pcbnew as p
import sys
boardpath=ROOT/'RoveCore_One.kicad_pcb';b=p.LoadBoard(str(boardpath))
session=ROOT/'reports'/sys.argv[1]
assert session.exists(),session
ok=p.ImportSpecctraSES(b,str(session));assert ok,'Specctra session import failed'
net=b.FindNet('GND');assert net
for layer in [p.In1_Cu,p.F_Cu,p.B_Cu]:
 z=p.ZONE(b);z.SetLayer(layer);z.SetNet(net);z.SetLocalClearance(p.FromMM(.18));z.SetThermalReliefGap(p.FromMM(.2));z.SetThermalReliefSpokeWidth(p.FromMM(.3));z.SetMinThickness(p.FromMM(.15));z.SetPadConnection(p.ZONE_CONNECTION_FULL if layer==p.In1_Cu else p.ZONE_CONNECTION_THERMAL)
 outline=z.Outline();outline.NewOutline()
 for x,y in [(.5,.5),(79.5,.5),(79.5,64.5),(.5,64.5)]:outline.Append(p.FromMM(x),p.FromMM(y))
 b.Add(z)
p.ZONE_FILLER(b).Fill(b.Zones());b.BuildConnectivity();p.SaveBoard(str(boardpath),b)
print('Imported',session.name,'tracks',len(list(b.GetTracks())),'zones',len(list(b.Zones())))
