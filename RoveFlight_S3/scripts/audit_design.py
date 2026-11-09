"""Independent netlist/board comparison and physical implementation audit."""
from cadlib import *
import pcbnew as p
import xml.etree.ElementTree as ET
from collections import defaultdict,Counter
parts=json.loads((ROOT/'design.json').read_text());manifest={(c['ref'],pin):net for c in parts for pin,net in c['nets'].items()};xml=ET.parse(ROOT/'reports/RoveFlight_S3.xml').getroot();actual={}
for net in xml.find('nets'):
 for pin in net.findall('node'):actual[(pin.attrib['ref'],pin.attrib['pin'])]=net.attrib['name'].lstrip('/')
b=p.LoadBoard(str(ROOT/'RoveFlight_S3.kicad_pcb'));fps={f.GetReference():f for f in b.GetFootprints()};errors=[]
for key,net in manifest.items():
 if actual.get(key)!=net:errors.append({'pin':key,'expected':net,'schematic':actual.get(key)})
 pads=[z for z in fps[key[0]].Pads() if z.GetNumber()==key[1]]
 if not pads:errors.append({'missing_pad':key})
 for pad in pads:
  if pad.GetNetname()!=net:errors.append({'pin':key,'expected':net,'pcb':pad.GetNetname()})
for key,net in actual.items():
 if not key[0].startswith('#') and key not in manifest and not net.startswith('unconnected-'):errors.append({'unexpected':key,'net':net})
def nn(ref,pin):return actual.get((ref,str(pin)))
checks={
 'all_manifest_and_board_pad_nets_match':not errors,
 'usb_native_gpio19_20':nn('U1',13)=='USB_DM' and nn('U1',14)=='USB_DP',
 'adc1_monitoring':nn('U1',39)=='CURRENT_ADC' and nn('U1',38)=='BAT_ADC',
 'four_pwm_unique':{nn('U1',i) for i in [4,5,6,7]}=={'PWM_M1','PWM_M2','PWM_M3','PWM_M4'},
 'four_low_side_stages':all(nn('Q'+str(i+2),2)=='GND' and nn('Q'+str(i+2),3)==f'M{i}_NEG' and nn('J'+str(i+2),1)=='VM' and nn('J'+str(i+2),2)==f'M{i}_NEG' for i in range(1,5)),
 'flyback_polarities':all(nn('D'+str(i+2),1)=='VM' and nn('D'+str(i+2),2)==f'M{i}_NEG' for i in range(1,5)),
 'latched_clear_faults':all(nn(ref,pin)=='SAFE_CLR_N' for ref,pin in [('U4',7),('U5',1),('U6',6),('Q2',3),('SW3',1)]),
 'physical_arm_disconnect':nn('JP1',1)=='ARMED_N' and nn('JP1',2)=='MOTOR_OE_N',
 'all_driver_enables_gated':all(nn('U7',i)=='MOTOR_OE_N' for i in [1,4,10,13]),
 'imu_spi':all(nn('U8',pin)==net for pin,net in [(1,'SPI_MISO'),(4,'IMU_INT'),(12,'IMU_CS'),(13,'SPI_SCK'),(14,'SPI_MOSI')]),
 'baro_spi_independent_cs':nn('U9',6)=='BARO_CS' and nn('U9',5)=='SPI_MISO',
 'battery_usb_diode_isolation':nn('D1',1)==nn('D2',1)=='SYS_IN' and nn('D1',2)=='VM' and nn('D2',2)=='USB_VBUS',
 'reverse_pfet_orientation':nn('Q1',5)=='BAT_FUSED' and nn('Q1',1)=='BAT_PROTECTED' and nn('Q1',4)=='GND',
 'shunt_kelvin_nets':nn('U12',3)==nn('R100',1)=='BAT_PROTECTED' and nn('U12',4)==nn('R100',2)=='VM',
 'receiver_uart_separate':nn('U1',34)=='RC_RX' and nn('U1',35)=='RC_TX' and nn('U1',36)=='DEBUG_RX' and nn('U1',37)=='DEBUG_TX',
}
report={'checks':checks,'electrical_entries':len(parts),'connected_pins':len(manifest),'nets':len({v for v in actual.values() if not v.startswith('unconnected-')}),'errors':errors,'all_passed':all(checks.values())};(ROOT/'reports/Connectivity_Audit.json').write_text(json.dumps(report,indent=2))
nets=defaultdict(lambda:{'length_mm':0.,'minimum_width_mm':99.,'widths_mm':Counter(),'layers':set(),'vias':0});inner=[];rf=[]
for tr in b.GetTracks():
 n=tr.GetNetname();e=nets[n]
 if isinstance(tr,p.PCB_VIA):e['vias']+=1;continue
 w=p.ToMM(tr.GetWidth());length=p.ToMM(tr.GetLength());e['length_mm']+=length;e['minimum_width_mm']=min(e['minimum_width_mm'],w);e['widths_mm'][str(round(w,4))]+=length;e['layers'].add(b.GetLayerName(tr.GetLayer()))
 if tr.GetLayer() in [p.In1_Cu,p.In4_Cu]:inner.append(n)
 for q in [tr.GetStart(),tr.GetEnd()]:
  if p.ToMM(q.y)<-.75:rf.append(n)
for n,e in nets.items():e['length_mm']=round(e['length_mm'],3);e['layers']=sorted(e['layers']);e['widths_mm']={k:round(v,3) for k,v in e['widths_mm'].items()}
with (ROOT/'Placement.csv').open('w') as f:
 w=csv.writer(f);w.writerow(['Reference','Value','X_mm','Y_mm','Rotation_deg','Side'])
 for fp in b.GetFootprints():
  q=fp.GetPosition();w.writerow([fp.GetReference(),fp.GetValue(),p.ToMM(q.x),p.ToMM(q.y),fp.GetOrientationDegrees(),'F' if fp.GetLayer()==p.F_Cu else 'B'])
dec=[]
for c in parts:
 if c['name']!='C' or c['parent'] not in fps:continue
 fp=fps[c['ref']];par=fps[c['parent']];cp=next((z for z in fp.Pads() if z.GetNumber()=='1'),None);pp=[z for z in par.Pads() if z.GetNetname()==c['nets'].get('1')]
 if cp is not None and pp:
  q=cp.GetPosition();dist=min(math.hypot(p.ToMM(q.x-z.GetPosition().x),p.ToMM(q.y-z.GetPosition().y)) for z in pp);dec.append({'ref':c['ref'],'parent':c['parent'],'rail':c['nets']['1'],'distance_mm':round(dist,3),'same_side':fp.GetLayer()==par.GetLayer()})
audit={'board_mm':[45,45],'copper_layers':6,'footprints':len(fps),'ground_plane_signal_tracks':inner,'rf_keepout_track_errors':rf,'nets':dict(nets),'decoupling':dec,'thermal_validation':'CALCULATED ONLY; measurements required','flight_validation':'NOT FLIGHT READY'};(ROOT/'reports/Physical_Audit.json').write_text(json.dumps(audit,indent=2));print(json.dumps(report,indent=2));print('Ground-plane signal tracks',len(inner),'RF violations',len(rf))
if not report['all_passed']:raise SystemExit(1)
