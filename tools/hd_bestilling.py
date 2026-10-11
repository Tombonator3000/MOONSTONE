#!/usr/bin/env python3
"""
hd_bestilling.py - lager bestillingslisten over HD-bildene som skal tegnes.

    python3 tools/hd_bestilling.py Moonstonecd32-AMIGA.zip docs/hd-bestilling-liste.csv
    python3 tools/hd_bestilling.py --maske assets/gfx/KN1.ob/012.png hd/KN1.ob/012.mask.png

Listen har en rad per bilde som må tegnes eller tegnes på nytt, i prioritert
rekkefølge, med eksakt sti i HD-pakken og størrelse. Den bygger på
docs/hd-mangler.md (prioriteten og hashene til bakgrunnene, som er målt i
emulatoren), spillfilen (størrelser, tomme bilder og like bilder), web/hd/manifest.json
(det som allerede har HD) og art/photoreal/catalog.json (utkast som finnes).

Regler:
  - Tomme bilder (ingen bitplan) og bilder som allerede har HD, tas ikke med.
  - Like bilder (samme størrelse og samme fargeindekser) får en rad. Merknaden sier
    hvor tegningen også skal ligge.
  - HE1-3.ob er ofte KN1-3.ob med indeksene 6, 7, 8 byttet til 9, 10, 11. Da er det
    samme tegning, og bare masken er forskjellig. Slike HE-bilder får ingen egen rad.
  - Filer som bare lastes av programmet `program` (intro og slutt) får prioritet
    «senere». De kan ikke vises i HD ennå (docs/hd-mangler.md punkt 4).
  - Skala 4 ganger originalen i begge retninger (se docs/hd-bestilling-chatgpt.md).

--maske lager et utgangspunkt for masken til en figur som får fargen fra paletten:
kildebildet fra tools/gfx.py extract forstørret 4 ganger med nærmeste nabo, med
palettindeksen i rødkanalen (grønn og blå 0) og alfa 255 der figuren er. Formatet
kan bli justert når visningskoden er ferdig.

Skriver også en oppsummering per gruppe til stdout, så tallene kan sjekkes mot
docs/hd-mangler.md.
"""
import collections
import csv
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import moonfiles as mf  # noqa: E402

ROT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKALA = 4
FIGURER = ('.cel', '.c', '.ob', '.f', '.font')

# Ridderne deler figursett og får fargen fra paletten (docs/hd-mangler.md punkt 4.2).
PALETT = {'KN1.ob', 'KN2.ob', 'KN3.ob', 'KN4.ob', 'KN5.ob', 'HE1.ob', 'HE2.ob', 'HE3.ob'}
HE_TIL_KN = {'HE1.ob': 'KN1.ob', 'HE2.ob': 'KN2.ob', 'HE3.ob': 'KN3.ob'}
HE_BYTTE = {6: 9, 7: 10, 8: 11}
# Har HD i dag, men skal tegnes paa nytt.
PAA_NYTT = {('bold.f', 73)}

MONSTRE = {
    'Balok': 'Balok', 'be1.c': 'beistet', 'be2.c': 'beistet (blod og hugg)', 'Demon': 'demonen',
    'DRAGON': 'dragen', 'Mudmen': 'mudmen', 'RATMEN': 'rottemennene', 'TROGGAxe': 'troggen med øks',
    'TROGGSpear': 'troggen med spyd', 'TROLL': 'trollet',
}

# Figurer i hovedspillet: prioritet, gruppe, hvor, merknad. Prioriteten er den i
# docs/hd-mangler.md punkt 2. KN5.ob står der både under ridderne og under blod;
# her ligger den under blod (10), fordi kroppene er viktigere enn sårene.
def figur_info(fil, nr):
    f = fil.lower()
    if f == 'mi.c':
        hvor = 'Kartet hele tiden: ridderhodet i ridderfarger, områdeomrisset, valgrullen (032) og dragen'
        return 2, 'Kartfigurer', hvor, 'Klar (fil/bilde), ikke prøvd. Hodene i ridderfarger er egne bilder, så faste farger går.'
    if f == 'ki.cel':
        if nr in (34, 35, 36):
            hvor = 'Statusskjermen: rankene på buen'
        elif nr == 44:
            hvor = 'Statusskjermen: NEXT KNIGHT'
        else:
            hvor = 'Statusskjermen: STR, CON, END, XP, GOLD, HIT'
        return 3, 'Statusskjerm', hvor, ('Klar. Lag den som konturikon som resten av ki.cel (tools/hd_ikoner_bygg.py). '
                                         'Fotoutkastene i art/photoreal passer ikke med konturikonene.')
    if f in ('kn1.ob', 'kn2.ob', 'kn3.ob', 'he1.ob', 'he2.ob', 'he3.ob'):
        farge = 'gylden i grafikklisten, indeksene 9-11' if f.startswith('he') else 'indeksene 6-8'
        return 5, 'Riddere', 'Alle kamper: ridderens kropp (%s), tegnes ti ganger i sekundet' % farge, \
            'Får støtte i koden i en parallell endring (figurer i flere deler og farge fra paletten).'
    if f == 'kn4.ob':
        return 5, 'Riddere', 'Alle kamper: ridderens våpen (sverd, lanse) over kroppen', \
            'Får støtte i koden i en parallell endring. Sverdet tegnes over kroppen i KN1-3.'
    if f == 'kn5.ob':
        return 10, 'Blod og sår', 'Kamp: blod og sår på ridderen', \
            'Ikke sett i tegnelisten ennå (antatt i bruk). Overlapper ridderen.'
    if f == 'blo.cel':
        return 10, 'Blod og sår', 'Kamp: blodsprut over ridder og monster', \
            'Faste farger. Ikke sett i tegnelisten ennå (antatt i bruk). Overlapper figuren under.'
    for start, navn in MONSTRE.items():
        if fil.lower().startswith(start.lower()):
            return 7, 'Monstre', 'Kamp i hi og ute: %s' % navn, \
                ('Delvis klar: deler som overlapper en tidligere tegning avvises i dag (render.js:948), '
                 'støtte kommer i en parallell endring. Bare TroggSpear er målt.')
    if f == 'bold.f':
        if nr == 73:
            return 7, 'Logo', 'Tittelmenyen: MOONSTONE-logoen', \
                ('Tegnes på nytt. Dagens web/hd/bold.f/073.png er 2172 x 724 (3,0:1) mot kildens 305 x 54 '
                 '(5,65:1) og blir flatklemt. Utkastet art/photoreal/candidates/bold.f/073.png har riktig '
                 'forhold i kjernen, men står i candidate_geometry_review.')
        return 11, 'Tittelmeny', 'Tittelmenyen: copyrightlinjene', 'Klar, ikke prøvd. Tegn teksten nøyaktig som i originalen.'
    if f == 'sel.cel':
        return 11, 'Meny', 'Trolig Select a Knight: en tom ramme (ikke menypilen)', 'Klar, ikke prøvd. Hvor den vises er antatt.'
    if f == 'dice.cel':
        return 8, 'Taverna og by', 'Tavernaen: terningspillet (terninger, beger, hender)', \
            'Klar. Bilde 6 og 7 er sett i tegnelisten, resten er ikke prøvd.'
    if f == 'mys.cel':
        return 8, 'Taverna og by', 'Waterdeep: Mythrid the Mystic (knapper og ting)', 'Klar, ikke prøvd.'
    if f == 'wi1.c':
        return 10, 'Stedsfigurer', 'Tårnet i fjellene: trollmannen Math', 'Klar, ikke prøvd.'
    if f == 'hen1.c':
        return 10, 'Stedsfigurer', 'Stonehenge og tempelet i slutten: ting og flammer', 'Klar, ikke prøvd.'
    raise SystemExit('Ingen prioritet for %s' % fil)


INTRO_HVOR = {
    'au1.cel': 'Introen eller slutten: et ansikt og hugg og våpenbiter',
    'co1.cel': 'Introen eller slutten: figurer i rødt og gull',
    'da1.cel': 'Introen eller slutten: små røde og hvite figurer',
    'dg1.cel': 'Introen eller slutten: et grønt beist med lange bein',
    'dw1.cel': 'Introen eller slutten: druidene ved Stonehenge og flammer',
    'ha1.cel': 'Introen eller slutten: hender og arm i rustning (Valley of the Gods)',
    'Klift1.CEL': 'Introen eller slutten: Klift',
    'li1.cel': 'Introen eller slutten: lyn og magi',
    'ov1.cel': 'Introen eller slutten: forgrunn (busker og røde blader)',
}
INTRO_MERKNAD = ('Kan ikke vises ennå: intro og slutt kjøres av programmet program, der laget og '
                 'tegnelisten mangler (docs/hd-mangler.md punkt 4.4). Ikke tegn dette før det er løst.')

# Bakgrunner. Hashene er målt i emulatoren (docs/hd-mangler.md punkt 2). For PIV-filene
# regnes hashen også ut her og sjekkes. (prioritet, gruppe, kildefil, bilde, hash, hvor, merknad)
LAIR_HASH = {
    'fol': ('skog', ['3a38d016', '5ecac111', '5e1dc378', '5c6a3697', '954ee2f9', 'db6fc7ba']),
    'gll': ('lysning', ['4b68f426', '8feef9f5', '6113f65e', '6b05bdcd', 'b95b11e9', '73c7f5c1']),
    'swl': ('sump', ['14a894c2', 'b7afa780', 'df1460be', '4aca74c6', '09b477b7', 'b33ce188']),
    'wal': ('klipper og vann', ['ed554452', '756408ca', '850cdd99', '93d40a06', '75c0760c', '5c5085b2']),
}

BAKGRUNNER = [
    (4, 'Byskjermer', '-', '', 'e868fda9', 'Butikken med to buer: Merchant og High Temple',
     'Klar. Bygget skjerm uten egen PIV-fil. Kilde: art/photoreal/references/runtime_background/e868fda9.png.'),
    (4, 'Byskjermer', '-', '', '94e65527', 'Inventaret mellom turene (en bue)',
     'Klar. Bygget skjerm uten egen PIV-fil. Kilde: art/photoreal/references/runtime_background/94e65527.png.'),
    (4, 'Byskjermer', 'hea.piv', 0, '2e3c32ae', 'Healeren i Highwood (Waterdeep antatt lik)',
     'Klar. Utkast finnes (needs_revision: bokdiagrammet er endret). Tegnes på nytt.'),
    (8, 'Steder', 'mys.piv', 0, 'd8b4018a', 'Mythrid the Mystic i Waterdeep',
     'Klar. Utkast finnes (needs_revision: nye tegn). Tegnes på nytt.'),
    (8, 'Steder', 'hen1.p', 0, '94c7f163', 'Druidene ved Stonehenge og tempelet i slutten',
     'Klar. hen1.p og bg5.piv er like, ett bilde dekker begge. Utkast finnes (candidate_geometry_review).'),
    (8, 'Steder', 'WI1.P', 0, '71970806', 'Trollmannen Math i tårnet',
     ('Trenger en scene i manifest.json, fordi spillet skriver tekst inn i bakgrunnen (målt 4d4fb3f3, 27ddabfe, '
      '7e2863f2). Tegn bildet uten tekst. Utkast finnes (needs_revision: synlig skjøt).')),
    (8, 'Steder', 'WI2.P', 0, 'da1dc997', 'Tårnet til Math sett utenfra',
     ('Trenger en scene. Hashen er regnet fra PIV-filen, skjermen uten tekst er aldri sett i spillet. '
      'Utkast finnes (needs_revision: en stjerne for mye og to mangler).')),
    (8, 'Taverna og by', 'dice.piv', 0, 'c6a4a00e', 'Tavernaen: bordet i terningspillet',
     ('Trenger en scene: hvert spill gir en ny hash (10 målt). Tegn det rene bordet. Utkastet er bare en '
      'treflate (candidate_geometry_review).')),
    (9, 'Introscener', 'bg3.PIV', 0, 'c2501c17', 'Introen: steinsirkelen sett ovenfra',
     'Scene (samsvar 1,0 målt). Utkast finnes (needs_revision: alteret og bakkelinjene).'),
    (9, 'Introscener', 'bg1b.PIV', 0, 'd744b02e', 'Introen: skog med tykke stammer',
     'Scene (samsvar 0,92-0,99 målt). Flisutkastene i art/photoreal er ikke satt sammen.'),
    (9, 'Introscener', 'bg2a.PIV', 0, 'a45a2508', 'Introen: ridderen foran Stonehenge',
     'Scene, men samsvaret er bare 0,74 målt. Utkast finnes (needs_revision: slyngen).'),
    (9, 'Introscener', 'mindscape', 0, '46963198', 'Introen: Mindscape-logoen',
     'Scene, men samsvaret er bare 0,77 målt. Utkast finnes (en gullflate, candidate_geometry_review).'),
    (11, 'Sluttscene', 'bg7.PIV', 0, 'e2e904b2', 'Slutten: virvel over vann',
     'Scene. 16 farger (fire plan). Ingen utkast finnes.'),
    (11, 'Sluttscene', 'bg8.PIV', 0, 'd0f67acb', 'Slutten: to figurer under stjernehimmelen',
     'Scene. Utkast finnes (needs_revision: for mange og for lyse stjerner).'),
]


def fnv(b):
    h = 2166136261
    for x in b:
        h = ((h ^ x) * 16777619) & 0xffffffff
    return '%08x' % h


def piv_hash(spill, fil, nr):
    bilder, _ = mf.piv_alle(spill.les('data/' + fil))
    plan, _, bp = bilder[nr]
    return fnv(bp + bytes(40 * 200 * 5 - len(bp)))


def utkast(katalog):
    ut = {}
    for r in katalog['rows']:
        d = r['id'].split(':')
        if d[0] == 'sprite':
            ut[(d[1].lower(), int(d[2]))] = r['status']
    return ut


def lag_maske(kilde, ut):
    from PIL import Image
    im = Image.open(kilde)
    if im.mode != 'P':
        raise SystemExit('%s er ikke et indeksert PNG fra tools/gfx.py extract' % kilde)
    w, h = im.size
    r = Image.frombytes('L', (w, h), im.tobytes()).resize((w * SKALA, h * SKALA), Image.NEAREST)
    null = Image.new('L', r.size, 0)
    alfa = r.point(lambda v: 255 if v else 0)
    os.makedirs(os.path.dirname(ut) or '.', exist_ok=True)
    Image.merge('RGBA', (r, null, null, alfa)).save(ut)
    print('%s: %d x %d' % (ut, r.size[0], r.size[1]))


def main():
    if len(sys.argv) == 4 and sys.argv[1] == '--maske':
        lag_maske(sys.argv[2], sys.argv[3])
        return
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    spill = mf.Spill(sys.argv[1])
    ut_sti = sys.argv[2]
    with open(os.path.join(ROT, 'web/hd/manifest.json')) as f:
        har_hd = {x['path'][:-4].lower() for x in json.load(f)['files'] if x['path'].endswith('.png')}
    with open(os.path.join(ROT, 'art/photoreal/catalog.json')) as f:
        utk = utkast(json.load(f))
    program = spill.les('data/program').lower()
    mog = spill.les('data/mog').lower()

    # alle figurbilder
    bilder = []      # (fil, nr, w, h, indekser)
    tomme = 0
    for sti in sorted(spill.data_filer(), key=str.lower):
        fil = sti.split('/', 1)[1]
        data = spill.filer[sti]
        if not (fil.lower().endswith(FIGURER) and mf.er_cel(data)):
            continue
        for nr, b in enumerate(mf.cel_les(data)[0]):
            if b['plan'] == 0:
                tomme += 1
                continue
            ind = mf.plan_til_indeks(b['data'], b['plan'], b['bredde'], b['hoyde'])
            bilder.append((fil, nr, b['bredde'], b['hoyde'], ind))

    def bare_intro(fil):
        f = fil.lower().encode()
        return f in program and f not in mog

    def rang(b):
        fil, nr = b[0], b[1]
        if bare_intro(fil):
            return (99, 2, fil.lower(), nr)
        p = figur_info(fil, nr)[0]
        return (p, 0 if fil.startswith('KN') else 1, fil.lower(), nr)

    mangler = [b for b in bilder if '%s/%03d' % (b[0].lower(), b[1]) not in har_hd or (b[0], b[1]) in PAA_NYTT]
    mangler.sort(key=rang)

    # like bilder: første i rekkefølgen tegnes, de andre nevnes i merknaden
    like = collections.defaultdict(list)
    forste = {}
    for b in mangler:
        k = (b[2], b[3], b[4])
        if k in forste:
            like[forste[k]].append(b)
        else:
            forste[k] = (b[0], b[1])
    for b in bilder:
        if (b[0], b[1]) in PAA_NYTT:
            continue
        if '%s/%03d' % (b[0].lower(), b[1]) in har_hd and (b[2], b[3], b[4]) in forste:
            raise SystemExit('%s/%03d har HD, men et likt bilde mangler' % (b[0], b[1]))
    dubletter = {(b[0], b[1]) for v in like.values() for b in v}

    # HE som er KN med indeksene 6-8 byttet til 9-11
    kn = {}
    for b in mangler:
        if b[0] in HE_TIL_KN.values() and (b[0], b[1]) not in dubletter:
            kn.setdefault((b[0], b[2], b[3]), []).append(b)
    he_kopi = collections.defaultdict(list)

    def er_bytte(k, h):
        # hver indeks i KN-bildet blir enten seg selv eller 6->9, 7->10, 8->11, alltid likt,
        # og KN-bildet bruker ikke 9-11, saa masken kan byttes tilbake entydig
        par = {}
        for p, q in zip(k, h):
            if par.setdefault(p, q) != q or (p != q and HE_BYTTE.get(p) != q):
                return False
        return not (set(par) & set(HE_BYTTE.values()))

    for b in mangler:
        if b[0] not in HE_TIL_KN or (b[0], b[1]) in dubletter:
            continue
        kandidater = kn.get((HE_TIL_KN[b[0]], b[2], b[3]), [])
        kandidater = sorted(kandidater, key=lambda k: (k[1] != b[1], k[1]))
        for k in kandidater:
            if er_bytte(k[4], b[4]):
                he_kopi[(k[0], k[1])].append(b)
                dubletter.add((b[0], b[1]))
                break

    rader = []
    teller = collections.Counter()
    for b in mangler:
        fil, nr, w, h, _ = b
        if (fil, nr) in dubletter:
            continue
        hd_fil = '%s/%03d.png' % (fil, nr)
        palett = 'ja' if fil in PALETT else 'nei'
        if bare_intro(fil):
            pri, gruppe, hvor, merk = 'senere', 'Intro og slutt', INTRO_HVOR[fil], INTRO_MERKNAD
        else:
            pri, gruppe, hvor, merk = figur_info(fil, nr)
        ekstra = []
        andre = like.get((fil, nr), [])
        if andre:
            ekstra.append('Samme bilde brukes også som %s. Legg samme tegning der.'
                          % ', '.join('%s/%03d.png' % (a[0], a[1]) for a in andre))
            if any(bare_intro(a[0]) for a in andre) and not bare_intro(fil):
                ekstra.append('Kopien i introfilen vises ikke ennå, men skader ikke.')
            if palett == 'ja' and any(a[0] not in PALETT for a in andre):
                ekstra.append('Kopien hos monsteret vises med tegningens egne farger, uten maske.')
        for a in he_kopi.get((fil, nr), []):
            ekstra.append('Samme tegning skal også ligge som %s/%03d.png. Der er indeksene 6, 7, 8 byttet til '
                          '9, 10, 11, så masken %s/%03d.mask.png er denne masken med de tre verdiene byttet.'
                          % (a[0], a[1], a[0], a[1]))
        s = utk.get((fil.lower(), nr))
        if s and 'candidates' not in merk:
            ekstra.append('Utkast i art/photoreal/candidates/%s (%s), ikke godkjent.' % (fil, s))
            if fil.upper().startswith('TROLL'):
                ekstra.append('Trollet er blått i spillet, utkastene er brune og gylne.')
        rader.append([pri, gruppe, fil, nr, hd_fil, w, h, w * SKALA, h * SKALA, palett, palett, hvor,
                      ' '.join([merk] + ekstra)])
        teller[(pri, gruppe)] += 1

    # bakgrunner
    bg = []
    for kort, (navn, hashes) in LAIR_HASH.items():
        for i, h in enumerate(hashes):
            fil = '%s%d.t' % (kort, i + 1)
            bg.append((1, 'Hulekamp', fil, '', h, 'Kamp etter Enter Lair: %s' % navn,
                       ('Klar. Utkast finnes (art/photoreal/candidates, needs_revision: runene). Godtar eieren ikke '
                        'runene, tegnes det på nytt. Kilde: art/photoreal/references/runtime_background/%s.png.' % fil)))
    for r in BAKGRUNNER:
        pri, gruppe, fil, nr, h, hvor, merk = r
        if fil != '-':
            regnet = piv_hash(spill, fil, nr)
            if regnet != h:
                raise SystemExit('Hashen til %s er %s, ikke %s' % (fil, regnet, h))
            merk += ' Kilde: assets/gfx/%s/%d.png (tools/gfx.py extract).' % (fil, nr)
        bg.append(r[:6] + (merk,))
    for pri, gruppe, fil, nr, h, hvor, merk in bg:
        if 'bg/' + h in har_hd:
            raise SystemExit('bg/%s har allerede HD' % h)
        rader.append([pri, gruppe, fil, nr, 'bg/%s.png' % h, 320, 200, 320 * SKALA, 200 * SKALA,
                      'nei', 'nei', hvor, merk])
        teller[(pri, gruppe)] += 1

    rader.sort(key=lambda r: (99 if r[0] == 'senere' else r[0], r[1], not r[4].startswith('bg/'),
                              not r[2].startswith('KN'), r[2].lower(), r[3] if r[3] != '' else -1))
    with open(ut_sti, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f, delimiter=';', lineterminator='\n')
        w.writerow(['prioritet', 'gruppe', 'fil', 'bilde', 'hd_fil', 'kilde_bredde', 'kilde_hoyde', 'hd_bredde',
                    'hd_hoyde', 'farger_fra_palett', 'trenger_maske', 'hvor_i_spillet', 'merknad'])
        w.writerows(rader)

    # oppsummering
    print('Figurbilder i spillet: %d, tomme %d, med innhold %d' % (len(bilder) + tomme, tomme, len(bilder)))
    ny = [b for b in mangler if (b[0], b[1]) not in PAA_NYTT]
    print('Med innhold uten HD: %d (hovedspillet %d, bare intro/slutt %d). Tegnes på nytt: %d'
          % (len(ny), sum(not bare_intro(b[0]) for b in ny), sum(bare_intro(b[0]) for b in ny), len(PAA_NYTT)))
    lik_n = sum(len(v) for v in like.values())
    he_n = sum(len(v) for v in he_kopi.values())
    print('Like bilder slått sammen: %d. HE-bilder som er KN med byttede indekser: %d' % (lik_n, he_n))
    print('Rader: %d (figurer %d, bakgrunner %d)' % (len(rader), len(rader) - len(bg), len(bg)))
    for (pri, gruppe), n in sorted(teller.items(), key=lambda x: (99 if x[0][0] == 'senere' else x[0][0], x[0][1])):
        print('  %-7s %-16s %4d' % (pri, gruppe, n))


if __name__ == '__main__':
    main()
