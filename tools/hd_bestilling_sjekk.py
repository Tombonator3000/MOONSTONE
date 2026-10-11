#!/usr/bin/env python3
"""Kontroller bestilling og maskering mot ekte, sparsomt lagrede CEL-ruter."""
import contextlib
import csv
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile

from PIL import Image

import gfx
import hd_bestilling as bestilling
import moonfiles as mf


def piksler(im):
    d = im.tobytes()
    return [tuple(d[i:i + 4]) for i in range(0, len(d), 4)]


def main():
    rot = Path(__file__).resolve().parents[1]
    spill_sti = rot / 'Moonstonecd32-AMIGA.zip'
    spill = mf.Spill(str(spill_sti))
    b = mf.cel_les(spill.les('data/HE3.ob'))[0][31]
    assert (b['maske'], b['bredde'], b['hoyde']) == (10, 4, 2)
    pakket = mf.plan_til_indeks(b['data'], b['plan'], b['bredde'], b['hoyde'])
    assert set(pakket) == {0, 3}
    pal = gfx.standard_palett(spill)
    antall = pakket.count(3) * 16
    kontroller = 0
    with tempfile.TemporaryDirectory(prefix='moonstone-bestilling-') as temp:
        temp = Path(temp)
        kilde = temp / 'HE3.ob' / '031.png'
        kilde.parent.mkdir()
        gfx.lagre_png(str(kilde), pakket, b['bredde'], b['hoyde'], pal)
        ut = temp / '031.mask.png'
        with contextlib.redirect_stdout(io.StringIO()):
            bestilling.lag_maske(str(kilde), str(ut), spill_sti=str(spill_sti))
        m = Image.open(ut)
        assert m.size == (16, 8)
        assert piksler(m).count((11, 128, 255, 255)) == antall
        assert set(piksler(m)) == {(0, 0, 0, 255), (11, 128, 255, 255)}
        kontroller += 3

        # Extract-sidecaren skal gi samme resultat uten å gjette PNG-indeks 3.
        (temp / 'index.json').write_text(json.dumps({'filer': {'data/HE3.ob': {
            'type': 'figurer', 'bilder': [dict(fil='031.png', sha1=hashlib.sha1(b['data']).hexdigest(), **{k: b[k] for k in
              ('bredde', 'hoyde', 'maske')})]}}}), encoding='utf-8')
        with contextlib.redirect_stdout(io.StringIO()):
            bestilling.lag_maske(str(kilde), str(ut))
        assert Image.open(ut).tobytes() == m.tobytes()
        kontroller += 1

        endret = Image.open(kilde)
        endret.putpixel((0, 0), 1 if pakket[0] != 1 else 0)
        endret.save(kilde)
        try:
            bestilling.lag_maske(str(kilde), str(ut))
        except SystemExit as e:
            assert 'originalhashen' in str(e)
        else:
            raise AssertionError('Endret original-PNG ble godtatt')
        gfx.lagre_png(str(kilde), pakket, b['bredde'], b['hoyde'], pal)
        kontroller += 1

        # Tegning i faktisk kildefarge skal bli nøytral, ikke behandles som indeks 3.
        palette = Image.open(kilde).getpalette()
        tegning = temp / 'farget.png'
        Image.new('RGB', (16, 8), tuple(palette[30:33])).save(tegning)
        with contextlib.redirect_stdout(io.StringIO()):
            bestilling.lag_maske(str(kilde), str(ut), str(tegning))
        assert piksler(Image.open(ut)).count((11, 128, 255, 255)) == antall
        kontroller += 1

        # Valgt grå referanse skiller seg fra automatisk farget kildenormalisering.
        Image.new('RGB', (16, 8), (128, 128, 128)).save(tegning)
        with contextlib.redirect_stdout(io.StringIO()):
            bestilling.lag_maske(str(kilde), str(ut), str(tegning), graa_referanse=128)
        assert piksler(Image.open(ut)).count((11, 128, 255, 255)) == antall
        Image.new('RGB', (16, 8), (64, 64, 64)).save(tegning)
        with contextlib.redirect_stdout(io.StringIO()):
            bestilling.lag_maske(str(kilde), str(ut), str(tegning), graa_referanse=128)
        assert piksler(Image.open(ut)).count((11, 64, 255, 255)) == antall
        kontroller += 2

        ukjent = temp / 'ukjent.cel' / '031.png'
        ukjent.parent.mkdir()
        Image.open(kilde).save(ukjent)
        try:
            bestilling.lag_maske(str(ukjent), str(ut), spill_sti=str(spill_sti))
        except SystemExit as e:
            assert 'Ukjent original-CEL-rute' in str(e)
        else:
            raise AssertionError('Ukjent CEL-kilde ble godtatt')
        kontroller += 1

        csv_sti = temp / 'bestilling.csv'
        resultat = subprocess.run([sys.executable, str(rot / 'tools/hd_bestilling.py'),
                                   str(spill_sti), str(csv_sti)], check=True,
                                  text=True, capture_output=True, cwd=rot)
        with csv_sti.open(encoding='utf-8') as f:
            rader = list(csv.DictReader(f, delimiter=';'))
        kn = next(r for r in rader if r['hd_fil'] == 'KN3.ob/031.png')
        assert kn['trenger_maske'] == 'ja'
        assert 'HE3.ob/031.mask.png' in kn['merknad']
        assert not any(r['hd_fil'] == 'HE3.ob/031.png' for r in rader)
        logo = next(r for r in rader if r['hd_fil'] == 'bold.f/073.png')
        assert (logo['hd_bredde'], logo['hd_hoyde']) == ('1220', '216')
        assert all(int(r['prioritet']) == 2 for r in rader if r['hd_fil'].startswith('bg/'))
        assert min(i for i, r in enumerate(rader) if r['gruppe'] == 'Monstre') > rader.index(logo)
        assert not any('Bruk dem gjerne' in r['merknad'] for r in rader)
        assert all(r['prioritet'] == ('1' if int(r['bilde']) <= 5 else '3')
                   for r in rader if r['fil'].lower() == 'mys.cel')
        assert all(r['prioritet'] == ('1' if int(r['bilde']) <= 5 else '4')
                   for r in rader if r['fil'].lower() == 'dice.cel')
        kontroller += 9
    print('%d kildebaserte bestillings-/maskekontroller består.' % kontroller)
    print(resultat.stdout.strip())


if __name__ == '__main__':
    main()
