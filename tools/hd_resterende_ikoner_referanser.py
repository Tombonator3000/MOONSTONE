#!/usr/bin/env python3
"""Skriv originale KI/MI-referanser og kildekontrakter uten aa endre HD-pakken.

PNG-ene er eksplisitte originalreferanser, ikke HD-nytegninger. Bitplanmasken
utvides til skjermindekser foer paletten slaas opp. MI bruker kartpaletten;
inventarpaletten gir feil spillerfarger og misvisende kartmotiver.
"""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from PIL import Image, ImageDraw
import moonfiles as mf

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT / 'art/hd-remaining-icons-2026-10-11/research/runtime'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def classify(bank, frame):
    if bank == 'ki.cel':
        if frame in (34, 35, 36):
            return 'decor-fragment', 'Inventarets vinranke, eget fragment med speiling', '08aeac..08af24'
        if 38 <= frame <= 43:
            names = ['STR:', 'CON:', 'END:', 'XP:', 'GOLD:', 'HIT:']
            return 'text-label', names[frame-38], '08af44..08b34a'
        if frame == 44:
            return 'text-label', 'NEXT KNIGHT', '08cace..08cbd6'
        if 45 <= frame <= 49:
            return 'moon-phase', 'Neste dag, eksisterende maanefase', '082b46..082ba6'
        return 'inventory-object', 'Inventargjenstand eller inventarens soeyle', '08af44..08bb76'
    if 0 <= frame <= 4:
        return 'map-knight-token', 'Ridderens kartbrikke, fargevariant '+str(frame), '0aab0a..0aab5e'
    if 5 <= frame <= 9:
        return 'map-knight-token', 'Aktiv ridder, pulskant, fargevariant '+str(frame-5), '0aaab0..0aab08;0810a6..0810d2'
    if 10 <= frame <= 14:
        return 'map-gem-token', 'Gem of Seeing, krystalkule paa ridderens sokkel, fargevariant '+str(frame-10), '0aaab0..0aab08'
    if 15 <= frame <= 18:
        return 'map-hawk-marker', 'Scroll of the Hawk, korsformet teleporteringsmaal, fargevariant '+str(frame-15), '0aaab0..0aab08'
    if frame in (19, 29):
        return 'empty', 'Tom plass i originalbanken, skal ikke tegnes', None
    if frame == 20:
        return 'map-site-marker', 'Stedsmarkoer uten pulskant', '0aab60..0aabbc'
    if 21 <= frame <= 28:
        return 'map-interaction-outline', 'Kontur for kartsted eller ridderens hjemsted', '080e8e..080f56;080ef0..080f28'
    if frame == 30:
        return 'map-interaction-outline', 'Smal kontur for kartsted', '080e8e..080f56'
    if frame == 31:
        return 'map-site-marker', 'Stedsmarkoer med pulskant', '08102e..081098'
    if frame == 32:
        return 'map-message-panel', 'Kartets tur-/interaksjonsmeldingsfelt', '0abc5c..0abd6c'
    if frame == 33:
        return 'map-grave-token', 'Doed annen ridders gravkors', '0aab0a..0aab5e'
    if 34 <= frame <= 41:
        return 'map-dragon-animation', 'Flygende drage, animasjonsrute '+str(frame-34), '0ab164..0ab244;096bc2'
    if frame == 42:
        return 'map-grave-token', 'Doed aktiv ridders gravkors', '0810a6..0810d2'
    return 'map-toad-token', 'Maths forvandlede ridder som statisk paddebrikke, fargevariant '+str(frame-43), '0aab0a..0aab5e'


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output', type=Path, default=DEFAULT)
    args = ap.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    game = mf.Spill(str(ROOT/'Moonstonecd32-AMIGA.zip'))
    piv_palettes = {}
    for name in ('ch.piv','tav.piv','test'):
        frames, _ = mf.piv_alle(game.les(name))
        piv_palettes[name] = [[mf.amiga_rgb(c) for c in pal] for _,pal,_ in frames]
    (out/'piv-palettes.json').write_text(json.dumps(piv_palettes,separators=(',',':'))+'\n')
    icon_meta = json.loads((ROOT/'web/hd/icons.json').read_text())
    active_icons = {m['key']: m for m in icon_meta['entries']}
    active_png = {f['path'] for f in json.loads((ROOT/'web/hd/manifest.json').read_text())['files']}
    palettes = {
        'inventory': json.loads((ROOT/'art/hd-icons-2026-10-11/source/inventory-palette.json').read_text()),
        'map': json.loads((ROOT/'art/hd-icons-2026-10-11/source/map-frame2000.json').read_text()),
    }
    result = {'scope': 'Originalreferanser og teknisk ruteaudit. Ikke nye HD-bilder, ikke runtimebevis for alle ruter.',
              'manifest_sha256': sha((ROOT/'web/hd/manifest.json').read_bytes()),
              'original_zip_sha256': sha((ROOT/'Moonstonecd32-AMIGA.zip').read_bytes()),
              'palettes': {}, 'banks': {}, 'entries': []}
    for name, record in palettes.items():
        result['palettes'][name] = {k: record[k] for k in ('frame', 'state', 'palette', 'lag')}
    for bank in ('ki.cel', 'mi.c'):
        data = game.les(bank)
        result['banks'][bank] = sha(data)
        frames, _ = mf.cel_les(data)
        pal_name = 'inventory' if bank == 'ki.cel' else 'map'
        palette = palettes[pal_name]['palette']
        for frame, g in enumerate(frames):
            w, h = g['bredde'], g['hoyde']
            packed = mf.plan_til_indeks(g['data'], g['plan'], w, h)
            bits = [1 << b for b in range(5) if g['maske'] & (1 << b)]
            px = bytes(sum(bit for p, bit in enumerate(bits) if value & (1 << p)) for value in packed)
            positions = [(i % w, i // w) for i, c in enumerate(px) if c]
            bounds = ([min(x for x, y in positions), min(y for x, y in positions),
                       max(x for x, y in positions)+1, max(y for x, y in positions)+1] if positions else None)
            key = f'{bank}/{frame:03}'
            category, meaning, asm = classify(bank, frame)
            old_55 = (bank == 'ki.cel' and frame in [34,35,36,38,39,40,41,42,43,44]) or (bank == 'mi.c' and g['maske'] != 0)
            entry = dict(key=key, source=dict(file=bank, frame=frame, bank_sha256=sha(data)),
                         width=w, height=h, scale=8, plane_mask=g['maske'],
                         packed_planes=g['plan'], expanded_plane_bits=bits, flag=g['flagg'],
                         indices_sha256=sha(px), indices=list(px), bounds=bounds,
                         source_nontransparent_pixels=len(positions), source_colors=sorted(set(px)-{0}),
                         source_palette=pal_name, category=category, meaning=meaning, disassembly=asm,
                         active_png=f'{key}.png' in active_png, active_icon_contract=key in active_icons,
                         included_in_previous_55_missing=old_55,
                         reference_palette={str(c):palette[c][:3] for c in sorted(set(px)-{0})})
            if positions:
                im = Image.new('RGBA', (w,h))
                im.putdata([tuple(palette[c][:3])+(255 if c else 0,) for c in px])
                file = Path('references') / f'{key}.png'
                target = out/file
                target.parent.mkdir(parents=True, exist_ok=True)
                im.resize((w*8,h*8), Image.Resampling.NEAREST).save(target)
                entry['reference_png'] = str(file)
            result['entries'].append(entry)
    missing = [e for e in result['entries'] if e['included_in_previous_55_missing']]
    assert len(missing) == 55, len(missing)
    result['previous_55_categories'] = dict(Counter(e['category'] for e in missing))
    result['missing_contracts'] = [e['key'] for e in missing if not e['active_icon_contract']]
    (out/'source-contracts.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    helmets=[]
    for frame in range(10):
        row=next(e for e in result['entries'] if e['key']==f'mi.c/{frame:03}');pal=palettes['map']['palette']
        mask=bytes(int(c not in(0,19,31)) for c in row['indices']);positions=[(i%row['width'],i//row['width']) for i,c in enumerate(mask) if c]
        bounds=[min(x for x,y in positions),min(y for x,y in positions),max(x for x,y in positions)+1,max(y for x,y in positions)+1]
        im=Image.new('RGBA',(row['width'],row['height']));im.putdata([tuple(pal[c][:3])+(255 if keep else 0,) for c,keep in zip(row['indices'],mask)])
        file=f'helmet-body-{frame:03}.png';im.resize((row['width']*16,row['height']*16),Image.Resampling.NEAREST).save(out/file)
        helmets.append(dict(key=row['key'],body_bounds=bounds,body_mask_sha256=sha(mask),preserve_indices=[19] if frame<5 else [19,31],reference=file,reference_palette=row['reference_palette']))
    assert len({v['body_mask_sha256'] for v in helmets})==1,'Hjelmenes kroppsgeometri har endret seg'
    (out/'helmet-body-contracts.json').write_text(json.dumps(helmets,indent=2)+'\n')
    # Gravkorset har original moerk ytterkant (19). Ny graa steinkropp
    # plasseres bare i de faktiske 2/3-bounds; kant og valgtpuls beholdes.
    graves=[]
    for frame in (33,42):
        row=next(e for e in result['entries'] if e['key']==f'mi.c/{frame:03}')
        positions=[(i%row['width'],i//row['width']) for i,c in enumerate(row['indices']) if c in (2,3)]
        bounds=[min(x for x,y in positions),min(y for x,y in positions),max(x for x,y in positions)+1,max(y for x,y in positions)+1]
        im=Image.new('RGBA',(row['width'],row['height']));pal=palettes['map']['palette']
        im.putdata([tuple(pal[c][:3])+(255 if c in(2,3) else 0,) for c in row['indices']])
        im.resize((row['width']*16,row['height']*16),Image.Resampling.NEAREST).save(out/f'grave-body-{frame:03}.png')
        graves.append(dict(key=row['key'],body_indices=[2,3],body_bounds=bounds,preserve_indices=[19] if frame==33 else [19,31],reference=f'grave-body-{frame:03}.png',shadow_pixels=row['indices'].count(19),pulse_pixels=row['indices'].count(31)))
    (out/'grave-body-contracts.json').write_text(json.dumps(graves,indent=2)+'\n')
    # Math-forvandlede kartbrikker er fire statiske objekter, ikke animasjon.
    # De har intern brun19 i oyne/munn og ingen31-valgkontur.
    toads=[]
    for frame,color in zip(range(43,47),(30,29,8,28)):
        row=next(e for e in result['entries'] if e['key']==f'mi.c/{frame:03}')
        assert row['width']==10 and row['height']==12 and 31 not in row['source_colors']
        assert [row['indices'][y*10+x] for y in(7,8) for x in(4,5)]==[color]*4
        assert [row['indices'][9*10+x] for x in(4,5)]==[18,18]
        toads.append(dict(key=row['key'],body_bounds=row['bounds'],reference=row['reference_png'],preserve_indices=[],stripe_rect=[4,7,2,2],stripe_index=color,stripe_rgb=row['reference_palette'][str(color)],fixed_brown_rect=[4,9,2,1],fixed_brown_rgb=row['reference_palette']['18']))
    (out/'map-toad-contracts.json').write_text(json.dumps(toads,indent=2)+'\n')
    # Egen teknisk rasterprobe: original kropp, transparent pulskant. Dette er
    # en kildefixture for rendererens vern, ikke en nytegnet leveranse.
    probe = next(e for e in result['entries'] if e['key']=='mi.c/009')
    px,w,h = probe['indices'],probe['width'],probe['height']
    colors = probe['source_colors']
    rectangles = lambda c: ''.join(f'M{i%w} {i//w}h1v1h-1Z' for i,v in enumerate(px) if v==c)
    meta = dict(key=probe['key'],width=w,height=h,scale=8,source=probe['source'],
                indices_sha256=probe['indices_sha256'],plane_mask=probe['plane_mask'],
                base_index=19,clip=''.join(rectangles(c) for c in colors),
                paths=[dict(index=c,d=rectangles(c)) for c in colors],
                render_mode='raster',reference_palette=probe['reference_palette'],preserve_indices=[31])
    (out/'mi009-preserved-probe-icons.json').write_text(json.dumps(dict(schema=1,entries=[meta]))+'\n')
    image = Image.new('RGBA',(w,h));pal=palettes['map']['palette']
    image.putdata([tuple(pal[c][:3])+(255 if c not in (0,31) else 0,) for c in px])
    image.resize((w*8,h*8),Image.Resampling.NEAREST).save(out/'mi009-preserved-probe.png')
    # Lille, laeselig kontaktflate med korrekt kartpalett. Kildebilder er urorte.
    for bank in ('ki.cel','mi.c'):
        rows = [e for e in result['entries'] if e['source']['file'] == bank and e.get('reference_png')]
        cw,ch = 192,180
        sheet = Image.new('RGB',(cw*8,ch*((len(rows)+7)//8)),(32,32,32))
        draw = ImageDraw.Draw(sheet)
        for i,e in enumerate(rows):
            x,y=(i%8)*cw,(i//8)*ch
            draw.text((x+6,y+5), e['key'],fill='white')
            im=Image.open(out/e['reference_png']).convert('RGBA')
            factor=min((cw-12)/im.width,(ch-30)/im.height,1)
            if factor<1: im=im.resize((max(1,round(im.width*factor)),max(1,round(im.height*factor))),Image.Resampling.NEAREST)
            sheet.paste(im,(x+6,y+25),im)
        sheet.save(out/f'{bank}-correct-palette-sheet.png')
    print(json.dumps({'entries':len(result['entries']),'previous_55':len(missing),
                      'categories':result['previous_55_categories'],'output':str(out)},ensure_ascii=False))


if __name__ == '__main__':
    main()
