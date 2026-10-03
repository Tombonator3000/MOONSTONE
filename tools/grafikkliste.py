#!/usr/bin/env python3
"""
grafikkliste.py - lager listen over all grafikken i Moonstone, til en HD-utgave.

    python3 tools/grafikkliste.py Moonstonecd32-AMIGA.zip docs

Skriver docs/grafikkliste.md (oversikt og hvert bilde) og docs/grafikkliste.csv
(ett bilde per linje, til regneark og skript). Listen sier hva hver fil er, hvor
store bildene er, og hva HD-bildet skal hete i en HD-pakke (se docs/hd-grafikk.md).

Bare stdlib; leser spillfilen med moonfiles.py.
"""
import csv
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import moonfiles as mf  # noqa: E402

# Hva filene er. Navnene er som i spillet; beskrivelsene er fra bildene selv og
# fra der spillet bruker dem.
OM = {
    # bilder (320 x 200, 32 eller 16 farger)
    'HighWood.PIV': ('By', 'Byen Highwood: borgen, med menyen Visit, Merchant, Tavern, Healer, High Temple, Exit til høyre.'),
    'WaterDeep.PIV': ('By', 'Byen Waterdeep, med menyen til høyre (Mythrid the Mystic i stedet for templet).'),
    'WI1.P': ('Sted', 'Trollmannen Math i tårnet (innsiden).'),
    'WI2.P': ('Sted', 'Tårnet til trollmannen sett utenfra, i fjellene.'),
    'bg1a.PIV': ('Kamp', 'Kampbakgrunn: fullmåne over en skog om natten.'),
    'bg1b.PIV': ('Kamp', 'Kampbakgrunn: skog med tykke stammer om natten.'),
    'bg1c.PIV': ('Kamp', 'Kampbakgrunn: mørk skog, nesten uten lys.'),
    'bg2.PIV': ('Sted', 'Stonehenge om natten.'),
    'bg2a.PIV': ('Sted', 'Stonehenge med en ridder i rustning foran (druidene).'),
    'bg3.PIV': ('Sted', 'Steinsirkelen sett ovenfra.'),
    'bg4.PIV': ('Sted', 'Alteret med Moonstone-skiven.'),
    'bg5.piv': ('Sted', 'Valley of the Gods: templet med statuer.'),
    'bg5a.PIV': ('Sted', 'Valley of the Gods: virvelen (portalen).'),
    'bg7.PIV': ('Sted', 'Virvel over vann.'),
    'bg8.PIV': ('Tittel', 'Stjernehimmel over trærne (introen).'),
    'ch.piv': ('Tittel', 'Tittelmenyen: nattehimmel med trær. Paletten er også fargene til fonten bold.f.'),
    'dice.piv': ('Taverna', 'Terningspillet i tavernaen.'),
    'hea.piv': ('By', 'Healeren.'),
    'hen1.p': ('Sted', 'Templet (samme scene som bg5, en annen variant).'),
    'message.piv': ('Melding', 'Meldingsskjermen: banneret øverst («Prepare yourself ...», «... may use their Scroll of protection»).'),
    'mindscape': ('Intro', 'Mindscape-logoen i introen.'),
    'mys.piv': ('By', 'Mythrid the Mystic.'),
    'tav.piv': ('Taverna', 'Tavernaen, med menyen til høyre.'),
    'test': ('Kart og kamp', 'Ni bilder: 0-3 er biter til kampbakgrunnene (trær, røtter, gress), 4-7 er kampbakgrunner (skog, skogkant, gresslette), 8 er kartet.'),
    # figurer
    'au1.cel': ('Kamp', 'Figurer i kamp: et ansikt (bilde 0) og hugg og våpenbiter.'),
    'Balok1.CEL': ('Monster', 'Balok i kamp, del 1.'),
    'Balok2.CEL': ('Monster', 'Balok i kamp, del 2.'),
    'Balok3.CEL': ('Monster', 'Balok i kamp, del 3 (blod og kropp).'),
    'be1.c': ('Monster', 'Beistet (ulvelignende) i kamp.'),
    'be2.c': ('Monster', 'Beistet: blod og hugg.'),
    'blo.cel': ('Kamp', 'Blodsprut.'),
    'bold.f': ('Font', 'Fonten i tittelmenyen og menyene: 0-25 A-Z, 26-51 a-z, 52-61 0-9, 62 !, 63 ?, 64 ., 65 ,, 66 #, 67 $, 68 %, 69 mellomrom, 70 \', 71 _ og /. 72 er en prikk, 73 er MOONSTONE-logoen, 74-75 copyright-linjene.'),
    'co1.cel': ('Kamp', 'Figurer i kamp (rødt og gull, kropp og biter).'),
    'da1.cel': ('Kamp', 'Små figurer (røde og hvite).'),
    'Demon1.CEL': ('Monster', 'Demonen i kamp, del 1.'),
    'Demon2.CEL': ('Monster', 'Demonen i kamp, del 2.'),
    'Demon3.CEL': ('Monster', 'Demonen i kamp, del 3 (piskeslag).'),
    'Demon4.CEL': ('Monster', 'Demonen i kamp, del 4.'),
    'dg1.cel': ('Monster', 'Et grønt beist med lange bein, i kamp.'),
    'dice.cel': ('Taverna', 'Terningspillet: terninger, beger, hender og bordet.'),
    'DRAGON1.CEL': ('Monster', 'Dragen i kamp, del 1 (de seks første bildene er tomme).'),
    'DRAGON2.CEL': ('Monster', 'Dragen i kamp, del 2.'),
    'DRAGON5.CEL': ('Monster', 'Dragen: ild og flammer.'),
    'dw1.cel': ('Sted', 'Hettekledde figurer (druidene ved Stonehenge) og flammer.'),
    'ha1.cel': ('Sted', 'Hender og arm i rustning (Valley of the Gods).'),
    'HE1.ob': ('Ridder', 'Ridderen i kamp, gylden rustning, del 1.'),
    'HE2.ob': ('Ridder', 'Ridderen i kamp, gylden rustning, del 2.'),
    'HE3.ob': ('Ridder', 'Ridderen i kamp, gylden rustning, del 3.'),
    'hen1.c': ('Sted', 'Figurer til templet (ting og flammer).'),
    'ki.cel': ('Inventar', 'Tingene i inventaret: skjold, flasker, ruller, nøkler osv.'),
    'Klift1.CEL': ('Monster', 'Klift i kamp.'),
    'KN1.ob': ('Ridder', 'Ridderen i kamp, rød, del 1 (gå, stå, slag).'),
    'KN2.ob': ('Ridder', 'Ridderen i kamp, rød, del 2.'),
    'KN3.ob': ('Ridder', 'Ridderen i kamp, rød, del 3.'),
    'KN4.ob': ('Ridder', 'Våpnene til ridderen (sverd, lanse) i kamp.'),
    'KN5.ob': ('Ridder', 'Blod og sår på ridderen.'),
    'li1.cel': ('Magi', 'Lyn og magi (og en hånd med stav).'),
    'mi.c': ('Inventar', 'Små flasker og dråper.'),
    'Mudmen1.CEL': ('Monster', 'Mudmen i kamp, del 1.'),
    'Mudmen2.CEL': ('Monster', 'Mudmen i kamp, del 2.'),
    'mys.cel': ('By', 'Mythrid the Mystic: knappene Exit, Ok, pilene og ting.'),
    'ov1.cel': ('Kamp', 'Forgrunn i kampbakgrunnene (busker og røde blader).'),
    'po.cel': ('Inventar', 'Pekeren (sverdet) i inventaret og byene.'),
    'RATMEN1.CEL': ('Monster', 'Rottemennene i kamp, del 1.'),
    'RATMEN2.CEL': ('Monster', 'Rottemennene i kamp, del 2.'),
    'sel.cel': ('Meny', 'Pilen i menyene (bilde 0) og de fire ridderne i Select a Knight (1-5).'),
    'Small.font': ('Font', 'Den lille fonten (5 x 6): inventaret, valgene på kartet. 0-25 A-Z, 26-51 også A-Z, 52-61 0-9, så tegn.'),
    'TROGGAxe1.CEL': ('Monster', 'Trogg med øks i kamp, del 1.'),
    'TROGGAxe2.CEL': ('Monster', 'Trogg med øks i kamp, del 2.'),
    'TROGGSpear1.CEL': ('Monster', 'Trogg med spyd i kamp, del 1.'),
    'TROGGSpear2.CEL': ('Monster', 'Trogg med spyd i kamp, del 2.'),
    'TROLL1.CEL': ('Monster', 'Trollet i kamp, del 1.'),
    'TROLL2.CEL': ('Monster', 'Trollet i kamp, del 2.'),
    'Wi1.C': ('Sted', 'Trollmannen Math (figurer).'),
}

# filer som har med grafikken aa gjore, men som verktoyene ikke pakker ut ennaa
ANDRE = {
    '.t': 'Hvordan kampbakgrunnene settes sammen av bitene i test (fo = skog, gl = lysning, sw = sump, wa = vann; '
          'l-filene er en variant). Ikke pakket ut ennå (todo.md).',
    '.stile': 'co.stile og intro.stile, 960 byte hver: ser ut som en tabell over biter (fliser). Ikke pakket ut.',
    'collide.hit': 'Tekst: treffsonene til figurene i kamp, fil for fil (Balok1.cel ...). Ikke grafikk, men må stemme om figurene endres.',
}


def piv_info(data):
    bilder, _ = mf.piv_alle(data)
    return [(320, 200, plan, 1 << plan) for (plan, _, _) in bilder]


def cel_info(data):
    n = struct.unpack('>H', data[:2])[0]
    ut = []
    for i in range(n):
        _, w, h, _, m = struct.unpack('>IHHBB', data[10 + i * 10:20 + i * 10])
        ut.append((w, h, bin(m).count('1'), m))
    return ut


def storrelser(bilder):
    if not bilder:
        return ''
    ws = [b[0] for b in bilder]
    hs = [b[1] for b in bilder]
    if min(ws) == max(ws) and min(hs) == max(hs):
        return '%d x %d' % (ws[0], hs[0])
    return '%d-%d x %d-%d' % (min(ws), max(ws), min(hs), max(hs))


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    spill = mf.Spill(sys.argv[1])
    ut = sys.argv[2]
    os.makedirs(ut, exist_ok=True)
    filer = []
    andre = []
    for sti in sorted(spill.data_filer(), key=str.lower):
        navn = sti.split('/', 1)[1]
        data = spill.filer[sti]
        n = navn.lower()
        if n.endswith(('.cel', '.c', '.ob', '.f', '.font')) and mf.er_cel(data):
            filer.append((navn, 'figurer', cel_info(data)))
        elif mf.er_piv(data):
            filer.append((navn, 'bilder', piv_info(data)))
        elif n.endswith('.t'):
            andre.append((navn, '.t', len(data)))
        elif n.endswith('.stile'):
            andre.append((navn, '.stile', len(data)))
        elif n == 'collide.hit':
            andre.append((navn, 'collide.hit', len(data)))

    antall = sum(len(b) for _, _, b in filer)
    tomme = sum(1 for _, t, b in filer if t == 'figurer' for x in b if x[3] == 0)
    with open(os.path.join(ut, 'grafikkliste.csv'), 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f, delimiter=';')
        w.writerow(['fil', 'bilde', 'bredde', 'hoyde', 'plan', 'farger', 'hd_fil', 'hd_4x', 'gruppe', 'beskrivelse'])
        for navn, t, bilder in filer:
            gruppe, om = OM.get(navn, ('', ''))
            for i, (bw, bh, plan, _) in enumerate(bilder):
                hd = 'bg/HASH.png (Lagre bakgrunnen)' if t == 'bilder' else '%s/%03d.png' % (navn, i)
                w.writerow([navn, i, bw, bh, plan, 1 << plan if plan else 0, hd, '%dx%d' % (bw * 4, bh * 4), gruppe, om])

    L = []
    L.append('# Grafikkliste\n')
    L.append('Laget med `python3 tools/grafikkliste.py Moonstonecd32-AMIGA.zip docs`. Ikke rediger for hånd; '
             'kjør verktøyet på nytt. Alle bildene med mål ligger også i `grafikkliste.csv` (ett bilde per linje).\n')
    L.append('Spillet har %d filer med grafikk som verktøyene pakker ut: %d figurfiler og %d bildefiler, '
             'til sammen %d bilder (%d av dem er tomme plassholdere). I tillegg kommer %d filer som beskriver '
             'kampbakgrunnene og treffsonene (nederst).\n'
             % (len(filer), sum(1 for f in filer if f[1] == 'figurer'), sum(1 for f in filer if f[1] == 'bilder'),
                antall, tomme, len(andre)))
    L.append('## Slik lager du HD-grafikk\n')
    L.append('1. Pakk ut originalene: `python3 tools/gfx.py extract Moonstonecd32-AMIGA.zip assets/gfx`. '
             'Du får en mappe per fil (f.eks. `assets/gfx/KN1.ob/000.png`), med samme navn som i listen under.\n'
             '2. Tegn et nytt bilde i høyere oppløsning, gjerne fire ganger (kolonnen `hd_4x` i CSV-filen). '
             'Bruk PNG med gjennomsiktighet; bildet strekkes til samme flate som originalen, så bredde og høyde '
             'bør ha samme forhold.\n'
             '3. Legg bildene i en mappe med samme oppbygning (`KN1.ob/000.png`, `bold.f/000.png` ...) og velg '
             'den under «HD-grafikk» i menyen på nettsiden. Store og små bokstaver i navnene spiller ingen rolle.\n'
             '4. Bakgrunnene (bildefilene og kampbakgrunnene som settes sammen av biter) byttes etter hvordan de '
             'ser ut: trykk «Lagre bakgrunnen» i menyen mens den vises, tegn den i HD, og legg den i mappen `bg` '
             'med samme navn (`bg/1a2b3c4d.png`). Se docs/hd-grafikk.md.\n'
             '5. «Grafikk: HD der den finnes / Original» i menyen bytter mellom HD-bildene og originalen uten å '
             'fjerne HD-pakken, så du kan sammenligne.\n')
    L.append('Figurene i spillet bruker fargene til skjermen de vises på (fargeindeksene 0-31), og 0 er '
             'gjennomsiktig. PNG-ene fra `gfx.py extract` har en forhåndsvisningspalett; HD-bildene er vanlige '
             'farge-PNG-er.\n')
    L.append('## Oversikt\n')
    L.append('| Fil | Gruppe | Type | Bilder | Størrelse | Hva det er | HD-mappe |')
    L.append('| --- | --- | --- | ---: | --- | --- | --- |')
    for navn, t, bilder in filer:
        gruppe, om = OM.get(navn, ('', ''))
        hd = '`bg/` (Lagre bakgrunnen)' if t == 'bilder' else '`%s/`' % navn
        L.append('| %s | %s | %s | %d | %s | %s | %s |'
                 % (navn, gruppe, 'bilde' if t == 'bilder' else 'figurer', len(bilder), storrelser(bilder), om or '?', hd))
    L.append('\n## Hvert bilde\n')
    L.append('Bildenummer: bredde x høyde (antall bitplan). Tomme bilder (ingen bitplan) er merket «tom».\n')
    for navn, t, bilder in filer:
        gruppe, om = OM.get(navn, ('', ''))
        L.append('### %s\n' % navn)
        if om:
            L.append(om + '\n')
        deler = []
        for i, (bw, bh, plan, _) in enumerate(bilder):
            nr = str(i) if t == 'bilder' else '%03d' % i
            deler.append('%s: %dx%d%s' % (nr, bw, bh, ' tom' if t == 'figurer' and plan == 0 else ' (%d)' % plan))
        L.append(', '.join(deler) + '\n')
    L.append('## Andre filer\n')
    L.append('| Fil | Størrelse | Hva det er |')
    L.append('| --- | ---: | --- |')
    for navn, slag, n in andre:
        L.append('| %s | %d byte | %s |' % (navn, n, ANDRE[slag]))
    with open(os.path.join(ut, 'grafikkliste.md'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(L) + '\n')
    print('%s: %d filer, %d bilder' % (os.path.join(ut, 'grafikkliste.md'), len(filer), antall))


if __name__ == '__main__':
    main()
