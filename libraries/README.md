# Project libraries

The `*_Board.kicad_mod` footprints are derived from the KiCad 10 community footprints (https://gitlab.com/kicad/libraries/kicad-footprints). They retain manufacturer pad geometry and upstream 3D-model references. Changes move selected silkscreen graphics to fabrication layers to avoid clipping/overlaps. The ESP32 copy retains this board's four-layer antenna keepout; its library polygon coordinates are relative to the module origin. These modified library footprints remain under the KiCad library licence in KiCad-LICENSE.md (CC BY-SA 4.0 with the KiCad exception).

`VEML7700_TT.kicad_mod` and `RoveCore.kicad_sym` were constructed for this design from the Vishay VEML7700-TT datasheet cited in datasheets/sources.json. `ServicePad_0.5mm.kicad_mod` is a project-local service pad. Original project library content uses the project CERN-OHL-P-2.0 licence. Embedded standard schematic symbols originate from the KiCad community symbol library (https://gitlab.com/kicad/libraries/kicad-symbols), under the same KiCad library licence and exception.

Models referenced with `${KICAD10_3DMODEL_DIR}` require the KiCad 10 model package; they are not embedded in the repository. Some parts have no assigned model, so renderings are illustrative rather than complete mechanical assemblies.
