"""Record the antenna-overhang footprint as an explicit project library asset.

The upstream module's off-board silkscreen belongs on the assembly drawing.
Pads, antenna copper keepout, courtyard and model geometry are preserved.
"""
from cadlib import *
import pcbnew as p

path = ROOT / 'RoveFlight_S3.kicad_pcb'
board = p.LoadBoard(str(path))
module = next(fp for fp in board.GetFootprints() if fp.GetReference() == 'U1')
for graphic in module.GraphicalItems():
    if graphic.GetLayer() == p.F_SilkS:
        bounds = graphic.GetBoundingBox()
        if p.ToMM(bounds.GetY()) < .2:
            graphic.SetLayer(p.F_Fab)
name = 'ESP32-S3-WROOM-1_Overhang'
module.SetFPID(p.LIB_ID('RoveFlight', name))
copy_fp = p.Cast_to_FOOTPRINT(module.Duplicate(False))
copy_fp.SetPosition(p.VECTOR2I(0, 0))
copy_fp.SetOrientationDegrees(0)
copy_fp.SetReference('REF**')
copy_fp.SetValue(name)
for pad in copy_fp.Pads():
    pad.SetNetCode(0)
p.FootprintSave(str(ROOT / 'libraries/RoveFlight.pretty'), copy_fp)
assert (ROOT / 'libraries/RoveFlight.pretty' / (name + '.kicad_mod')).is_file()
p.SaveBoard(str(path), board)

old, new = 'RF_Module:ESP32-S3-WROOM-1', 'RoveFlight:' + name
for schematic in ROOT.glob('*.kicad_sch'):
    text = schematic.read_text()
    # Symbol IDs and footprint IDs happen to share the upstream name. Keep
    # the symbol's identity and child-unit names intact; change only land patterns.
    text = text.replace('(symbol "' + new + '"', '(symbol "' + old + '"')
    text = text.replace('(lib_id "' + new + '"', '(lib_id "' + old + '"')
    text = text.replace('(property "Footprint" "' + old + '"',
                        '(property "Footprint" "' + new + '"')
    schematic.write_text(text)
parts = json.loads((ROOT / 'design.json').read_text())
for part in parts:
    if part['ref'] == 'U1':
        part['fp'] = new
(ROOT / 'design.json').write_text(json.dumps(parts, indent=2) + '\n')
for name in ('BOM.csv', 'BOM_Grouped.csv'):
    file = ROOT / name
    file.write_text(file.read_text().replace(old, new))
print('Saved project overhang footprint and synchronized schematic/BOM manifest')
