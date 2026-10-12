"""Kontroller faktisk synlig nytt materiale inne i hver originalankrede rute."""
from pathlib import Path
from PIL import Image
import hashlib
import json

ART = Path(__file__).resolve().parent
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
p = ART / 'verification/observed14-actual-v1/test.json'
d = json.loads(p.read_text())
assert d['status'] == 'passed'
sources = json.loads((ART / 'source-contracts.json').read_text())
rows = []
checks = []
for cap in d['captures']:
    if 'body' not in cap:
        continue
    body = cap['body']
    frame = body['bilde']
    c = next(c for c in sources['entries'] if c['bank'] == 'RATMEN1.CEL' and c['frame'] == frame)
    original = ART / f'verification/observed14-actual-v1/{frame:03}-original.png'
    hd = ART / f'verification/observed14-actual-v1/{frame:03}-hd.png'
    assert sha(original) == cap['original_sha256']
    checks.append(c['key'] + '_original_capture_SHA')
    assert sha(hd) == cap['hd_sha256']
    checks.append(c['key'] + '_HD_capture_SHA')
    old = Image.open(original)
    new = Image.open(hd)
    assert old.size == new.size == (960, 600)
    checks.append(c['key'] + '_actual_3x_canvas')
    changed = 0
    for y in range(c['height']):
        for x in range(c['width']):
            index = c['indices'][y*c['width'] + (c['width']-1-x if body['speilet'] else x)]
            if index == 0:
                continue
            screen = ((body['x']+x)*3+1, (body['y']+y)*3+1)
            changed += old.getpixel(screen) != new.getpixel(screen)
    assert changed > 0, c['key']
    checks.append(c['key'] + '_visible_change_inside_own_source')
    rows.append(dict(key=c['key'], actual_frame=cap['frame'], changed_opaque_source_centers=changed, original_png_sha256=sha(original), hd_png_sha256=sha(hd)))
proof = dict(schema=1, status='passed', runtime_proof_sha256=sha(p), source_contracts_sha256=sha(ART/'source-contracts.json'), runtime_script_sha256=sha(Path(__file__)), scope='Bilde-/SHA-kontroll av originalkampfangster. Hver av13ruter har synlig endring innen egne opake kildepikselmidtpunkter, med original speiling og faktisk3xcanvas.', assets=rows, checks=checks)
(ART/'verification/observed13-actual-source-centers.json').write_text(json.dumps(proof, indent=2)+'\n')
print(json.dumps(dict(status='passed', checks=len(checks), assets=len(rows))))
