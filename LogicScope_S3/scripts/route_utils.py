"""Exact copper geometry helpers for front-layer routing and ground-only vias."""
from cadlib import *
import pcbnew as p
import numpy as np
from shapely.geometry import Point,LineString,Polygon,box
from shapely.strtree import STRtree

b=p.LoadBoard(str(ROOT/'LogicScope_S3.kicad_pcb'))
layers=[p.F_Cu,p.B_Cu]
geoms={l:[] for l in layers};owners={l:[] for l in layers};smd={l:[] for l in layers};holes=[]
fps={f.GetReference():f for f in b.GetFootprints()}
for fp in b.GetFootprints():
    for pad in fp.Pads():
        for layer in layers:
            if not pad.IsOnLayer(layer):continue
            ps=pad.GetEffectivePolygon(layer)
            for oi in range(ps.OutlineCount()):
                ring=ps.COutline(oi)
                g=Polygon([(p.ToMM(ring.CPoint(i).x),p.ToMM(ring.CPoint(i).y)) for i in range(ring.PointCount())])
                if not g.is_valid:g=g.buffer(0)
                if g.is_empty:continue
                geoms[layer].append(g);owners[layer].append(pad.GetNetname() or '__MECHANICAL')
                if pad.GetAttribute()==p.PAD_ATTRIB_SMD:smd[layer].append(g)
        ds=pad.GetDrillSize()
        if ds.x:
            q=pad.GetPosition()
            holes.append(Point(p.ToMM(q.x),p.ToMM(q.y)).buffer(max(p.ToMM(ds.x),p.ToMM(ds.y))/2))
for tr in b.GetTracks():
    a,z=tr.GetStart(),tr.GetEnd();net=tr.GetNetname()
    if isinstance(tr,p.PCB_VIA):
        g=Point(p.ToMM(a.x),p.ToMM(a.y)).buffer(p.ToMM(tr.GetWidth(p.F_Cu))/2)
        for layer in layers:geoms[layer].append(g);owners[layer].append(net)
        holes.append(Point(p.ToMM(a.x),p.ToMM(a.y)).buffer(p.ToMM(tr.GetDrill())/2))
    else:
        g=LineString([(p.ToMM(a.x),p.ToMM(a.y)),(p.ToMM(z.x),p.ToMM(z.y))]).buffer(p.ToMM(tr.GetWidth())/2)
        geoms[tr.GetLayer()].append(g);owners[tr.GetLayer()].append(net)
for area in b.Zones():
    if not area.GetIsRuleArea() or not area.GetDoNotAllowTracks():continue
    if area.GetLayer()!=p.F_Cu:continue
    poly=area.Outline()
    for i in range(poly.OutlineCount()):
        ring=poly.COutline(i)
        shape=Polygon([(p.ToMM(ring.CPoint(j).x),p.ToMM(ring.CPoint(j).y)) for j in range(ring.PointCount())])
        geoms[p.F_Cu].append(shape);owners[p.F_Cu].append('__KEEP_OUT')
trees={layer:STRtree(geoms[layer]) for layer in layers}
smdtrees={layer:STRtree(smd[layer]) for layer in layers}
extra={layer:[] for layer in layers}
def pad(ref,num):return next(z for z in fps[ref].Pads() if z.GetNumber()==str(num))
def xy(obj):
    q=obj.GetPosition();return p.ToMM(q.x),p.ToMM(q.y)
def clear(g,layer,net,margin=.16):
    if not box(.3,.3,54.7,39.7).covers(g):return False
    for i in trees[layer].query(g.buffer(margin)):
        if owners[layer][i]!=net and g.distance(geoms[layer][i])<margin:return False
    return not any(on!=net and g.distance(other)<margin for other,on in extra[layer])
def track(a,z,net,width=.2,layer=p.F_Cu):
    if math.dist(a,z)<.000001:return None
    item=p.PCB_TRACK(b);item.SetStart(p.VECTOR2I(p.FromMM(float(a[0])),p.FromMM(float(a[1]))));item.SetEnd(p.VECTOR2I(p.FromMM(float(z[0])),p.FromMM(float(z[1]))))
    item.SetWidth(p.FromMM(width));item.SetLayer(layer);item.SetNet(b.FindNet(net));b.Add(item)
    extra[layer].append((LineString([a,z]).buffer(width/2),net))
    return item
def route(points,net,width=.2,check=True):
    g=LineString(points).buffer(width/2)
    if check:assert clear(g,p.F_Cu,net),(net,points,width)
    for a,z in zip(points,points[1:]):track(a,z,net,width)
def save():
    p.ZONE_FILLER(b).Fill(b.Zones());b.BuildConnectivity();p.SaveBoard(str(ROOT/'LogicScope_S3.kicad_pcb'),b)
