# HD-grafikk: hva som mangler

Oversikt per 11. oktober 2026. Den bygger på målinger med headless-emulatoren (lagringer fra kart, by, taverna, inventar, kamp og slutten, pluss tvungne besøk), opptelling mot `docs/grafikkliste.csv` og `web/hd/manifest.json`, og lesing av koden. Hver linje er merket med hvordan vi vet det:

- **målt**: kjørt i emulatoren eller regnet ut fra filene
- **kode**: lest i koden, ikke kjørt
- **antatt**: slutning vi ikke har kontrollert

Skriptene og dumpene ligger i scratchpad for økten (`hdm/`), ikke i repoet. Linjenumre i `disasm/*.s` gjelder disassemblyen som lages lokalt.

## 1. Status

### Dette har HD i dag (målt)

`web/hd/manifest.json` har 292 PNG: 252 figurer, tekst og ikoner, og 40 bakgrunner i `bg/`.

| Hva | Antall | Merknad |
|---|---|---|
| Figurer med fil/bilde-nøkkel | 189 av 2329 | bold.f 72/76, Small.font 71/72, ki.cel 40/50, po.cel 1/1, sel.cel 5/6 |
| Overlegg i scener | 58 | scene-text 20, map-icons 26, map-landmarks 6, scene-icons 6 |
| Ridderposer (`web/hd/poses.json`) | 5 bilder | Dekker kn1.ob 0-9 og kn4.ob 1 (11 kildebilder), bare den blå ridderen i øvingskampen |
| Kampbakgrunner (.t) | 32 av 56 | fo, gl, sw og wa 1-8. De 24 hulevariantene mangler |
| PIV-bakgrunner | 8 av 31 hasher | ch (tittel), HighWood, WaterDeep, tav, test:8 (kartet), bg2, bg4 og bg5a (intro) |

PIV-tallet: 32 PIV-bilder (23 filer pluss 9 bilder i `test`) gir 31 ulike hasher, fordi bg5.piv og hen1.p er like.

### Dette mangler, figurer per gruppe (målt)

Gruppene er de i `docs/grafikkliste.csv`, uten PIV-radene. «Bare intro/slutt» er filer som bare lastes av programmet `program` (filnavnene står i `data/program` og ikke i `data/mog`). De kan ikke få HD med dagens kode, se punkt 4.

| Gruppe | Bilder | Har HD | Tomme | Mangler | Av dem bare intro/slutt |
|---|---|---|---|---|---|
| Monster | 1264 | 0 | 26 | 1238 | 110 (dg1.cel, Klift1.CEL) |
| Ridder | 387 | 0 | 0 | 387 | 0 |
| Kamp | 214 | 0 | 0 | 214 | 173 (au1, co1, da1, ov1). Bare blo.cel (41) brukes i hovedspillet |
| Sted | 151 | 0 | 7 | 144 | 72 (dw1, ha1) |
| Inventar | 98 | 41 | 2 | 55 | 0 (45 er mi.c, som egentlig er kartfigurene) |
| Magi | 30 | 0 | 0 | 30 | 30 (li1.cel) |
| Taverna | 23 | 0 | 0 | 23 | 0 |
| By | 8 | 0 | 0 | 8 | 0 |
| Font | 148 | 143 | 3 | 2 | 0 (copyrightlinjene bold.f 74 og 75) |
| Meny | 6 | 5 | 0 | 1 | 0 (sel.cel 1, en tom ramme) |
| **Sum** | **2329** | **189** | **38** | **2102** | **385** |

I hovedspillet mangler altså 1717 figurbilder med innhold. 1128 av dem er monstre og 387 er riddere.

## 2. Det som mangler, viktigst først

Bestillingen med en rad per bilde ligger i `docs/hd-bestilling-liste.csv` (laget med `tools/hd_bestilling.py`), og meldingen til den som tegner i `docs/hd-bestilling-chatgpt.md`.

«Klar» betyr at en PNG med riktig navn virker uten kodeendring. «Scene» betyr en ny rad i `manifest.scenes` (data, ikke kode), som må prøves. «Kode» betyr at render.js eller porten må endres først.

| Pri | Hva | Fil eller hash | Bilder | Hvor | Bruk | Belegg |
|---|---|---|---|---|---|---|
| 1 | Hulekamp, skog | fol1-6: 3a38d016, 5ecac111, 5e1dc378, 5c6a3697, 954ee2f9, db6fc7ba | 6 | Enter Lair i skog | Klar (`bg/HASH.png`). Utkast finnes | målt |
| 1 | Hulekamp, lysning | gll1-6: 4b68f426, 8feef9f5, 6113f65e, 6b05bdcd, b95b11e9, 73c7f5c1 | 6 | Enter Lair i lysning | Klar. Utkast finnes | målt |
| 1 | Hulekamp, sump | swl1-6: 14a894c2, b7afa780, df1460be, 4aca74c6, 09b477b7, b33ce188 | 6 | Enter Lair i sump | Klar. Utkast finnes | målt |
| 1 | Hulekamp, klipper og vann | wal1-6: ed554452, 756408ca, 850cdd99, 93d40a06, 75c0760c, 5c5085b2 | 6 | Enter Lair i fjell og vann | Klar. Utkast finnes | målt |
| 2 | Kartfigurene mi.c | mi.c 0-46 (45 med innhold) | 45 | Kartet hele tiden: ridderhodet, områdeomrisset, valgrullen (mi.c 32), dragen | Klar (fil/bilde). Ikke prøvd. Hoder i ridderfarger er egne bilder, så faste farger går | målt |
| 3 | Statusskjermen | ki.cel 34-36 (rankene på buen), 38-43 (STR, CON, END, XP, GOLD, HIT), 44 (NEXT KNIGHT) | 10 | Status og inventar for hver ridder | Klar. Lag dem helst som konturikoner med `tools/hd_ikoner_bygg.py`, som resten av ki.cel | målt |
| 4 | Butikken med to buer | e868fda9 | 1 | Merchant og High Temple | Klar (`bg/HASH.png`) | målt |
| 4 | Inventaret (buen) | 94e65527 | 1 | Inventar mellom turene | Klar | målt |
| 4 | Healeren | hea.piv 2e3c32ae | 1 | Healer i Highwood (Waterdeep antatt lik) | Klar. Utkast finnes | målt |
| 5 | Ridderne | KN1-5.ob, HE1-3.ob | 387 | Alle kamper, ca. 35 x 62 px, tegnes ti ganger i sekundet | Kode. Overlapp og farge stopper dem, se punkt 4 | målt |
| 6 | Lasteskjermen | skjermhash d218609e | hele skjermen | Etter introen og etter slutten («MOONSTONE ... Loading») | Kode eller scene. Nesten alt er forgrunn (63957-64000 px), så `bg/HASH` virker ikke | målt |
| 6 | Prepare yourself, Loading, Select a Knight | forgrunn over tom bakgrunn | ukjent | Før hver kamp og ved riddervalget | Kode. Hvilke filer banneret og teksten kommer fra er ikke kartlagt. Teksten tegnes før hashen skifter og mister HD (render.js:484) | målt |
| 7 | Monstrene i hovedspillet | Balok1-3, be1.c, be2.c, Demon1-4, DRAGON1/2/5, Mudmen1-2, RATMEN1-2, TROGGAxe1-2, TROGGSpear1-2, TROLL1-2 | 1128 | Kamp i hi og ute | Delvis klar. Deler som overlapper en tidligere tegning avvises (render.js:948). Hvor mange monstre som tegnes i flere deler er ikke målt | målt for TroggSpear |
| 7 | Logoen har feil sideforhold | bold.f/073.png er 2172 x 724 (3,0:1), kilden er 305 x 54 (5,65:1) | 1 | Tittelmenyen | Klar når den lages på nytt i 5,65:1. I dag blir den flatklemt | målt |
| 8 | Mythrid | mys.piv d8b4018a | 1 | Waterdeep | Klar. Utkast finnes | målt (tvunget besøk) |
| 8 | Druidene ved Stonehenge | hen1.p / bg5.piv 94c7f163 | 1 | Stonehenge, tempelet i slutten | Klar i hovedspillet. Utkast finnes | målt (tvunget besøk) |
| 8 | Trollmannen Math | WI1.P 71970806 (ren), med tekst 4d4fb3f3, 27ddabfe, 7e2863f2. WI2.P ren da1dc997 er aldri sett | 2 bilder, minst 4 hasher | Tårnet i fjellene | Scene. Teksten ligger i bakgrunnskopien og endrer hashen | målt (tvunget besøk) |
| 8 | Terningspillet | dice.piv c6a4a00e (ren, aldri sett). 10 målte varianter | 1 bilde, ny hash hvert spill | Tavernaen | Scene (samsvar 0,96 mot dice.piv) | målt |
| 8 | Taverna og by, figurer | dice.cel (23), mys.cel (8) | 31 | Terningspillet, Mythrid | Klar for dice.cel 6 og 7, som er sett i tegnelisten. Resten ikke prøvd | målt |
| 9 | Steinsirkelen blinker | scene stone-circle (bg2.PIV 93153ff2) | 0 nye | Introen | Scene: detaljkravet 0,95 holder bare i 9 av 46 prøver (detalj 0,876-0,971). Senk `minimum_detail` og prøv | målt (Python-kopi av scenes.js) |
| 9 | Portalen andre gang | scene portal (bg5a.PIV 6e5a5c07) | 0 nye | Introen, bilde 5560-5850 | Scene: 0 av 30 treff (samsvar 0,76 mot 0,85). Første gang 26 av 30 | målt (samme metode) |
| 9 | Introscener | bg3.PIV c2501c17 (samsvar 1,0), bg1b.PIV d744b02e (0,92-0,99), bg2a.PIV a45a2508 (0,74), mindscape 46963198 (0,77) | 4 | Introen | Scene. bg3 og bg1b treffer godt nok. bg1a og bg1c rulles og passer ikke som stillbilde | målt |
| 10 | Blod og sår | blo.cel (41), KN5.ob (65) | 106 | Kamp | Kode (overlapper ridderen). Ikke sett i tegnelisten | antatt |
| 10 | Stedsfigurer i hovedspillet | Wi1.C (21), hen1.c (55, = Klift1.CEL) | 76 | Tårnet, Stonehenge | Klar, ikke prøvd. Lag hen1.c én gang og legg den også som Klift1.CEL | antatt |
| 11 | Sluttscenen | bg7.PIV e2e904b2, bg8.PIV d0f67acb, hen1 94c7f163, bg3 | 4 | Slutten | Scene | målt |
| 11 | Copyrightlinjene | bold.f 74, 75 | 2 | Tittelmenyen | Klar, ikke prøvd | målt |
| 11 | Tom ramme | sel.cel 1 | 1 | Trolig Select a Knight | Klar, ikke prøvd | antatt |
| 12 | Intro- og sluttfigurer | au1, co1, da1, dg1, dw1, ha1, Klift1, li1, ov1 | 385 med innhold | Introen og slutten | Kode. Ingen tegneliste i `program`. Ikke bestill nå | målt |

### Dette skal ikke bestilles

| Hva | Hvorfor | Belegg |
|---|---|---|
| `bg/045a1ac5.png` | 045a1ac5 er hashen av en helt tom bakgrunnskopi (40000 nullbyte). En PNG her ville vises på alle tomme bakgrunner og i alle overganger | målt |
| 8dbce956 (månen) og c234c097 (stjernene) | Bakgrunnskopien har dem, men lasteskjermen dekker hele skjermen (skjermhash d218609e) | målt |
| test:0-7 | 4-7 er bakteppet kampen bygges på og står bare 1 til 2 bilder før bitene legges på. 0-3 er arkene med biter. Ferdig kamp har en .t-hash | målt |
| bg2.PIV i hovedspillet | Lastes bare til disksjekken (mog.s:2205-2213) | kode |

## 3. Utkast i arkivet som ikke er slått på

`art/photoreal/catalog.json` har 616 rader. 529 av dem har ingen HD i spillet og ingen erstatning (målt). Ikon- og tekstarkivene (`art/hd-icons-2026-10-11`, `art/hd-text-2026-10-11`) er helt slått på, bortsett fra logo-v1 og world-map-v1, som er erstattet av nyere versjoner. Fra `art/hd-backgrounds-2026-10-11` er waterdeep, highwood, tavern og world-map i bruk, byteidentiske med bg/d097d0ff, 438c8bc2, 44898895 og 2c1e0fa5.

| Utkast | Antall | Status | Hva som skal til |
|---|---|---|---|
| Hulebakgrunner fol, gll, swl, wal 1-6 (`art/photoreal/candidates/combat-*`) | 24 | needs_revision. Teknisk kontroll bestått, runene er tegnet om | Eieren godtar runene eller får dem tegnet på nytt. Kopier til `web/hd/bg/<hash>.png` og før dem i manifest.json (kind background, sha256, bytes). Hashene er i `art/photoreal/production-plan-2026-10-03.json` og målt i spillet |
| hea, mys, bg5/hen1 | 3 | needs_revision eller candidate_geometry_review | Rett avvikene i notatene (endret bokdiagram hos healeren, nye tegn hos Mythrid), legg inn som `bg/HASH.png`. Hashene er målt |
| WI1, WI2, dice | 3 | needs_revision og candidate_geometry_review. Planen sier at de trenger maskert lag | Lag scener med teksten som avvik. WI1 har en synlig skjøt, WI2 har en stjerne for mye og mangler to |
| bg2a, bg3, bg8, mindscape | 4 | needs_revision eller candidate_geometry_review | Scener i intro og slutt. Rett avvikene (slyngen i bg2a, alteret i bg3, stjernene i bg8) |
| message | 1 | Ingen rute | Kan ikke brukes som bakgrunn (045a1ac5 er tom skjerm). Trenger scene |
| test:004-007 | 4 | candidate_geometry_review | Ingen nytte som bakgrunn. Kan brukes som grunnlag når .t-bakgrunner tegnes |
| Fliser i bg1a (40 av 80) og bg1b (70 av 80) | 110 | Ikke satt sammen | Hører til introen, ikke kamp. Må settes sammen etter `intro.stile`/`co.stile` (formatet er ikke dekodet) og vises via scene |
| Riddere KN1-5, HE1-2 | 301 | Uprøvde råkandidater, røde | Kodeendring først (punkt 4). Deretter fast eksportrektangel og anker per rute, og farge per ridder |
| Troll TROLL1-2 | 63 | Geometri og revisjon | Trollet i spillet er blått, utkastene er brune og gylne. Lag blå varianter med fast eksportrektangel |
| ki.cel 034-036, 038-044 | 10 | Blandet | Fotostil passer ikke med konturikonene. Lag heller konturikoner |
| ov1.cel | 4 | Revisjon | Brukes bare i intro og slutt. Kan ikke vises i dag |
| sel.cel:001 | 1 | needs_revision | Er en tom ramme, ikke menypilen |
| Overflødige (ki.cel 000-033 og 037, po.cel, bold.f:073, sel.cel:000, fire byer og kartet) | 41 | Erstattet | Ingenting |

Ingen utkast finnes for bg7.PIV og bg1c.PIV, og 1872 av 2417 ruter i produksjonsplanen er pending_photoreal (målt).

Feil i arkivets metadata (målt): `enabled_in_game` står true for sel.cel:000, men bildet i spillet kommer fra ikonpakken. Den står false for bg2, bg4 og bg5a, men de er i bruk som bg/93153ff2, 64e5c054 og 6e5a5c07. `art/photoreal/README.md:7` sier 48 bilder, manifestet har 292. `tools/hd_arkiv_hash_sjekk.cjs` forventer 43 aktiverte og må endres samtidig med merkene.

## 4. Kodemangler som hindrer HD

1. **Figurer i flere deler avvises.** En tegning avvises hvis den overlapper en tegning som kom tidligere i listen, uansett om den andre har PNG, og også hvis en overlappende tegning har PNG eller ukjent kilde (web/src/render.js:948). I øvingskampen overlapper 1064 av 1602 tegninger (målt). Sverdet kn4 over kroppen kn1 avvises alltid. Gjelder riddere, blod og trolig de fleste monstre.
2. **Ingen farge fra paletten for vanlige figurer.** PNG-en vises med faste farger (render.js:956-983 sammenligner bare indekser). Ridderne får fargen fra paletten, så ett sett KN-bilder kan ikke vise fire ridderfarger. Posene krever eksakt RGB (render.js:844) og identitetsindeksene 6, 7, 8 (render.js:847), og avvises ved fremmed overlapp (render.js:821). I en kamp i et hi er paletten en annen enn i øvingskampen, så posene avvises der (målt). Ikonene fargelegges allerede med skjermens palett (render.js:1160), og samme løsning trengs for ridderne.
3. **Bitene i kampbakgrunnene** settes sammen av en egen blitter-rutine ($099BB8 i mog) rett i bakgrunnskopien. De får aldri en fil/bilde-nøkkel, bare hele bakgrunnen per .t-fil (målt med --blit-log).
4. **Intro og slutt** kjøres av `program`. Der er laget ugyldig (port/src/lag.c:54, port/src/whdload.c:304-305) og tegnelisten tom (målt). Bare hele bilder via SceneHd virker. 385 figurbilder kan derfor ikke få HD.
5. **Tekst forsvinner ved hashbytte.** render.js:484 tømmer alle plasserte figurer når bakgrunnshashen endres. På lasteskjermen tegnes teksten i bilde 863-870, hashen skifter i bilde 950 (målt).
6. **Utsnittsbakgrunner kan strekkes feil (kode).** bg/438c8bc2, 44898895 og d097d0ff dekker bare en del av skjermen (1419 x 1108 og 1414 x 1113). Utsnittet settes bare av SceneHd (web/src/scenes.js:116). Står hashen igjen uten scenetreff, strekkes bildet over hele 320 x 200 (render.js:1079-1091). Det er målt at bakgrunnslaget kan stå på Highwood mens en meldingsskjerm vises.
7. **Toning og fargebytte.** HD-figurer og bakgrunner får bare lysstyrke (render.js:1029, 1089). Posene vises med lys 1 og avvises mens skjermen toner (kode).
8. **SceneHd sammenligner med bakgrunnskopien når laget er gyldig** (scenes.js:46). For Math, terningspillet og kartet er teksten og markørene en del av den, så kravene i en ny scene må tåle dem.
9. **Faste særtilfeller i tittelmenyen.** Pilen, titteltekstene og månefasene har faste koordinater, paletter og bankhasher (render.js:437-440, 729-789, 868-904). En oversatt eller endret meny faller tilbake til originalen (kode).
10. **Utenfor spillet:** grensesnittet på nettsiden (sidemenyen, knappene, hint) bruker originalpikslene og har egne glyfer for æ, ø, å og tegn spillet ikke har (web/src/grafikk.js:145-161). PC-versjonen leser ikke HD i det hele tatt (kode).

## 5. Usikkert eller ikke målt

- Waterdeep, Mythrid, druidene og Math er målt ved å bytte adressen i healer-kallet i Highwood, ikke ved å reise dit. Bakgrunnen bygges likevel av originalrutinen.
- Scenetreffene i intro og slutt er regnet med en Python-kopi av regelen i scenes.js på skjermdumper fra headless, ikke i nettleseren.
- Ikke målt: healeren i Waterdeep, WI2 uten tekst, Math med andre gaver, bg8 i hovedspillet (filnavnet står ved «You have completed the quest», disasm/mog.s:11954), Next Day med alle fem månefaser og bakgrunnen der, butikker utover Highwood, en kamp med fire riddere, dueller i Hver for seg og Turns.
- Hvilke indekser (6-8 og 9-11) hver av de fire ridderne og den svarte ridderen får i kamp, er ikke målt. Det trengs før ridderne kan tegnes med fargemaske.
- Hvilke monstre som er vanligst er ikke målt. Bare ett hi (TroggSpear) er kjørt. KN5, blo.cel og monstrenes treffbilder er ikke sett i tegnelisten.
- Hvilke filer banneret i Prepare yourself og Select a Knight kommer fra, er ikke kartlagt.
- Kart, terningspill og Math gir mange hasher. Antallet varianter er ikke uttømt.
- At mi.c, Wi1.C, hen1.c og bold.f 74/75 virker som vanlige figurer er utledet av koden. Ingen PNG er prøvd.
- At de tre utsnittsbakgrunnene faktisk vises strukket i nettleseren, er ikke sett.
- Leverte størrelser avviker fra kolonnen hd_4x i grafikkliste.csv: 37 bakgrunner er 1586 x 992 (ca. 4,96x), fontene 6x, ki.cel og po.cel 8x, månefasene 25x og portrettene 18x (målt). Det er uavklart hvilken skala som skal gjelde.
- Av 82 lagringer i scratchpad lot bare en del seg laste (21 til 32, etter hvem som telte). Resten er gamle formater.
