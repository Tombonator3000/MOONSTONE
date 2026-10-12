"""Lag den regenererbare Balok026-testreferansen direkte fra original ZIP."""
from pathlib import Path
import argparse
import hashlib
import io
import json
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
import moonfiles as mf
from hd_bestilling import utvid_indekser
from PIL import Image

EXPECTED = 'bf74a278d3cd328cc45705214bd116816d262fb7def3a59f8bd495736bdac906'
sha = lambda b: hashlib.sha256(b).hexdigest()
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, default=HERE / 'retention/Balok1.CEL-026-original-shadow4x.png')
parser.add_argument('--receipt', type=Path)
args = parser.parse_args()
archive = ROOT / 'Moonstonecd32-AMIGA.zip'
bank = mf.Spill(archive).les('Balok1.CEL')
source = mf.cel_les(bank)[0][26]
w, h = source['bredde'], source['hoyde']
indices = utvid_indekser(mf.plan_til_indeks(source['data'], source['plan'], w, h), source['maske'])
assert (w, h, source['maske'], set(indices)) == (65, 13, 5, {0, 5})
image = Image.new('RGBA', (w, h))
image.putdata([(0, 0, 0, 255) if i else (0, 0, 0, 0) for i in indices])
image = image.resize((w * 4, h * 4), Image.Resampling.NEAREST)
buffer = io.BytesIO()
image.save(buffer, format='PNG')
png = buffer.getvalue()
assert sha(png) == EXPECTED, 'Regenerert PNG avviker fra den frosne testreferansen'
if args.output.exists():
    assert sha(args.output.read_bytes()) == EXPECTED, 'Bevar avvikende eksisterende fil for undersoekelse'
else:
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(png)
report = dict(schema=1, status='passed', source='Balok1.CEL/026', source_zip_sha256=sha(archive.read_bytes()), source_bank_sha256=sha(bank), source_indices_sha256=sha(indices), source_size=[w, h], source_plane_mask=source['maske'], output_size=list(image.size), png_sha256=EXPECTED, generator_sha256=sha(Path(__file__).read_bytes()), frozen_runtime_script_sha256=sha((HERE / 'runtime-retention-fixtures-v4.cjs').read_bytes()), scope='Regenererbar original svart skygge til test. Ingen nytegning, kandidataktivering eller endring av frosne leveranser.')
if args.receipt:
    data = json.dumps(report, indent=2) + '\n'
    if args.receipt.exists():
        assert args.receipt.read_text() == data, 'Bevar tidligere kvittering'
    else:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(data)
print(json.dumps(report))
