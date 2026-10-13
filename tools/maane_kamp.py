#!/usr/bin/env python3
"""
maane_kamp.py - maaler steinen, Ratmen og sykdommen i en ekte kamp (docs/undersokelser/maane.md).

    make -C port headless
    python3 tools/maane_kamp.py [--game Moonstonecd32-AMIGA.zip]

Lager et spill paa kartet, setter ridder 1 ved Ratmen-hulen (lair 0) og gaar inn
med samme oppskrift som tools/lag_lair_fixture.py. Fra den samme lagringen kjoeres
kampen paa nytt med bare ett felt endret om gangen:

  1. steinen: bit 0-3 i inventaret (+$16) mot maanebildet ($08CEA6), og ridderen
     slaar med fire+venstre. Ut kommer livet til rotta ($50) etter hvert slag.
  2. Ratmen og maanen: ingen inndata, saa rottene slaar ridderen. Med og uten
     --maaneregler (lagringen maa lages med valget, delen MAAN).
  3. smitten: om rottebittet (angrep type 4, $0855EC) setter $82 paa ridderen.
  4. sykdommen over tid: $82 settes rett i minnet paa kartet, og livsnivaaet $49
     foelges over flere doegn sammen med dagtelleren.
"""
import argparse
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HER = Path(__file__).resolve().parent
sys.path.insert(0, str(HER))
from lag_loot_fixture import BOOT, memory, longword, word  # noqa: E402

ROT = HER.parent
PROG = ROT / 'port' / 'moonstone-headless'
RIDDER = 0x8d5b4
BILDER = {0x2d: 'nymaane', 0x2f: 'halvmaane', 0x31: 'fullmaane'}


def kjor(spill, valg, vakt=None):
    cmd = [str(PROG), '--game', spill, '--headless', '--online-meny', '--log', '0'] + [str(v) for v in valg]
    if vakt is not None:
        cmd += ['--vakt', '%x' % vakt]
    r = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if r.returncode or 'Stoppet i bilde' in r.stdout:
        sys.exit('Kjoeringen stoppet:\n' + r.stdout[-2000:])
    return [(int(m.group(1)), m.group(2), int(m.group(3), 16))
            for m in re.finditer(r'vakt bilde (\d+) pc ([0-9a-f]+): \d byte til [0-9a-f]+ = ([0-9a-f]+)', r.stdout)]


def lag_kamp(spill, mappe, ekstra):
    """Kartet og Ratmen-kampen i lair 0. Gir (kamp.sav, kart.sav, rotta)."""
    kart = mappe / 'kart.sav'
    kjor(spill, ekstra + BOOT + ['--frames', 2001, '--save-state', '2000:%s' % kart])
    mem = memory(kart)
    tabell = longword(mem, 0x8cdb2)
    if word(mem, tabell + 4) != 0x24:
        sys.exit('Lair 0 er ikke Ratmen i denne utgaven')
    x, y = word(mem, tabell + 10), word(mem, tabell + 12)
    kamp = mappe / 'kamp.sav'
    valg = ekstra + ['--load-state', kart]
    for a, v in ((RIDDER + 0x7e, x - 1), (RIDDER + 0x80, y), (tabell + 6, 0)):
        valg += ['--skriv', '2019:%x:%d:2' % (a, v)]
    kjor(spill, valg + ['--press', '2020:right:4', '--press', '2040:fire:4', '--frames', 600,
                        '--save-state', '600:%s' % kamp])
    mem = memory(kamp)
    if longword(mem, 0x95f28) != tabell or mem[0x8ce42] != 0x24:
        sys.exit('Kom ikke inn i Ratmen-kampen')
    figurer = longword(mem, 0x8cdf4)
    rotte = next(figurer + i * 0x84 for i in range(1, 20) if longword(mem, figurer + i * 0x84))
    return kamp, kart, rotte, longword(mem, RIDDER + 0x60) + 0x16


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--game', default=str(ROT / 'Moonstonecd32-AMIGA.zip'))
    a = ap.parse_args()
    if not PROG.exists():
        sys.exit('Bygg foerst: make -C port headless')
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        (tmp / 'orig').mkdir()
        (tmp / 'valg').mkdir()
        kamp, kart, rotte, stein = lag_kamp(a.game, tmp / 'orig', [])
        kamp_mr, _, _, _ = lag_kamp(a.game, tmp / 'valg', ['--maaneregler'])

        print('1. Steinen: livet til rotta etter hvert slag fra ridderen (fire+venstre)')
        for bit in (0, 1, 2, 4, 8):
            rad = []
            for bilde in BILDER:
                skriv = ['--skriv', '2601:8cea6:%d:2' % bilde, '--skriv', '2601:%x:%d:1' % (stein, bit)]
                liv = [v for _, _, v in kjor(a.game, ['--load-state', kamp, '--frames', 600, '--press', '2610:fire:300',
                                                      '--press', '2610:left:300'] + skriv, rotte + 0x50)][:3]
                rad.append('%s %s' % (BILDER[bilde], ' '.join(str(v - 0x10000 if v > 0x7fff else v) for v in liv)))
            print('   stein-bit %d: %s' % (bit, ' | '.join(rad)))

        print('2. Ratmen og maanen: livet til ridderen etter hvert rottebitt (ingen inndata)')
        for navn, fil in (('originalen', kamp), ('maanereglene', kamp_mr)):
            rad = []
            for bilde in BILDER:
                liv = [v for _, pc, v in kjor(a.game, ['--load-state', fil, '--frames', 800,
                                                       '--skriv', '2601:8cea6:%d:2' % bilde], RIDDER + 0x50)
                       if pc.endswith('85608') or pc.endswith('855de')][:3]
                rad.append('%s %s' % (BILDER[bilde], ' '.join(str(v - 0x10000 if v > 0x7fff else v) for v in liv)))
            print('   %-12s %s' % (navn, ' | '.join(rad)))

        print('3. Smitten: bitt av type 4 setter $82 paa ridderen (livet satt til 60 saa han overlever)')
        for start in (0, 40, 60, 130):
            treff = [b for b, pc, v in kjor(a.game, ['--load-state', kamp, '--frames', 1500, '--skriv', '2601:8d604:60:2',
                                                     '--press', '%d:right:40' % (2610 + start),
                                                     '--press', '%d:fire:200' % (2700 + start),
                                                     '--press', '%d:left:200' % (2700 + start)], RIDDER + 0x80)
                     if pc.endswith('855ec')]
            print('   ventet %3d bilder: %s' % (start, 'smittet i bilde %d' % treff[0] if treff else 'ikke smittet'))

        print('4. Sykdommen over tid: $82 = 1 paa kartet, livsnivaa $49 og dagtelleren')
        trykk = []
        for f in range(2100, 17000, 500):
            trykk += ['--press', '%d:e:6' % f]
        for f in range(2350, 17000, 1000):
            trykk += ['--press', '%d:fire:6' % f]
        felles = ['--load-state', kart, '--skriv', '2001:%x:1:1' % (RIDDER + 0x82), '--frames', 17000] + trykk
        hendelser = [(b, 'dag (teller %d)' % v) for b, pc, v in kjor(a.game, felles, 0x8cea8) if pc.endswith('8065e')]
        for b, pc, v in kjor(a.game, felles, RIDDER + 0x48):
            if pc.endswith('80756'):
                hendelser.append((b, 'sykdommen: livsnivaa %d' % (v & 0xff)))
            elif pc.endswith('80446'):
                hendelser.append((b, 'tapt kamp: livsnivaa %d' % (v & 0xff)))
        for b, tekst in sorted(hendelser):
            print('   %6d  %s' % (b, tekst))


if __name__ == '__main__':
    main()
