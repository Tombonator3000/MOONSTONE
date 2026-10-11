#!/usr/bin/env python3
"""Bygg originaltro UI-konturer separat fra den aktive HD-pakken.

Dette er kantutjevning av originale UI-former og bokstavformer, ikke
fotografisk nytegning. Pergament og tre vinranker beholder kildefargene;
egen materialnytegning gjenstaar for disse fire rutene.
"""
import hashlib
import json
import argparse
from pathlib import Path
from collections import defaultdict

from PIL import Image, ImageDraw
import hd_ikoner_bygg as kontur
import moonfiles as mf

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT/'art/hd-ui-followup-2026-10-11'
BASE_ART = ART
SELECTIONS = {
    'mi.c': list(range(21, 29)) + [30, 32],
    'ki.cel': [34, 35, 36] + list(range(38, 45)),
    'sel.cel': [1],
}


def ui_contours(px, w, h, accept):
    """Forbind diagonale UI-stroek uten aa flytte kildepikselmidtpunkter.

    De tynne originalkonturene bruker diagonalt tilstoetende piksler som ett
    sammenhengende pennestroek. Det tvetydige marching-squares-tilfellet skal
    derfor ha sammenhengende forgrunn, ikke separate perler.
    """
    cases = {1: [(3, 0)], 2: [(0, 1)], 3: [(3, 1)], 4: [(1, 2)],
             5: [(3, 2), (0, 1)], 6: [(0, 2)], 7: [(3, 2)], 8: [(2, 3)],
             9: [(0, 2)], 10: [(3, 0), (1, 2)], 11: [(1, 2)],
             12: [(3, 1)], 13: [(0, 1)], 14: [(3, 0)]}
    edges = defaultdict(list)
    def yes(x, y):
        return 0 <= x < w and 0 <= y < h and accept(px[y*w+x])
    for y in range(-1, h):
        for x in range(-1, w):
            code = sum(1 << i for i, (dx, dy) in enumerate([(0, 0), (1, 0), (1, 1), (0, 1)]) if yes(x+dx, y+dy))
            pts = [(2*x+2, 2*y+1), (2*x+3, 2*y+2), (2*x+2, 2*y+3), (2*x+1, 2*y+2)]
            for a, b in cases.get(code, []):
                edges[pts[a]].append(pts[b]); edges[pts[b]].append(pts[a])
    loops = []
    while edges:
        start = cur = next(iter(edges)); loop = []
        while True:
            loop.append(cur); nxt = edges[cur].pop()
            if not edges[cur]:
                del edges[cur]
            edges[nxt].remove(cur)
            if not edges[nxt]:
                del edges[nxt]
            cur = nxt
            if cur == start:
                break
        keep = []
        for i, p in enumerate(loop):
            a, b = loop[i-1], loop[(i+1) % len(loop)]
            if (p[0]-a[0])*(b[1]-p[1]) != (p[1]-a[1])*(b[0]-p[0]):
                keep.append(p)
        if len(keep) >= 3:
            loops.append([(x/2, y/2) for x, y in keep])
    def fmt(x):
        return f'{x:.4f}'.rstrip('0').rstrip('.')
    parts = []
    for points in loops:
        joins = []
        for i, b in enumerate(points):
            a, c = points[i-1], points[(i+1) % len(points)]
            def near(v):
                dx, dy = v[0]-b[0], v[1]-b[1]
                length = (dx*dx+dy*dy)**.5
                f = min(.12, length*.2)/length
                return b[0]+dx*f, b[1]+dy*f
            joins.append((near(a), b, near(c)))
        p = joins[-1][2]
        s = f'M{fmt(p[0])} {fmt(p[1])}'
        for a, b, c in joins:
            s += f'L{fmt(a[0])} {fmt(a[1])}Q{fmt(b[0])} {fmt(b[1])} {fmt(c[0])} {fmt(c[1])}'
        parts.append(s+'Z')
    return ''.join(parts)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def identity(bank, frame):
    if bank == 'mys.cel':
        if frame in (0, 1):
            return ('donation-purse', 'Donasjonssekk hos '+('mystikeren' if frame == 0 else 'healeren'),
                    'disasm/mog.s:089b02..089b04;089d6c..089d6e;089fd8..08a01e',
                    'source-contour-material-pending')
        return ('donation-ui', {2: 'Exit', 3: 'OK', 4: 'Pil mot venstre', 5: 'Pil mot hoeyre'}[frame],
                'disasm/mog.s:08a024..08a07e', 'source-bound-ui-contours')
    if bank == 'dice.cel':
        return ('dragon-dice-outcome', 'Dragon Dice-utfall '+str(frame),
                'disasm/mog.s:08a600..08a690', 'source-contour-material-pending')
    if bank == 'mi.c':
        if frame == 32:
            return ('message-panel', 'Pergamentfelt for tur og valg paa kartet',
                    'disasm/mog.s:0abc5c..0abd6c', 'source-contour-material-pending')
        return ('selection-outline', 'Pulserende kartkontur for sted/hjemsted',
                'disasm/mog.s:080e8e..080f56', 'source-bound-ui-contours')
    if bank == 'sel.cel':
        return ('selection-frame', 'Rektangulaer riddervalgmarkering',
                'Original sel.cel/001: bare indeks15 i en 64x76 ramme',
                'source-bound-ui-contours')
    if frame in (34, 35, 36):
        return ('vine-fragment', 'Inventarets vinranke, separat speilbart fragment',
                'disasm/mog.s:08ae50..08af24', 'source-contour-material-pending')
    words = {38: 'STR:', 39: 'CON:', 40: 'END:', 41: 'XP:', 42: 'GOLD:',
             43: 'HIT:', 44: 'NEXT KNIGHT'}
    return ('text-label', words[frame],
            'disasm/mog.s:08af44..08b34a;08cace..08cbd6',
            'source-bound-ui-contours')


def main():
    global ART
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--additional', action='store_true', help='Bygg donasjons-UI og seks Dragon Dice-utfall i egen undermappe.')
    args = ap.parse_args()
    selections = ({'mys.cel': list(range(6)), 'dice.cel': list(range(6))} if args.additional else SELECTIONS)
    if args.additional:
        ART = BASE_ART/'additional'
    ART.mkdir(parents=True, exist_ok=True)
    kontur.ART = ART
    kontur.contours = ui_contours
    game = mf.Spill(str(ROOT/'Moonstonecd32-AMIGA.zip'))
    reference = ROOT/'art/hd-remaining-icons-2026-10-11/research/runtime/source-contracts.json'
    palettes = json.loads(reference.read_text())['palettes']
    _, rawpal, _ = mf.piv_alle(game.les('ch.piv'))[0][0]
    palette_selection = [mf.amiga_rgb(c) for c in rawpal]
    piv_palettes = {}
    if args.additional:
        for name in ('mys.piv', 'hea.piv', 'dice.piv'):
            _, raw, _ = mf.piv_alle(game.les(name))[0][0]
            piv_palettes[name] = [mf.amiga_rgb(c) for c in raw]
    entries, contracts, banks = [], [], {}
    for bank, frames in selections.items():
        data = game.les(bank)
        banks[bank] = sha(data)
        source_frames, _ = mf.cel_les(data)
        for frame in frames:
            if bank == 'mys.cel':
                pal_name = 'hea.piv' if frame == 1 else 'mys.piv'
                palette = piv_palettes[pal_name]
                variants = [dict(id=name.split('.')[0], palette=piv_palettes[name]) for name in
                            (('mys.piv', 'hea.piv') if frame in (2, 3, 4, 5) else (pal_name,))]
            elif bank == 'dice.cel':
                palette = piv_palettes['dice.piv']
                variants = []
            else:
                palette = (palette_selection if bank == 'sel.cel' else
                           palettes['map' if bank == 'mi.c' else 'inventory']['palette'])
                variants = []
            f = source_frames[frame]
            w, h = f['bredde'], f['hoyde']
            packed = mf.plan_til_indeks(f['data'], f['plan'], w, h)
            bits = [1 << b for b in range(5) if f['maske'] & (1 << b)]
            px = [sum(bit for p, bit in enumerate(bits) if v & (1 << p)) for v in packed]
            key = f'{bank}/{frame:03}'
            source = dict(file=bank, frame=frame, bank_sha256=sha(data))
            category, meaning, evidence, quality = identity(bank, frame)
            meta = kontur.make_entry(key, px, w, h, palette, source,
                                    plane_mask=f['maske'], render_mode='contours')
            entries.append(meta)
            contracts.append(dict(key=key, source=source, width=w, height=h,
                                  plane_mask=f['maske'], packed_planes=f['plan'],
                                  expanded_plane_bits=bits, indices=px,
                                  indices_sha256=sha(bytes(px)), palette=palette,
                                  source_colors=sorted(set(px)-{0}), category=category,
                                  meaning=meaning, evidence=evidence,
                                  quality_status=quality,
                                  live_palette=31 in px))
            if args.additional:
                contracts[-1] = {k: v for k, v in contracts[-1].items() if k != 'live_palette'} | {'alternate_palettes': variants, 'live_palette': 31 in px}
            im = Image.new('RGBA', (w, h))
            im.putdata([tuple(palette[c][:3])+(255 if c else 0,) for c in px])
            path = ART/'references'/f'{key}.png'
            path.parent.mkdir(parents=True, exist_ok=True)
            im.resize((w*8, h*8), Image.Resampling.NEAREST).save(path)
    active_bytes = (ROOT/'web/hd/icons.json').read_bytes()
    active = json.loads(active_bytes)
    old = {m['key']: m for m in active['entries']}
    own_keys = {m['key'] for m in entries}
    previous_source = ART/'source-contracts.json'
    previous_candidate = ART/'candidate-icons.json'
    previous_fragment = ART/'fragment-icons.json'
    baseline_sha = sha(active_bytes)
    baseline = active
    if previous_source.exists():
        # Gjenbygg mot den frosne opprinnelige baselinen, ikke mot egne
        # allerede aktiverte UI-ruter eller senere materialleveranser.
        previous = json.loads(previous_source.read_text())
        candidate_bytes = previous_candidate.read_bytes()
        assert sha(candidate_bytes) == previous['candidate_icons_sha256'], 'Frosset kandidat endret'
        prior_fragment = json.loads(previous_fragment.read_text())
        prior_keys = {m['key'] for m in prior_fragment['entries']}
        assert prior_keys == own_keys, 'Utvalget er endret; bruk en ny artmappe'
        baseline = json.loads(candidate_bytes)
        baseline['entries'] = [m for m in baseline['entries'] if m['key'] not in prior_keys]
        baseline_sha = previous['baseline_icons_sha256']
        frozen_rasters = {m['key']: m for m in baseline['entries'] if m.get('render_mode') == 'raster'}
        assert len(frozen_rasters) == previous['baseline_raster_count']
        assert sha(json.dumps([frozen_rasters[k] for k in sorted(frozen_rasters)], sort_keys=True).encode()) == previous['baseline_raster_sha256']
        assert all(old.get(k) == m for k, m in frozen_rasters.items()), 'Et tidligere rasterikon er endret'
    else:
        assert not set(old) & own_keys, 'Nytt utvalg overlapper aktive ikoner'
    baseline_entries = {m['key']: m for m in baseline['entries']}
    raster_count = sum(m.get('render_mode') == 'raster' for m in baseline['entries'])
    fragment = dict(schema=1, method='source-bound-ui-contours', banks=banks, entries=entries)
    (ART/'fragment-icons.json').write_text(json.dumps(fragment, ensure_ascii=False, indent=2)+'\n')
    combined = dict(baseline)
    combined['banks'] = {**baseline.get('banks', {}), **banks}
    combined['entries'] = sorted(baseline['entries']+entries, key=lambda m: m['key'])
    (ART/'candidate-icons.json').write_text(json.dumps(combined, ensure_ascii=False, separators=(',', ':'))+'\n')
    report = dict(scope='UI-kantutjevning med originale former. Ingen fotografisk materialgodkjenning.',
                  original_zip_sha256=sha((ROOT/'Moonstonecd32-AMIGA.zip').read_bytes()),
                  baseline_icons_sha256=baseline_sha,
                  baseline_raster_count=raster_count,
                  baseline_raster_sha256=sha(json.dumps([baseline_entries[k] for k in sorted(baseline_entries) if baseline_entries[k].get('render_mode') == 'raster'], sort_keys=True).encode()),
                  candidate_icons_sha256=sha((ART/'candidate-icons.json').read_bytes()),
                  banks=banks, entries=contracts)
    (ART/'source-contracts.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(dict(assets=len(entries), ui_ready=sum(c['quality_status']=='source-bound-ui-contours' for c in contracts),
                          material_pending=sum(c['quality_status']=='source-contour-material-pending' for c in contracts))))


if __name__ == '__main__':
    main()
