from cadlib import *
import pcbnew as p
from collections import defaultdict,Counter
b=p.LoadBoard(str(ROOT/'RoveCore_One.kicad_pcb'));parts=json.loads((ROOT/'design.json').read_text());meta={c['ref']:c for c in parts};fpmap={f.GetReference():f for f in b.GetFootprints()}
nets=defaultdict(lambda:{'track_length_mm':0,'minimum_width_mm':99,'widths_mm':Counter(),'vias':0,'layers':set(),'segments':0})
rf=[];innerground=[]
for tr in b.GetTracks():
 n=tr.GetNetname();entry=nets[n]
 if isinstance(tr,p.PCB_VIA):entry['vias']+=1;continue
 w=p.ToMM(tr.GetWidth());length=p.ToMM(tr.GetLength());entry['track_length_mm']+=length;entry['minimum_width_mm']=min(entry['minimum_width_mm'],w);entry['widths_mm'][str(round(w,4))]+=length;entry['layers'].add(b.GetLayerName(tr.GetLayer()));entry['segments']+=1
 if tr.GetLayer()==p.In1_Cu and n!='GND':innerground.append(n)
 for pt in [tr.GetStart(),tr.GetEnd()]:
  if -2<=p.ToMM(pt.x)<=46 and p.ToMM(pt.y)<-.56:rf.append({'net':n,'x':p.ToMM(pt.x),'y':p.ToMM(pt.y)})
for n,e in nets.items():e['track_length_mm']=round(e['track_length_mm'],3);e['widths_mm']={k:round(v,3) for k,v in e['widths_mm'].items()};e['layers']=sorted(e['layers'])
decouplers=[]
for c in parts:
 if c['name']!='C' or c['parent'] not in fpmap or c['ref'] not in fpmap:continue
 cap=fpmap[c['ref']];par=fpmap[c['parent']];supply=c['nets'].get('1');cp=next((pa for pa in cap.Pads() if pa.GetNumber()=='1'),None)
 if cp is None:continue
 pp=[pad for pad in par.Pads() if pad.GetNetname()==supply]
 if pp:
  pos=cp.GetPosition();dist=min(math.hypot(p.ToMM(pos.x-pad.GetPosition().x),p.ToMM(pos.y-pad.GetPosition().y)) for pad in pp)
  decouplers.append({'capacitor':c['ref'],'parent':c['parent'],'value':c['value'],'rail':supply,'pad_distance_mm':round(dist,3),'same_side':cap.GetLayer()==par.GetLayer()})
placement=[]
with (ROOT/'Placement.csv').open('w') as f:
 w=csv.writer(f);w.writerow(['Reference','Value','X_mm','Y_mm','Rotation_deg','Side'])
 for fp in b.GetFootprints():
  pt=fp.GetPosition();row=[fp.GetReference(),fp.GetValue(),p.ToMM(pt.x),p.ToMM(pt.y),fp.GetOrientationDegrees(),'F' if fp.GetLayer()==p.F_Cu else 'B'];w.writerow(row);placement.append(row)
audit={'board_mm':[80,65],'copper_layers':4,'electrical_components':len(parts),'footprints':len(fpmap),'vias':sum(e['vias'] for e in nets.values()),'nets':dict(nets),'rf_keepout_track_violations':rf,'non_ground_tracks_on_In1':innerground,'decoupling_pad_distances':decouplers,'placement':placement,'thermal_validation':'NOT MEASURED','certification':'ENGINEERING PROTOTYPE; not a fabrication release'}
(ROOT/'reports/Physical_Audit.json').write_text(json.dumps(audit,indent=2))
print('Physical audit saved; RF violations',len(rf),'In1 signal traces',len(innerground),'vias',audit['vias'])
