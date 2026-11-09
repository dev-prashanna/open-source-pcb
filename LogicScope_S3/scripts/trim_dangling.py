"""Remove only KiCad-reported dangling copper, then refill and recheck.

Run after routing. Each pass uses a fresh DRC report, so branches that become
dangling after a previous removal are pruned without deleting connected routes.
"""
from cadlib import *
import subprocess

path = ROOT / 'LogicScope_S3.kicad_pcb'
report = ROOT / 'reports/DRC_trim.json'
removed = 0
for iteration in range(100):
    subprocess.run(['kicad-cli', 'pcb', 'drc', '--refill-zones', '--save-board', '--format', 'json',
                    '--output', str(report), str(path)], check=True,
                   stdout=subprocess.DEVNULL)
    data = json.loads(report.read_text())
    ids = {item['uuid'] for violation in data['violations']
           if violation['type'] in ('track_dangling', 'via_dangling')
           for item in violation['items']}
    if not ids:
        break
    document = sx.loads(path.read_text())
    kept = [entry for entry in document if not (
        isinstance(entry, list) and entry and str(entry[0]) in ('segment', 'via')
        and atom(entry, 'uuid') in ids)]
    count = len(document) - len(kept)
    if not count:
        raise RuntimeError('DRC dangling UUIDs did not match board copper')
    path.write_text(sx.dumps(kept))
    removed += count
    print(f'Pass {iteration + 1}: removed {count} dangling items', flush=True)
else:
    raise RuntimeError('Dangling copper did not converge')
print(f'Removed {removed} dangling items; review {report.name}')
