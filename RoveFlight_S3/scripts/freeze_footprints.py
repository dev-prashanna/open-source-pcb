"""Name and vendor local silkscreen variants instead of hiding library warnings.

Uses the current reports/DRC.json to identify footprint copies changed by
silkscreen.py. Copper, pad numbering, courtyards and models are preserved.
"""
from cadlib import *
import pcbnew as p
from collections import defaultdict

board=p.LoadBoard(str(ROOT/'RoveFlight_S3.kicad_pcb'))
fps={fp.GetReference():fp for fp in board.GetFootprints()}
report=json.loads((ROOT/'reports/DRC.json').read_text())
mapping={}
for issue in report['violations']:
    if issue['type']!='lib_footprint_mismatch':continue
    ref=issue['items'][0]['description'].removeprefix('Footprint ')
    fp=fps[ref]
    old=fp.GetFPIDAsString()
    name=old.split(':')[1]+'_RF_'+ref
    new='RoveFlight:'+name
    fp.SetFPID(p.LIB_ID('RoveFlight',name))
    clone=p.Cast_to_FOOTPRINT(fp.Duplicate(False))
    if clone.GetLayer()==p.B_Cu:clone.Flip(clone.GetPosition(),False)
    clone.SetPosition(p.VECTOR2I(0,0));clone.SetOrientationDegrees(0)
    clone.SetReference('REF**');clone.SetValue(name)
    for pad in clone.Pads():pad.SetNetCode(0)
    p.FootprintSave(str(ROOT/'libraries/RoveFlight.pretty'),clone)
    assert (ROOT/'libraries/RoveFlight.pretty'/(name+'.kicad_mod')).is_file()
    mapping[ref]={'source':old,'footprint':new,'change':'Silkscreen moved to Fab where covered by exposed pads; copper unchanged'}
p.SaveBoard(str(ROOT/'RoveFlight_S3.kicad_pcb'),board)

for file in ROOT.glob('*.kicad_sch'):
    doc=sx.loads(file.read_text())
    # Keep the upstream cached symbol definition equal to its source library.
    for symbol in nodes(node(doc,'lib_symbols',[]),'symbol'):
        if str(symbol[1])=='RF_Module:ESP32-S3-WROOM-1':
            for field in nodes(symbol,'property'):
                if field[1]=='Footprint':field[2]='RF_Module:ESP32-S3-WROOM-1'
    for symbol in nodes(doc,'symbol'):
        fields={field[1]:field for field in nodes(symbol,'property')}
        ref=fields['Reference'][2]
        if ref in mapping:fields['Footprint'][2]=mapping[ref]['footprint']
    file.write_text(sx.dumps(doc))
parts=json.loads((ROOT/'design.json').read_text())
for part in parts:
    if part['ref'] in mapping:part['fp']=mapping[part['ref']]['footprint']
(ROOT/'design.json').write_text(json.dumps(parts,indent=2)+'\n')
(ROOT/'libraries/Footprint_Variants.json').write_text(json.dumps(mapping,indent=2)+'\n')
with (ROOT/'BOM.csv').open(newline='') as file:
    reader=csv.DictReader(file);fields=reader.fieldnames;rows=list(reader)
for row in rows:
    if row['Reference'] in mapping:row['Footprint']=mapping[row['Reference']]['footprint']
with (ROOT/'BOM.csv').open('w',newline='') as file:
    writer=csv.DictWriter(file,fieldnames=fields);writer.writeheader();writer.writerows(rows)
groups=defaultdict(list)
for part in parts:groups[(part['mpn'],part['value'],part['fp'],part['mfr'])].append(part['ref'])
with (ROOT/'BOM_Grouped.csv').open('w',newline='') as file:
    writer=csv.writer(file);writer.writerow(['Quantity','References','Value','MPN','Manufacturer','Footprint'])
    for (mpn,value,fp,mfr),refs in groups.items():writer.writerow([len(refs),','.join(refs),value,mpn,mfr,fp])
print('Vendored',len(mapping),'explicit footprint variants and synchronized schematic/BOM')
