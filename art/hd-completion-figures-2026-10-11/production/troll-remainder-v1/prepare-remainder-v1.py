"""Samle fire egne Troll-figurer, aatte nye bevegelsesmaterialer og en originalskygge."""
from pathlib import Path
import hashlib
import json
from PIL import Image

H = Path(__file__).resolve().parent
R = H.parents[3]
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
rows = json.loads((H / 'runtime-geometries-four-v2.json').read_text())
candidates = json.loads((H / 'candidates-four-v2.json').read_text())['entries']
motion_rows = json.loads((H / 'motion/geometries-v1.json').read_text())
motion_candidates = json.loads((H / 'motion/candidates-v1.json').read_text())
for item in motion_candidates:
    item['generation_tool'] = 'builtin_image_gen'
    candidates.append(item)
rows.extend(motion_rows)
shadow = next(r for r in json.loads((H / 'sources-v1.json').read_text()) if r['bank'] == 'TROLL1.CEL' and r['frame'] == 12)
assert set(shadow['indices']) == {0, 5}
image = Image.new('RGBA', (shadow['width'], shadow['height']))
image.putdata([(0, 0, 0, 255 if i else 0) for i in shadow['indices']])
image = image.resize((shadow['width'] * 4, shadow['height'] * 4), Image.Resampling.NEAREST)
target = H / 'shadow012-v1.png'
image.save(target, optimize=True)
prompt = H / 'shadow012-v1.txt'
prompt.write_text('Eksakt original svart indeks5-skygge i4x, ingen fotonytegning. Indeks0 er gjennomsiktig og indeks5 er svart opak.\n')
shadow.update(number='012', needs_mask=False, packed_candidate_path=str(target.relative_to(R)))
rows.append(shadow)
candidates.append(dict(key=shadow['key'], candidate=str(target.relative_to(R)), candidate_sha256=sha(target), raw=str(target.relative_to(R)), raw_sha256=sha(target), prompt=str(prompt.relative_to(R)), prompt_sha256=sha(prompt), generation_tool='preserved_original_black_shadow'))
assert len(rows) == 13 and len({r['key'] for r in rows}) == 13
rows.sort(key=lambda r: r['key'])
candidates.sort(key=lambda r: r['key'])
(H / 'runtime-geometries-remainder-v1.json').write_text(json.dumps(rows, indent=2) + '\n')
(H / 'candidates-remainder-v1.json').write_text(json.dumps(candidates, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(dict(routes=13, photographic_body_foot_masters=4, photographic_motion_materials=8, preserved_black_shadows=1, activated=False)))
