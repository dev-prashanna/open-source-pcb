"""Short buck loops and front-to-rear ground drops outside solder apertures."""
from route_utils import *

log=[]
def link(points,net,width):
    route(points,net,width);log.append({'net':net,'width_mm':width,'points':points})
link([xy(pad('U3','2')),xy(pad('U3','3'))],'VUSB',.5)
link([xy(pad('U3','5')),(45.1,31.0),(46.1,32.0),xy(pad('L1','1'))],'SW',.6)
link([xy(pad('C8','1')),xy(pad('U3','6'))],'BST',.2)
link([xy(pad('C8','2')),(43.1,28.775),(43.1,31.0),xy(pad('U3','5'))],'SW',.2)

def ground_via(vx,vy,start,width):
    g=Point(vx,vy).buffer(.3);hole=Point(vx,vy).buffer(.15)
    if any(hole.distance(old)<.26 for old in holes):return False
    if any(g.distance(smd[l][i])<.06 for l in layers for i in smdtrees[l].query(g.buffer(.07))):return False
    if not all(clear(g,l,'GND') for l in layers):return False
    if not clear(LineString([start,(vx,vy)]).buffer(width/2),p.F_Cu,'GND'):return False
    via=p.PCB_VIA(b);via.SetPosition(p.VECTOR2I(p.FromMM(vx),p.FromMM(vy)))
    via.SetWidth(p.FromMM(.6));via.SetDrill(p.FromMM(.3));via.SetViaType(p.VIATYPE_THROUGH)
    via.SetLayerPair(p.F_Cu,p.B_Cu);via.SetNet(b.FindNet('GND'));b.Add(via)
    for l in layers:extra[l].append((g,'GND'))
    holes.append(hole);track(start,(vx,vy),'GND',width)
    return True

# ESD ground takes the short route to the reference plane, between signal pins.
assert ground_via(22.96,29.05,xy(pad('U4','3')),.3)
log.append({'ref':'U4','pad':'3','via':[22.96,29.05],'width_mm':.3})
targets=[('U1','1'),('U1','40'),('U2','10'),('U3','4')]
targets += [(ref,z.GetNumber()) for ref in ['C1','C2','C4','C5','C6','C7','C9','C10'] for z in fps[ref].Pads() if z.GetNetname()=='GND']
for ref,num in targets:
    start=xy(pad(ref,num));done=False;width=.4 if ref in ('U3','C6','C9','C10') else .25
    for radius in [.7,.8,1.,1.2,1.5,1.8,2.,2.5]:
        for angle in range(0,360,15):
            vx=round(start[0]+radius*math.cos(math.radians(angle)),4)
            vy=round(start[1]+radius*math.sin(math.radians(angle)),4)
            if ground_via(vx,vy,start,width):
                log.append({'ref':ref,'pad':num,'via':[vx,vy],'width_mm':width});done=True;break
        if done:break
    if not done:print('Ground drop needs later review',ref,num,flush=True)
save()
(ROOT/'reports/Ground_and_Power.json').write_text(json.dumps(log,indent=2)+'\n')
print('Added short buck loops and',sum('via' in q for q in log),'ground drops; rear layer has no signal tracks')
