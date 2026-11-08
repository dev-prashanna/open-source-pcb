"""Set design constraints after a pcbnew process has finished saving its project."""
from pathlib import Path
import json
root=Path(__file__).resolve().parents[1];path=root/'RoveCore_One.kicad_pro';j=json.loads(path.read_text())
r=j['board']['design_settings']['rules']
r.update(min_clearance=.15,min_track_width=.125,min_via_diameter=.4,min_through_hole_diameter=.2,min_copper_edge_clearance=.25,min_text_height=.6,min_text_thickness=.1,min_silk_clearance=.1)
n=j['net_settings'];n['classes']=[]
classes={'Default':(.15,.18,.6,.3),'LogicPower':(.15,.65,.7,.3),'Motor':(.15,.8,.8,.4),'Servo':(.15,1.2,.9,.4),'Battery':(.15,1.2,.9,.4)}
for name,(cl,tw,vd,dr) in classes.items():n['classes'].append(dict(name=name,clearance=cl,track_width=tw,via_diameter=vd,via_drill=dr,microvia_diameter=.3,microvia_drill=.1,diff_pair_width=.18,diff_pair_gap=.18,diff_pair_via_gap=.2,wire_width=6,bus_width=12,line_style=0,pcb_color='rgba(0, 0, 0, 0.000)',schematic_color='rgba(0, 0, 0, 0.000)'))
assign={}
for c in json.loads((root/'design.json').read_text()):
 for name in c['nets'].values():
  if name in ['VM','MOTOR_RAW','MOTOR_FUSED','MOTOR_A_P','MOTOR_A_N','MOTOR_B_P','MOTOR_B_N','ISENSE_A','ISENSE_B']:assign[name]='Motor'
  elif name in ['SERVO_BUCK','SERVO5','SERVO_EXT','SERVO_EXT_RAW','SERVO_SELECTED','SW_SERVO']:assign[name]='Servo'
  elif name in ['BAT_RAW','BAT_FUSED','VBAT']:assign[name]='Battery'
  elif name in ['+3V3','+3V3_SENS','BAT5','LOGIC5','SW_3V3','SW_BAT','USB_VBUS','EXT5_RAW','EXT5_FUSED','USB_FUSED']:assign[name]='LogicPower'
n['netclass_assignments']={};n['netclass_patterns']=[{'pattern':k,'netclass':v} for k,v in sorted(assign.items())]
path.write_text(json.dumps(j,indent=2))
print('Project constraints set: 0.15mm min copper clearance / 0.20mm thermal drills / 0.25mm edge')
