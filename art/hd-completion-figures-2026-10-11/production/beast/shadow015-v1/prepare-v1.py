"""Bevar be1.c/015 som nøyaktig svart originalskygge, uten ny fotomaster."""
from pathlib import Path
import hashlib
import json
import sys
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT / 'tools'))
import moonfiles as mf
from hd_bestilling import utvid_indekser

sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
bank = mf.Spill(ROOT / 'Moonstonecd32-AMIGA.zip').les('be1.c')
source = mf.cel_les(bank)[0][15]
w, h = source['bredde'], source['hoyde']
indices = utvid_indekser(mf.plan_til_indeks(source['data'], source['plan'], w, h), source['maske'])
assert (w, h, source['maske'], set(indices)) == (13, 5, 5, {0, 5})
image = Image.new('RGBA', (w, h))
image.putdata([(0, 0, 0, 255) if i else (0, 0, 0, 0) for i in indices])
image = image.resize((w * 4, h * 4), Image.Resampling.NEAREST)
png = HERE / 'packed/be1.c/015.png'
if png.exists():
    with Image.open(png) as current:
        assert current.mode == 'RGBA' and current.size == image.size and current.tobytes() == image.tobytes()
else:
    png.parent.mkdir(parents=True, exist_ok=True)
    image.save(png)
assert sha(png) == 'f8d9485904407227c511f4093ca7ba7363e4d17bbf7e1262ab64c0196ec73c33'
print(json.dumps(dict(status='exact_original_shadow_preserved', source='be1.c/015', source_size=[w, h], source_plane_mask=source['maske'], opaque_cells=sum(i == 5 for i in indices), output_sha256=sha(png))))
