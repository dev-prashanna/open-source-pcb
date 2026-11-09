"""Route the native Full-Speed USB pair before other signals.

Main pair: 0.75-mm width, 0.17-mm gap over the rear reference plane.
Short necks at connector, ESD and 0402 damping resistors are explicit.
Impedance is a stack-dependent target requiring fabricator verification.
"""
from route_utils import *

assert not list(b.GetTracks()), 'USB initialization must precede other routing'
records=[]
def add(points,net,width):
    route(points,net,width)
    records.append({'net':net,'width_mm':width,'points':points})
# Reversible Type-C pin pairs: one tie below the contact row, one above it.
add([xy(pad('J3','A6')),(25.75,34.2),(26.75,34.2),xy(pad('J3','B6'))],'USB_DP_CONN',.15)
add([xy(pad('J3','B7')),(25.25,32.4),(26.25,32.4),xy(pad('J3','A7'))],'USB_DM_CONN',.15)
# Connector to the two independent ESD shunts, maintaining channel ordering.
dp=xy(pad('U4','2'));dm=xy(pad('U4','1'))
add([xy(pad('J3','B6')),(26.75,32.0),(dp[0],32.0-(26.75-dp[0])),dp],'USB_DP_CONN',.2)
add([xy(pad('J3','B7')),(25.25,32.0),(24.,30.75),(dm[0],30.75),dm],'USB_DM_CONN',.2)
# Narrow ESD breakouts clear its centre ground pin; widen above the device.
add([dm,(dm[0],26.9),(22.5,26.7)],'USB_DM_CONN',.2)
add([dp,(dp[0],26.9),(23.42,26.7)],'USB_DP_CONN',.2)
# The two principal lines are a coupled pair, with matched 45-degree bends.
add([(22.5,26.7),(22.5,17.48),(24.0,15.98)],'USB_DM_CONN',.75)
add([(23.42,26.7),(23.42,17.86),(24.02,17.26)],'USB_DP_CONN',.75)
add([(24.0,15.98),xy(pad('R33','1'))],'USB_DM_CONN',.2)
add([(24.02,17.26),xy(pad('R32','1'))],'USB_DP_CONN',.2)
# Module-side breakouts have no vias or off-route test stubs.
add([xy(pad('R33','2')),xy(pad('TP7','1')),xy(pad('U1','13'))],'USB_DM',.25)
add([xy(pad('R32','2')),xy(pad('TP6','1')),xy(pad('U1','14'))],'USB_DP',.25)
save()
(ROOT/'reports/USB_Routing.json').write_text(json.dumps({'records':records,'trunk_width_mm':.75,'trunk_gap_mm':.17,'reference':'B.Cu GND','routing_vias':0,'impedance':'90 ohm target; fabricator field-solver signoff pending'},indent=2)+'\n')
print('USB pair routed with explicit coupling, Type-C ties and zero routing vias')
