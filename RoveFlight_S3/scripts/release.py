"""Validate the current native design and export an engineering fabrication pack.

Does not rebuild schematics, replace placement, or run an autorouter.
Requires KiCad 10, pcbnew, and requirements.txt in a system-site-packages venv.
"""
from pathlib import Path
import hashlib
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
NAME = 'RoveFlight_S3'

def run(*args):
    subprocess.run(args, cwd=ROOT, check=True)

run('kicad-cli', 'sch', 'erc', '--format', 'json', '--output',
    'reports/ERC.json', NAME + '.kicad_sch')
run('kicad-cli', 'pcb', 'drc', '--refill-zones', '--save-board',
    '--schematic-parity', '--format', 'json', '--output',
    'reports/DRC.json', NAME + '.kicad_pcb')
erc = json.loads((ROOT / 'reports/ERC.json').read_text())
drc = json.loads((ROOT / 'reports/DRC.json').read_text())
erc_issues = [v for sheet in erc.get('sheets', []) for v in sheet['violations']]
if erc_issues or any(drc.get(key) for key in
                     ('violations', 'unconnected_items', 'schematic_parity')):
    raise SystemExit('Release blocked: resolve ERC/DRC/parity findings in reports/')
run('kicad-cli', 'sch', 'export', 'netlist', '--format', 'kicadxml',
    '--output', 'reports/' + NAME + '.xml', NAME + '.kicad_sch')
run(sys.executable, 'scripts/audit_design.py')
run(sys.executable, 'scripts/audit_assembly.py')
physical = json.loads((ROOT / 'reports/Physical_Audit.json').read_text())
if physical['ground_plane_signal_tracks'] or physical['rf_keepout_track_errors']:
    raise SystemExit('Release blocked: ground reference or RF keepout audit failed')
for folder in ('fabrication/gerbers', 'fabrication/assembly', 'previews'):
    (ROOT / folder).mkdir(parents=True, exist_ok=True)
run('kicad-cli', 'pcb', 'export', 'gerbers', '--output', 'fabrication/gerbers/',
    '--layers', 'F.Cu,In1.Cu,In2.Cu,In3.Cu,In4.Cu,B.Cu,F.Mask,B.Mask,F.Silkscreen,B.Silkscreen,Edge.Cuts',
    NAME + '.kicad_pcb')
run('kicad-cli', 'pcb', 'export', 'drill', '--output', 'fabrication/gerbers/',
    NAME + '.kicad_pcb')
run('kicad-cli', 'pcb', 'export', 'pos', '--format', 'csv', '--units', 'mm',
    '--output', 'fabrication/assembly/Placement.csv', NAME + '.kicad_pcb')
run('kicad-cli', 'sch', 'export', 'pdf', '--output', 'fabrication/Schematic.pdf',
    NAME + '.kicad_sch')
run('kicad-cli', 'pcb', 'export', 'pdf', '--layers', 'F.Fab,B.Fab,Edge.Cuts',
    '--output', 'fabrication/assembly/Assembly.pdf', NAME + '.kicad_pcb')
files = [ROOT / (NAME + suffix) for suffix in ('.kicad_pcb', '.kicad_sch', '.kicad_pro')]
files += sorted(ROOT.glob('[0-9]*.kicad_sch'))
files += sorted(path for path in (ROOT / 'libraries').rglob('*') if path.is_file())
files += sorted((ROOT / 'docs').glob('*.md'))
files += [ROOT / name for name in ('README.md', 'design.json', 'fp-lib-table',
          'sym-lib-table', 'GPIO_Allocation.csv', 'Connector_Pinouts.csv')]
files += [ROOT / name for name in ('BOM.csv', 'BOM_Grouped.csv', 'Placement.csv',
          'reports/ERC.json', 'reports/DRC.json', 'reports/Connectivity_Audit.json',
          'reports/Physical_Audit.json', 'reports/Assembly_Audit.json')]
files += sorted(path for path in (ROOT / 'fabrication').rglob('*')
                if path.is_file() and path.name != 'SHA256SUMS')
(ROOT / 'fabrication/SHA256SUMS').write_text(''.join(
    f'{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.relative_to(ROOT)}\n'
    for path in files))
print('Engineering package exported. Bench/thermal/RF/flight validation remains required.')
