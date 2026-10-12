#!/usr/bin/env python3
"""Pakk eget armfoto i029; bevar kildens stiplete bevegelsesbue eksplisitt."""
from collections import deque
import hashlib
import json
import os
from pathlib import Path
import subprocess
from PIL import Image
from contours import source_contours
ART = Path(__file__).resolve().parent
FIGURES = ART.parent
ROOT = FIGURES.parents[1]
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    key = 'Balok1.CEL/029.png'
    row = next(r for r in json.loads((FIGURES / 'queue.json').read_text())['entries'] if r['key'] == key)
    palette_path = FIGURES / 'palettes/cases/balok.json'
    palette = json.loads(palette_path.read_text())
    ref = next(r for r in palette['references'] if r['key'] == key)
    assert ref['source_indices_sha256'] == row['indices_sha256']
    original = Image.open(FIGURES / 'palettes' / ref['original']).convert('RGBA')
    reference = ART / 'references/Balok1.CEL/029/solid-component-v1'
    components_path = reference / 'components.json'
    components = json.loads(components_path.read_text())['components']
    core = {tuple(xy) for xy in components[0]}
    opaque = {(x, y) for y in range(original.height) for x in range(original.width) if original.getpixel((x, y))[3]}
    assert len(core) == 201 and all(x <= 7 and 2 <= y <= 39 for x, y in core)
    retained = opaque - core
    assert core | retained == opaque and not core & retained
    raw_path = ART / 'balok/raw/029-arm-v1.png'
    prompt = ART / 'balok/prompts/029-arm-v1.txt'
    raw = Image.open(raw_path).convert('RGBA')
    window = raw.getchannel('A').point(lambda a: 255 if a >= 8 else 0).getbbox()
    assert window
    outside = [raw.getpixel((x, y))[3] for y in range(raw.height) for x in range(raw.width) if not (window[0] <= x < window[2] and window[1] <= y < window[3])]
    assert max(outside, default=0) <= 7
    generated = raw.crop(window).resize((32, 152), Image.Resampling.LANCZOS)
    source_crop = Image.open(reference / 'original-solid-crop.png').convert('RGBA')
    source4 = source_crop.resize(generated.size, Image.Resampling.NEAREST)
    s = [a >= 128 for a in source4.getchannel('A').getdata()]
    g = [a >= 128 for a in generated.getchannel('A').getdata()]
    iou = sum(a and b for a, b in zip(s, g)) / sum(a or b for a, b in zip(s, g))
    assert iou >= .90, 'Armmaterialets form krever ny generering'
    out = ART / 'bound/Balok1.CEL/029' / sha(raw_path)[:16] / 'separate-arm-photo-original-motion-v1'
    assert not out.exists(), 'Bevar eldre bevis'
    out.mkdir(parents=True)
    shape = source_contours(list(source_crop.getchannel('A').getdata()), 8, 38, lambda a: a > 0)
    svg = out / 'arm-alpha.svg'
    svg.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="32" height="152" viewBox="0 0 8 38"><path d="{shape}" fill="white" fill-rule="evenodd"/></svg>\n')
    env = os.environ.copy()
    env.setdefault('NODE_PATH', '/home/tombonator3000t/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules')
    node = env.get('NODE', '/home/tombonator3000t/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node')
    subprocess.run([node, str(ART / 'mask.cjs'), str(svg), str(out / 'arm-alpha.png'), '32', '152'], env=env, check=True)
    alpha = Image.open(out / 'arm-alpha.png').getchannel('A')
    nearest = {}; distance = {}; pending = deque()
    for y in range(generated.height):
        for x in range(generated.width):
            if generated.getpixel((x, y))[3] >= 128:
                nearest[x, y] = (x, y); distance[x, y] = 0; pending.append((x, y))
    while pending:
        x, y = pending.popleft()
        for n in [(x-1,y),(x+1,y),(x,y-1),(x,y+1)]:
            if 0 <= n[0] < 32 and 0 <= n[1] < 152 and n not in nearest:
                nearest[n] = nearest[x,y]; distance[n] = distance[x,y] + 1; pending.append(n)
    result = Image.new('RGBA', (original.width * 4, original.height * 4))
    for x, y in retained:
        for dy in range(4):
            for dx in range(4):result.putpixel((x*4+dx,y*4+dy),original.getpixel((x,y)))
    extensions = []
    for y in range(152):
        for x in range(32):
            if not alpha.getpixel((x,y)):continue
            u,v = nearest[x,y]
            if distance[x,y]:extensions.append(dict(x=x,y=y,from_x=u,from_y=v,distance=distance[x,y]))
            result.putpixel((x,y+8),generated.getpixel((u,v))[:3]+(alpha.getpixel((x,y)),))
    assert max((e['distance'] for e in extensions),default=0) <= 3
    missing=[]; false=[]
    for y in range(original.height):
        for x in range(original.width):
            expected=original.getpixel((x,y))[3]>=128;actual=result.getpixel((x*4+2,y*4+2))[3]>=128
            if expected and not actual:missing.append([x,y])
            if actual and not expected:false.append([x,y])
    assert not missing and not false
    for x,y in retained:
        for dy in range(4):
            for dx in range(4):assert result.getpixel((x*4+dx,y*4+dy))==original.getpixel((x,y))
    candidate=out/'candidate.png';result.save(candidate,optimize=True)
    record=dict(key=key,candidate_sha256=sha(candidate),source_indices_sha256=row['indices_sha256'],authoring_method='individual_redraw',generator='built-in ChatGPT image generator; exact model version not exposed',raw_sha256=sha(raw_path),raw_file=str(raw_path.relative_to(ROOT)),prompt=str(prompt.relative_to(ROOT)),prompt_sha256=sha(prompt),palette_case='balok',palette_contract_sha256=sha(palette_path),palette_reference_sha256=sha(FIGURES/'palettes'/ref['original']),packing='Eget generert armfoto i201 sammenhengende kildeceller. Kildens adskilte stiplete bevegelsesbue beholdes med eksakt originalRGBA og4x-naermeste pikselform; bevegelsesbuen er ikke fotonytegnet. Eget foto tilpasses bare ett globalt utsnitt; ingen anatomisk per-rad-flytting eller originalRGB i armflaten.',raw_padding_window=list(window),raw_margin_proof=dict(max_alpha=max(outside,default=0),visible_content_clipped=False),raw_silhouette_iou=iou,aligned_silhouette_iou=iou,alignment_gate=.90,geometry_gate_passed=True,max_opaque_edge_extension_px=3,source_pixel_midpoints_checked=original.width*original.height,missing_opaque_source_midpoints=missing,false_filled_transparent_source_midpoints=false,extended_edge_pixels=len(extensions),max_edge_extension_px=max((e['distance'] for e in extensions),default=0),edge_extension_map=extensions,retained_original_effect=dict(source_bank_sha256=row['source_bank']['sha256'],source_indices_sha256=row['indices_sha256'],source_component_contract=str(components_path.relative_to(ROOT)),source_component_contract_sha256=sha(components_path),photographic_source_cells=201,retained_source_cells=len(retained),retained_cells=sorted([list(xy) for xy in retained]),method='Eksakt originalRGBA og4x-naermeste alfa i adskilte kildeceller. Ingen foto-/nytegningspaastand for bevegelsesbuen.',native_source_observation=str((ART/'balok/probes/original-arc029-v1/source-observation.json').relative_to(ROOT))))
    (out/'art-record.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(path=str(out.relative_to(ROOT)),candidate_sha256=sha(candidate),raw_iou=iou,photo_cells=201,retained_original_effect_cells=len(retained),midpoint_errors=len(missing)+len(false))))

if __name__=='__main__':main()
