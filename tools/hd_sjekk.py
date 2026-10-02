#!/usr/bin/env python3
"""
hd_sjekk.py - sjekker at tegnelisten plasserer figurene riktig.

HD-laget i nettleseren (docs/hd-grafikk.md) tegner bilder over Amiga-bildet
der tegnelisten sier at spillet tegnet en figur. Dette verktoyet kjorer
emulatoren uten vindu, henter tegnelisten og skjermbildene, legger de
utpakkede figurbildene (tools/gfx.py extract) oppaa der listen sier, og
regner ut hvor godt de treffer. Figurene har egne farger per skjerm, saa vi
sammenligner ikke farger direkte: for hver fargeindeks i figuren ser vi om
skjermen har samme farge overalt der indeksen brukes. 1.00 er treff paa
hver piksel. Piksler som en figur tegnet senere dekker, telles ikke.

Spillet tegner figurene for ett skjermbilde i bilder paa rad (i kamp den ene
ridderen i ett bilde og resten i det neste). Det ferdige bildet vises to bilder
etter det siste i klyngen. Det er den samme regelen som web/src/render.js bruker.

Bruk:
  python3 tools/hd_sjekk.py --gfx assets/gfx --state kamp.sav [--fra F] [--antall N]
      [--press F:HVA:LENGDE ...] [--spill Moonstonecd32-AMIGA.zip]

Lag en tilstand med figurer paa skjermen forst, f.eks. med --save-state i
moonstone-headless eller PageDown i PC-versjonen.
"""
import argparse
import os
import re
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict

from PIL import Image

ROT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FORSINKELSE = 2          # bilder fra siste tegning til den vises
DIW_X, DIW_Y = 70, 19    # spillvinduet i rammebufferet (hires-piksler, linjer)

LINJE = re.compile(r'\s+(\S*) bilde (\d+) x (-?\d+) y (-?\d+) \((\d+)x(\d+), xoff (\d+)(, speilet)?\)')


def piksler(figur, fx, fy, speilet):
    """(skjerm-x, skjerm-y, fargeindeks) for hver piksel som ikke er gjennomsiktig"""
    w, h = figur.size
    fp = figur.load()
    ut = []
    for j in range(h):
        for i in range(w):
            c = fp[w - 1 - i if speilet else i, j]
            if c:
                ut.append((fx + 2 * i, fy + j, c))
    return ut


def treff(skjerm, px, dekket):
    sp = skjerm.load()
    farger = defaultdict(Counter)
    n = 0
    for x, y, c in px:
        if (x, y) in dekket or not (0 <= x < skjerm.size[0] and 0 <= y < skjerm.size[1]):
            continue
        farger[c][sp[x, y]] += 1
        n += 1
    if not n:
        return None
    return sum(t.most_common(1)[0][1] for t in farger.values()) / n


def main():
    a = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument('--gfx', required=True, help='mappen fra tools/gfx.py extract')
    a.add_argument('--state', required=True, help='tilstand aa starte fra')
    a.add_argument('--spill', default=os.path.join(ROT, 'Moonstonecd32-AMIGA.zip'))
    a.add_argument('--fra', type=int, default=10, help='antall bilder etter starten foer vi begynner aa se')
    a.add_argument('--antall', type=int, default=40, help='antall bilder aa se paa')
    a.add_argument('--press', action='append', default=[], help='som i moonstone-headless (bilde regnes fra starten)')
    a.add_argument('--grense', type=float, default=0.9, help='lavere treff enn dette regnes som feil')
    arg = a.parse_args()

    exe = os.path.join(ROT, 'port', 'moonstone-headless')
    if not os.path.exists(exe):
        sys.exit('Fant ikke %s, kjor make -C port headless' % exe)
    mapper = {d.lower(): d for d in os.listdir(arg.gfx)}

    with tempfile.TemporaryDirectory() as tmp:
        # forst: hvilket bilde tilstanden er fra
        ut = subprocess.run([exe, '--game', arg.spill, '--headless', '--load-state', arg.state, '--frames', '0'],
                            capture_output=True, text=True).stdout
        m = re.search(r'Tilstand lastet, bilde (\d+)', ut)
        if not m:
            sys.exit('Kunne ikke laste tilstanden:\n' + ut)
        start = int(m.group(1))
        cmd = [exe, '--game', arg.spill, '--headless', '--load-state', arg.state,
               '--frames', str(arg.fra + arg.antall + FORSINKELSE + 1),
               '--tegneliste', '%d:%d' % (start + arg.fra, arg.antall),
               '--shot-every', '1', '--shot-dir', tmp]
        for p in arg.press:
            f, rest = p.split(':', 1)
            cmd += ['--press', '%d:%s' % (start + int(f), rest)]
        ut = subprocess.run(cmd, capture_output=True, text=True).stdout

        # tegnelister per bilde, samlet til klynger av bilder paa rad
        lister, bilde = {}, None
        for l in ut.splitlines():
            m = re.match(r'tegneliste bilde (\d+)', l)
            if m:
                bilde = int(m.group(1))
                lister[bilde] = []
            elif bilde is not None and LINJE.match(l):
                lister[bilde].append(LINJE.match(l).groups())
        klynger, forrige = [], None
        for b in sorted(lister):
            if not lister[b]:
                continue
            if forrige == b - 1 and klynger:
                klynger[-1][1].extend(lister[b])
                klynger[-1][0] = b
            else:
                klynger.append([b, list(lister[b])])
            forrige = b

        feil = sjekket = 0
        for siste, figurer in klynger:
            vis = siste + FORSINKELSE
            sti = os.path.join(tmp, 'shot_%05d.png' % (vis - start))
            if not os.path.exists(sti):
                continue
            skjerm = Image.open(sti).convert('RGB')
            print('bilde %d (tegnet til og med %d):' % (vis, siste))
            alle = []
            for fil, nr, x, y, w, h, xoff, sp in figurer:
                mappe = mapper.get(fil.lower())
                png = os.path.join(arg.gfx, mappe, '%03d.png' % int(nr)) if mappe else ''
                px = piksler(Image.open(png), DIW_X + (int(x) - int(xoff)) * 2, DIW_Y + int(y), bool(sp)) \
                    if os.path.exists(png) else None
                alle.append(px)
            for k, (fil, nr, x, y, w, h, xoff, sp) in enumerate(figurer):
                navn = '%s bilde %s' % (fil or '?', nr)
                if alle[k] is None:
                    print('  %-22s ingen utpakket fil' % navn)
                    continue
                # det figurer tegnet senere dekker, skal ikke telle
                dekket = {(x2, y2) for px in alle[k + 1:] if px for x2, y2, _ in px}
                t = treff(skjerm, alle[k], dekket)
                if t is None:
                    print('  %-22s utenfor skjermen eller dekket' % navn)
                    continue
                sjekket += 1
                if t < arg.grense:
                    feil += 1
                print('  %-22s x %4s y %4s%s  treff %.2f%s' % (navn, x, y, ' speilet' if sp else '        ', t,
                                                              '  FEIL' if t < arg.grense else ''))
        print('%d figurer sjekket, %d under %.2f' % (sjekket, feil, arg.grense))
        sys.exit(1 if feil or not sjekket else 0)


if __name__ == '__main__':
    main()
