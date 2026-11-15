"""Prune only copper that KiCad reports as unused dangling branches."""
from pathlib import Path
import json,sys,sexpdata as sx
ROOT=Path(__file__).resolve().parents[1];f=ROOT/'hardware/TIWARI.kicad_pcb'
def node(a,k):return next((x for x in a if isinstance(x,list)and x and str(x[0])==k),None)
s=sx.loads(f.read_text());j=json.loads((ROOT/'reports'/sys.argv[1]).read_text())
bad={i['uuid']for v in j['violations']if v['type']in['track_dangling','via_dangling']for i in v['items']}
s=[a for a in s if not(isinstance(a,list)and a and str(a[0])in['segment','arc','via']and node(a,'uuid')and str(node(a,'uuid')[1])in bad)];f.write_text(sx.dumps(s)+'\n');print('Pruned',len(bad),'unused branches')
