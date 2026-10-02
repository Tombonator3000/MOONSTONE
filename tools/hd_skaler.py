#!/usr/bin/env python3
"""
hd_skaler.py INN UT [--ganger 2|4] - lager en HD-pakke ved aa skalere pikselgrafikk.

INN er en mappe med PNG-er slik tools/gfx.py extract gir dem (kn1.ob/012.png osv.),
eller bakgrunner fra moonstone-headless --lag-dump / "Lagre bakgrunnen som PNG"
(legg dem i INN/bg). UT faar samme mapper og navn, med bildene skalert med Scale2x
(EPX), en eller to ganger. Scale2x runder av trappetrinn paa skraa kanter uten aa
blande nye farger, saa pikselstilen beholdes. Gjennomsiktighet (alfa) beholdes.

Resultatet er et utgangspunkt: velg UT-mappen under "HD-grafikk" paa nettsiden, og
tegn over de bildene du vil forbedre for haand.

Krever Pillow (pip install pillow).
"""
import argparse
import os
import sys

from PIL import Image


def scale2x(im):
    """Scale2x (EPX) paa et RGBA-bilde: hver piksel blir fire, kantene rundes av."""
    w, h = im.size
    src = im.load()
    out = Image.new('RGBA', (w * 2, h * 2))
    dst = out.load()
    for y in range(h):
        for x in range(w):
            p = src[x, y]
            a = src[x, y - 1] if y > 0 else p          # opp
            b = src[x + 1, y] if x < w - 1 else p      # hoyre
            c = src[x - 1, y] if x > 0 else p          # venstre
            d = src[x, y + 1] if y < h - 1 else p      # ned
            e0 = e1 = e2 = e3 = p
            if c == a and c != d and a != b:
                e0 = a
            if a == b and a != c and b != d:
                e1 = b
            if d == c and d != b and c != a:
                e2 = c
            if b == d and b != a and d != c:
                e3 = d
            dst[2 * x, 2 * y] = e0
            dst[2 * x + 1, 2 * y] = e1
            dst[2 * x, 2 * y + 1] = e2
            dst[2 * x + 1, 2 * y + 1] = e3
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('inn')
    ap.add_argument('ut')
    ap.add_argument('--ganger', type=int, default=4, choices=(2, 4))
    ap.add_argument('--bare', nargs='*', help='bare disse mappene (f.eks. bold.f Small.font bg)')
    a = ap.parse_args()
    n = 0
    for mappe in sorted(os.listdir(a.inn)):
        kilde = os.path.join(a.inn, mappe)
        if not os.path.isdir(kilde):
            continue
        if a.bare and mappe.lower() not in [b.lower() for b in a.bare]:
            continue
        maal = os.path.join(a.ut, mappe)
        os.makedirs(maal, exist_ok=True)
        for f in sorted(os.listdir(kilde)):
            if not f.lower().endswith('.png'):
                continue
            im = Image.open(os.path.join(kilde, f)).convert('RGBA')
            im = scale2x(im)
            if a.ganger == 4:
                im = scale2x(im)
            im.save(os.path.join(maal, f))
            n += 1
    print('%d bilder skalert til %s' % (n, a.ut), file=sys.stderr)


if __name__ == '__main__':
    main()
