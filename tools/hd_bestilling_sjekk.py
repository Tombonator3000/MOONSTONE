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

        # Math bruker levende spillerfarger6..10 bare i taarnrutene15..20.
        # Balkongrutene0..14 har faste farger, ogsaa med de samme indeksene.
        assert bestilling.maskefarger('Wi1.C', 15) == set(range(6, 11))
        assert bestilling.maskefarger('Wi1.C', 20) == set(range(6, 11))
        assert bestilling.maskefarger('Wi1.C', 14) == set()
        assert 11 not in bestilling.maskefarger('Wi1.C', 15)
        for nr in (0, 15, 16, 17, 18, 19, 20):
            original = mf.cel_les(spill.les('data/Wi1.C'))[0][nr]
            packed = mf.plan_til_indeks(original['data'], original['plan'], original['bredde'], original['hoyde'])
            expanded = bestilling.utvid_indekser(packed, original['maske'])
            wi = temp / 'Wi1.C' / ('%03d.png' % nr)
            wi.parent.mkdir(exist_ok=True)
            gfx.lagre_png(str(wi), packed, original['bredde'], original['hoyde'], pal)
            with contextlib.redirect_stdout(io.StringIO()):
                bestilling.lag_maske(str(wi), str(ut), spill_sti=str(spill_sti))
            expected = [(v + 1, 128, 255, 255) if v in bestilling.maskefarger('Wi1.C', nr)
                        else (0, 0, 0, 255) for v in expanded]
            expected_image = Image.new('RGBA', (original['bredde'], original['hoyde']))
            expected_image.putdata(expected)
            expected_image = expected_image.resize((original['bredde']*4, original['hoyde']*4), Image.Resampling.NEAREST)
            assert Image.open(ut).tobytes() == expected_image.tobytes()
        kontroller += 11

        # Stålhanske/bord bruker tav-paletten.006/007 har levende drakt6..10.
        assert bestilling.maskefarger('dice.cel',6)==set(range(6,11))
        assert bestilling.maskefarger('dice.cel',7)==set(range(6,11))
        assert bestilling.maskefarger('dice.cel',8)==set()
        assert bestilling.maskefarger('dice.cel',22)==set()
        for nr in (6,7,8,22):
            original=mf.cel_les(spill.les('data/dice.cel'))[0][nr]
            packed=mf.plan_til_indeks(original['data'],original['plan'],original['bredde'],original['hoyde'])
            expanded=bestilling.utvid_indekser(packed,original['maske'])
            source=temp/'dice.cel'/('%03d.png'%nr);source.parent.mkdir(exist_ok=True)
            gfx.lagre_png(str(source),packed,original['bredde'],original['hoyde'],pal)
            with contextlib.redirect_stdout(io.StringIO()):
                bestilling.lag_maske(str(source),str(ut),spill_sti=str(spill_sti))
            expected=Image.new('RGBA',(original['bredde'],original['hoyde']))
            expected.putdata([(v+1,128,255,255) if v in bestilling.maskefarger('dice.cel',nr) else (0,0,0,255) for v in expanded])
            expected=expected.resize((original['bredde']*4,original['hoyde']*4),Image.Resampling.NEAREST)
            assert Image.open(ut).tobytes()==expected.tobytes()
        kontroller += 8

        # KN5: original dragekamp setter faste roedfarger9/11/15 og ild29..31.
        # Blod-/saarruter med6..8 trenger maske, brennende058..064 gjoer ikke det.
        assert bestilling.maskefarger('Kn5.ob', 0) == {6, 7, 8}
        assert bestilling.maskefarger('KN5.ob', 58) == {6, 7, 8}
        kn5 = mf.cel_les(spill.les('data/KN5.ob'))[0]
        maskerte = []
        faste = {9, 11, 15, 29, 30, 31}
        for nr, original in enumerate(kn5):
            packed = mf.plan_til_indeks(original['data'], original['plan'], original['bredde'], original['hoyde'])
            expanded = bestilling.utvid_indekser(packed, original['maske'])
            if set(expanded) & {6, 7, 8}:
                maskerte.append(nr)
            source = temp / 'KN5.ob' / ('%03d.png' % nr)
            source.parent.mkdir(exist_ok=True)
            gfx.lagre_png(str(source), packed, original['bredde'], original['hoyde'], pal)
            with contextlib.redirect_stdout(io.StringIO()):
                bestilling.lag_maske(str(source), str(ut), spill_sti=str(spill_sti))
            mask = Image.open(ut).convert('RGBA')
            for y in range(original['hoyde']):
                for x in range(original['bredde']):
                    indeks = expanded[y * original['bredde'] + x]
                    expected = (indeks + 1, 128, 255, 255) if indeks in {6, 7, 8} else (0, 0, 0, 255)
                    assert mask.getpixel((x * 4 + 2, y * 4 + 2)) == expected
            if nr >= 58:
                assert set(expanded) & faste
                assert not set(expanded) & {6, 7, 8}
                assert set(piksler(mask)) == {(0, 0, 0, 255)}
        assert maskerte == [0, 1, 4, 5, 6, 20, 22, 23]
        kontroller += 75

        # Monsterbankenes innbakte ridderbiter maa ha samme farge som spilleren.
        # Kontroller alle faktiske kilderuter, ikke bare de fem dragefragmentene.
        mog = mf.legg_ut(spill.les('mog'))[0]
        assert mog[0x8c5a:0x8c60] == bytes.fromhex('d1fc0000000c')
        assert mog[0x8c74:0x8c78] == bytes.fromhex('6100002a')
        assert mog[0x8caa:0x8cb6] == bytes.fromhex('30fc000a30fc000730bc0004')
        monster_masker = 0
        for bank, frames in bestilling.KAMP_RIDDER_RUTER.items():
            found = set()
            for nr, original in enumerate(mf.cel_les(spill.les(bank))[0]):
                packed = mf.plan_til_indeks(original['data'], original['plan'], original['bredde'], original['hoyde'])
                indices = bestilling.utvid_indekser(packed, original['maske'])
                if not set(indices) & {6, 7, 8}:
                    trogg = bank.lower().startswith('trogg')
                    assert bestilling.maskefarger(bank, nr) == (set(range(9, 15)) if trogg else set())
                    continue
                found.add(nr)
                source = temp / bank / ('%03d.png' % nr)
                source.parent.mkdir(exist_ok=True)
                gfx.lagre_png(str(source), packed, original['bredde'], original['hoyde'], pal)
                with contextlib.redirect_stdout(io.StringIO()):
                    bestilling.lag_maske(str(source), str(ut), spill_sti=str(spill_sti))
                expected = Image.new('RGBA', (original['bredde'], original['hoyde']))
                live = set(range(6, 15)) if bank.lower().startswith('trogg') else {6, 7, 8}
                expected.putdata([(v + 1, 128, 255, 255) if v in live else (0, 0, 0, 255) for v in indices])
                expected = expected.resize((original['bredde'] * 4, original['hoyde'] * 4), Image.Resampling.NEAREST)
                assert Image.open(ut).tobytes() == expected.tobytes(), (bank, nr)
                monster_masker += 1
            assert found == frames, bank
            assert bestilling.maskefarger(bank, 10000) == set()
        assert monster_masker == 107
        kontroller += 3 + monster_masker + len(bestilling.KAMP_RIDDER_RUTER) * 2

        # Troggens haand/erm skifter med terrenget, ikke riddervalget.
        # Bind dette til originalens tre palettgrener og alle fire grepkilder.
        assert mog[0x8b40:0x8b5c] == bytes.fromhex('30fc002530fc000430fc000130fc083030fc040030fc0f8030bc0c00')
        assert mog[0x8b6c:0x8b88] == bytes.fromhex('30fc010430fc010230fc000030fc060030fc030030fc069330bc0c00')
        assert mog[0x8b8c:0x8ba8] == bytes.fromhex('30fc050030fc020030fc000030fc0b4030fc061030fc089530bc0c00')
        trogg = mf.cel_les(spill.les('TROGGAxe2.CEL'))[0]
        for nr in [62, 63, 65, 66]:
            b = trogg[nr]
            packed = mf.plan_til_indeks(b['data'], b['plan'], b['bredde'], b['hoyde'])
            ix = bestilling.utvid_indekser(packed, b['maske'])
            assert set(ix) & {11, 12, 13}
            source = temp / 'TROGGAxe2.CEL' / ('%03d.png' % nr)
            source.parent.mkdir(exist_ok=True)
            gfx.lagre_png(str(source), packed, b['bredde'], b['hoyde'], pal)
            with contextlib.redirect_stdout(io.StringIO()):
                bestilling.lag_maske(str(source), str(ut), spill_sti=str(spill_sti))
            expected = Image.new('RGBA', (b['bredde'], b['hoyde']))
            expected.putdata([(v+1,128,255,255) if 9 <= v <= 14 else (0,0,0,255) for v in ix])
            expected = expected.resize((b['bredde']*4,b['hoyde']*4),Image.Resampling.NEAREST)
            assert Image.open(ut).tobytes() == expected.tobytes()
        # Rene vaapen har ingen9..14-piksler, selv om bankens fargekontrakt er felles.
        for nr in (55,79):
            b = trogg[nr]
            ix = bestilling.utvid_indekser(mf.plan_til_indeks(b['data'],b['plan'],b['bredde'],b['hoyde']),b['maske'])
            assert not set(ix) & bestilling.maskefarger('TROGGAxe2.CEL',nr)
        # Full kildebankdekning: terrengfelt og ofre skal kunne farges samtidig.
        for bank, count in [('TROGGAxe1.CEL',37),('TROGGAxe2.CEL',80),
                            ('TROGGSpear1.CEL',41),('TROGGSpear2.CEL',67)]:
            frames = mf.cel_les(spill.les(bank))[0]
            assert len(frames) == count
            for nr,b in enumerate(frames):
                ix = bestilling.utvid_indekser(mf.plan_til_indeks(b['data'],b['plan'],b['bredde'],b['hoyde']),b['maske'])
                live = bestilling.maskefarger(bank,nr)
                assert set(range(9,15)) <= live
                assert ({6,7,8} <= live) == bool(set(ix)&{6,7,8})
                kontroller += 1
        kontroller += 9

        csv_sti = temp / 'bestilling.csv'
        resultat = subprocess.run([sys.executable, str(rot / 'tools/hd_bestilling.py'),
                                   str(spill_sti), str(csv_sti)], check=True,
                                  text=True, capture_output=True, cwd=rot)
        with csv_sti.open(encoding='utf-8') as f:
            rader = list(csv.DictReader(f, delimiter=';'))
        kn = next((r for r in rader if r['hd_fil'] == 'KN3.ob/031.png'), None)
        if kn is not None:
            assert kn['trenger_maske'] == 'ja'
            assert 'HE3.ob/031.mask.png' in kn['merknad']
        else:
            # Etter aktivering skal bestillingen utelate begge, mens den faktiske
            # pakken fortsatt maa bevare RGB-kopien og HE-indeksbyttet i masken.
            filstier = {r['path'] for r in json.loads((rot / 'web/hd/manifest.json').read_text())['files']}
            assert {'KN3.ob/031.png', 'HE3.ob/031.png', 'KN3.ob/031.mask.png', 'HE3.ob/031.mask.png'} <= filstier
            assert (rot / 'web/hd/KN3.ob/031.png').read_bytes() == (rot / 'web/hd/HE3.ob/031.png').read_bytes()
            kn_m = Image.open(rot / 'web/hd/KN3.ob/031.mask.png').convert('RGBA')
            he_m = Image.open(rot / 'web/hd/HE3.ob/031.mask.png').convert('RGBA')
            assert piksler(he_m) == [(r + 3 if r in (7, 8, 9) else r, g, b, a) for r, g, b, a in piksler(kn_m)]
        assert not any(r['hd_fil'] == 'HE3.ob/031.png' for r in rader)
        files = json.loads((rot / 'web/hd/manifest.json').read_text())['files']
        assert bestilling.logo_gjennomfort(str(rot), files)
        assert not any(r['hd_fil'] == 'bold.f/073.png' for r in rader)
        bad_files = [dict(r, sha256='0'*64) if r['path'] == 'bold.f/073.png' else r for r in files]
        assert not bestilling.logo_gjennomfort(str(rot), bad_files)
        assert all(int(r['prioritet']) == 2 for r in rader if r['hd_fil'].startswith('bg/'))
        assert all(r['prioritet'] == '4' for r in rader if r['gruppe'] == 'Intro og slutt')
        assert not any('Kan ikke vises ennå' in r['merknad'] or 'vises ikke ennå' in r['merknad'] for r in rader)
        for r in rader:
            if r['fil'].lower() == 'wi1.c':
                assert r['trenger_maske'] == ('ja' if 15 <= int(r['bilde']) <= 20 else 'nei')
            if r['fil'].lower() == 'dice.cel':
                assert r['trenger_maske'] == ('ja' if int(r['bilde']) in (6,7) else 'nei')
            if r['fil'].lower() == 'kn5.ob':
                assert r['trenger_maske'] == ('ja' if int(r['bilde']) in (0, 1, 4, 5, 6, 20, 22, 23) else 'nei')
        assert not any('Bruk dem gjerne' in r['merknad'] for r in rader)
        assert all(r['prioritet'] == ('1' if int(r['bilde']) <= 5 else '3')
                   for r in rader if r['fil'].lower() == 'mys.cel')
        assert all(r['prioritet'] == ('1' if int(r['bilde']) <= 5 else '4')
                   for r in rader if r['fil'].lower() == 'dice.cel')
        kontroller += 12
    print('%d kildebaserte bestillings-/maskekontroller består.' % kontroller)
    print(resultat.stdout.strip())


if __name__ == '__main__':
    main()
