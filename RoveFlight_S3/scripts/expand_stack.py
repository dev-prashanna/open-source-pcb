"""Six-layer revision: add signal space while retaining two ground references."""
from cadlib import *
import pcbnew as p
path=ROOT/'RoveFlight_S3.kicad_pcb';b=p.LoadBoard(str(path));b.SetCopperLayerCount(6)
z=p.ZONE(b);z.SetLayer(p.In4_Cu);z.SetNet(b.FindNet('GND'));z.SetLocalClearance(p.FromMM(.18));z.SetMinThickness(p.FromMM(.15));z.SetPadConnection(p.ZONE_CONNECTION_FULL);z.SetIslandRemovalMode(p.ISLAND_REMOVAL_MODE_ALWAYS);poly=z.Outline();poly.NewOutline()
for x,y in [(.5,.5),(44.5,.5),(44.5,44.5),(.5,44.5)]:poly.Append(p.FromMM(x),p.FromMM(y))
b.Add(z);tb=b.GetTitleBlock();tb.SetComment(0,'45x45mm | 6 layers | 25.5mm M2 mounting');b.SetTitleBlock(tb)
p.ZONE_FILLER(b).Fill(b.Zones());b.BuildConnectivity();p.SaveBoard(str(path),b);print('Six layers: F, GND, mixed power/signals, signals, GND, B')
