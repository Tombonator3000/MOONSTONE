# HD-grafikk til Moonstone: bestilling

Dette er en melding til deg som skal lage HD-bildene. Den sier hva som mangler, hvilket format bildene må ha, og hva du ikke skal lage ennå. Hver påstand viser til fil:linje i repoet https://github.com/Tombonator3000/MOONSTONE (main), så du kan sjekke den selv (linjenumrene er fra 11. oktober 2026 og kan ha flyttet seg litt). Kommandoene kjøres fra roten av repoet.

## 1. Spillet og stilen

Moonstone: A Hard Days Knight kom i 1991 på Amiga, fra Mindscape. Det er mørk og brutal fantasy med riddere, monstre, blod, steinsirkler og nattlige skoger. Originalen er pikselgrafikk i 320 x 200 med 32 farger (fem bitplan). HD-bildene skal ha samme motiv, form og plassering, bare tegnet skarpere. Ikke tegn nye motiver.

## 2. Dette virker allerede i nettsiden

- Du velger en HD-pakke som en mappe under «Velg HD-mappe» i sidemenyen (web/src/index.html:98, web/src/app.js:1765-1771). Mappen blir ikke husket. Du må velge den på nytt hver gang siden lastes. Velger du en ny mappe, legges filene til de som allerede er lastet (web/src/render.js:529-555). «Fjern» tømmer pakken (web/src/app.js:1772, web/src/render.js:558-563).
- Bryteren «HD der den finnes / Original» slår HD av og på (web/src/index.html:92, web/src/app.js:1774-1779).
- Bryteren «Gult felt der HD-bilde mangler» legger en gul flate over hver figur som mangler HD-bilde (web/src/index.html:95, web/src/render.js:270, web/src/render.js:463). Den er slått av hver gang siden lastes (web/src/app.js:1824).
- Figurer byttes ut én og én ut fra hvilket filnavn og bildenummer spillet tegner (web/src/render.js:458). Bakgrunner byttes ut ut fra en hash av innholdet (web/src/render.js:493).
- Mangler et HD-bilde, vises originalen (web/src/render.js:459-460, web/src/render.js:504-508).

## 3. Nøyaktig format

### 3.1 Mapper og filnavn

Nettsiden lager en nøkkel av de to siste leddene i stien: mappenavnet og filnavnet uten .png, begge med små bokstaver (web/src/render.js:532-534). Mapper lenger opp betyr ingenting. Store og små bokstaver spiller ingen rolle.

| Hva | Sti i pakken | Regel |
|---|---|---|
| Figur | `KN1.ob/012.png` | Mappen heter som grafikkfilen. Filen er bildenummeret med tre sifre og nuller foran (web/src/render.js:458). |
| Bakgrunn | `bg/62d8d655.png` | `bg/` + hash med 8 heksadesimale sifre, små bokstaver og nuller foran (web/src/render.js:493, docs/hd-grafikk.md:120-122). |

Eksempler som virker:
- `MinPakke/figurer/KN1.ob/012.png` gir nøkkelen `kn1.ob/012`
- `hd/bg/62d8d655.png` gir `bg/62d8d655`
- `Balok1.CEL/000.png` og `bold.f/073.png` (MOONSTONE-logoen, docs/hd-grafikk.md:136-138)

Eksempler som aldri treffer:
- `KN1.ob/12.png`, fordi bildenummeret må ha tre sifre (web/src/render.js:458)
- `KN1.ob/012@4x.png` eller `012.png.png`, fordi nøkkelen blir en annen (web/src/render.js:534)
- `HighWood.PIV/0.png`, `bg1a.PIV/000.png` eller `test/8.png`. Bakgrunner slås bare opp med hash (web/src/render.js:493).

Bruk navnene i kolonnen hd_fil i docs/grafikkliste.csv (docs/grafikkliste.md:9-13, docs/grafikkliste.csv:1-2).

To par filer i spillet er byte for byte like:
- Klift1.CEL og hen1.c er like. Lag tegningene én gang, men legg dem i begge mappene, fordi nettsiden slår opp på filnavnet spillet laster (port/src/game.c:169-178, web/src/render.js:458).
- hen1.p og bg5.piv er like. De gir samme bakgrunnshash, så ett HD-bilde dekker begge.

### 3.2 Skala og størrelse

- Lag bildene i nøyaktig 4 x originalens bredde og høyde. Det er tallet i kolonnen hd_4x i CSV-filen, for eksempel 44 x 89 som blir 176 x 356 (docs/grafikkliste.csv:2). En bakgrunn blir 1280 x 800.
- HD-figuren strekkes til figurens lowres-flate, d.w x d.h (web/src/render.js:465, port/src/game.c:208-209). d.w er den virkelige bredden. Den er ikke rundet opp til 16. Har bildet et annet sideforhold, blir det forvrengt.
- Bakgrunnen strekkes over 320 x 200 (web/src/render.js:512).
- Større enn 4x gir ikke skarpere bilde. Det sammensatte bildet er høyst 4 x lowres (web/src/render.js:302). Teksturene har ingen mipmaps (web/src/render.js:544-545), så 8x eller mer kan bli kornete.

### 3.3 Farger og palett

- Lever vanlige RGB- eller RGBA-PNG-er. En PNG med palett blir gjort om til RGB, og fargeindeksene betyr ingenting (web/src/render.js:536-549).
- HD-bildene får ikke fargene fra spillets palett. De har faste farger på alle skjermer (docs/hd-grafikk.md:160-161, docs/grafikkliste.md:16). Velg fargene fra skjermen figuren vanligvis vises på.
- PNG-ene fra `gfx.py extract` har en forhåndsvisningspalett tatt fra test bilde 4. Det er ikke alltid fargene skjermen bruker (tools/gfx.py:52-58, docs/hd-grafikk.md:155-156). Bruk dem til form, ikke som fasit for farge.
- Følgen er at riddere som deler et figursett, får samme farge i HD (docs/hd-grafikk.md:160-161).
- Det eneste nettsiden endrer i HD-bildet, er lysstyrken ved toning (web/src/render.js:464, web/src/render.js:502).

### 3.4 Gjennomsiktighet

- Figurer bruker alfakanalen, og myke kanter virker (web/src/render.js:549, docs/hd-grafikk.md:52-53). Fargeindeks 0 betyr ikke gjennomsiktig. Det som skal være gjennomsiktig, må være det i alfa.
- Originalfiguren ligger fortsatt under HD-bildet (web/src/render.js:488, web/src/render.js:264). Der HD-bildet er gjennomsiktig innenfor figurens felt, synes originalpikslene. HD-bildet må derfor dekke hele originalens silhuett.
- Skyggen lages av originalen og ikke av HD-bildet (web/src/render.js:259-261).
- Bakgrunner ignorerer alfa (web/src/render.js:91). Lag dem helt dekkende, 1280 x 800, uten gjennomsiktige deler.

### 3.5 Speiling

Ikke lag speilede filer. Nettsiden snur bildet selv (web/src/render.js:466, port/src/game.c:207-211). Tegn hvert bilde vendt samme vei som gfx.py pakker det ut.

## 4. Grafikk som må lages, i prioritert rekkefølge

Det finnes ingen HD-pakke i repoet ennå (docs/hva-mangler.md:118-147). Totalt har spillet 74 grafikkfiler med 2361 bilder, og 38 av dem er tomme (docs/grafikkliste.md:5). Hopp over de tomme bildene (plan 0 i CSV). Størrelsene er bredde x høyde.

| Pri. | Gruppe | Filer (antall bilder) | Original | HD (4x) |
|---|---|---|---|---|
| 1 | Riddere | KN1.ob (60), KN2.ob (24), KN3.ob (64), KN4.ob (26, våpen), KN5.ob (65, blod og sår), HE1.ob (60), HE2.ob (24), HE3.ob (64). Til sammen 387. | Varierer. Bredest er KN5.ob/040 på 126 x 9, høyest KN5.ob/058 på 39 x 74. Eksempel: HE1.ob/000 er 23 x 54. | Fra hd_4x, for eksempel 92 x 216 |
| 2 | Fonter | bold.f (76, med 69 og 72 tomme), Small.font (72, med 69 tomt) | bold.f 0-71 er 19 høye. 73 er logoen på 305 x 54, 74-75 er copyright-linjene. Small.font er 3-6 x 6. | 4x, logoen blir 1220 x 216 |
| 3 | Meny og tittel | sel.cel (6: pilen og portrettene) | Pilen 38 x 19, portrettene 64 x 76 | 152 x 76 og 256 x 304 |
| 4 | Kamp (felles) | au1.cel (92), blo.cel (41), co1.cel (25), da1.cel (52), ov1.cel (4), li1.cel (30, magi) | ov1.cel opptil 51 x 144 og 140 x 96. au1.cel/000 er 44 x 89. | Fra hd_4x |
| 5 | Inventar | ki.cel (50), mi.c (47, med 019 og 029 tomme), po.cel (1, pekeren) | mi.c/032 er 174 x 51, po.cel er 16 x 18 | Fra hd_4x |
| 6 | Monstre | Balok1-3, be1.c, be2.c, Demon1-4, dg1.cel, DRAGON1/2/5, Klift1 (= hen1.c), Mudmen1-2, RATMEN1-2, TROGGAxe1-2, TROGGSpear1-2, TROLL1-2. Til sammen 1264, 26 tomme. | Opptil 156 x 15 (DRAGON2/027) og 39 x 97 (DRAGON5/002) | Fra hd_4x |
| 7 | Steder og figurer der | dw1.cel (53), ha1.cel (22), hen1.c (55, = Klift1), Wi1.C (21), mys.cel (8), dice.cel (23) | Se CSV | Fra hd_4x |
| 8 | Bakgrunner, etter hash | Én fil per skjerm som allerede er lagret: bg/HASH.png. Kjente hasher: 62d8d655 (øvingskampen), 55bb9767 (stjernehimmelen i tittelmenyen), 045a1ac5. | 320 x 200 | 1280 x 800 |

Kilder til tabellen: docs/grafikkliste.md:21-94 og docs/grafikkliste.csv. Rekkefølgen er en vurdering av hvor ofte grafikken vises. Den er ikke målt. Ridderne tegnes ti ganger i sekundet i hver kamp (memory.md:66-67). Repoet sier ikke hvilke monstre som er vanligst.

For bakgrunner får du hashen fra spillet. Du kan ikke regne den ut fra PIV-filen (se punkt 5).

## 5. Slik får du tak i originalbildene

Fra roten av repoet (krever Pillow):

```
python3 tools/gfx.py extract Moonstonecd32-AMIGA.zip assets/gfx
```

- Kommandoen gir 74 mapper og index.json (tools/gfx.py:5, tools/gfx.py:121).
- Figurfilene blir `NAVN/000.png` (tools/gfx.py:115). Bildefiler som PIV blir `NAVN/0.png` (tools/gfx.py:107). PIV-filene er bare til referanse.
- Listen over all grafikk lages på nytt med `python3 tools/grafikkliste.py Moonstonecd32-AMIGA.zip docs` (tools/grafikkliste.py:5).

Bakgrunner lagres fra spillet på en av to måter.

Med nettsiden: start spillet og gå til skjermen. Vent til den er ferdig tonet inn, og trykk «Lagre bakgrunnen». Du får `HASH.png` på 320 x 200, som legges i `bg/` (web/src/index.html:100, web/src/app.js:1739-1764). Knappen gjør ingenting før spillet er startet. På skjermer uten bakgrunn kommer en melding (web/src/app.js:1740, web/src/app.js:1746).

Uten vindu:

```
mkdir -p bg
port/moonstone-headless --game Moonstonecd32-AMIGA.zip --headless --frames 1400 \
  --press 100:esc --press 700:down --press 760:down --press 820:fire --lag-dump bg
```

- Kommandoen gir 045a1ac5.png, 55bb9767.png og 62d8d655.png.
- Mappen må finnes på forhånd. Ellers skrives ingenting, og ingen feil vises (port/src/png.c:35-36, port/src/main.c:182).
- En bakgrunn skrives når den har stått i 50 bilder (port/src/main.c:167-183).
- `--lag F:PREFIKS` lagrer én bestemt skjerm (port/src/main.c:121, port/src/main.c:156-166).

En automatisk startpakke, som er nyttig å sammenligne med:

```
python3 tools/hd_skaler.py assets/gfx hd --ganger 4 --bare KN1.ob KN2.ob ... bg
```

Bruk `--bare` med figurmappene og bg (tools/hd_skaler.py:56-64). Uten `--bare` blir også de 24 bildemappene skalert, og dem leser nettsiden aldri.

## 6. Slik tester du

1. Legg pakken i en mappe, for eksempel `hd/KN1.ob/000.png` og `hd/bg/62d8d655.png`.
2. Bygg og åpne nettsiden. Velg «Velg HD-mappe» og pek på `hd`. Statusen viser hvor mange bilder som ble lest (web/src/app.js:1768-1769).
3. Slå på «Gult felt der HD-bilde mangler». Gule felt viser figurer som fortsatt mangler.
4. Slå «HD/Original» av og på og sammenlign plassering og silhuett.
5. Sjekk at de utpakkede figurene treffer skjermen. Lag først en lagret tilstand med figurer på skjermen (--save-state i moonstone-headless), og kjør:

```
python3 tools/hd_sjekk.py --gfx assets/gfx --state kamp.sav
```

Verktøyet leser `MAPPE/%03d.png` og finner mappen uten å bry seg om store og små bokstaver (tools/hd_sjekk.py:19, tools/hd_sjekk.py:83, tools/hd_sjekk.py:132-133). Det trenger port/moonstone-headless (tools/hd_sjekk.py:80-82).

## 7. Dette skal du IKKE gjøre

- Ikke endre filer i repoet. Lever bare PNG-filer i pakkemappen.
- Ikke lag bakgrunner med navn etter PIV-filer, som `HighWood.PIV/0.png` eller `bg1a.PIV/000.png`. De blir aldri lest (web/src/render.js:493).
- Ikke lag HD-bilder av bitene i `test` (bilde 0-8). De blir aldri slått opp (web/src/render.js:458, web/src/render.js:493).
- Ikke lag speilede varianter, og ikke lag filnavn uten tre sifre.
- Ikke lag mer enn 4x, og ikke endre sideforholdet.
- Ikke bruk fargeindeks 0 eller en palett-PNG for gjennomsiktighet. Bruk alfa.
- Ikke gjør HD-figuren mindre enn originalens silhuett, siden originalen synes under.
- Ikke flytt eller endre motivet. Treffsonene (collide.hit) følger originalen (docs/hd-grafikk.md:3-4).

## 8. Kan ikke vises i HD ennå. Ikke lag dette, eller merk det som senere

- **Kartet (test bilde 8).** Ridderne tegnes inn i selve bakgrunnskopien når turen starter (port/src/hver.c:15-16). Da endres hashen etter hvor de står. Ett HD-kart passer trolig bare én stilling. Det er ikke målt. Vent.
- **Kampbakgrunnene fra .t-filene.** De kan bare få HD som én ferdig bakgrunn per hash (web/src/render.js:493). Hvordan .t-filene setter dem sammen, er ukjent (todo.md:19). Lag bare de hashene som er lagret fra spillet. I dag er det øvingskampen, 62d8d655.
- **Byer, tavernaen og stedene (PIV).** Det går bare etter hash. Hver skjerm må lagres med «Lagre bakgrunnen» først. Skjermer der spillet skriver inn i bakgrunnen, for eksempel en markør, får ny hash (docs/hd-grafikk.md:162-164).
- **Introen (mindscape, bg8.PIV) og sluttscenen.** Lagene og tegnelisten finnes bare når mog er lastet (port/src/lag.c:54, docs/hd-grafikk.md:23). Nettsiden slår dessuten av HD i sluttscenen (docs/hva-mangler.md:75-81).
- **Menyrammer og tekst som ikke tegnes med tegn_figur.** De har ingen HD-nøkkel og kan bare byttes som en del av en bakgrunn (docs/hd-grafikk.md:165-169).
- **Select a Knight.** Hele skjermen er forgrunn, så det finnes ingen bakgrunn å bytte (docs/hd-grafikk.md:99-100). Portrettene i sel.cel kan byttes som figurer. Sjekk i spillet hvilke av bilde 1-5 som er de fire ridderne før du tegner, fordi bilde 1 har fire plan og 2-5 har fem (docs/grafikkliste.csv:1963-1967).
- **Sidemenyen og knappene på nettsiden.** De bruker ikke HD-pakken (web/src/grafikk.js:1-21).
- **Inntoning første gang en skjerm vises.** Her vises HD-bildet i full styrke mens originalen toner inn (web/src/render.js:495-497). Det er en feil i koden, ikke noe du skal rette i bildene.
- **Butikken (Merchant), figurene på kartet og om po.cel er en figur.** Dette er ikke kartlagt. Vent til det er sjekket med `--tegneliste`.
