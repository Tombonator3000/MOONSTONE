#!/usr/bin/env python3
"""Bind generert gullmateriale til original bold.f/073; ingen aktivering."""
from collections import Counter
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw
import hd_bestilling as order
from hd_ui_bygg import ui_contours
import moonfiles as mf

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT/'art/hd-completion-backgrounds-2026-10-11'
OUT = ART/'logo'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def save(path, image):
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, optimize=True)
    return dict(path=str(path.relative_to(OUT)), sha256=sha(path.read_bytes()), width=image.width, height=image.height)


def freeze(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        assert path.read_bytes() == data, str(path)+' er endret'
    else:
        path.write_bytes(data)


def bounds(px, w, predicate):
    pts = [i for i, v in enumerate(px) if predicate(i//w, v)]
    return [min(i % w for i in pts), min(i//w for i in pts), max(i % w for i in pts)+1, max(i//w for i in pts)+1]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    game = mf.Spill(str(ROOT/'Moonstonecd32-AMIGA.zip'))
    raw_bank, raw_palette = game.les('bold.f'), game.les('ch.piv')
    source = mf.cel_les(raw_bank)[0][73]
    w, h = source['bredde'], source['hoyde']
    assert (w, h) == (305, 54)
    packed = mf.plan_til_indeks(source['data'], source['plan'], w, h)
    px = list(order.utvid_indekser(packed, source['maske']))
    palette = [mf.amiga_rgb(v) for v in mf.piv_alle(raw_palette)[0][0][1]]
    freeze(OUT/'source/bold.f', raw_bank)
    freeze(OUT/'source/ch.piv', raw_palette)
    original = Image.new('RGBA', (w, h))
    original.putdata([tuple(palette[v])+(255 if v else 0,) for v in px])
    with Image.open(ART/'references/logo.png') as supplied:
        assert supplied.mode == 'RGBA' and supplied.tobytes() == original.tobytes(), 'Referansen avviker fra originalbank+palett'
    original_record = save(OUT/'source/original.png', original)
    save(OUT/'source/nearest4x-reference.png', original.resize((w*4, h*4), Image.Resampling.NEAREST))
    paths = dict(alpha=ui_contours(px, w, h, lambda c: c != 0),
                 face=ui_contours(px, w, h, lambda c: c not in (0, 5)),
                 shadow=ui_contours(px, w, h, lambda c: c == 5))
    for kind, shape in paths.items():
        (OUT/(kind+'.svg')).write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="1220" height="216" viewBox="0 0 305 54"><path d="{shape}" fill="white" fill-rule="evenodd"/></svg>\n')
    most = Counter(v for v in px if v not in (0, 5)).most_common(1)[0][0]
    # Originalens flater styrer lysplasseringen; materialets farger er dempet gull.
    # Den brede hvite kildeflaten blir lys gull, ikke hvit glitrende metallfolie.
    gold_palette = {1:(226,205,147), 4:(77,66,46), 6:(52,43,30),
                    9:(243,223,177), 10:(198,164,90), 11:(151,112,49), 12:(96,66,31)}
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="1220" height="216" viewBox="0 0 305 54">',
           '<defs><clipPath id="face"><path d="'+paths['face']+'" clip-rule="evenodd"/></clipPath></defs>',
           '<g clip-path="url(#face)">',
           '<path d="'+paths['face']+'" fill="rgb('+','.join(map(str, gold_palette[most]))+')" fill-rule="evenodd"/>']
    for color in sorted(set(px)-{0, 5}):
        svg.append('<path d="'+ui_contours(px, w, h, lambda c: c == color)+'" fill="rgb('+','.join(map(str, gold_palette[color]))+')" fill-rule="evenodd"/>')
    svg.append('</g></svg>')
    (OUT/'tone.svg').write_text('\n'.join(svg)+'\n')
    # Bare et sammenhengende fotografisk gullfelt hentes fra råkandidaten.
    # Bokstavform, omriss, hull og undertekst fra råkandidaten brukes aldri.
    raw_path = ART/'raw/logo-v1.png'
    raw = Image.open(raw_path).convert('RGBA')
    rw, rh = raw.size
    rgba = list(raw.getdata())
    valid = [a >= 240 and r >= g >= b and r-g < 120 and g-b > 12 and r > 90
             for r, g, b, a in rgba]
    integral = [0]*((rw+1)*(rh+1))
    for y in range(rh):
        row = 0
        for x in range(rw):
            row += valid[y*rw+x]
            integral[(y+1)*(rw+1)+x+1] = integral[y*(rw+1)+x+1]+row
    chosen = None
    for size in (64, 48, 40, 32, 24, 16):
        for y in range(0, rh-size, 4):
            for x in range(0, rw-size, 4):
                count = integral[(y+size)*(rw+1)+x+size]-integral[y*(rw+1)+x+size]-integral[(y+size)*(rw+1)+x]+integral[y*(rw+1)+x]
                if count == size*size:
                    chosen = [x, y, size, size]
                    break
            if chosen:
                break
        if chosen:
            break
    assert chosen, 'Fant ikke rent gullmateriale uten råkandidatens konturer'
    x, y, tw, th = chosen
    texture = raw.crop((x, y, x+tw, y+th)).convert('RGB')
    texture_record = save(OUT/'source/gold-material.png', texture)
    gray = texture.convert('L')
    mean = sum(gray.getdata())/(tw*th)
    gain = [max(.94, min(1.06, 1+(v/mean-1)*.18)) for v in gray.getdata()]
    contract = dict(schema=1, key='bold.f/073.png', status='source_bound_material_candidate_not_activated',
        method='original_source_contours_with_generated_gold_material', target=[1220,216], source_size=[w,h], scale=4,
        source_zip_sha256=sha((ROOT/'Moonstonecd32-AMIGA.zip').read_bytes()),
        bank_sha256=sha(raw_bank), palette_bank_sha256=sha(raw_palette), bitplane_sha256=sha(source['data']),
        plane_mask=source['maske'], indices_sha256=sha(bytes(px)), indices=px, palette=palette,
        original=original_record, raw_material_sha256=sha(raw_path.read_bytes()), raw_material_source=str(raw_path.relative_to(ROOT)),
        material_patch=chosen, material=texture_record, material_gain=gain, gold_palette=gold_palette,
        material_policy='Only source-contained low-contrast luminance grain; no raw lettering or alpha used. Original index regions retain their light/shadow roles.',
        source_main_reference_rect=[0,0,305,38], source_subtitle_reference_rect=[55,36,242,54],
        reference_rect_policy='Overlapping inspection areas only. No cutting, resizing or relocation of either text line.',
        geometry_policy='Original source pixel midpoints and face/shadow regions; source corner rounding <=0.12 pixel',
        proposed_text_metadata=dict(file='bold.f',frame=73,path='bold.f/073.png',raw_rect_px=[0,0,1220,216],draw_rect=[0,0,305,54]),
        activation=False)
    (OUT/'contract.json').write_text(json.dumps(contract,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:contract[k] for k in ('key','target','material_patch','activation')}))


if __name__ == '__main__':
    main()
