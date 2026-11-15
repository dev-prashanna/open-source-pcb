# Hardware construction and release utilities

The native KiCad 10 project is the delivered source of truth. Open it directly
for normal editing. The scripts are engineering helpers, not a replacement
for KiCad or a one-command reproduction of every routing decision.

`release.py` checks ERC and DRC with schematic parity and exports the exact
current board. It requires Python 3 and KiCad 10's `kicad-cli`; it does not
regenerate the schematic, placement, or routing. `tools/audit_hardware.py`
requires Python's pcbnew module and checks the manifest against actual pads.

`build_hardware.py`, `layout.py`, `prepare_routing.py`, and the fanout/routing
helpers are destructive construction tools. Use a separate working copy.
The final layout includes reviewed manual routing and silkscreen changes.
Do not run a constructor on the release board expecting it to preserve those.

For construction helpers on Ubuntu with KiCad 10 installed, create a Python
environment that can see system pcbnew and install the geometry dependencies:

```sh
/usr/bin/python3 -m venv --system-site-packages .venv-cad
.venv-cad/bin/pip install sexpdata shapely numpy scipy
```

The recorded construction environment used sexpdata 1.0.2, Shapely 2.2.0,
NumPy 2.5.3 and SciPy 1.18.1. Interactive/automatic routing used Freerouting;
its session files are transient work products, not required to open the PCB.
The published PCB already contains all final routing and local library assets.
