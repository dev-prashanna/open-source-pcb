from pathlib import Path
import json,re
root=Path(__file__).resolve().parents[1];p=root/'reports/RoveCore_One.dsn';s=p.read_text()
s=s.replace('(layer In1.Cu\n      (type signal)','(layer In1.Cu\n      (type power)')
s=s.replace('    (boundary\n','    (plane GND (polygon In1.Cu 0  500 -500 79500 -500 79500 -64500 500 -64500))\n    (boundary\n')
# Prevent ground-layer signal routing. In2 remains available for power and signals.
start=s.index('    (class kicad_default ');end=s.index('\n  (wiring',start)
header=s[:start];footer=s[end:]
nets=re.findall(r'\(net\s+([^\s()]+)',s[s.index('  (network'):start])
netset=set(nets);groups={'Default':[],'LogicPower':[],'Motor':[],'Servo':[],'Battery':[]}
j=json.loads((root/'RoveCore_One.kicad_pro').read_text());mapping={a['pattern']:a['netclass'] for a in j['net_settings']['netclass_patterns']}
for n in sorted(netset):groups[mapping.get(n,'Default')].append(n)
widths={'Default':180,'LogicPower':650,'Motor':800,'Servo':1200,'Battery':1200}
classes=''
for name,ns in groups.items():
 if not ns:continue
 classes+='    (class '+name+' '+' '.join(ns)+'\n      (circuit (use_via "Via[0-3]_600:300_um"))\n      (rule (width '+str(widths[name])+') (clearance 150))\n    )\n'
s=header+classes+'  )'+footer
# The general rule must agree with the minimum component land spacing.
s=s.replace('(clearance 200)','(clearance 150)').replace('(clearance 50 (type smd_smd))','(clearance 150 (type smd_smd))')
p.write_text(s)
print('Routing prepared: 3 routing layers + reserved In1 ground; class widths',widths)
