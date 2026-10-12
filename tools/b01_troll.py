#!/usr/bin/env python3
"""
b01_troll.py - forsoek paa aa gjenskape trollkrasjet (B01 i docs/kuttet-innhold-og-feil.md).

    make -C port headless
    python3 tools/b01_troll.py [--forsok 40] [--bilder 3000] [--ut MAPPE] [--game Moonstonecd32-AMIGA.zip]

Rapporten fra spillerne: to troll vender mot hverandre og slaar over hodet samtidig,
og spillet krasjer. Se docs/undersokelser/b01-troll.md for hva som er funnet.

Skriptet
  1. skriver utgaven (SHA-256 for arkivet, slaven og spillfilene, og CRC-en
     emulatoren bruker for lagringer)
  2. lager et spill paa kartet og gaar inn i trollhulen (lair 6, monstertype $30)
     med ridder 1. Ridderen faar 90 i liv saa kampen varer.
  3. lager to kampstarter: den naturlige (ett troll, slik originalen alltid gjoer)
     og en testvariant der instruksjonen paa $084208 (move.w #1,$8CFBE, som tvinger
     ett troll paa skjermen) faar 2, saa to troll er ute samtidig. Testvarianten
     endrer spillkoden og er bare for aa proeve scenarioet.
  4. kjoerer hver start med de samme tilfeldige, men faste inndataene (frø 1..N),
     baade med C-krokene og med --nohooks, og med --unntak, som melder ord- og
     langordtilganger paa oddetallsadresser (Address Error paa en ekte 68000) og
     stopper ved hopp til unntaksvektorene.
  5. skriver for hvert forsoek: stoppet eller ikke, foerste odde tilgang med
     registre og stakk, og om kampen staar fast (ingen faar skade og ingen
     flytter seg paa 1500 bilder der ridderen slaar). Siste bilde lagres i --ut.
"""
import argparse
import hashlib
import random
import re
import subprocess
import sys
import tempfile
import zlib
from pathlib import Path

HER = Path(__file__).resolve().parent
sys.path.insert(0, str(HER))
from lag_loot_fixture import BOOT, memory, longword, word  # noqa: E402
import moonfiles as mf  # noqa: E402

ROT = HER.parent
PROG = ROT / 'port' / 'moonstone-headless'
RIDDER = 0x8d5b4
TROLLHULE = 6
EN_TROLL = 0x8420a          # immediate i move.w #1,$8CFBE paa $084208


def utgave(spill):
    s = mf.Spill(spill)
    ut = [('arkiv', hashlib.sha256(Path(spill).read_bytes()).hexdigest())]
    for navn in ('Moonstone.Slave', 'data/mog', 'data/program'):
        data = s.les(navn)
        ut.append((navn, '%s crc32 %08x' % (hashlib.sha256(data).hexdigest(), zlib.crc32(data))))
    return ut


def kjor(spill, valg):
    cmd = [str(PROG), '--game', spill, '--headless', '--online-meny', '--log', '0'] + [str(v) for v in valg]
    return subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT).stdout


def lag_start(spill, mappe, to_troll):
    kart = mappe / 'kart.sav'
    if not kart.exists():
        kjor(spill, BOOT + ['--frames', 2001, '--save-state', '2000:%s' % kart])
    mem = memory(kart)
    tabell = longword(mem, 0x8cdb2)
    hule = tabell + TROLLHULE * 22
    if word(mem, hule + 4) != 0x30:
        sys.exit('Lair %d er ikke troll i denne utgaven' % TROLLHULE)
    x, y = word(mem, hule + 10), word(mem, hule + 12)
    skriv = [(RIDDER + 0x7e, x - 1, 2), (RIDDER + 0x80, y, 2), (RIDDER + 0x50, 90, 2), (RIDDER + 0x54, 90, 2)]
    if to_troll:
        skriv.append((EN_TROLL, 2, 2))
    valg = ['--load-state', kart]
    for a, v, n in skriv:
        valg += ['--skriv', '2019:%x:%d:%d' % (a, v, n)]
    start = mappe / ('to.sav' if to_troll else 'en.sav')
    kjor(spill, valg + ['--press', '2020:right:4', '--press', '2040:fire:4', '--frames', 700,
                        '--save-state', '700:%s' % start])
    mem = memory(start)
    figurer = longword(mem, 0x8cdf4)
    troll = [figurer + i * 0x84 for i in range(8) if longword(mem, figurer + i * 0x84) and mem[0x8ce42] == 0x30]
    if longword(mem, 0x95f28) != hule or not troll:
        sys.exit('Kom ikke inn i trollhulen')
    return start, len(troll), skriv


def inndata(frø, fra, bilder):
    """Faste tilfeldige trykk: retning og fire i korte og lange stoet, ogsaa fire+retning."""
    r = random.Random(frø)
    ut, f = [], fra + 5
    while f < fra + bilder - 50:
        lengde = r.choice((6, 12, 25, 50, 100))
        hva = r.choice(('left', 'right', 'up', 'down', 'fire', 'fire+left', 'fire+right', 'fire+up', 'fire+down', None))
        if hva:
            for h in hva.split('+'):
                ut += ['--press', '%d:%s:%d' % (f, h, lengde)]
        f += lengde + r.choice((0, 5, 20))
    return ut


def bilde_av_kampen(sav):
    """Liv, posisjon og angrep ($40) for ridderen og trollene."""
    mem = memory(sav)
    figurer = longword(mem, 0x8cdf4)
    ut = [(word(mem, RIDDER + 0x50), word(mem, RIDDER + 4), word(mem, RIDDER + 8), word(mem, RIDDER + 0x40))]
    for i in range(8):
        f = figurer + i * 0x84
        if longword(mem, f):
            ut.append((word(mem, f + 0x50), word(mem, f + 4), word(mem, f + 8), word(mem, f + 0x40)))
    return ut, mem[0x8ce42] == 0x30 and word(mem, 0x98088) == 0    # trollkamp, og ikke inventaret (pekeren)


def forsok(spill, start, frø, bilder, nohooks, ut):
    fra = 2700
    navn = '%s-%s-%03d' % (Path(start).stem, 'nohooks' if nohooks else 'kroker', frø)
    mappe = ut / navn
    mappe.mkdir(parents=True, exist_ok=True)
    kroker = ['--nohooks'] if nohooks else []
    slutt = mappe / 'slutt.sav'
    logg = kjor(spill, ['--load-state', start, '--frames', bilder, '--unntak', 3, '--shot-every', bilder,
                        '--shot-dir', mappe, '--save-state', '%d:%s' % (bilder, slutt)] + inndata(frø, fra, bilder) + kroker)
    (mappe / 'logg.txt').write_text(logg)
    stopp = re.search(r'Stoppet i bilde (\d+): (.*)', logg)
    odde = re.search(r'^odde .*(?:\n  .*){3}', logg, re.M)
    laast = ''
    if slutt.exists():
        foer, i_kamp = bilde_av_kampen(slutt)
        if i_kamp and foer[0][0] > 0 and all(f[0] > 0 for f in foer[1:]):
            # 1500 bilder til der ridderen slaar mot venstre: rikker ingen seg, er kampen laast
            trykk = []
            for f in range(fra + bilder + 10, fra + bilder + 1500, 40):
                trykk += ['--press', '%d:fire:10' % f, '--press', '%d:left:10' % f]
            etter_sav = mappe / 'etter.sav'
            kjor(spill, ['--load-state', slutt, '--frames', 1500, '--save-state', '1500:%s' % etter_sav] + trykk + kroker)
            etter, _ = bilde_av_kampen(etter_sav)
            # angrepet ($40) og trollenes posisjon gaar i ring i en laast kamp, saa bare liv og ridderens plass sammenlignes
            if [f[0] for f in etter] == [f[0] for f in foer] and etter[0][1:3] == foer[0][1:3]:
                laast = 'kampen staar fast: ridder (liv, x, y, angrep) %s, troll %s' % (foer[0], foer[1:])
    bilder_ut = sorted(mappe.glob('shot_*.png'))
    return {'navn': navn, 'stopp': stopp.group(0) if stopp else '', 'odde': odde.group(0) if odde else '',
            'laast': laast, 'siste': str(bilder_ut[-1]) if bilder_ut else ''}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--game', default=str(ROT / 'Moonstonecd32-AMIGA.zip'))
    ap.add_argument('--forsok', type=int, default=20)
    ap.add_argument('--bilder', type=int, default=3000)
    ap.add_argument('--ut', type=Path)
    a = ap.parse_args()
    if not PROG.exists():
        sys.exit('Bygg foerst: make -C port headless')
    for k, v in utgave(a.game):
        print('utgave %-16s %s' % (k, v))
    with tempfile.TemporaryDirectory() as tmp:
        ut = a.ut or Path(tmp)
        ut.mkdir(parents=True, exist_ok=True)
        funn = 0
        for to_troll in (False, True):
            start, antall, skriv = lag_start(a.game, ut, to_troll)
            print('\n%s: %d troll paa skjermen ved start, oppsett %s' % (
                'testvariant ($084208 gir 2)' if to_troll else 'naturlig start', antall,
                ', '.join('$%06x=%d' % (adr, v) for adr, v, _ in skriv)))
            for frø in range(1, a.forsok + 1):
                for nohooks in (False, True):
                    r = forsok(a.game, start, frø, a.bilder, nohooks, ut)
                    feil = r['stopp'] or r['odde'] or r['laast']
                    funn += bool(feil)
                    print('  %-24s %s' % (r['navn'], 'ok' if not feil else ''))
                    if r['stopp']:
                        print('     ' + r['stopp'])
                    if r['odde']:
                        print('     ' + r['odde'].replace('\n', '\n     '))
                    if r['laast']:
                        print('     %s\n     siste bilde %s' % (r['laast'], r['siste']))
        print('\n%d forsoek med noe aa se paa' % funn)


if __name__ == '__main__':
    main()
