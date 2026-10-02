#!/usr/bin/env python3
"""
gfx.py - pakker grafikken i Moonstone ut som PNG og inn igjen.

    python3 tools/gfx.py extract Moonstonecd32-AMIGA.zip assets/gfx
    (rediger PNG-ene, behold fargeindeksene)
    python3 tools/gfx.py build Moonstonecd32-AMIGA.zip assets/gfx mod
    port/moonstone --mod mod          (eller velg mod-mappen på nettsiden)

extract lager en mappe per fil:
  bilder (PIV, .p, mindscape, Test): et PNG per bilde, 320 x 200, med paletten fra filen
  figurer (CEL, .c, .ob, .f, .font): et PNG per bilde (000.png, 001.png ...)
og assets/gfx/index.json som beskriver alt.

PNG-ene er indekserte. Det er indeksene (0-31) som teller; fargene i figurene er
bare forhåndsvisning (spillet bruker paletten til skjermen de vises på). Bruk et
tegneprogram som beholder paletten (f.eks. GIMP i modus "Indeksert", Aseprite).

build leser PNG-ene og lager nye datafiler i utmappen, bare for filer som er
endret. En fil som ikke er endret, blir byte for byte lik originalen
(rundtur-sjekk: build uten endringer gir ingen filer, og --alle gir kopier som
er identiske med originalene).

Krever Python 3 og Pillow (pip install pillow).
"""
import hashlib
import json
import os
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import moonfiles as mf  # noqa: E402

FIGURER = ('.cel', '.c', '.ob', '.f', '.font')


def sha(b):
    return hashlib.sha1(b).hexdigest()


def finn_type(navn, data):
    n = navn.lower()
    if n.endswith(FIGURER) and mf.er_cel(data):
        return 'figurer'
    if mf.er_piv(data):
        return 'bilder'
    return None


def standard_palett(spill):
    """Palett til forhåndsvisning av figurer: skogbakgrunnen i Test (bilde 4)."""
    try:
        bilder, _ = mf.piv_alle(spill.les('data/test'))
        return bilder[4][1]
    except Exception:
        return [i * 0x111 & 0xfff for i in range(32)]


def palett_liste(palett):
    ut = []
    for c in palett:
        ut += mf.amiga_rgb(c & 0xfff)
    ut += [0] * (768 - len(ut))
    return ut


def lagre_png(sti, indekser, bredde, hoyde, palett):
    im = Image.frombytes('P', (bredde, hoyde), bytes(indekser))
    im.putpalette(palett_liste(palett))
    im.info['transparency'] = 0
    im.save(sti, optimize=True)


def les_png(sti, bredde, hoyde):
    im = Image.open(sti)
    if im.mode != 'P':
        raise SystemExit('%s er ikke et indeksert PNG (modus %s). Lagre med palett.' % (sti, im.mode))
    if im.size != (bredde, hoyde):
        raise SystemExit('%s har feil størrelse %s, skal være %dx%d' % (sti, im.size, bredde, hoyde))
    return im.tobytes()


def figur_indekser(b):
    return mf.plan_til_indeks(b['data'], b['plan'], b['bredde'], b['hoyde'])


def extract(spill_sti, ut):
    spill = mf.Spill(spill_sti)
    os.makedirs(ut, exist_ok=True)
    pal_fig = standard_palett(spill)
    indeks = {'filer': {}}
    for sti in spill.data_filer():
        data = spill.filer[sti]
        navn = sti.split('/', 1)[1]
        t = finn_type(navn, data)
        if not t:
            continue
        mappe = os.path.join(ut, navn)
        os.makedirs(mappe, exist_ok=True)
        if t == 'bilder':
            bilder, slutt = mf.piv_alle(data)
            info = {'type': t, 'sha1': sha(data), 'bilder': [], 'hale': data[slutt:].hex()}
            for i, (plan, palett, bitplan) in enumerate(bilder):
                ind = mf.plan_til_indeks(bitplan, plan)
                fil = '%d.png' % i
                lagre_png(os.path.join(mappe, fil), ind, 320, 200, palett)
                info['bilder'].append({'fil': fil, 'plan': plan, 'palett': ['%04x' % c for c in palett],
                                       'sha1': sha(bitplan)})
        else:
            bilder, minne = mf.cel_les(data)
            info = {'type': t, 'sha1': sha(data), 'minne': minne, 'bilder': []}
            for i, b in enumerate(bilder):
                fil = '%03d.png' % i
                lagre_png(os.path.join(mappe, fil), figur_indekser(b), b['bredde'], b['hoyde'], pal_fig)
                info['bilder'].append({'fil': fil, 'bredde': b['bredde'], 'hoyde': b['hoyde'],
                                       'flagg': b['flagg'], 'maske': b['maske'], 'sha1': sha(b['data'])})
        indeks['filer'][sti] = info
        print('%-24s %s, %d bilder' % (navn, t, len(info['bilder'])))
    with open(os.path.join(ut, 'index.json'), 'w') as f:
        json.dump(indeks, f, indent=1)
    print('Ferdig: %d filer i %s' % (len(indeks['filer']), ut))


def build(spill_sti, inn, ut, alle=False):
    spill = mf.Spill(spill_sti)
    with open(os.path.join(inn, 'index.json')) as f:
        indeks = json.load(f)
    os.makedirs(ut, exist_ok=True)
    endret = 0
    for sti, info in indeks['filer'].items():
        navn = sti.split('/', 1)[1]
        mappe = os.path.join(inn, navn)
        original = spill.filer[sti]
        nye = []
        lik = True
        if info['type'] == 'bilder':
            for b in info['bilder']:
                ind = les_png(os.path.join(mappe, b['fil']), 320, 200)
                bitplan = mf.indeks_til_plan(ind, b['plan'])
                if sha(bitplan) != b['sha1']:
                    lik = False
                nye.append((b['plan'], [int(c, 16) for c in b['palett']], bitplan))
            data = original if lik else b''.join(mf.piv_lag(*x) for x in nye) + bytes.fromhex(info.get('hale', ''))
        else:
            for b in info['bilder']:
                ind = les_png(os.path.join(mappe, b['fil']), b['bredde'], b['hoyde'])
                plan = bin(b['maske']).count('1')
                ind = bytes(v & ((1 << plan) - 1) for v in ind)
                d = mf.indeks_til_plan(ind, plan, b['bredde'], b['hoyde'])
                if sha(d) != b['sha1']:
                    lik = False
                nye.append(dict(bredde=b['bredde'], hoyde=b['hoyde'], flagg=b['flagg'], maske=b['maske'], data=d))
            data = original if lik else mf.cel_lag(nye)
        if lik and not alle:
            continue
        if not lik:
            endret += 1
            print('endret: %s (%d -> %d byte)' % (navn, len(original), len(data)))
        with open(os.path.join(ut, navn), 'wb') as f:
            f.write(data)
    print('Ferdig: %d endrede filer i %s' % (endret, ut))


def main():
    a = sys.argv[1:]
    if len(a) >= 3 and a[0] == 'extract':
        extract(a[1], a[2])
    elif len(a) >= 4 and a[0] == 'build':
        build(a[1], a[2], a[3], '--alle' in a)
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == '__main__':
    main()
