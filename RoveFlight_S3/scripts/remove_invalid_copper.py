"""Remove measured offending imported copper for subsequent rerouting."""
from cadlib import *
import sys
path=ROOT/'RoveFlight_S3.kicad_pcb';doc=sx.loads(path.read_text());report=json.loads((ROOT/'reports'/sys.argv[1]).read_text());remove=set()
for v in report['violations']:
 if v['severity']!='error' or v['type']=='courtyards_overlap':continue
 for item in v['items']:
  if item['description'].startswith(('Track ','Via ')):remove.add(item['uuid'])
doc=[z for z in doc if not(isinstance(z,list) and z and str(z[0]) in ['segment','via'] and atom(z,'uuid') in remove)]
path.write_text(sx.dumps(doc));print('Removed',len(remove),'offending copper items for rerouting')
