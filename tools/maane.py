#!/usr/bin/env python3
"""
maane.py - maaler maanefasene i originalkoden (docs/undersokelser/maane.md).

    python3 tools/maane.py [--dager 40] [--game Moonstonecd32-AMIGA.zip] [--nohooks]

Lager et spill paa kartet (samme oppskrift som tests/nettleser/felles.js),
trykker End turn til dagene gaar, og foelger med paa to felt med --vakt:
dagtelleren ($08CEA8, 1-4) og maanebildet ($08CEA6, ki.cel 45-49) som
sub_08064a skriver hver ny dag. Skriver utgaven (SHA-256 for spillfilene og
slaven) og en tabell over dag, fase og bilde. Et nytt spill etter game over
($084C72) vises som egen linje.
"""
import argparse
import hashlib
import os
import re
import subprocess
import sys
import tempfile

HER = os.path.dirname(os.path.abspath(__file__))
ROT = os.path.dirname(HER)
sys.path.insert(0, HER)
import moonfiles as mf  # noqa: E402

PROG = os.path.join(ROT, 'port', 'moonstone-headless')
TIL_KARTET = ['--headless', '--online-meny', '--log', '0', '--press', '100:esc:4', '--press', '700:down:10',
              '--press', '760:down:10', '--press', '820:down:10', '--press', '880:fire:10',
              '--press', '1300:fire:10', '--press', '1500:return:6']
BILDE = {0x2d: 'nymaane', 0x2e: 'sigd', 0x2f: 'halvmaane', 0x30: 'trekvart', 0x31: 'fullmaane'}   # 48-46 ogsaa naar den avtar


def utgave(spill):
    """SHA-256 for arkivet og filene som styrer spillet, saa maalingen kan knyttes til en utgave."""
    s = mf.Spill(spill)
    ut = {'arkiv': hashlib.sha256(open(spill, 'rb').read()).hexdigest()}
    for navn in ('Moonstone.Slave', 'data/mog', 'data/program'):
        ut[navn] = hashlib.sha256(s.les(navn)).hexdigest()
    return ut


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dager', type=int, default=40)
    ap.add_argument('--game', default=os.path.join(ROT, 'Moonstonecd32-AMIGA.zip'))
    ap.add_argument('--nohooks', action='store_true')
    a = ap.parse_args()
    if not os.path.exists(PROG):
        sys.exit('Bygg foerst: make -C port headless')
    for k, v in utgave(a.game).items():
        print('utgave %-14s %s' % (k, v))
    with tempfile.TemporaryDirectory() as tmp:
        kart = os.path.join(tmp, 'kart.sav')
        subprocess.run([PROG, '--game', a.game] + TIL_KARTET + ['--save-state', '2000:' + kart, '--frames', '2001'],
                       check=True, capture_output=True)
        bilder = 2000 + a.dager * 2600          # en dag tar rundt 2000 bilder med trykkene under
        trykk = []
        for f in range(2100, bilder, 500):
            trykk += ['--press', '%d:e:6' % f]
        for f in range(2350, bilder, 1000):
            trykk += ['--press', '%d:fire:6' % f]
        r = subprocess.run([PROG, '--game', a.game, '--headless', '--load-state', kart, '--frames', str(bilder),
                            '--log', '0', '--vakt', '8cea6'] + (['--nohooks'] if a.nohooks else []) + trykk,
                           capture_output=True, text=True)
    dag = 0
    print('%7s %4s %6s  %s' % ('bilde', 'dag', 'teller', 'maane'))
    for l in r.stdout.splitlines():
        m = re.match(r'vakt bilde (\d+) pc ([0-9a-f]+): 2 byte til (0008cea[68]|08cea[68]) = ([0-9a-f]+)', l)
        if not m:
            continue
        bilde, pc, adr, verdi = int(m.group(1)), m.group(2), m.group(3), int(m.group(4), 16)
        if pc.endswith('84c72'):
            print('%7d  nytt spill: maanen settes til nymaane, men faseindeksen $08F152 beholdes' % bilde)
        elif adr.endswith('a8') and pc.endswith('8065e'):
            dag += 1
            print('%7d %4d %6d' % (bilde, dag, verdi))
        elif adr.endswith('a6') and pc.endswith('806a6'):
            print('%7d %4s %6s  bilde %d (%s)' % (bilde, '', '', verdi, BILDE.get(verdi, '?')))


if __name__ == '__main__':
    main()
