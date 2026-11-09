import sys
sys.argv=['route_bypasses.py','DRC_bypasses1.json','--small-vias']
exec(open('scripts/route_bypasses.py').read().split("report=json.loads")[0])
r=json.load(open('reports/DRC_bypasses1.json'));b.BuildConnectivity()
for entry in r['unconnected_items']:
 es=entry['items'];o=objects.get(es[0]['uuid'])
 if o is None or o.GetNetname()=='GND':continue
 net=o.GetNetname();aa,sa=options(es[0]);zz,sz=options(es[1]);pairs=sorted(((a,z) for a in aa for z in zz),key=lambda q:math.dist(q[0][:2],q[1][:2]))[:1]
 for a,z in pairs:
  pts=search(a,z,net,.15)
  print(net,'from',a,'to',z,'points',pts,flush=True)
  if not pts:continue
  print('Validation',validate(pts,net,.15),flush=True)
  for x,y in zip(pts,pts[1:]):
   if x[2]!=y[2]:
    g=Point(y[0],y[1]).buffer(LAND/2)
    print('VIA',y,[clear(g,l,net) for l in layers],g.intersects(protected))
   else:
    g=LineString([x[:2],y[:2]]).buffer(.075)
    if not clear(g,layers[x[2]],net):
     print('BAD',x,y,[(owners[layers[x[2]]][i],g.distance(geoms[layers[x[2]]][i])) for i in trees[layers[x[2]]].query(g.buffer(.17)) if owners[layers[x[2]]][i]!=net])
