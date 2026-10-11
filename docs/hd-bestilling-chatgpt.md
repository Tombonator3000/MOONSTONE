# HD-grafikk til Moonstone: bestilling

Dette er en melding til deg som skal lage HD-bildene. Den sier hva som mangler, hvilket format bildene må ha, og hva du ikke skal lage ennå. Hver påstand viser til fil:linje i repoet https://github.com/Tombonator3000/MOONSTONE (main), så du kan sjekke den selv (linjenumrene er fra 11. oktober 2026 og kan ha flyttet seg litt). Kommandoene kjøres fra roten av repoet.

## 1. Spillet og stilen

Moonstone: A Hard Days Knight kom i 1991 på Amiga, fra Mindscape. Det er mørk og brutal fantasy med riddere, monstre, blod, steinsirkler og nattlige skoger. Originalen er pikselgrafikk i 320 x 200 med 32 farger (fem bitplan). HD-bildene skal ha samme motiv, form og plassering, bare tegnet skarpere. Ikke tegn nye motiver.

## 2. Dette virker allerede i nettsiden

- Når HD er slått på, lastes standardpakken i `web/hd` automatisk (web/src/hd.js:81-116, web/src/app.js:203). Den har 292 PNG: fontene, inventarikonene, pekeren, riddervalget, 40 bakgrunner, overlegg i scener og fem poser av den blå ridderen. Se docs/hd-mangler.md for hva som finnes og mangler.
- Du kan i tillegg velge en egen HD-pakke som en mappe under «Velg HD-mappe» i sidemenyen (web/src/index.html:113, web/src/app.js:1880-1887). Mappen blir ikke husket. Filene legges til de som allerede er lastet, og en fil med samme nøkkel erstatter den gamle (web/src/render.js:1340-1345). «Fjern» tømmer pakken (web/src/index.html:115, web/src/app.js:1888-1892, web/src/render.js:1359). «Standardgrafikk» laster standardpakken på nytt (web/src/app.js:1893-1899).
- Bryteren «HD der den finnes / Original» slår HD av og på (web/src/index.html:107, web/src/app.js:1901-1915).
- Bryteren «Gult felt der HD-bilde mangler» legger en gul flate over hver figur som mangler HD-bilde (web/src/index.html:110, web/src/app.js:1839, web/src/render.js:1022-1027). Den er slått av hver gang siden lastes (web/src/app.js:1971).
- Figurer byttes ut én og én ut fra hvilket filnavn og bildenummer spillet tegner (web/src/render.js:931). Bakgrunner byttes ut ut fra en hash av innholdet (web/src/render.js:1079), eller gjennom en scene som kjenner igjen hele bildet (web/src/scenes.js:33-55).
- Mangler et HD-bilde, eller passer ikke originalpikslene, vises originalen (web/src/render.js:931-983, web/src/render.js:1094-1098).

## 3. Nøyaktig format

### 3.1 Mapper og filnavn

Nettsiden lager en nøkkel av de to siste leddene i stien: mappenavnet og filnavnet uten .png, begge med små bokstaver (web/src/render.js:1325-1327). Mapper lenger opp betyr ingenting. Store og små bokstaver spiller ingen rolle.

| Hva | Sti i pakken | Regel |
|---|---|---|
| Figur | `KN1.ob/012.png` | Mappen heter som grafikkfilen. Filen er bildenummeret med tre sifre og nuller foran (web/src/render.js:931). |
| Bakgrunn | `bg/62d8d655.png` | `bg/` + hash med 8 heksadesimale sifre, små bokstaver og nuller foran (web/src/render.js:1079, docs/hd-grafikk.md:120-122). |

Eksempler som virker:
- `MinPakke/figurer/KN1.ob/012.png` gir nøkkelen `kn1.ob/012`
- `hd/bg/62d8d655.png` gir `bg/62d8d655`
- `Balok1.CEL/000.png` og `bold.f/073.png` (MOONSTONE-logoen, docs/hd-grafikk.md:136-138)

Eksempler som aldri treffer:
- `KN1.ob/12.png`, fordi bildenummeret må ha tre sifre (web/src/render.js:931)
- `KN1.ob/012@4x.png` eller `012.png.png`, fordi nøkkelen blir en annen (web/src/render.js:1327)
- `HighWood.PIV/0.png`, `bg1a.PIV/000.png` eller `test/8.png`. Bakgrunner slås bare opp med hash (web/src/render.js:1079).

Bruk navnene i kolonnen hd_fil i docs/grafikkliste.csv (docs/grafikkliste.md:9-13, docs/grafikkliste.csv:1-2).

To par filer i spillet er byte for byte like:
- Klift1.CEL og hen1.c er like. Lag tegningene én gang, men legg dem i begge mappene, fordi nettsiden slår opp på filnavnet spillet laster (port/src/game.c:169-178, web/src/render.js:931). Klift1.CEL brukes bare i introen og slutten, som ikke kan få HD ennå, så hen1.c er den som teller.
- hen1.p og bg5.piv er like. De gir samme bakgrunnshash, så ett HD-bilde dekker begge.

### 3.2 Skala og størrelse

- Lag bildene i nøyaktig 4 x originalens bredde og høyde. Det er tallet i kolonnen hd_4x i CSV-filen, for eksempel 44 x 89 som blir 176 x 356 (docs/grafikkliste.csv:2). En bakgrunn blir 1280 x 800. Merk at standardpakken avviker: de fleste bakgrunnene er 1586 x 992, fontene 6x og inventarikonene 8x (målt). Det som betyr noe, er at sideforholdet er det samme som originalen.
- HD-figuren strekkes til figurens lowres-flate, d.w x d.h (web/src/render.js:1031, port/src/game.c:208-209). d.w er den virkelige bredden. Den er ikke rundet opp til 16. Har bildet et annet sideforhold, blir det forvrengt. Logoen bold.f/073.png i standardpakken har dette problemet (2172 x 724 mot 305 x 54).
- Bakgrunnen strekkes over 320 x 200, eller over utsnittet en scene oppgir (web/src/render.js:1090-1091, web/src/render.js:1101).
- Større enn 4x gir ikke skarpere bilde. Det sammensatte bildet er høyst 4 x lowres (web/src/render.js:356). Teksturene har ingen mipmaps (web/src/render.js:1135), så 8x eller mer kan bli kornete.

### 3.3 Farger og palett

- Lever vanlige RGB- eller RGBA-PNG-er. En PNG med palett blir gjort om til RGB, og fargeindeksene betyr ingenting (web/src/render.js:1127-1135).
- HD-bildene får ikke fargene fra spillets palett (web/src/render.js:956-983 sammenligner bare indekser). Unntaket er konturikonene i icons.json, som fargelegges med skjermens palett (web/src/render.js:1160). De har faste farger på alle skjermer (docs/hd-grafikk.md:160-161, docs/grafikkliste.md:16). Velg fargene fra skjermen figuren vanligvis vises på.
- PNG-ene fra `gfx.py extract` har en forhåndsvisningspalett tatt fra test bilde 4. Det er ikke alltid fargene skjermen bruker (tools/gfx.py:52-58, docs/hd-grafikk.md:155-156). Bruk dem til form, ikke som fasit for farge.
- Følgen er at riddere som deler et figursett, får samme farge i HD (docs/hd-grafikk.md:160-161).
- Det eneste nettsiden endrer i vanlige HD-bilder, er lysstyrken ved toning (web/src/render.js:1029, web/src/render.js:1089).

### 3.4 Gjennomsiktighet

- Figurer bruker alfakanalen, og myke kanter virker (docs/hd-grafikk.md:52-53). Fargeindeks 0 betyr ikke gjennomsiktig. Det som skal være gjennomsiktig, må være det i alfa.
- Når HD-figuren godtas, fjernes originalpikslene den dekker fra forgrunnen (web/src/render.js:984). Der HD-bildet er gjennomsiktig innenfor originalens silhuett, synes bakgrunnen og ikke figuren. HD-bildet må derfor dekke hele originalens silhuett.
- Skyggen lages av forgrunnslaget og ikke av HD-bildet (web/src/render.js:313-314).
- Lag bakgrunner helt dekkende, uten gjennomsiktige deler (bakgrunnsmaterialet er web/src/render.js:299).

### 3.5 Speiling

Ikke lag speilede filer. Nettsiden snur bildet selv (web/src/render.js:1032, port/src/game.c:207-211). Tegn hvert bilde vendt samme vei som gfx.py pakker det ut.

## 4. Grafikk som må lages, i prioritert rekkefølge

Den fulle oversikten, med belegg og det som er usikkert, står i docs/hd-mangler.md. Kort fortalt har standardpakken i `web/hd` i dag fontene (143 av 148), 40 av 50 bilder i ki.cel, pekeren, riddervalget, 40 bakgrunner og fem poser av den blå ridderen. Av 2329 figurbilder har 189 HD. Spillet har 74 grafikkfiler med 2361 bilder, og 38 av dem er tomme (docs/grafikkliste.md:5). Hopp over de tomme bildene (plan 0 i CSV). Størrelsene er bredde x høyde.

«Klar» betyr at en PNG med riktig navn virker uten kodeendring. «Venter» betyr at nettsiden må endres først (punkt 8).

| Pri. | Hva | Filer eller hash (antall bilder) | Original | Klar? |
|---|---|---|---|---|
| 1 | Kampbakgrunner i huler | `bg/HASH.png` for fol1-6 (3a38d016, 5ecac111, 5e1dc378, 5c6a3697, 954ee2f9, db6fc7ba), gll1-6 (4b68f426, 8feef9f5, 6113f65e, 6b05bdcd, b95b11e9, 73c7f5c1), swl1-6 (14a894c2, b7afa780, df1460be, 4aca74c6, 09b477b7, b33ce188) og wal1-6 (ed554452, 756408ca, 850cdd99, 93d40a06, 75c0760c, 5c5085b2). 24 bilder. Utkast finnes i art/photoreal | 320 x 200 | Klar |
| 2 | Kartfigurene | mi.c (47, med 019 og 029 tomme): ridderhoder i fire farger, områdeomriss, valgrullen (mi.c/032, 174 x 51), dragen. Beskrivelsen «Små flasker og dråper» i docs/grafikkliste.csv:1643 er feil | Se CSV | Klar |
| 3 | Statusskjermen | ki.cel 034-036 (rankene på buen), 038-043 (STR, CON, END, XP, GOLD, HIT), 044 (NEXT KNIGHT). 10 bilder. Lag dem som konturikoner, som resten av ki.cel (tools/hd_ikoner_bygg.py) | ki.cel/034 er 27 x 60 | Klar |
| 4 | Skjermer i byene | `bg/HASH.png` for butikken e868fda9, inventaret 94e65527 og healeren 2e3c32ae (hea.piv) | 320 x 200 | Klar |
| 5 | Riddere | KN1.ob (60), KN2.ob (24), KN3.ob (64), KN4.ob (26, våpen), KN5.ob (65, blod og sår), HE1.ob (60), HE2.ob (24), HE3.ob (64). 387 bilder. HE er KN med andre fargeindekser | HE1.ob/000 er 23 x 54 | Venter |
| 6 | Monstre i hovedspillet | Balok1-3, be1.c, be2.c, Demon1-4, DRAGON1/2/5, Mudmen1-2, RATMEN1-2, TROGGAxe1-2, TROGGSpear1-2, TROLL1-2. 1128 bilder med innhold. TROGGSpear deler mange bilder med TROGGAxe | Opptil 156 x 15 og 39 x 97 | Delvis. Deler som overlapper en annen tegning avvises |
| 7 | Logoen på nytt | bold.f/073 i riktig sideforhold, 1220 x 216 | 305 x 54 | Klar |
| 8 | Steder i hovedspillet | `bg/HASH.png` for Mythrid d8b4018a (mys.piv) og druidene 94c7f163 (hen1.p = bg5.piv). Figurene dice.cel (23), mys.cel (8), Wi1.C (21) og hen1.c (55) | Se CSV | Klar |
| 9 | Copyrightlinjene og rammen | bold.f 074 og 075, sel.cel 001 (tom ramme, ikke pilen) | 269 x 8, 91 x 8, 64 x 76 | Klar |
| 10 | Blod | blo.cel (41) | Se CSV | Venter (overlapper ridderen) |

Kilder: docs/hd-mangler.md, docs/grafikkliste.csv og web/hd/manifest.json. Rekkefølgen er en vurdering av hvor ofte grafikken vises, delvis målt med tegnelisten. Repoet sier ikke hvilke monstre som er vanligst.

Bakgrunner kan få hashen regnet ut fra PIV-filen når skjermen viser bildet uendret (FNV-1a over de fem planene, port/src/lag.c:77-80). Skjermer der spillet skriver tekst eller markører inn i bakgrunnen, får en annen hash, og den må lagres fra spillet (se punkt 5).

## 5. Slik får du tak i originalbildene

Fra roten av repoet (krever Pillow):

```
python3 tools/gfx.py extract Moonstonecd32-AMIGA.zip assets/gfx
```

- Kommandoen gir 74 mapper og index.json (tools/gfx.py:5, tools/gfx.py:121).
- Figurfilene blir `NAVN/000.png` (tools/gfx.py:115). Bildefiler som PIV blir `NAVN/0.png` (tools/gfx.py:107). PIV-filene er bare til referanse.
- Listen over all grafikk lages på nytt med `python3 tools/grafikkliste.py Moonstonecd32-AMIGA.zip docs` (tools/grafikkliste.py:5).

Bakgrunner lagres fra spillet på en av to måter.

Med nettsiden: start spillet og gå til skjermen. Vent til den er ferdig tonet inn, og trykk «Lagre bakgrunnen». Du får `HASH.png` på 320 x 200, som legges i `bg/` (web/src/index.html:116, web/src/app.js:1854-1879). Knappen gjør ingenting før spillet er startet. På skjermer uten bakgrunn kommer en melding (web/src/app.js:1855, web/src/app.js:1861).

Uten vindu:

```
mkdir -p bg
port/moonstone-headless --game Moonstonecd32-AMIGA.zip --headless --frames 1400 \
  --press 100:esc --press 700:down --press 760:down --press 820:fire --lag-dump bg
```

- Kommandoen gir blant annet 55bb9767.png (tittelmenyen) og 62d8d655.png (øvingskampen, wa1.t). Den gir også 045a1ac5.png, som er en helt tom bakgrunn. Den skal du ikke tegne (punkt 7).
- Mappen må finnes på forhånd. Ellers skrives ingenting, og ingen feil vises (port/src/png.c:35-36, port/src/main.c:182).
- En bakgrunn skrives når den har stått i 50 bilder (port/src/main.c:167-183).
- `--lag F:PREFIKS` lagrer én bestemt skjerm (port/src/main.c:121, port/src/main.c:147-166).

En automatisk startpakke, som er nyttig å sammenligne med:

```
python3 tools/hd_skaler.py assets/gfx hd --ganger 4 --bare KN1.ob KN2.ob ... bg
```

Bruk `--bare` med figurmappene og bg (tools/hd_skaler.py:56-64). Uten `--bare` blir også de 24 bildemappene skalert, og dem leser nettsiden aldri.

## 6. Slik tester du

1. Legg pakken i en mappe, for eksempel `hd/KN1.ob/000.png` og `hd/bg/62d8d655.png`.
2. Bygg og åpne nettsiden. Velg «Velg HD-mappe» og pek på `hd`. Statusen viser hvor mange bilder som ble lest (web/src/app.js:1883-1885).
3. Slå på «Gult felt der HD-bilde mangler». Gule felt viser figurer som fortsatt mangler.
4. Slå «HD/Original» av og på og sammenlign plassering og silhuett.
5. Sjekk at de utpakkede figurene treffer skjermen. Lag først en lagret tilstand med figurer på skjermen (--save-state i moonstone-headless), og kjør:

```
python3 tools/hd_sjekk.py --gfx assets/gfx --state kamp.sav
```

Verktøyet leser `MAPPE/%03d.png` og finner mappen uten å bry seg om store og små bokstaver (tools/hd_sjekk.py:19, tools/hd_sjekk.py:83, tools/hd_sjekk.py:132-133). Det trenger port/moonstone-headless (tools/hd_sjekk.py:80-82).

## 7. Dette skal du IKKE gjøre

- Ikke endre filer i repoet. Lever bare PNG-filer i pakkemappen.
- Ikke lag bakgrunner med navn etter PIV-filer, som `HighWood.PIV/0.png` eller `bg1a.PIV/000.png`. De blir aldri lest (web/src/render.js:1079).
- Ikke lag HD-bilder av bitene i `test` (bilde 0-7). De blir aldri slått opp som figurer, og bakteppet 4-7 står bare 1 til 2 bilder før kampbitene legges på. Kartet (test bilde 8) har allerede HD.
- Ikke lag `bg/045a1ac5.png`. Det er hashen av en helt tom bakgrunn, og bildet ville vises på alle tomme skjermer og i overganger.
- Ikke lag `bg/8dbce956.png` (månen) eller `bg/c234c097.png` (stjernene). De ligger bak lasteskjermen og synes aldri.
- Ikke lag speilede varianter, og ikke lag filnavn uten tre sifre.
- Ikke lag mer enn 4x, og ikke endre sideforholdet.
- Ikke bruk fargeindeks 0 eller en palett-PNG for gjennomsiktighet. Bruk alfa.
- Ikke gjør HD-figuren mindre enn originalens silhuett, siden originalen synes under.
- Ikke flytt eller endre motivet. Treffsonene (collide.hit) følger originalen (docs/hd-grafikk.md:3-4).

## 8. Kan ikke vises i HD ennå. Ikke lag dette, eller merk det som senere

Detaljer og belegg står i docs/hd-mangler.md, punkt 4.

- **Riddere og blod.** En figur avvises hvis den overlapper en tegning som kom tidligere i listen, eller en tegning som har en egen PNG (web/src/render.js:948). Sverdet kn4 tegnes over kroppen, så det avvises alltid. Ridderne får dessuten fargen fra paletten, mens vanlige HD-figurer har faste farger (web/src/render.js:956-983). Posene i web/hd/poses.json krever nøyaktig samme palett som i øvingskampen (web/src/render.js:844, 847) og avvises i en kamp i et hi (målt). Vent til nettsiden kan sette sammen figurer i flere deler og fargelegge dem med skjermens palett.
- **Introen og slutten.** De kjøres av programmet `program`, der laget og tegnelisten mangler (port/src/lag.c:54, port/src/whdload.c:304-305). Figurene au1, co1, da1, dg1, dw1, ha1, Klift1, li1 og ov1 (385 bilder med innhold) og flisbankene bg1a, bg1b og bg1c brukes bare der. Hele stillbilder kan få HD som scene (web/src/scenes.js), men det er en kodeoppgave, ikke en PNG du kan levere alene.
- **Skjermer der spillet skriver inn i bakgrunnen.** Math (WI1.P, WI2.P), terningspillet (dice.piv) og kartet får en ny hash for hver tekst eller markør. Kartet virker allerede gjennom en scene. De andre trenger en scene i manifest.json før en HD-bakgrunn er til nytte.
- **Lasteskjermen, Prepare yourself og Select a Knight.** Nesten alt er forgrunn over en tom bakgrunn, så det finnes ingen bakgrunn å bytte. Hvilke filer banneret og teksten kommer fra, er ikke kartlagt. Teksten tegnes før bakgrunnshashen skifter og mister HD når den skifter (web/src/render.js:484). Portrettene i sel.cel har allerede HD.
- **Bitene i kampbakgrunnene.** De settes sammen av en egen rutine rett i bakgrunnskopien. Bare hele bakgrunnen per .t-fil kan byttes, og 32 av 56 har det allerede.
- **Sidemenyen og knappene på nettsiden.** De bruker originalpikslene og ikke HD-pakken (web/src/grafikk.js:1-20).
- **PC-versjonen.** Den leser ikke HD i det hele tatt.
