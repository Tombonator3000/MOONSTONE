"""Source-pixel midpoint preserving marching squares; .4px rounded corners.
Adapted from tools/hd_ui_bygg.py. Runtime midpoint checks remain mandatory.
"""
from collections import defaultdict

def source_contours(px, w, h, accept):
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
                f = min(.4, length*.45)/length
                return b[0]+dx*f, b[1]+dy*f
            joins.append((near(a), b, near(c)))
        p = joins[-1][2]
        s = f'M{fmt(p[0])} {fmt(p[1])}'
        for a, b, c in joins:
            s += f'L{fmt(a[0])} {fmt(a[1])}Q{fmt(b[0])} {fmt(b[1])} {fmt(c[0])} {fmt(c[1])}'
        parts.append(s+'Z')
    return ''.join(parts)
