"""Validate and export the delivered board without regenerating its layout."""
from pathlib import Path
import hashlib
import json
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / 'RoveCore_One.kicad_pcb'
SCHEMATIC = ROOT / 'RoveCore_One.kicad_sch'


def run(*args):
    subprocess.run(['kicad-cli', *map(str, args)], check=True, cwd=ROOT)


def main():
    reports = ROOT / 'reports'
    reports.mkdir(exist_ok=True)
    run('pcb', 'drc', '--schematic-parity', '--exit-code-violations',
        '--format', 'json', '--output', reports / 'DRC.json', BOARD)
    run('sch', 'erc', '--format', 'json', '--output', reports / 'ERC.json', SCHEMATIC)
    erc = json.loads((reports / 'ERC.json').read_text())
    errors = [v for sheet in erc['sheets'] for v in sheet['violations']
              if v['severity'] == 'error']
    if errors:
        raise SystemExit(f'ERC has {len(errors)} errors; exports stopped')
    run('sch', 'export', 'netlist', '--format', 'kicadxml', '--output',
        reports / 'RoveCore_One.xml', SCHEMATIC)
    gerbers = ROOT / 'fabrication' / 'gerbers'
    assembly = ROOT / 'fabrication' / 'assembly'
    previews = ROOT / 'previews'
    for directory in (gerbers, assembly, previews):
        directory.mkdir(parents=True, exist_ok=True)
    run('pcb', 'export', 'gerbers', '--layers',
        'F.Cu,In1.Cu,In2.Cu,B.Cu,F.Mask,B.Mask,F.Silkscreen,B.Silkscreen,Edge.Cuts',
        '--output', str(gerbers) + '/', BOARD)
    run('pcb', 'export', 'drill', '--excellon-separate-th',
        '--output', str(gerbers) + '/', BOARD)
    for side in ('front', 'back'):
        run('pcb', 'export', 'pos', '--side', side, '--format', 'csv', '--units',
            'mm', '--exclude-dnp', '--output', assembly / f'{side}-positions.csv', BOARD)
    run('sch', 'export', 'pdf', '--output', previews / 'RoveCore_One_Schematic.pdf', SCHEMATIC)
    for side, layers in [('front', 'F.Cu,F.Silkscreen,Edge.Cuts'),
                         ('back', 'B.Cu,B.Silkscreen,Edge.Cuts')]:
        run('pcb', 'export', 'svg', '--mode-single', '--layers', layers, '--page-size-mode', '2',
            '--output', previews / f'PCB_{side}.svg', BOARD)
    archive = ROOT / 'fabrication' / 'RoveCore_One-Gerbers.zip'
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as out:
        for path in sorted(gerbers.iterdir()):
            if path.is_file():
                out.write(path, path.name)
    files = [BOARD, SCHEMATIC, *sorted(gerbers.iterdir()), archive]
    lines = [f'{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.relative_to(ROOT)}'
             for path in files if path.is_file()]
    (ROOT / 'fabrication' / 'SHA256SUMS').write_text('\n'.join(lines) + '\n')
    print('Validation and fabrication exports complete.')


if __name__ == '__main__':
    main()
