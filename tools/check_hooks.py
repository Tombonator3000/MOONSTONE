#!/usr/bin/env python3
"""
check_hooks.py - sjekker at C-erstatningene (port/src/decomp) gir samme spill som originalen.

    python3 tools/check_hooks.py [--frames N] [--game Moonstonecd32-AMIGA.zip]

Kjorer spillet to ganger uten vindu med de samme knappetrykkene: en gang med
C-versjonene og en gang bare med originalkoden (--nohooks). Chip-minnet lagres
med jevne mellomrom og sammenlignes, det samme gjor skjermbildene til slutt.
Er C-versjonene riktige (ogsaa antall sykluser), er alt likt byte for byte.
"""
import argparse
import os
import subprocess
import sys
import tempfile

HER = os.path.dirname(os.path.abspath(__file__))
ROT = os.path.dirname(HER)
PROG = os.path.join(ROT, 'port', 'moonstone-headless')

# et lite spill: hopp over introen, to spillere, velg riddere, flytt, inventar, avslutt turer
TRYKK = ('400:esc:4 7650:right:8 7700:down:8 7750:down:8 7800:down:8 7850:fire:8 8020:fire:8 '
         '8150:return:4 8300:fire:8 8450:return:4 9000:right:30 9100:down:40 9300:space:4 9400:fire:6 '
         '9520:e:4 9920:e:4 11000:fire:6 11600:e:4 12000:e:4').split()


def kjor(mappe, med_hooks, frames, spill, hvert):
    a = [PROG, '--game', spill, '--headless', '--frames', str(frames), '--log', '0',
         '--shot-every', str(frames), '--shot-dir', mappe]
    for t in TRYKK:
        a += ['--press', t]
    for f in range(hvert, frames, hvert):
        a += ['--dump', '%d:%s/ram_%06d.bin' % (f, mappe, f)]
    if not med_hooks:
        a.append('--nohooks')
    else:
        a.append('--hook-report')
    r = subprocess.run(a, capture_output=True, text=True)
    if r.returncode:
        print(r.stdout, r.stderr)
        sys.exit('kjoringen feilet')
    return r.stdout


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--frames', type=int, default=12500)
    p.add_argument('--hvert', type=int, default=500)
    p.add_argument('--game', default=os.path.join(ROT, 'Moonstonecd32-AMIGA.zip'))
    a = p.parse_args()
    if not os.path.exists(PROG):
        sys.exit('Bygg forst: make -C port headless')
    with tempfile.TemporaryDirectory() as t:
        m1, m2 = os.path.join(t, 'c'), os.path.join(t, 'orig')
        os.makedirs(m1)
        os.makedirs(m2)
        ut = kjor(m1, True, a.frames, a.game, a.hvert)
        print(''.join(l + '\n' for l in ut.splitlines() if 'kjort i C' in l), end='')
        kjor(m2, False, a.frames, a.game, a.hvert)
        ulike = 0
        for f in sorted(os.listdir(m1)):
            b1 = open(os.path.join(m1, f), 'rb').read()
            b2 = open(os.path.join(m2, f), 'rb').read()
            if b1 != b2:
                ulike += 1
                if f.startswith('ram_'):
                    forste = next(i for i in range(len(b1)) if b1[i] != b2[i])
                    antall = sum(1 for i in range(len(b1)) if b1[i] != b2[i])
                    print('%s: %d byte ulike, forste paa $%06x' % (f, antall, forste))
                else:
                    print('%s: ulikt bilde' % f)
        n = len(os.listdir(m1))
        if ulike:
            sys.exit('%d av %d sammenligninger er ulike' % (ulike, n))
        print('OK: %d av %d sammenligninger er like byte for byte' % (n, n))


if __name__ == '__main__':
    main()
