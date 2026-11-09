"""Order-preserving short front-layer routes for all eight acquisition bits."""
from route_utils import *

records=[]
for bit,mpin in enumerate([4,5,6,7,8,9,10,11]):
    a=xy(pad('U2',18-bit));z=xy(pad('U1',mpin));x=24.2
    delta=z[1]-a[1]
    points=[a,(x,a[1]),(x+abs(delta),z[1]),z]
    points=[q for i,q in enumerate(points) if i==0 or q!=points[i-1]]
    route(points,f'D{bit}',.2)
    records.append({'net':f'D{bit}','points':points,'width_mm':.2})
save()
(ROOT/'reports/Acquisition_Bus_Routing.json').write_text(json.dumps(records,indent=2)+'\n')
print('Routed all eight acquisition bits on the front, in order, with no vias')
