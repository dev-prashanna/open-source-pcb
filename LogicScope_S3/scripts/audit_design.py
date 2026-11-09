"""Independent manifest/XML/PCB pin checks and ground-return geometry audit."""
from route_utils import *
import xml.etree.ElementTree as ET
from collections import defaultdict
from shapely.ops import unary_union
parts=json.loads((ROOT/'design.json').read_text());manifest={(c['ref'],pin):net for c in parts for pin,net in c['nets'].items()};xml=ET.parse(ROOT/'reports/LogicScope_S3.xml').getroot();actual={}
for net in xml.find('nets'):
 for q in net.findall('node'):actual[(q.attrib['ref'],q.attrib['pin'])]=net.attrib['name'].lstrip('/')
errors=[]
for (ref,num),net in manifest.items():
 pads=[q for q in fps[ref].Pads() if q.GetNumber()==num]
 if not pads:errors.append([ref,num,'missing pad'])
 for q in pads:
  if net is None:
   if q.GetNetname() and not q.GetNetname().startswith('unconnected-'):errors.append([ref,num,'unexpected connected NC',q.GetNetname()])
  elif actual.get((ref,num))!=net or q.GetNetname()!=net:errors.append([ref,num,net,actual.get((ref,num)),q.GetNetname()])
for key,net in actual.items():
 if not key[0].startswith('#') and key not in manifest and not net.startswith('unconnected-'):errors.append(['unexpected pin',key,net])
def nn(ref,num):return actual.get((ref,str(num)))
checks={
 'manifest_schematic_and_pcb_match':not errors,
 'eight_parallel_bits':all(nn('U1',4+i)==nn('U2',18-i)==f'D{i}' for i in range(8)),
 'input_protection_each_channel':all(nn('R'+str(10+i),1)==f'CH{i}' and nn('R'+str(10+i),2)==nn('U2',2+i)==f'IN{i}' for i in range(8)),
 'pulldowns_each_input':all(nn('R'+str(20+i),1)==f'IN{i}' and nn('R'+str(20+i),2)=='GND' for i in range(8)),
 'buffer_direction_and_supply':nn('U2',1)==nn('U2',20)=='+3V3' and nn('U2',10)=='GND' and nn('U2',19)=='BUF_OE_N',
 'usb_native_gpio19_20':nn('U1',13)=='USB_DM' and nn('U1',14)=='USB_DP',
 'usb_dual_data_pads':nn('J3','A6')==nn('J3','B6')=='USB_DP_CONN' and nn('J3','A7')==nn('J3','B7')=='USB_DM_CONN',
 'usb_cc_separate':nn('J3','A5')==nn('R30',1)=='USB_CC1' and nn('J3','B5')==nn('R31',1)=='USB_CC2' and nn('R30',2)==nn('R31',2)=='GND',
 'buck_pin_map':all(nn('U3',pin)==net for pin,net in [(1,'+3V3'),(2,'VUSB'),(3,'VUSB'),(4,'GND'),(5,'SW'),(6,'BST')]),
 'hardware_clock_loopback':nn('U1',20)==nn('R4',1)=='SAMPLE_CLK' and nn('R4',2)==nn('U1',19)=='CAM_PCLK',
 'no_external_5V_direct_to_mcu':not any(q.GetNetname() in {'USB_5V','VUSB'} or q.GetNetname().startswith('CH') for q in fps['U1'].Pads()),
 'two_copper_layers':b.GetCopperLayerCount()==2,
 'optional_esd_dnp':all(bool(fps[ref].GetAttributes()&p.FP_DNP) for ref in ['U5','U6']),
 'etched_and_silk_tiwari':all(any(isinstance(q,p.PCB_TEXT) and q.GetText()=='TIWARI' and q.GetLayer()==layer for q in b.GetDrawings()) for layer in [p.F_Cu,p.F_SilkS]),
}
for ref,nets in [('J1',['CH0','GND','CH1','GND','CH2','GND','CH3','GND','CH4','GND']),('J2',['CH5','GND','CH6','GND','CH7','GND','VREF_3V3','GND',None,None])]:
 checks[ref+'_pinout']=all(nn(ref,i+1)==net if net else nn(ref,i+1).startswith('unconnected-') for i,net in enumerate(nets))
connectivity={'checks':checks,'errors':errors,'electrical_parts':len(parts),'all_passed':all(checks.values())}
(ROOT/'reports/Connectivity_Audit.json').write_text(json.dumps(connectivity,indent=2)+'\n')

def filled(z):
 ps=z.GetFilledPolysList(z.GetLayer())
 def ring(r):return [(p.ToMM(r.CPoint(k).x),p.ToMM(r.CPoint(k).y)) for k in range(r.PointCount())]
 return [Polygon(ring(ps.COutline(i)),[ring(ps.CHole(i,j)) for j in range(ps.HoleCount(i))]).buffer(0) for i in range(ps.OutlineCount())]
rear_zones=[z for z in b.Zones() if not z.GetIsRuleArea() and z.GetLayer()==p.B_Cu and z.GetNetname()=='GND']
rear_polys=[g for z in rear_zones for g in filled(z)];rear=unary_union(rear_polys)
netstats=defaultdict(lambda:{'length_mm':0.,'rear_length_mm':0.,'vias':0,'widths_mm':set(),'layers':set()});critical_errors=[];plane_gaps=[];via_pad=[]
for tr in b.GetTracks():
 net=tr.GetNetname();e=netstats[net]
 if isinstance(tr,p.PCB_VIA):
  e['vias']+=1;hole=Point(*xy(tr)).buffer(p.ToMM(tr.GetDrill())/2)
  if any(hole.intersects(g) for l in layers for g in smd[l]):via_pad.append({'net':net,'xy':xy(tr)})
  continue
 a,z=tr.GetStart(),tr.GetEnd();path=LineString([(p.ToMM(a.x),p.ToMM(a.y)),(p.ToMM(z.x),p.ToMM(z.y))]);length=p.ToMM(tr.GetLength());e['length_mm']+=length;e['widths_mm'].add(round(p.ToMM(tr.GetWidth()),4));e['layers'].add(b.GetLayerName(tr.GetLayer()))
 if tr.GetLayer()==p.B_Cu:e['rear_length_mm']+=length
 if net in {f'D{i}' for i in range(8)} or net.startswith('USB_D'):
  if tr.GetLayer()!=p.F_Cu:critical_errors.append(net)
  if not rear.buffer(.01).covers(path):plane_gaps.append({'net':net,'length_missing_mm':path.difference(rear.buffer(.01)).length})
for e in netstats.values():
 for key in ['length_mm','rear_length_mm']:e[key]=round(e[key],4)
 for key in ['layers','widths_mm']:e[key]=sorted(e[key])
critical_vias={n:e['vias'] for n,e in netstats.items() if (n.startswith('USB_D') or n in {f'D{i}' for i in range(8)}) and e['vias']}
antenna=[]
for fp in b.GetFootprints():
 for zone in fp.Zones():
  if not zone.GetIsRuleArea():continue
  ps=zone.Outline()
  for i in range(ps.OutlineCount()):
   r=ps.COutline(i);g=Polygon([(p.ToMM(r.CPoint(k).x),p.ToMM(r.CPoint(k).y)) for k in range(r.PointCount())])
   for l in layers:
    if any(g.intersection(s).area>1e-5 for s,n in zip(geoms[l],owners[l]) if n!='__KEEP_OUT'):antenna.append('copper overlap')
   if g.intersection(rear).area>1e-5:antenna.append('rear fill overlap')
physical={'copper_layers':b.GetCopperLayerCount(),'board_mm':[55,40],'nominal_thickness_mm':p.ToMM(b.GetDesignSettings().GetBoardThickness()),'footprints':len(fps),'rear_ground_polygons':len(rear_polys),'rear_ground_area_mm2':round(rear.area,3),'rear_coverage_of_2200mm2_percent':round(100*rear.area/2200,2),'critical_routes_on_wrong_layer':critical_errors,'critical_vias':critical_vias,'critical_centerline_reference_gaps':plane_gaps,'antenna_copper_errors':antenna,'board_via_drills_in_smd_lands':via_pad,'nets':dict(netstats),'performance_validation':'UNMEASURED; finite capture target 1 MS/s, no released continuous rate'}
physical['all_passed']=len(rear_polys)==1 and not any([critical_errors,critical_vias,plane_gaps,antenna,via_pad])
(ROOT/'reports/Physical_Audit.json').write_text(json.dumps(physical,indent=2)+'\n')
with (ROOT/'Placement.csv').open('w') as f:
 w=csv.writer(f);w.writerow(['Reference','Value','X_mm','Y_mm','Rotation_deg','Side','DNP'])
 for ref,fp in sorted(fps.items()):w.writerow([ref,fp.GetValue(),*xy(fp),fp.GetOrientationDegrees(),'F' if fp.GetLayer()==p.F_Cu else 'B','YES' if fp.GetAttributes()&p.FP_DNP else 'NO'])
print('Connectivity checks',checks,'errors',errors)
print('Physical audit:',{k:v for k,v in physical.items() if k!='nets'})
if not connectivity['all_passed'] or not physical['all_passed']:raise SystemExit(1)
