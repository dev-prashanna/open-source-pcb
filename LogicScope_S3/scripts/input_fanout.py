from route_utils import *
def via_at(ref,num,where,path=None):
 q=pad(ref,num);net=q.GetNetname();g=Point(*where).buffer(.25);h=Point(*where).buffer(.125)
 path=path or [xy(q),where]
 if not all(clear(g,l,net) for l in layers):return False
 if any(g.distance(smd[l][i])<.06 for l in layers for i in smdtrees[l].query(g.buffer(.07))):return False
 if any(h.distance(old)<.26 for old in holes):return False
 if not clear(LineString(path).buffer(.075),p.F_Cu,net):return False
 route(path,net,.15);v=p.PCB_VIA(b);v.SetPosition(p.VECTOR2I(p.FromMM(where[0]),p.FromMM(where[1])));v.SetWidth(p.FromMM(.5));v.SetDrill(p.FromMM(.25));v.SetViaType(p.VIATYPE_THROUGH);v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetNet(b.FindNet(net));b.Add(v)
 for l in layers:extra[l].append((g,net))
 holes.append(h);print('Escape',ref,num,net,where,flush=True);return True
for num,y in [('1',9.7),('2',10.5),('4',11.5),('5',12.3)]:
 assert via_at('U5',num,(7.9,y)),('U5',num)
for ref,num in [('U2','19'),('U1','21')]:
 q=pad(ref,num);a=xy(q);done=False
 for r in [.9,1.,1.1,1.2,1.4,1.6,1.8,2.]:
  for ang in range(0,360,15):
   pos=(round(a[0]+r*math.cos(math.radians(ang)),4),round(a[1]+r*math.sin(math.radians(ang)),4))
   if via_at(ref,num,pos):done=True;break
  if done:break
 if not done:print('Needs escape',ref,num)
save()
