"""Remove copper involved in actual rule violations before targeted rerouting."""
from pathlib import Path
import json,sys
import sexpdata as sx
ROOT=Path(__file__).resolve().parents[1];path=ROOT/'hardware/TIWARI.kicad_pcb'
j=json.loads((ROOT/'reports'/sys.argv[1]).read_text());bad=set()
for v in j['violations']:
 if v['type']in['shorting_items','clearance','hole_clearance','solder_mask_bridge']:
  bad.update(i['uuid']for i in v['items'])
def node(a,k):return next((x for x in a if isinstance(x,list)and x and str(x[0])==k),None)
s=sx.loads(path.read_text());out=[];removed=0
for item in s:
 if isinstance(item,list)and item and str(item[0])in['segment','arc','via']:
  uuid=node(item,'uuid');net=node(item,'net')
  if uuid and str(uuid[1])in bad:removed+=1;continue
  if '--usb' in sys.argv and net and str(net[1])in['USB_DP','USB_DM']:removed+=1;continue
 out.append(item)
path.write_text(sx.dumps(out)+'\n');print('Removed',removed,'copper items')
