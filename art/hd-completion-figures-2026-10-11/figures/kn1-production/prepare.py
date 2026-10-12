"""Frys originalens form og sourcekontrakt for KN1-kandidatene."""
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path

ART = Path(__file__).resolve().parent
ROOT = ART.parents[3]
FIGURES = ART.parents[1]
sys.path.insert(0, str(ROOT/'tools'))
import moonfiles as mf
from hd_ui_bygg import ui_contours
from hd_bestilling import utvid_indekser

sha = lambda b: hashlib.sha256(b).hexdigest()

def figure_contours(indices, w, h, accept):
    """Bevar opakt areal og ditherhull; avrund bare kildegridets hjoerner."""
    edges = defaultdict(list)
    yes = lambda x, y: 0 <= x < w and 0 <= y < h and accept(indices[y*w+x])
    for y in range(h):
        for x in range(w):
            if not yes(x, y): continue
            for neighbor, a, b in [((x,y-1),(x,y),(x+1,y)), ((x+1,y),(x+1,y),(x+1,y+1)),
                                    ((x,y+1),(x+1,y+1),(x,y+1)), ((x-1,y),(x,y+1),(x,y))]:
                if not yes(*neighbor): edges[a].append(b)
    loops = []
    directions = {(1,0): 0, (0,1): 1, (-1,0): 2, (0,-1): 3}
    while edges:
        start = cur = next(iter(edges)); previous = None; loop = []
        while True:
            loop.append(cur)
            options = edges[cur]
            if previous is None: nxt = options[0]
            else:
                before = directions[(cur[0]-previous[0], cur[1]-previous[1])]
                turn = lambda p: (directions[(p[0]-cur[0],p[1]-cur[1])]-before) % 4
                nxt = min(options, key=lambda p: {1:0,0:1,3:2,2:3}[turn(p)])
            options.remove(nxt)
            if not options: del edges[cur]
            previous, cur = cur, nxt
            if cur == start: break
        keep = [p for i,p in enumerate(loop) if (p[0]-loop[i-1][0])*(loop[(i+1)%len(loop)][1]-p[1]) != (p[1]-loop[i-1][1])*(loop[(i+1)%len(loop)][0]-p[0])]
        loops.append(keep)
    fmt = lambda n: f'{n:.4f}'.rstrip('0').rstrip('.')
    paths = []
    for loop in loops:
        joins = []
        for i,b in enumerate(loop):
            def near(a):
                dx,dy=a[0]-b[0],a[1]-b[1];length=(dx*dx+dy*dy)**.5;f=min(.12,length*.2)/length
                return b[0]+dx*f,b[1]+dy*f
            joins.append((near(loop[i-1]),b,near(loop[(i+1)%len(loop)])))
        start = joins[-1][2]
        paths.append(f'M{fmt(start[0])} {fmt(start[1])}'+''.join(f'L{fmt(a[0])} {fmt(a[1])}Q{fmt(b[0])} {fmt(b[1])} {fmt(c[0])} {fmt(c[1])}' for a,b,c in joins)+'Z')
    return ''.join(paths)

queue = json.loads((ART/'queue-subset.json').read_text())
game = mf.Spill(str(ROOT/'Moonstonecd32-AMIGA.zip'))
game_files = {k.lower(): v for k, v in game.filer.items()}
entries = []
for q in queue['entries']:
    if q['role'] != 'redraw':
        continue
    bank = game_files[q['source_bank']['path'].lower()]
    assert sha(bank) == q['source_bank']['sha256'], q['key']
    frames, _ = mf.cel_les(bank)
    f = frames[q['frame']]
    packed = mf.plan_til_indeks(f['data'], f['plan'], q['width'], q['height'])
    assert f['maske'] == q['plane_mask']
    indices = utvid_indekser(packed, f['maske'])
    assert sha(indices) == q['indices_sha256'], q['key']
    original = FIGURES/q['original']['path']
    assert sha(original.read_bytes()) == q['original']['sha256'], q['key']
    entries.append({**q, 'indices': list(indices),
                    'blood_path': figure_contours(indices, q['width'], q['height'], lambda i:i==15) if 15 in indices else None,
                    'clip': figure_contours(indices, q['width'], q['height'], bool),
                    'dark_paths': [{'index': i, 'd': figure_contours(indices, q['width'], q['height'], lambda p: p == i)}
                                   for i in (5,) if i in indices]})
(ART/'source-contracts.json').write_text(json.dumps({'schema': 1, 'entries': entries,
    'queue_sha256': queue['queue_sha256'], 'scope': 'Originalens planmaske, indeksverdier og alfakontur. Kampforhaandsvisning er ingen fargegodkjenning.'}, indent=2)+'\n')
print(json.dumps({'contracts': len(entries)}))
