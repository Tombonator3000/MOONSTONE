"""Masker fra kildeplanmasken og faktisk ny graa fototekstur, aldri malbildet."""
import json
import sys
from pathlib import Path
ART=Path(__file__).resolve().parent
ROOT=ART.parents[3]
FIGURES=ART.parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from hd_bestilling import lag_maske
queue=json.loads((ART/'queue-subset.json').read_text())
for c in queue['entries']+queue['aliases']:
    png=ART/'packed'/c['key']
    if not c['needs_mask'] or not png.exists():continue
    lag_maske(str(FIGURES/c['packed_original']['path']),str(png.with_name(png.stem+'.mask.png')),str(png),str(ROOT/'Moonstonecd32-AMIGA.zip'),128)
