"""Validate current native hardware and export an engineering fabrication pack."""
from pathlib import Path
import subprocess,json,sys,hashlib,csv,shutil
ROOT=Path(__file__).resolve().parents[1];NAME='LogicScope_S3'
def run(*args):subprocess.run(args,cwd=ROOT,check=True)
for folder in ['reports','fabrication/gerbers','fabrication/assembly','previews']:(ROOT/folder).mkdir(parents=True,exist_ok=True)
run('kicad-cli','sch','erc','--format','json','--output','reports/ERC.json',NAME+'.kicad_sch')
run('kicad-cli','pcb','drc','--refill-zones','--save-board','--schematic-parity','--format','json','--output','reports/DRC.json',NAME+'.kicad_pcb')
e=json.loads((ROOT/'reports/ERC.json').read_text());d=json.loads((ROOT/'reports/DRC.json').read_text())
if any(s['violations'] for s in e.get('sheets',[])) or any(d.get(k) for k in ['violations','unconnected_items','schematic_parity']):raise SystemExit('Export blocked: review ERC/DRC reports')
run('kicad-cli','sch','export','netlist','--format','kicadxml','--output','reports/'+NAME+'.xml',NAME+'.kicad_sch')
run(sys.executable,'scripts/audit_design.py')
# Preserve the raw MCP all-layer output as execution evidence, outside the fab upload.
raw=ROOT/'reports/MCP_Gerber_All_Layers'
if not raw.exists() and any((ROOT/'fabrication/gerbers').iterdir()):shutil.copytree(ROOT/'fabrication/gerbers',raw)
for f in (ROOT/'fabrication/gerbers').iterdir():
 if f.is_file():f.unlink()
run('kicad-cli','pcb','export','gerbers','--output','fabrication/gerbers/','--layers','F.Cu,B.Cu,F.Mask,B.Mask,F.Silkscreen,B.Silkscreen,Edge.Cuts',NAME+'.kicad_pcb')
run('kicad-cli','pcb','export','drill','--excellon-separate-th','--generate-map','--map-format','pdf','--generate-report','--report-path','fabrication/Drill_Report.txt','--output','fabrication/gerbers/',NAME+'.kicad_pcb')
run('kicad-cli','pcb','export','pos','--format','csv','--units','mm','--exclude-dnp','--output','fabrication/assembly/Placement.csv',NAME+'.kicad_pcb')
run('kicad-cli','sch','export','pdf','--output','fabrication/Schematic.pdf',NAME+'.kicad_sch')
run('kicad-cli','pcb','export','pdf','--layers','F.Fab,Edge.Cuts','--crossout-DNP-footprints-on-fab-layers','--output','fabrication/assembly/Assembly.pdf',NAME+'.kicad_pcb')
# Paste-only native variant excludes the two DNP arrays from the baseline stencil.
import pcbnew as p
board=p.LoadBoard(str(ROOT/(NAME+'.kicad_pcb')))
for fp in board.GetFootprints():
 if fp.GetAttributes()&p.FP_DNP:
  for q in fp.Pads():
   ls=q.GetLayerSet();ls.RemoveLayer(p.F_Paste);ls.RemoveLayer(p.B_Paste);q.SetLayerSet(ls)
temp=Path('/tmp/LogicScope_S3_BaselinePaste.kicad_pcb');p.SaveBoard(str(temp),board)
run('kicad-cli','pcb','export','gerbers','--output','fabrication/assembly/','--layers','F.Paste',str(temp))
for name in ['BOM.csv','BOM_Grouped.csv']:shutil.copyfile(ROOT/name,ROOT/'fabrication/assembly'/name)
report=(ROOT/'docs/Engineering_Report.md').read_text()
for name in ['Electrical_and_Fabrication.md','Acquisition_Architecture.md','Validation_Plan.md']:report=report.replace(']('+name+')','](../docs/'+name+')')
(ROOT/'fabrication/Engineering_Report.md').write_text(report)
# All-source placement is for review; manufacturing placement above excludes DNP/TP/holes.
files=[f for f in ROOT.rglob('*') if f.is_file() and f.suffix in ['.kicad_pcb','.kicad_sch','.kicad_pro','.kicad_dru','.kicad_sym','.kicad_mod'] and 'research' not in f.parts]
files += [ROOT/n for n in ['README.md','LICENSE','design.json','fp-lib-table','sym-lib-table','BOM.csv','BOM_Grouped.csv','Placement.csv','GPIO_Allocation.csv','Connector_Pinouts.csv']]
files += list((ROOT/'docs').glob('*.md'))+list((ROOT/'libraries').glob('*.md'))
files += [ROOT/'reports'/n for n in ['ERC.json','DRC.json','Connectivity_Audit.json','Physical_Audit.json']]
files += [f for f in (ROOT/'fabrication').rglob('*') if f.is_file() and f.name!='SHA256SUMS']
files += list((ROOT/'previews').glob('*.png'))
files += list((ROOT/'scripts').glob('*.py'))+[ROOT/'requirements.txt',ROOT/'reports/MCP_Validation.md']
(ROOT/'fabrication/SHA256SUMS').write_text(''.join(f'{hashlib.sha256(f.read_bytes()).hexdigest()}  {f.relative_to(ROOT)}\n' for f in sorted(set(files))))
print('Engineering fabrication pack exported; physical performance remains unmeasured.')
