"""Explicit staggered QFN fanout prevents adjacent vias trapping 0.5mm pins.
Run on the routed development copy before the final routing pass.
"""
from pathlib import Path
import json
import pcbnew as p
import sexpdata as sx
ROOT=Path(__file__).resolve().parents[1];path=ROOT/'hardware/TIWARI.kicad_pcb'
b=p.LoadBoard(str(path));fps={f.GetReference():f for f in b.GetFootprints()}
moves={'C28':(31,17,0),'C29':(35,15.8,0),'C26':(34.5,21.3,0),
 'C27':(31,20.5,0),'C30':(31,9.5,0),'C31':(35,10.5,0),'C24':(36,18.5,90),
 'R10':(35.5,12.5,0),'R11':(26.5,20.5,0),'R12':(26.5,23,0)}
for ref,(x,y,angle)in moves.items():
 fp=fps[ref]
 if fp.GetLayer()!=p.B_Cu:fp.Flip(fp.GetPosition(),False)
 fp.SetPosition(p.VECTOR2I(p.FromMM(x),p.FromMM(y)));fp.SetOrientationDegrees(angle)
p.SaveBoard(str(path),b)
def node(a,k):return next((v for v in a if isinstance(v,list)and v and str(v[0])==k),None)
s=sx.loads(path.read_text());filtered=[];removed=0
for item in s:
 if not isinstance(item,list)or not item:filtered.append(item);continue
 kind=str(item[0]);drop=False
 if kind in ['segment','arc','via']:
  at=node(item,'at');a=node(item,'start');z=node(item,'end')
  if kind=='via':
   x,y=map(float,at[1:3]);drop=26.0<x<41.0 and 11.0<y<26.0
   if any(abs(x-u)<.01 and abs(y-v)<.01 for u,v in[(33,17),(35,17),(33,19),(35,19)]):drop=False
  elif a and z:
   x0,y0=map(float,a[1:3]);x1,y1=map(float,z[1:3]);drop=max(x0,x1)>26 and min(x0,x1)<41 and max(y0,y1)>11 and min(y0,y1)<26
 if kind=='segment' and node(item,'layer') and str(node(item,'layer')[1])=='In1.Cu':drop=True
 if drop:removed+=1
 else:filtered.append(item)
path.write_text(sx.dumps(filtered)+'\n');b=p.LoadBoard(str(path));cpu=next(f for f in b.GetFootprints()if f.GetReference()=='U1');added=0
for pad in cpu.Pads():
 num=pad.GetNumber()
 if not num or num=='49' or not pad.GetNetname()or pad.GetNetname().startswith('unconnected'):continue
 n=int(num);x,y=p.ToMM(pad.GetPosition().x),p.ToMM(pad.GetPosition().y)
 if n<=12:vx,vy=(29.0 if n%2 else 28.4),y
 elif n<=24:vx,vy=x,(22.75 if n%2 else 23.35)
 elif n<=36:vx,vy=(38.75 if n%2 else 39.35),y
 else:vx,vy=x,(13.0 if n%2 else 12.4)
 tr=p.PCB_TRACK(b);tr.SetStart(pad.GetPosition());tr.SetEnd(p.VECTOR2I(p.FromMM(vx),p.FromMM(vy)));tr.SetWidth(p.FromMM(.15));tr.SetLayer(p.F_Cu);tr.SetNet(pad.GetNet());b.Add(tr)
 via=p.PCB_VIA(b);via.SetPosition(tr.GetEnd());via.SetWidth(p.FromMM(.5));via.SetDrill(p.FromMM(.25));via.SetViaType(p.VIATYPE_THROUGH);via.SetLayerPair(p.F_Cu,p.B_Cu);via.SetNet(pad.GetNet());b.Add(via);added+=1
p.SaveBoard(str(path),b)
# Reload avoids stale connectivity objects after the bulk edit.
b=p.LoadBoard(str(path));p.ZONE_FILLER(b).Fill(b.Zones());b.BuildConnectivity();p.SaveBoard(str(path),b)
manifest=json.loads((ROOT/'hardware/design.json').read_text())
for part in manifest:
 if part['ref']in moves:
  x,y,angle=moves[part['ref']];part.update(xy=[x,y],rot=angle,side='B')
(ROOT/'hardware/design.json').write_text(json.dumps(manifest,indent=2))
print('Replaced',removed,'ring copper items with',added,'staggered CPU fanouts')
