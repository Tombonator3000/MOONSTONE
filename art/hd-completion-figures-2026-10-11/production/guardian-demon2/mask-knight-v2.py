"""Streng original-NN-maske for den innbakte ridderen i Demon2/060."""
from pathlib import Path
import hashlib, json
from PIL import Image

HERE = Path(__file__).resolve().parent
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
c = json.loads((HERE / 'geometries.json').read_text())[60]
assert c['frame'] == 60 and c['live_palette_indices'] == [6, 7, 8]
png = HERE / 'packed' / c['key']
im = Image.open(png)
assert im.mode == 'RGBA' and im.size == (c['width'] * 4, c['height'] * 4)
mask = Image.new('RGBA', im.size, (0, 0, 0, 255))
live = 0
for y in range(im.height):
    for x in range(im.width):
        index = c['indices'][y // 4 * c['width'] + x // 4]
        if index in c['live_palette_indices']:
            reference = sum(v * k for v, k in zip(c['palette'][index][:3], [.2126, .7152, .0722]))
            light = sum(v * k for v, k in zip(im.getpixel((x, y))[:3], [.2126, .7152, .0722]))
            assert reference > 0
            g = max(0, min(255, round(light * 128 / reference)))
            mask.putpixel((x, y), (index + 1, g, 255, 255))
            live += 1
dest = png.with_suffix('.mask.png')
mask.save(dest)
report = dict(schema=1, status='passed', frame=60, source_contracts_sha256=sha(HERE / 'source-contracts.json'),
    source_bank_sha256=c['source_bank_sha256'], source_indices_sha256=c['indices_sha256'],
    photo_sha256=sha(png), mask_sha256=sha(dest), script_sha256=sha(Path(__file__)),
    live_source_cells=live // 16, live_HD_pixels=live, source_palette=c['palette'],
    contract='R=source NN index+1 for6..8 and B=255, otherwise R/B=0, independent of alpha; G=photographic luminance/reference palette luminance*128; A=255.')
(HERE / 'verification/mask-knight-v2.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(dict(status='passed', live_source_cells=live // 16, mask_sha256=report['mask_sha256'])))
