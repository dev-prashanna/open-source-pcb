"""Expose B0..2 at local solder pads; J19 supplies B3..7 and extra grounds."""
from cadlib import *
import pcbnew as p
import xml.etree.ElementTree as ET
import os,sys
path=ROOT/'RoveCore_One.kicad_pcb'
if '--add' not in sys.argv:
 b=p.LoadBoard(str(path));b.BuildConnectivity();fps={f.GetReference():f for f in b.GetFootprints()};keep={};remove=set()
 for i in range(3):
  pad=next(z for z in fps['U21'].Pads() if z.GetNumber()==str(i+1));keep[i]={str(z.m_Uuid.AsString()) for z in b.GetConnectivity().GetConnectedItems(pad)}
  for z in b.GetTracks():
   if z.GetNetname()==f'EXP_B{i}' and str(z.m_Uuid.AsString()) not in keep[i]:remove.add(str(z.m_Uuid.AsString()))
 doc=sx.loads(path.read_text());doc=[n for n in doc if not(isinstance(n,list) and n and str(n[0]) in ['segment','via'] and atom(n,'uuid') in remove)];path.write_text(sx.dumps(doc))
 print('Removed',len(remove),'obsolete remote expansion tracks',flush=True)
 os.execv(sys.executable,[sys.executable,__file__,'--add'])
print('Loading board',flush=True);b=p.LoadBoard(str(path));print('Loaded board',flush=True);fps={f.GetReference():f for f in b.GetFootprints()}
for pad in fps['J19'].Pads():
 if pad.GetNumber() in ['3','4','5']:pad.SetNet(b.FindNet('GND'))
meta={c['ref']:c for c in json.loads((ROOT/'design.json').read_text())};xml=ET.parse(ROOT/'reports/RoveCore_One.xml').getroot();comps={c.attrib['ref']:c for c in xml.find('components')}
for ref in ['TP1','TP2','TP3']:
 print('Adding',ref,flush=True);c=meta[ref];fp=p.FootprintLoad(str(ROOT/'libraries/RoveCore.pretty'),'ServicePad_0.5mm');b.Add(fp);fp.SetReference(ref);fp.SetValue(c['value']);fp.SetFPID(p.LIB_ID('RoveCore','ServicePad_0.5mm'));fp.Flip(fp.GetPosition(),False);fp.SetPosition(p.VECTOR2I(p.FromMM(c['xy'][0]),p.FromMM(c['xy'][1])))
 print('Loaded footprint',ref,flush=True);comp=comps[ref];fp.SetPath(p.KIID_PATH(comp.find('sheetpath').attrib['tstamps']+comp.find('tstamps').text.split()[0]))
 for pad in fp.Pads():pad.SetNet(b.FindNet(c['nets']['1']))
 for name in ['MPN','Manufacturer']:
  f=p.PCB_FIELD(fp,p.FIELD_T_USER,name);f.SetText(c['mpn'] if name=='MPN' else c['mfr']);f.SetVisible(False);fp.Add(f)
 print('Set fields',ref,flush=True);fp.GetField(p.FIELD_T_REFERENCE).SetVisible(False);print('Added',ref,flush=True)
p.ZONE_FILLER(b).Fill(b.Zones());b.BuildConnectivity();p.SaveBoard(str(path),b);print('Added three local service pads')
