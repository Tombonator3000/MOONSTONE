"""Bevar alle originale indeks5-skyggeceller byteeksakt; oevrig foto er urort."""
from pathlib import Path
import hashlib
import json
from PIL import Image

H = Path(__file__).resolve().parent
R = H.parents[3]
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
rows = json.loads((H / 'runtime-geometries-four-v1.json').read_text())
index = json.loads((H.parent / 'candidates-troll-source-usage-unresolved-v1.json').read_text())
index['scope'] = 'Egne foto beholdes, eksakt original svart indeks5-skygge er mekanisk pakket i to kandidater. Ingen aktivering.'
entries = {e['key']: e for e in index['entries']}
checks = []
for row in rows:
    if row['key'] not in ['TROLL1.CEL/019.png', 'TROLL2.CEL/010.png']:
        continue
    old = entries[row['key']]
    original = Image.open(R / old['candidate']).convert('RGBA')
    image = original.copy()
    changed = []
    for y in range(image.height):
        for x in range(image.width):
            i = row['indices'][y // 4 * row['width'] + x // 4]
            if i == 5:
                if image.getpixel((x, y)) != (0, 0, 0, 255):
                    changed.append([x, y])
                image.putpixel((x, y), (0, 0, 0, 255))
            else:
                assert image.getpixel((x, y)) == original.getpixel((x, y))
    target = H / 'packed-exact-shadow-v2' / row['bank'] / ('%03d.png' % row['frame'])
    target.parent.mkdir(parents=True, exist_ok=True)
    image.save(target, optimize=True)
    art = json.loads((R / old['art_record']).read_text())
    art['candidate_sha256'] = sha(target)
    art['original_flat_shadow_packing']['method'] = 'Alle16 HD-piksler per original indeks5-celle er eksakt svart RGBA0,0,0,255. Alt oevrig fotografisk materiale og alfa er byteuendret.'
    art['source_shadow_correction_v2'] = dict(parent_candidate=old['candidate'], parent_candidate_sha256=old['candidate_sha256'], corrected_hd_pixels=changed, changed_pixels_outside_original_index5=0, helper=str(Path(__file__).relative_to(R)), helper_sha256=sha(Path(__file__)))
    art_path = target.with_suffix('.art-record.json')
    art_path.write_text(json.dumps(art, ensure_ascii=False, indent=2) + '\n')
    row['packed_candidate_path'] = str(target.relative_to(R))
    old.update(candidate=str(target.relative_to(R)), candidate_sha256=sha(target), art_record=str(art_path.relative_to(R)), art_record_sha256=sha(art_path))
    checks.append(dict(key=row['key'], corrected_hd_pixels=len(changed), other_pixels_unchanged=True, original_shadow_exact=True))
(H / 'runtime-geometries-four-v2.json').write_text(json.dumps(rows, indent=2) + '\n')
(H / 'candidates-four-v2.json').write_text(json.dumps(index, ensure_ascii=False, indent=2) + '\n')
(H / 'shadow-correction-v2.json').write_text(json.dumps(dict(status='passed', entries=checks), indent=2) + '\n')
print(json.dumps(checks))
