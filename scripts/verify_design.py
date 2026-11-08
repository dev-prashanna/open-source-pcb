"""Compare exported electrical connectivity to the design manifest and PCB."""
from cadlib import ROOT
import json, xml.etree.ElementTree as ET
parts=json.loads((ROOT/'design.json').read_text());root=ET.parse(ROOT/'reports/RoveCore_One.xml').getroot()
actual={};netnodes={}
for net in root.find('nets'):
 name=net.attrib['name'].lstrip('/')
 for n in net.findall('node'):
  key=(n.attrib['ref'],n.attrib['pin']);actual[key]=name;netnodes.setdefault(name,[]).append(key)
errors=[];expected={}
for c in parts:
 for pin,net in c['nets'].items():
  for num in pin.strip('[]').split(','):
   key=(c['ref'],num);expected[key]=net
   if actual.get(key)!=net:errors.append({'ref':c['ref'],'pin':num,'expected':net,'actual':actual.get(key)})
for key,net in actual.items():
 if key[0].startswith('#'):continue
 if key not in expected and not net.startswith('unconnected-'):errors.append({'unexpected_pin':key,'net':net})
checks={
 'all_manifest_pins_match_exported_schematic':not errors,
 'distinct_power_sources':len({actual.get(('D1','2')),actual.get(('D2','2')),actual.get(('D3','2'))})==3,
 'usb_dp':actual.get(('J2','A6'))==actual.get(('U2','3'))=='USB_DP',
 'usb_dm':actual.get(('J2','B7'))==actual.get(('U2','4'))=='USB_DM',
 'uart_tx_rx_crossed':actual.get(('U2','21'))==actual.get(('U1','34'))=='U0_RX' and actual.get(('U2','20'))==actual.get(('U1','35'))=='U0_TX',
 'boot_and_reset_independent':actual.get(('U1','3'))=='EN' and actual.get(('U1','25'))=='BOOT',
 'servo_power_not_logic':actual.get(('J12','2'))=='SERVO5' and actual.get(('U19','28'))=='+3V3',
 'motor_power_not_logic':actual.get(('U7','12'))=='VM',
 'encoder_inputs_only':{actual.get(('U1',v)) for v in ['4','5','6','7']}=={'ENC_LA','ENC_LB','ENC_RA','ENC_RB'},
 'five_volt_echo_buffered':actual.get(('J9','3'))=='US_ECHO_RAW' and actual.get(('U1','16'))=='US_ECHO',
 'four_motor_inputs_unique':len({actual.get(('U7',v)) for v in ['9','10','15','16']})==4,
 'i2c_addresses_unique':len(set([0x10,0x1c,0x20,0x29,0x40,0x48,0x6a,0x76]))==8,
 'auto_reset_truth_table':actual.get(('Q1','2'))=='RTS' and actual.get(('Q2','2'))=='DTR',
}
boardpath=ROOT/'RoveCore_One.kicad_pcb'
pcb_errors=[]
if boardpath.exists():
 import pcbnew as p
 b=p.LoadBoard(str(boardpath));bparts={f.GetReference():f for f in b.GetFootprints()}
 for (ref,pin),net in expected.items():
  if ref not in bparts:pcb_errors.append({'missing_ref':ref});continue
  pads=[pad for pad in bparts[ref].Pads() if pad.GetNumber()==pin]
  if not pads:pcb_errors.append({'missing_pad':[ref,pin]})
  for pad in pads:
   if pad.GetNetname().lstrip('/')!=net:pcb_errors.append({'pcb_pin':[ref,pin],'expected':net,'actual':pad.GetNetname()})
 checks['schematic_to_pcb_pad_nets_match']=not pcb_errors
report={'checks':checks,'electrical_parts':len(parts),'physical_connected_pins':len(expected),'net_count':len(netnodes),'connectivity_errors':errors,'pcb_errors':pcb_errors,'all_passed':all(checks.values())}
(ROOT/'reports/Connectivity_Audit.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if not report['all_passed']:raise SystemExit(1)
