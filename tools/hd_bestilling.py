#!/usr/bin/env python3
"""
hd_bestilling.py - lager bestillingslisten over HD-bildene som skal tegnes.

    python3 tools/hd_bestilling.py Moonstonecd32-AMIGA.zip docs/hd-bestilling-liste.csv
    python3 tools/hd_bestilling.py --maske assets/gfx/KN1.ob/012.png hd/KN1.ob/012.mask.png [hd/KN1.ob/012.png]
    python3 tools/hd_bestilling.py --maske assets/gfx/HE3.ob/031.png hd/HE3.ob/031.mask.png hd/HE3.ob/031.png --graa-referanse 128

Listen har en rad per bilde som må tegnes eller tegnes på nytt, i prioritert
rekkefølge, med eksakt sti i HD-pakken og størrelse. Den bygger på
docs/hd-mangler.md (prioriteten og hashene til bakgrunnene, som er målt i
emulatoren), spillfilen (størrelser, tomme bilder og like bilder), web/hd/manifest.json
(det som allerede har HD) og art/photoreal/catalog.json (utkast som finnes).

Regler:
  - Tomme bilder (ingen bitplan) og bilder med egen bank-PNG i manifestet tas ikke
    med. Poser som dekker flere originalruter er egne metodeprøver, ikke ferdige
    separate ruter; de utelater derfor ikke nytegningene i bestillingen.
  - Like bilder (samme størrelse og samme fargeindekser) får en rad. Merknaden sier
    hvor tegningen også skal ligge.
  - HE1-3.ob er ofte KN1-3.ob med indeksene 6, 7, 8 byttet til 9, 10, 11. Da er det
    samme tegning, og bare masken er forskjellig. Slike HE-bilder får ingen egen rad.
  - Ikoner og UI tas først, deretter alle bakgrunner og logoen. Figurer og
    animasjoner tas til slutt, hver rute for seg.
  - Intro og slutt har teknisk HD-støtte og får prioritet4, etter ikonene og
    bakgrunnene. Hver rute trenger fortsatt separat nytegning og runtimekontroll.
  - Skala 4 ganger originalen i begge retninger (se docs/hd-bestilling-chatgpt.md).

--maske lager masken til en figur som får fargen fra paletten, i formatet visningen
leser (docs/hd-grafikk.md, «Farge fra paletten»): R = palettindeks + 1 for
ridderfargene (indeks 6-11; Math015..020 bare6..10), ellers 0 (behold tegningens farge); G = lysstyrke
(128 = palettfargen); B = 255 der R er satt; alfa 255. Kilden er det indekserte
bildet fra tools/gfx.py extract, forstørret med nærmeste nabo til 4x, eller til
målene på HD-tegningen når den er gitt. Med tegningen regnes G ut av lysstyrken i
tegningen mot lysstyrken til forhåndsvisningsfargen i kilden, så skyggene i
rustningen blir med.

Skriver også en oppsummering per gruppe til stdout, så tallene kan sjekkes mot
docs/hd-mangler.md.
"""
import argparse
import collections
import csv
import hashlib
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
# Indeksene spillet farger etter hvilken ridder som kjemper: 6-8 (kn) og 9-11 (he).
# Bare de faar maske; resten av tegningen beholder fargene sine.
RIDDERFARGER = set(range(6, 12))
# Har HD i dag, men skal tegnes paa nytt.
PAA_NYTT = {('bold.f', 73)}
LOGO_SHA256 = 'd7d656cab28178c074feac994a463d1d558ee4bdcfb955675c09881c41071846'


def maskefarger(bank, frame):
    """Eksakte levende indeksfelt, uavhengig av den valgte forhåndspaletten."""
    # KN5 brukes ogsaa i dragekampen: $088c16 setter faste roedfarger9..15
    # og ild29..31. Riddervelgeren $088ca0 endrer bare6..8, ikke9..11.
    if bank.lower() == 'kn5.ob':
        return {6, 7, 8}
    # Bare disse dragefragmentene inneholder den aktive ridderens drakt.
    # Dragens roede9..15 og ild29..31 er faste i $088c16.
    if bank.lower() == 'dragon2.cel' and frame in (17, 18, 19):
        return {6, 7, 8}
    if bank.lower() == 'dragon5.cel' and frame in (32, 35):
        return {6, 7, 8}
    if bank.lower() in {b.lower() for b in PALETT}:
        return RIDDERFARGER
    # Math-tårnet: $089478-$089484 sender WI2.P+12 til $08a9b6.
    # Aktiv ridder+0x36 velger fem farger. Balkonens000..014 er faste.
    if bank.lower() == 'wi1.c' and 15 <= frame <= 20:
        return set(range(6, 11))
    # Tavernaen: $08a3b2 sender tav-palett+12 til samme originale setter.
    # Bare006/007 har levende draktindekser;008/009 er hanske,010..022 er terninger.
    if bank.lower() == 'dice.cel' and frame in (6, 7):
        return set(range(6, 11))
    # LI1: originalintro4464/4473/4528 bruker svart, normal og hvitblink.
    # Hvert ikke-null kildefelt trenger sin eksakte NN-indeks, ikke bare draktfarger.
    if bank.lower() == 'li1.cel' and 0 <= frame < 30:
        return set(range(1, 32))
    # Oppstigningen deler den faktiske bla skanout-paletten med LI1.
    # Bare040..054 bruker modus3; tidligere ritual- og flammeruter er uendret.
    if bank.lower() in {'hen1.c', 'klift1.cel'} and 40 <= frame <= 54:
        return set(range(1, 32))
    return set()


def logo_gjennomfort(rot, filer):
    """Bare den kildebundne1220x216-leveransen fjerner logoens revisjon."""
    from PIL import Image
    path = os.path.join(rot, 'web/hd/bold.f/073.png')
    entry = next((r for r in filer if r['path'] == 'bold.f/073.png'), None)
    if not entry or entry.get('sha256') != LOGO_SHA256 or not os.path.isfile(path):
        return False
    with open(path, 'rb') as f:
        if hashlib.sha256(f.read()).hexdigest() != LOGO_SHA256:
            return False
    with Image.open(path) as im:
        return im.size == (1220, 216) and im.mode == 'RGBA'

MONSTRE = {
    'Balok': 'Balok', 'be1.c': 'beistet', 'be2.c': 'beistet (blod og hugg)', 'Demon': 'demonen',
    'DRAGON': 'dragen', 'Mudmen': 'mudmen', 'RATMEN': 'rottemennene', 'TROGGAxe': 'troggen med øks',
    'TROGGSpear': 'troggen med spyd', 'TROLL': 'trollet',
}

# Figurer i hovedspillet: prioritet, gruppe, hvor, merknad. Brukerens rekkefølge
# gjelder foran den eldre frekvensbaserte listen i docs/hd-mangler.md.
def figur_info(fil, nr):
    f = fil.lower()
    if f == 'mi.c':
        if 34 <= nr <= 41:
            return 4, 'Drageanimasjon', 'Kartet: drageanimasjon, åtte ruter', \
                'Figuranimasjon, tas til slutt. Nytegn hver rute separat og kontroller bevegelse og overlapping mot originalen.'
        if nr == 32:
            return 1, 'Kart-UI', 'Kartet: meldingsfelt eller valgrull (032)', \
                'UI-fragment. Bevar originalens tekst, plassering og visningstid.'
        return 1, 'Kart-UI', 'Kartet: valgkontur eller områdeomriss', \
            'UI-fragment. Bevar originalens form og levende palett; ikke tegn en ny gjenstand.'
    if f == 'ki.cel':
        return 1, 'Inventar-UI', 'Inventaret: tekst- eller rammefragment', \
            'Bevar originalens bokstavform, ramme, plassering og levende palett. Kontroller delene samlet i inventaret.'
    if f in ('kn1.ob', 'kn2.ob', 'kn3.ob', 'he1.ob', 'he2.ob', 'he3.ob'):
        farge = 'gylden i grafikklisten, indeksene 9-11' if f.startswith('he') else 'indeksene 6-8'
        return 3, 'Riddere', 'Alle kamper: ridderens kropp (%s), tegnes ti ganger i sekundet' % farge, \
            'Koden støtter figurer i flere deler og farge fra paletten. Hver ny rute og overlapping må prøves.'
    if f == 'kn4.ob':
        return 3, 'Riddere', 'Alle kamper: ridderens våpen (sverd, lanse) over kroppen', \
            'Koden støtter flere deler. Sverdet tegnes over kroppen i KN1-3; ny grafikk må prøves med kroppen.'
    if f == 'kn5.ob':
        return 4, 'Blod og sår', 'Kamp: blod og sår på ridderen', \
            'Ikke sett i tegnelisten ennå (antatt i bruk). Overlapper ridderen.'
    if f == 'blo.cel':
        return 4, 'Blod og sår', 'Kamp: blodsprut over ridder og monster', \
            'Faste farger. Ikke sett i tegnelisten ennå (antatt i bruk). Overlapper figuren under.'
    for start, navn in MONSTRE.items():
        if fil.lower().startswith(start.lower()):
            return 3, 'Monstre', 'Kamp i hi og ute: %s' % navn, \
                ('Koden støtter eierskap per piksel for deler som overlapper. '
                 'Ny grafikk og animerte overlappinger må prøves; bare TroggSpear er målt i den eldre kartleggingen.')
    if f == 'bold.f':
        if nr == 73:
            return 2, 'Logo', 'Tittelmenyen: MOONSTONE-logoen', \
                ('Den kildebundne1220x216-leveransen mangler eller har avvikende SHA. '
                 'Originalens305x54-form, ansikt, skygge, treO-hull og undertekst er fasit. '
                 'Logoens tekstmetadata må passe1220x216-leveransen. '
                 'Eldre avviste utkast er bare dokumentasjon av feil, ikke tegnereferanser.')
        return 1, 'Tittelmeny', 'Tittelmenyen: copyrightlinjene', 'Klar, ikke prøvd. Tegn teksten nøyaktig som i originalen.'
    if f == 'sel.cel':
        return 1, 'Meny', 'Trolig Select a Knight: en tom ramme (ikke menypilen)', 'Klar, ikke prøvd. Hvor den vises er antatt.'
    if f == 'dice.cel':
        if nr <= 5:
            return 1, 'Kro- og byikoner', 'Tavernaen: seks faste terningsutfall', \
                'Statiske utfallsbilder. Originalkoden velger 0-5 i vis_gull_vunnet ($08a600-$08a690). Bevar hvert symbol.'
        if nr >= 10:
            return 4, 'Kroanimasjoner', 'Tavernaen: tre kastede Dragon Dice over bordet', \
                ('Animasjonsruter, tas til slutt.010..022 bruker tav.piv-paletten. '
                 'Originalsekvens0ad76e tegner hanske009 på fast posisjon mellom terningrutene. '
                 'Nytegn de tre grå terningene med nøyaktig original plassering, rotasjon og størrelse.')
        return 4, 'Kroanimasjoner', 'Tavernaen: ridderens stålhanske og arm over bordet', \
            ('Animasjonsruter, tas til slutt.006..022 bruker tav.piv-paletten, ikke dice.piv. '
             '006/007 bruker levende draktindekser6..10 fra aktiv ridder ($08a3b2→$08a9b6). '
             'Nytegn og kontroller hver rute separat i tavernascenen.')
    if f == 'mys.cel':
        if nr >= 6:
            hvor = 'Healeren: begge øyne lukket' if nr == 6 else 'Mystikeren: ett øye lukket'
            return 3, 'Stedsfigurer', hvor, \
                'Figuranimasjon, tas etter ikonene og bakgrunnene. 006 bruker HEA-paletten, 007 MYS-paletten. Kontroller mot hele originalscenen.'
        return 1, 'Kro- og byikoner', 'Mystikeren og healeren: donasjonsknapper, tekst og piler', \
            'Statisk UI. donasjon ($08a002-$08a07e) tegner knappene 0-5. Bevar originalens tekst og symboler.'
    if f == 'wi1.c':
        return 3, 'Stedsfigurer', 'Tårnet i fjellene: trollmannen Math', \
            ('Teknisk støttet.015..020 bruker WI2.P og levende maskefarger6..10 fra aktiv ridder; '
             '000..014 bruker WI1.P med fast kappe/flamme. Hver ny rute må kontrolleres i originalscenen.')
    if f == 'hen1.c':
        return 3, 'Stedsfigurer', 'Stonehenge og tempelet i slutten: ting og flammer', 'Klar, ikke prøvd.'
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
INTRO_MERKNAD = ('Teknisk HD-støtte for originalprogrammet er på plass, inkludert tegneliste og rullefliser. '
                 'Nytegn hver rute separat og kontroller dens faktiske programbruk, palett, buffer og overlapping. '
                 'Observerte tegnekall er ikke alene bevis på synlige skjermpiksler eller full animasjonsdekning.')

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
     'Har scene. hen1.p og bg5.piv er like, ett bilde dekker begge. Aktiv eldre master skal revideres direkte mot originalen.'),
    (8, 'Steder', 'WI1.P', 0, '71970806', 'Trollmannen Math i tårnet',
     ('Har scene i manifest.json fordi spillet skriver tekst inn i bakgrunnen. Tegn uten tekst og bevar '
      'originalfiguren. Eldre avvist utkast er bare feilarkiv (synlig skjøt).')),
    (8, 'Steder', 'WI2.P', 0, 'da1dc997', 'Tårnet til Math sett utenfra',
     ('Har scene. Tegn tårn, stjerner og bakgrunn direkte etter original-PIV. '
      'Eldre avvist utkast er bare feilarkiv (feil stjerner).')),
    (8, 'Taverna og by', 'dice.piv', 0, 'c6a4a00e', 'Tavernaen: bordet i terningspillet',
     ('Har scene: spillets tekst og terninger endrer skjermhashen. Tegn det rene bordet. '
      'Eldre avvist utkast er bare feilarkiv (manglende motiv).')),
    (9, 'Introscener', 'bg3.PIV', 0, 'c2501c17', 'Introen: steinsirkelen sett ovenfra',
     'Har scene. Aktiv eldre master revideres mot originalens alter og bakkelinjer. Eldre avvist kandidat er bare feilarkiv.'),
    (9, 'Introscener', 'bg1b.PIV', 0, 'd744b02e', 'Introen: skog med tykke stammer',
     'Scene (samsvar 0,92-0,99 målt). Flisutkastene i art/photoreal er ikke satt sammen.'),
    (9, 'Introscener', 'bg2a.PIV', 0, 'a45a2508', 'Introen: ridderen foran Stonehenge',
     'Har scene med beskyttet originalforgrunn. Revider aktiv master mot originalens slyng og arkitektur; bevar figuren.'),
    (9, 'Introscener', 'mindscape', 0, '46963198', 'Introen: Mindscape-logoen',
     'Har scene. Bevar logoens eksakte originalform. Eldre avvist gullflate er bare feilarkiv, ikke tegnereferanse.'),
    (11, 'Sluttscene', 'bg7.PIV', 0, 'e2e904b2', 'Slutten: virvel over vann',
     'Scene. 16 farger (fire plan). Ingen utkast finnes.'),
    (11, 'Sluttscene', 'bg8.PIV', 0, 'd0f67acb', 'Slutten: to figurer under stjernehimmelen',
     'Har scene. Revider aktiv master mot originalens antall, plassering og lysstyrke på stjernene; bevar figurene.'),
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


def lys(r, g, b):
    return 0.299 * r + 0.587 * g + 0.114 * b


def utvid_indekser(pakket, maske):
    """Pakkede CEL-planer til de faktiske fargeindeksene som Amigaen tegner."""
    bits = [1 << p for p in range(8) if maske & (1 << p)]
    grense = 1 << len(bits)
    if pakket and max(pakket) >= grense:
        raise ValueError('PNG-indekser passer ikke CEL-planmasken %02x' % maske)
    tabell = bytes(sum(bit for p, bit in enumerate(bits) if i & (1 << p)) for i in range(grense))
    return bytes(tabell[i] for i in pakket)


def kilde_planmaske(kilde, im, spill_sti=None):
    """Les maske fra extract-sidecar eller originalbanken, aldri gjett av PNG-fargen."""
    mappe = os.path.dirname(os.path.abspath(kilde))
    bank = os.path.basename(mappe)
    fil = os.path.basename(kilde)
    sidecar = os.path.join(os.path.dirname(mappe), 'index.json')
    info = None
    if not spill_sti and os.path.isfile(sidecar):
        with open(sidecar, encoding='utf-8') as f:
            indeks = json.load(f)
        for sti, data in indeks.get('filer', {}).items():
            if sti.split('/')[-1].lower() != bank.lower() or data.get('type') != 'figurer':
                continue
            info = next((b for b in data['bilder'] if b['fil'].lower() == fil.lower()), None)
            break
        if info is None:
            raise SystemExit('Ingen original-CEL-rute for %s i %s' % (kilde, sidecar))
        try:
            utvid_indekser(im.tobytes(), info['maske'])
        except ValueError as e:
            raise SystemExit(str(e))
        plan = bin(info['maske']).count('1')
        data = mf.indeks_til_plan(im.tobytes(), plan, *im.size)
        if not info.get('sha1') or hashlib.sha1(data).hexdigest() != info['sha1']:
            raise SystemExit('%s stemmer ikke med originalhashen i %s' % (kilde, sidecar))
    else:
        spill_sti = spill_sti or os.path.join(ROT, 'Moonstonecd32-AMIGA.zip')
        if not os.path.isfile(spill_sti):
            raise SystemExit('Mangler originalbank for %s. Behold extract-index.json eller bruk --spill STI.' % kilde)
        spill = mf.Spill(spill_sti)
        sti = next((s for s in spill.data_filer() if s.split('/')[-1].lower() == bank.lower()), None)
        try:
            nr = int(os.path.splitext(fil)[0])
            data = spill.les(sti) if sti else b''
            bilder = mf.cel_les(data)[0] if mf.er_cel(data) else []
            if nr < 0:
                raise IndexError
            b = bilder[nr]
        except (ValueError, IndexError, TypeError, KeyError):
            raise SystemExit('Ukjent original-CEL-rute %s. Bruk originalens bankmappe og bildenummer.' % kilde)
        pakket = mf.plan_til_indeks(b['data'], b['plan'], b['bredde'], b['hoyde'])
        if im.size != (b['bredde'], b['hoyde']) or im.tobytes() != pakket:
            raise SystemExit('%s stemmer ikke med den uendrede originalruten i %s' % (kilde, spill_sti))
        info = b
    if im.size != (info['bredde'], info['hoyde']):
        raise SystemExit('%s har feil størrelse for originalruten' % kilde)
    if info['maske'] & ~31:
        raise SystemExit('CEL-planmasken %02x bruker indekser utenfor spillets 32 farger' % info['maske'])
    return info['maske']


def lag_maske(kilde, ut, tegning=None, spill_sti=None, graa_referanse=None):
    from PIL import Image
    im = Image.open(kilde)
    if im.mode != 'P':
        raise SystemExit('%s er ikke et indeksert PNG fra tools/gfx.py extract' % kilde)
    w, h = im.size
    hd = Image.open(tegning).convert('RGB') if tegning else None
    maal = hd.size if hd else (w * SKALA, h * SKALA)
    maske = kilde_planmaske(kilde, im, spill_sti)
    bank = os.path.basename(os.path.dirname(os.path.abspath(kilde)))
    frame = int(os.path.splitext(os.path.basename(kilde))[0])
    levende = maskefarger(bank, frame)
    try:
        indekser = utvid_indekser(im.tobytes(), maske)
    except ValueError as e:
        raise SystemExit(str(e))
    ind = Image.frombytes('L', (w, h), indekser).resize(maal, Image.NEAREST)
    pal = im.getpalette() or []
    pal += [0] * (96 - len(pal))
    ref = [lys(*pal[i * 3:i * 3 + 3]) for i in range(32)]
    if graa_referanse is not None:
        if hd is None or not 1 <= graa_referanse <= 255:
            raise SystemExit('--graa-referanse krever tegning og et grånivå fra 1 til 255')
        ref = [graa_referanse] * 32
    ip = ind.load()
    hp = hd.load() if hd else None
    m = Image.new('RGBA', maal, (0, 0, 0, 255))
    mp = m.load()
    satt = 0
    for y in range(maal[1]):
        for x in range(maal[0]):
            i = ip[x, y]
            if i not in levende:
                continue
            g = 128
            if hp and ref[i] > 8:
                g = max(0, min(255, round(128 * lys(*hp[x, y]) / ref[i])))
            mp[x, y] = (i + 1, g, 255, 255)
            satt += 1
    os.makedirs(os.path.dirname(ut) or '.', exist_ok=True)
    m.save(ut)
    print('%s: %d x %d, %d piksler med ridderfarge' % (ut, maal[0], maal[1], satt))


def main():
    global PAA_NYTT
    if len(sys.argv) > 1 and sys.argv[1] == '--maske':
        parser = argparse.ArgumentParser(description='Lag palettmaske fra uendret, pakket original-PNG.')
        parser.add_argument('kilde')
        parser.add_argument('ut')
        parser.add_argument('tegning', nargs='?')
        parser.add_argument('--spill', help='Original-ZIP når extract-index.json ikke brukes.')
        parser.add_argument('--graa-referanse', type=int, help='Grånivå i tegningen som skal gi G=128.')
        args = parser.parse_args(sys.argv[2:])
        lag_maske(args.kilde, args.ut, args.tegning, args.spill, args.graa_referanse)
        return
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    spill = mf.Spill(sys.argv[1])
    ut_sti = sys.argv[2]
    with open(os.path.join(ROT, 'web/hd/manifest.json')) as f:
        filer = json.load(f)['files']
    PAA_NYTT = set() if logo_gjennomfort(ROT, filer) else {('bold.f', 73)}
    har_hd = {x['path'][:-4].lower() for x in filer if x['path'].endswith('.png')}
    with open(os.path.join(ROT, 'art/photoreal/catalog.json')) as f:
        katalog = json.load(f)
    utk = utkast(katalog)
    # bakgrunner som er slaatt paa som utkast (ikke godkjent i arkivet): i bruk, men skal
    # fortsatt tegnes paa nytt, saa de blir staaende i bestillingen
    uferdig = {r['photo_sha256'] for r in katalog['rows'] if r['status'] != 'runtime_verified'}
    utkast_i_bruk = {x['path'][:-4].lower() for x in filer if x.get('kind') == 'background' and x['sha256'] in uferdig}
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
            pakket = mf.plan_til_indeks(b['data'], b['plan'], b['bredde'], b['hoyde'])
            ind = utvid_indekser(pakket, b['maske'])
            bilder.append((fil, nr, b['bredde'], b['hoyde'], ind))

    def bare_intro(fil):
        f = fil.lower().encode()
        return f in program and f not in mog

    def rang(b):
        fil, nr = b[0], b[1]
        if bare_intro(fil):
            return (4, 2, fil.lower(), nr)
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
        # bare bilder med ridderfargene trenger maske (noen vaapen i KN4.ob har ingen)
        palett = 'ja' if maskefarger(fil, nr) & set(b[4]) else 'nei'
        if bare_intro(fil):
            pri, gruppe, hvor, merk = 4, 'Intro og slutt', INTRO_HVOR[fil], INTRO_MERKNAD
        else:
            pri, gruppe, hvor, merk = figur_info(fil, nr)
        ekstra = []
        andre = like.get((fil, nr), [])
        if andre:
            ekstra.append('Samme bilde brukes også som %s. Legg samme tegning der.'
                          % ', '.join('%s/%03d.png' % (a[0], a[1]) for a in andre))
            if any(bare_intro(a[0]) for a in andre) and not bare_intro(fil):
                ekstra.append('Introkopien har teknisk HD-støtte, men må kontrolleres i sin egen programsekvens.')
            if palett == 'ja' and any(not maskefarger(a[0], a[1]) for a in andre):
                ekstra.append('Kopien hos monsteret vises med tegningens egne farger, uten maske.')
        for a in he_kopi.get((fil, nr), []):
            ekstra.append('Samme tegning skal også ligge som %s/%03d.png. Der er indeksene 6, 7, 8 byttet til '
                          '9, 10, 11, så masken %s/%03d.mask.png er denne masken med R byttet fra 7, 8, 9 til '
                          '10, 11, 12 (G og B som før).' % (a[0], a[1], a[0], a[1]))
        s = utk.get((fil.lower(), nr))
        if s and 'candidates' not in merk:
            ekstra.append('Eldre utkast i art/photoreal/candidates/%s (%s), ikke godkjent. '
                          'Bare feilarkiv; bruk originalen som tegnereferanse.' % (fil, s))
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
            bg.append((2, 'Hulekamp', fil, '', h, 'Kamp etter Enter Lair: %s' % navn,
                       ('Klar. Utkast finnes (art/photoreal/candidates, needs_revision: runene). Godtar eieren ikke '
                        'runene, tegnes det på nytt. Kilde: art/photoreal/references/runtime_background/%s.png.' % fil)))
    for r in BAKGRUNNER:
        pri, gruppe, fil, nr, h, hvor, merk = r
        if fil != '-':
            regnet = piv_hash(spill, fil, nr)
            if regnet != h:
                raise SystemExit('Hashen til %s er %s, ikke %s' % (fil, regnet, h))
            merk += ' Kilde: assets/gfx/%s/%d.png (tools/gfx.py extract).' % (fil, nr)
        bg.append((2,) + r[1:6] + (merk,))
    for pri, gruppe, fil, nr, h, hvor, merk in bg:
        if 'bg/' + h in utkast_i_bruk:
            merk = 'I bruk som utkast i spillet. ' + merk
        elif 'bg/' + h in har_hd:
            continue        # ferdig HD i standardpakken: trengs ikke
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
    print('Med innhold uten egen bank-PNG: %d (hovedspillet %d, bare intro/slutt %d). Tegnes på nytt: %d'
          % (len(ny), sum(not bare_intro(b[0]) for b in ny), sum(bare_intro(b[0]) for b in ny), len(PAA_NYTT)))
    print('Hele poseprøver er ikke talt som ferdige separate figurruter.')
    lik_n = sum(len(v) for v in like.values())
    he_n = sum(len(v) for v in he_kopi.values())
    print('Rader med maske: %d' % sum(r[10] == 'ja' for r in rader))
    print('Like bilder slått sammen: %d. HE-bilder som er KN med byttede indekser: %d' % (lik_n, he_n))
    nbg = sum(1 for r in rader if r[4].startswith('bg/'))
    print('Rader: %d (figurer %d, bakgrunner %d)' % (len(rader), len(rader) - nbg, nbg))
    for (pri, gruppe), n in sorted(teller.items(), key=lambda x: (99 if x[0][0] == 'senere' else x[0][0], x[0][1])):
        print('  %-7s %-16s %4d' % (pri, gruppe, n))


if __name__ == '__main__':
    main()
