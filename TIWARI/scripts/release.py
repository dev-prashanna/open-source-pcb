"""Validate and export the reviewed TIWARI board; never regenerate routing."""
from pathlib import Path
import csv,hashlib,json,subprocess,zipfile
ROOT=Path(__file__).resolve().parents[1]
H=ROOT/'hardware';REPORTS=ROOT/'reports'
BOARD=H/'TIWARI.kicad_pcb';SCH=H/'TIWARI.kicad_sch'
def run(*args):
 subprocess.run(['kicad-cli',*map(str,args)],check=True,cwd=ROOT)
def main():
 REPORTS.mkdir(exist_ok=True)
 run('sch','erc','--format','json','--exit-code-violations','--output',REPORTS/'ERC.json',SCH)
 run('pcb','drc','--schematic-parity','--format','json','--exit-code-violations','--output',REPORTS/'DRC.json',BOARD)
 subprocess.run(['python3',str(ROOT/'tools/check_pins.py')],check=True,cwd=ROOT)
 run('sch','export','netlist','--format','kicadxml','--output',REPORTS/'TIWARI.xml',SCH)
 fab=ROOT/'fabrication';gerber=fab/'gerbers';assembly=fab/'assembly';preview=ROOT/'previews'
 for d in[gerber,assembly,preview]:d.mkdir(parents=True,exist_ok=True)
 run('pcb','export','gerbers','--layers','F.Cu,In1.Cu,In2.Cu,B.Cu,F.Mask,B.Mask,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,Edge.Cuts','--output',str(gerber)+'/',BOARD)
 run('pcb','export','drill','--excellon-separate-th','--output',str(gerber)+'/',BOARD)
 for side in['front','back']:
  run('pcb','export','pos','--side',side,'--format','csv','--units','mm','--exclude-dnp','--output',assembly/f'{side}-positions.csv',BOARD)
 run('sch','export','pdf','--output',preview/'TIWARI_Schematic.pdf',SCH)
 for side,layers in[('front','F.Cu,F.Silkscreen,Edge.Cuts'),('back','B.Cu,B.Silkscreen,Edge.Cuts')]:
  run('pcb','export','svg','--mode-single','--layers',layers,'--page-size-mode','2','--output',preview/f'PCB_{side}.svg',BOARD)
 parts=json.loads((H/'design.json').read_text())
 with(assembly/'BOM.csv').open('w')as f:
  w=csv.writer(f);w.writerow(['Reference','Value','MPN','Manufacturer','Footprint','Datasheet'])
  for part in parts:
   if part['mpn']=='PCB_FEATURE':continue
   w.writerow([part.get(k,'')for k in['ref','value','mpn','mfr','fp','source']])
 archive=fab/'TIWARI-TW8-A0-Gerbers.zip'
 with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED)as out:
  for p in sorted(gerber.iterdir()):
   if p.is_file():out.write(p,p.name)
 files=[BOARD,SCH,*H.glob('0*.kicad_sch'),*gerber.iterdir(),*assembly.iterdir(),archive,* (ROOT/'firmware/prebuilt').glob('*')]
 lines=[f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(ROOT)}'for p in sorted(files)if p.is_file()]
 (fab/'SHA256SUMS').write_text('\n'.join(lines)+'\n')
 print('TIWARI release exported from the reviewed, passing board')
if __name__=='__main__':main()
