# HD-grafikk til Moonstone: bestilling

Alt under streken er en ferdig melding. Lim den inn til ChatGPT og legg ved `docs/hd-bestilling-liste.csv`. Listen lages på nytt med `python3 tools/hd_bestilling.py Moonstonecd32-AMIGA.zip docs/hd-bestilling-liste.csv`, og tallene under er fra den kjøringen (11. oktober 2026). Bakgrunnen for listen, med belegg, står i `docs/hd-mangler.md`.

Send ikke meldingen før to ting er flettet til main, for meldingen viser til dem: denne bestillingen (`docs/hd-bestilling-liste.csv`, `tools/hd_bestilling.py`, `docs/hd-mangler.md` og de to kildebildene i `art/photoreal/references/runtime_background/`), og visningen av figurer i flere deler med farge fra paletten (masken i punkt 3.5, beskrevet i `docs/hd-grafikk.md` under «Farge fra paletten»). Sjekk at filene finnes på https://github.com/Tombonator3000/MOONSTONE/tree/main før du sender.

---

Hei! Jeg vil ha hjelp til å tegne HD-grafikk til et gammelt Amiga-spill. Vedlagt er en liste med en rad per bilde. Under står hva spillet er, hvordan bildene skal se ut, nøyaktig hvilket format nettsiden trenger, og hvor du finner originalbildet til hver rad. Repoet er https://github.com/Tombonator3000/MOONSTONE (grenen main). Kommandoene kjøres fra roten av repoet og krever Python 3 med Pillow.

## 1. Spillet og stilen

Moonstone: A Hard Days Knight kom på Amiga i 1991, fra Mindscape. Det er mørk og brutal fantasy: fire riddere på jakt etter en magisk stein, kamper mot troll, demoner og drager, blod, steinsirkler, skoger om natten. Originalen er pikselgrafikk i 320 x 200 med 32 farger. Nettsiden kjører det originale spillet i en emulator og legger HD-bildene oppå, rute for rute, der spillet tegner originalen.

Stilen er den som allerede er i bruk i `web/hd/`: bakgrunnene er malt nesten fotografisk, med mørkt nattlys og jordfarger (se for eksempel `web/hd/bg/62d8d655.png`, øvingskampen). Logoen er gullmetall. Ikonene i inventaret (`web/hd/ki.cel/`) er rene konturtegninger som får fargen fra spillet.

Det viktigste: **samme motiv, samme form, samme plassering, bare skarpere.** Ikke legg til ting, ikke flytt noe, ikke endre posen. Et sverd som peker opp til høyre i originalen, skal peke opp til høyre i HD-bildet, og det skal slutte på samme sted. Spillets treffsoner følger originalens piksler.

## 2. Listen

`docs/hd-bestilling-liste.csv` har 1871 rader, skilt med semikolon. Kolonnene:

| Kolonne | Hva |
|---|---|
| prioritet | 1 er viktigst. «senere» betyr at det ikke kan vises ennå |
| gruppe | Hva slags grafikk |
| fil, bilde | Originalfilen i spillet og bildenummeret i den |
| hd_fil | Eksakt sti i HD-pakken. Bruk den uendret |
| kilde_bredde, kilde_hoyde | Originalens størrelse i piksler |
| hd_bredde, hd_hoyde | Størrelsen HD-bildet skal ha |
| farger_fra_palett | ja: spillet bytter noen av fargene (rustningen til ridderne). Se punkt 3.5 |
| trenger_maske | ja: lever også en maske. Se punkt 3.5 |
| hvor_i_spillet | Hvor bildet vises |
| merknad | Hva som er spesielt: like bilder, utkast som finnes, kilde til bakgrunner |

Antall per gruppe, i rekkefølgen du bør ta dem:

| Pri | Gruppe | Rader | Filer |
|---|---|---|---|
| 1 | Hulekamp | 24 | Bakgrunner: fol1-6, gll1-6, swl1-6, wal1-6 (.t) |
| 2 | Kartfigurer | 45 | mi.c |
| 4 | Byskjermer | 3 | Butikken, inventaret, healeren (bakgrunner) |
| 5 | Riddere | 196 | KN1-4.ob, HE1-3.ob |
| 7 | Logo | 1 | bold.f/073, på nytt i riktig sideforhold |
| 7 | Monstre | 1050 | Balok, beistet, Demon, DRAGON, Mudmen, RATMEN, TROGGAxe, TROGGSpear, TROLL |
| 8 | Steder | 4 | Mythrid, druidene, Math inne og ute (bakgrunner) |
| 8 | Taverna og by | 32 | dice.cel, mys.cel, bordet i terningspillet |
| 9 | Introscener | 4 | bg3, bg1b, bg2a, mindscape (bakgrunner) |
| 10 | Blod og sår | 106 | KN5.ob, blo.cel |
| 10 | Stedsfigurer | 72 | Wi1.C, hen1.c |
| 11 | Meny, tittelmeny, sluttscene | 5 | sel.cel/001, bold.f 074 og 075, bg7, bg8 |
| senere | Intro og slutt | 329 | au1, co1, da1, dg1, dw1, ha1, li1, ov1 |

Det er 38 bakgrunner og 1833 figurbilder. 156 rader trenger maske: ridderbildene og blodbildene som har rustningsfarger i seg (KN1 55, KN3 45, KN2 21, KN5 15, HE1 13, HE2 6, KN4 1). I tillegg kommer 101 masker til HE-kopiene (punkt 3.5). Prioritet 3 i oversikten vår (statusskjermen) er ikke med; den lager vi selv (punkt 7).

Rekkefølgen følger hvor ofte grafikken vises og hvor lite som skal til før den virker. Prioritet 1, 2 og 4 skal virke så snart filen ligger i en mappe du velger med «Velg HD-mappe» (punkt 6). For bakgrunnene er hashene målt i spillet, for mi.c er det lest ut av koden og ikke prøvd. I standardpakken på nettsiden (`web/hd/`) må hver fil i tillegg føres i `web/hd/manifest.json` med sha256 og størrelse, og bakgrunnene for Math, terningspillet og introen trenger en scene der. Det gjør vi når du leverer. Ridderne, monstrene og blodet får støtte i koden i en endring som pågår nå. Prioritet 6 i oversikten vår (lasteskjermen og bannerne) er ikke med, fordi den ikke kan bestilles ennå (punkt 7). Vi vet ikke hvilke monstre som er vanligst, så ta dem i den rekkefølgen listen har.

## 3. Format

### 3.1 Mappe og filnavn

Bruk stien i kolonnen hd_fil, for eksempel `KN1.ob/012.png` eller `bg/3a38d016.png`. Legg alt i én mappe med de samme undermappene. Nettsiden lager nøkkelen av de to siste leddene i stien (mappen og filnavnet uten .png), og store og små bokstaver spiller ingen rolle (web/src/render.js:1327). Derfor:

- Figurer: mappen heter som originalfilen, filnavnet er bildenummeret med tre sifre: `KN1.ob/012.png`, ikke `KN1.ob/12.png`.
- Bakgrunner: `bg/` og åtte heksadesimale sifre, som er en hash av innholdet. Navn etter PIV-filen (`hea.piv/0.png`) blir aldri lest.
- Ikke legg til noe i navnet (`012@4x.png`, `012_v2.png`). Da treffer det ikke.

### 3.2 Størrelse: 4 ganger originalen

Lag hvert bilde i nøyaktig 4 ganger originalens bredde og høyde, slik kolonnene hd_bredde og hd_hoyde sier. En bakgrunn blir 1280 x 800. Logoen blir 1220 x 216.

Hvorfor 4: nettsiden setter sammen bildet i høyst 4 ganger spillets oppløsning (web/src/render.js:356), så mer gir ikke skarpere bilde. Med et helt tall svarer hver originalpiksel til nøyaktig 4 x 4 HD-piksler, så kanter, ankerpunkt og masken (3.5) ligger likt med originalen. Det er også tallet i `docs/grafikkliste.csv` (hd_4x). Bildene som allerede ligger i pakken, er laget i andre skalaer (de fleste bakgrunnene er 1586 x 992, fontene 6x, ikonene 8x). De virker, fordi alt strekkes til originalens flate, men nye bilder skal være 4x. Sideforholdet må være det samme som originalen, ellers blir bildet forvrengt. Logoen i pakken i dag er et eksempel på det: 2172 x 724 mot originalens 305 x 54, så den blir flatklemt.

### 3.3 Ett bilde per rute, samme rektangel

Hver rad er én rute i originalen, og HD-bildet strekkes over nøyaktig samme rektangel som den. Altså:

- Lerretet er hele originalruten ganger 4. Ikke beskjær til motivet, og ikke legg til marg.
- Motivet skal ligge på samme sted i lerretet som i originalen. Øverst til venstre i originalen er øverst til venstre i HD-bildet.
- Mange figurer er deler av en større figur (ridderens kropp i ett bilde, beina i det neste, sverdet i et tredje). Delene settes sammen av spillet. Tegn hver del for seg, og la kantene slutte der originalen slutter, så delene passer sammen. Ikke tegn hele ridderen i én rute.
- Ikke lag speilede varianter. Nettsiden snur bildet selv når spillet tegner figuren andre veien.

### 3.4 Gjennomsiktighet

- Figurer: RGBA-PNG. Det som er gjennomsiktig i originalen (fargeindeks 0), skal ha alfa 0. Myke kanter går fint.
- HD-bildet må dekke hele originalens silhuett. Der HD-bildet er gjennomsiktig innenfor originalens figur, synes bakgrunnen og ikke figuren.
- Bakgrunner: helt dekkende, ingen gjennomsiktige deler.
- Lever figurer som RGBA, ikke som palett-PNG med gjennomsiktig farge. Nettleseren gjør riktignok den om til alfa, men da får du ingen myke kanter, og det er lett å miste gjennomsiktigheten når bildet redigeres.

### 3.5 Maske for figurer som får fargen fra paletten

Ridderne (KN1-5.ob og HE1-3.ob) har ikke fast farge på rustningen. Spillet gir hver ridder sin farge ved å bytte fargene i paletten: KN-bildene bruker indeksene 6, 7 og 8 til rustningen og HE-bildene 9, 10 og 11. Den samme tegningen skal derfor kunne vises i alle ridderfargene (blå, grønn, oransje, rød og så videre). Radene med trenger_maske=ja har slike piksler. For dem leverer du to filer:

1. Tegningen, `KN1.ob/012.png`, som vanlig. Tegn i fargene originalen har når du pakker den ut (punkt 4), eller tegn rustningen i grått. Fargen på rustningen kommer uansett fra masken; det som teller der, er lys, skygge og detaljer.
2. Masken, `KN1.ob/012.mask.png` (navnet i hd_fil uten .png, pluss .mask.png). Samme størrelse som tegningen, RGBA, og den leses piksel for piksel uten utjevning:

| Kanal | Betydning |
|---|---|
| R | 0 = behold fargen i tegningen. 7, 8, 9 = palettindeks 6, 7, 8 (indeksen + 1); 10, 11, 12 = indeks 9, 10, 11 |
| G | lysstyrke: 128 gir palettfargen, 0 svart, 255 nesten dobbelt så lyst |
| B | hvor mye av palettfargen som brukes: 255 helt, 0 ingenting |
| A | brukes ikke, la den være 255 |

Bare rustningen skal ha R satt. Alt annet (hud, lær, sverd, kanter) har R = 0, G = 0, B = 0, og vises med tegningens egne farger. Der R er satt og B er 255, spiller tegningens farge ingen rolle; da bestemmer G hvor lyst det blir. Skyggene og detaljene i HD-rustningen må derfor ligge i G. Mykere overgang mot resten av tegningen får du med B under 255 langs kanten.

Masken lages med

```
python3 tools/hd_bestilling.py --maske assets/gfx/KN1.ob/012.png hd/KN1.ob/012.mask.png hd/KN1.ob/012.png
```

Første fil er originalen (punkt 4), andre er masken som lages, og tredje er tegningen din. Kommandoen forstørrer originalens indekser til tegningens størrelse med nærmeste nabo, setter R og B der originalen har indeksene 6-11, og regner ut G av lysstyrken i tegningen delt på lysstyrken til den samme fargen i originalen. Tegner du i originalens farger, blir G 128 der tegningen har samme lysstyrke som originalen, og skyggene i tegningen blir med. Uten den tredje filen blir masken 4x originalen med G = 128 overalt. Etterpå kan du rette kantene for hånd så de følger tegningen. Ikke bytt indeksene, og ikke bruk utjevning i R.

Mange bilder i HE1-3.ob er de samme som i KN1-3.ob, bare med indeksene 6, 7 og 8 byttet til 9, 10 og 11. De står ikke som egne rader. Merknaden på KN-raden sier hvor tegningen også skal ligge: legg samme tegning der, og legg ved masken med R byttet fra 7, 8, 9 til 10, 11, 12 (G og B som før). Kommandoen over med HE-originalen som første fil gir det samme.

### 3.6 Like bilder

Noen bilder finnes i flere filer, byte for byte like (troggen med øks og troggen med spyd deler 62 bilder, hen1.c og Klift1.CEL er like, sverdene i KN4.ob brukes også av noen monstre). De står bare én gang i listen. Merknaden sier hvor tegningen også skal ligge. Lag en tegning og kopier filen dit.

## 4. Slik finner du originalbildet

Figurer:

```
python3 tools/gfx.py extract Moonstonecd32-AMIGA.zip assets/gfx
```

Det gir en mappe per fil med ett PNG per bilde, med samme navn som i hd_fil: `assets/gfx/KN1.ob/012.png` er originalen til raden med hd_fil `KN1.ob/012.png`. PNG-ene er indekserte. Fargene er en forhåndsvisning med paletten fra skogkampen, ikke alltid fargene skjermen bruker, så bruk dem til form og som utgangspunkt for farge. Størrelser og en kort beskrivelse av hver fil står i `docs/grafikkliste.md`, som lages med `python3 tools/grafikkliste.py Moonstonecd32-AMIGA.zip docs`.

Bakgrunner: merknaden på hver bakgrunnsrad sier hvor kilden ligger.

- Hulekampene (prioritet 1): `art/photoreal/references/runtime_background/fol1.t.png` og så videre. De er satt sammen av spillet og finnes ikke som egen fil.
- Butikken og inventaret: `art/photoreal/references/runtime_background/e868fda9.png` og `94e65527.png`, lagret fra emulatoren.
- De andre er bildefiler i spillet: `assets/gfx/hea.piv/0.png`, `assets/gfx/mys.piv/0.png` og så videre etter kommandoen over.

Alle er 320 x 200. Det finnes også eldre utkast i `art/photoreal/candidates/` for mange rader (merknaden sier hvilke og hvilken status de har). Ingen av dem er godkjent. Bruk dem gjerne som utgangspunkt, men følg originalen der de avviker.

## 5. Det som skal tegnes på nytt

- **Logoen** (`bold.f/073.png`, 1220 x 216). Dagens logo er fin, men har feil sideforhold. Behold uttrykket (gullmetall, MOONSTONE med de tre O-diamantene og «A Hard Days Knight» under), men tegn den så den fyller 305 x 54 ganger 4, som originalen.
- **Hulekampene** (24 bakgrunner). Utkastene er teknisk i orden, men runene på steinene er tegnet om. Vil eieren ikke ha de nye runene, tegnes de på nytt etter originalen.
- **Healeren, Mythrid, druidene, Math inne og ute og introscenene** har utkast med avvik som står i merknaden (endret bokdiagram, nye tegn, en stjerne for mye og så videre). Tegn dem på nytt der avviket er.
- **Trollet** er blått i spillet. Utkastene er brune og gylne.

## 6. Levering og test

Lever PNG-filene i en mappe med samme oppbygning som hd_fil (for eksempel `hd/KN1.ob/012.png`, `hd/KN1.ob/012.mask.png`, `hd/bg/3a38d016.png`). Ikke endre noe annet i repoet.

Du kan prøve pakken selv: bygg nettsiden (`make -C port web`) eller bruk https://tombonator3000.github.io/MOONSTONE/, åpne sidemenyen, velg «Velg HD-mappe» og pek på mappen. Slå på «Gult felt der HD-bilde mangler», så ser du hvilke figurer som fortsatt mangler. «HD / Original» bytter mellom HD og originalen, så du kan sjekke at plasseringen stemmer. For ridderne: i øvingskampen skal din ridder være blå og motstanderen grønn med de samme tegningene. Er rustningen i tegningens egne farger, er masken ikke lest (feil navn eller størrelse).

## 7. Dette skal du ikke lage

- `bg/045a1ac5.png`. Det er hashen av en helt tom skjerm, og bildet ville vist seg på alle tomme skjermer og i overganger.
- `bg/8dbce956.png` (månen) og `bg/c234c097.png` (stjernene). De ligger bak lasteskjermen og synes aldri.
- Bitene i `test` (bilde 0-7). Kampbakgrunnene settes sammen av dem, men bare den ferdige bakgrunnen kan byttes, og 32 av 56 har HD allerede.
- Lasteskjermen («MOONSTONE ... Loading»), «Prepare yourself» og «Select a Knight». Nesten alt der er tegnet oppå en tom bakgrunn, og vi vet ikke hvilke filer banneret og teksten kommer fra. De kommer i en senere bestilling.
- Flisene i bg1a, bg1b og bg1c. De settes sammen i introen etter en tabell vi ikke har dekodet.
- ki.cel 034-036 og 038-044 (statusskjermen). Ikonene i inventaret er konturtegninger i 8 ganger originalen som lages av originalens piksler med `tools/hd_ikoner_bygg.py`, med en oppføring i `web/hd/icons.json` som gir dem fargen fra spillet. Nettsiden godtar bare den skalaen for ikonene. Dem lager vi selv.
- Det som allerede har HD: fontene, ki.cel 000-033 og 037, pekeren, riddervalget og 40 bakgrunner (`web/hd/manifest.json`). Bare logoen skal tegnes på nytt.
- Rader med prioritet «senere» (intro og slutt, 329 rader). Introen og slutten kjøres av et eget program der nettsiden ikke ser hva som tegnes, så bildene kan ikke vises ennå. Vent med dem.

## 8. Det som ikke er sikkert

- Masken (3.5) er prøvd med syntetiske bilder (originalene 4x med rød rustning): samme bilde ble blått, grønt, oransje og rødt etter hvilken ridder som kjemper. Den er ikke prøvd med en ekte HD-tegning ennå.
- Hvilke indekser hver av de fire ridderne og den svarte ridderen får i kamp, er ikke målt. Masken lages derfor av originalens indekser, ikke av fargene.
- KN5.ob og blo.cel (blod og sår) er ikke sett på skjermen i målingene våre. Vi antar at de brukes.
- Bakgrunnene for Math (WI1.P, WI2.P), terningspillet og introscenene trenger en scene i `web/hd/manifest.json` før de vises. Den lager vi. Tegn bildet uten tekst og markører. WI2.P uten tekst er aldri sett i spillet, så hashen er regnet ut fra filen.
- Monstre kan ha andre farger i et hi enn ute, fordi paletten er en annen. Vi har bare målt ett hi. Ser et monster feil ut i spillet, kommer vi tilbake til det.
