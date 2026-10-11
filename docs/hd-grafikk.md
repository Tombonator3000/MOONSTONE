# Plan for HD-grafikk

Målet er å kunne bytte ut grafikken med versjoner i høy oppløsning, uten å endre
spillkoden eller reglene. Porten kjører originalkoden, så Amigaen tegner fortsatt
320 x 200 i 32 farger. Det er to veier, og de kan brukes sammen.

## 1. Endre filene (virker i dag)

`tools/gfx.py extract` gir alle bakgrunner og figurer som PNG. Rediger dem og kjør
`tools/gfx.py build`, så lages nye datafiler som porten bruker med `--mod MAPPE` (eller
«Egne filer» på nettsiden). Grensene er Amigaens: samme størrelse, samme antall farger,
og fargene til figurene kommer fra paletten til skjermen de vises på. Det er bra for
oppussing og egne varianter, men ikke for ekte HD.

## 2. HD-lag i three.js (figurene virker, eksperimentelt)

Nettsiden tegner Amiga-bildet som en tekstur på en flate i en three.js-scene
(`web/src/render.js`). HD-grafikk legges som egne flater i samme scene, oppå
Amiga-pikslene. Det er samme teknikk som "HD packs" i emulatorer.

### Hva som tegnes hvor (tegnelisten)

Alle figurene tegnes av `tegn_figur` på $9DCEC i mog: A0 er CEL-filen i minnet,
D0 bildenummeret, D1 x og D2 y (lowres-piksler i spillvinduet). Filnavnet finner vi
ved å se på slavens lasterutine for CEL-filer (slave+$58E, A0 navnet, A1 hvor filen
legges). `port/src/game.c` observerer begge og bygger en liste per bilde
(`game_draws`). Den endrer ingenting i spillet, så nettspill og `check_hooks.py`
er upåvirket. Kjernen gir listen til JavaScript med `ms_draws()` og
`Kjerne.tegneliste()`, og PC-versjonen skriver den ut med
`--tegneliste F[:N]`.

Ting vi fant ut underveis:

- **Speiling.** Figurene finnes bare i én retning i filene. `sub_09db16` snur et
  bilde der det ligger i minnet (med tabellen fra `sub_09dbc6` som snur bitene i en
  byte) og skriver om byte 8 i bildetabellen: 1 for vanlig, (utfylling << 4) for
  speilet. `tegn_figur` trekker den øvre halvdelen av byten fra x, så figuren havner
  på samme sted i begge retninger. Tegnelisten har derfor `speilet`, og HD-laget
  snur bildet (negativ bredde på flaten).
- **Klynger.** Spillet tegner figurene i en buffer utenfor skjermen, ofte fordelt på
  bilder på rad (i kamp den ene ridderen i ett bilde og resten i det neste), ti
  ganger i sekundet. Det ferdige bildet vises to bilder etter det siste i klyngen.
  `render.js` samler tegninger fra bilder på rad og viser dem på det tidspunktet.
- **Retning på teksturen.** WebGL snur ikke `ImageBitmap`, så HD-bildene tegnes på
  et lerret før de blir tekstur.

### HD-pakken

En mappe med PNG-er navngitt som `tools/gfx.py extract` gjør det, med mappe per fil
og bildenummer med tre siffer, f.eks. `kn1.ob/012.png` (store og små bokstaver spiller
ingen rolle). Bildet strekkes over figurens plass, så et bilde i fire ganger
størrelse gir fire ganger så skarp figur. Det som skal være gjennomsiktig, må være
gjennomsiktig i PNG-en (alfakanalen).

På nettsiden: Meny, «HD-grafikk», velg mappen. Slå på «Gult felt der HD-bilde
mangler», så vises et gult felt der spillet tegner en figur som ikke har HD-bilde. Da
er det lett å se hva som mangler.

**Liste over all grafikken:** `docs/grafikkliste.md` (laget med
`tools/grafikkliste.py`) har hver fil, hva den er, og hvert bilde med størrelse og
navnet HD-bildet skal ha. `docs/grafikkliste.csv` har det samme med ett bilde per
linje, også et forslag til størrelse i fire ganger originalen.

**Bytte mellom HD og originalen:** «Grafikk: HD der den finnes / Original» i menyen
slår HD-bildene av og på uten å fjerne pakken (`Visning.settHd` i render.js), så
man kan sammenligne. Valget huskes i innstillingene.

### Sjekk av plasseringen

`tools/hd_sjekk.py` kjører emulatoren uten vindu fra en lagret tilstand, legger de
utpakkede figurbildene der tegnelisten sier, og måler treffet mot skjermbildet:

```
python3 tools/hd_sjekk.py --gfx assets/gfx --state kamp.sav --press 5:left:40
```

I kamp og på kartet treffer alle figurene (1,00, eller litt under der noe annet
enn en figur ligger over).

## 3. Lagene: bakgrunn og forgrunn hver for seg

Spillet holder selv en ren kopi av bakgrunnen: fem bitplan på 320 x 200, med en
peker på $8CDE8. Figurene tegnes i et av to skjermbuffere (pekeren til det det
tegnes i, ligger på $AA948), og når en figur flyttes, kopierer spillet bakgrunnen
tilbake fra kopien (rutinen på $882E2, som bruker blitterrutinen på $9E252 for hvert
plan). Det gjør at bildet kan deles i to lag, helt uten å vite hva slags skjerm det
er (`port/src/lag.c`):

- **bakgrunn**: kopien, gjort om til farger med paletten på hver linje
- **forgrunn**: det skjermen viser, der det er annerledes enn bakgrunnen

Forgrunnen tas fra det ferdige skjermbildet, så sprites og fargeskift kommer med.
Lagt oppå hverandre gir lagene derfor nøyaktig det spillet viser (testet: 0 av
614 400 piksler forskjellige). Lagene finnes når skjermen er slik spillet vanligvis
har den (fem plan, 320 x 200); ellers vises skjermbildet som før.

Eksempler: i kamp er bakgrunnen landskapet og forgrunnen ridderne. På kartet er
bakgrunnen kartet og forgrunnen ridderen og markøren. I tittelmenyen er bakgrunnen
stjernehimmelen med trærne, og logoen, tekstene og pilen er forgrunn. Noen skjermer
(«Select a Knight») bruker ikke kopien; da er alt forgrunn.

Det koster rundt 0,3 ms per bilde, og regnes bare ut når noe trenger lagene.

### Renderen

`web/src/render.js` tegner i to trinn. Først settes lagene sammen i et bilde med
høy oppløsning (spillets 320 x 200 ganger 2-6, etter skjermen): hele skjermbildet
underst, så bakgrunnen (eller HD-bakgrunnen), skygge, forgrunnen og HD-figurene.
Så tegnes det bildet på skjermen med filteret (skarp, piksel, myk, CRT) og
effektene. Effektene velges i menyen under «Effekter»:

- **Skygger** under figurer og tekst (forgrunnen i svart, litt forskjøvet)
- **Uskarp bakgrunn**, så figurene trer fram
- **Glød** rundt lyse ting
- **Sterkere og varmere farger**
- **Vignett**

### HD-bakgrunner

En bakgrunn kjennes igjen på innholdet: en hash av de fem bitplanene, skrevet som åtte
heksadesimale sifre. HD-bildet legges i mappen `bg` i HD-pakken med det navnet, for
eksempel `bg/62d8d655.png` for øvingskampen. Det strekkes over hele spillvinduet, så
et bilde på 1280 x 800 gir fire ganger så skarp bakgrunn. Slik får du bakgrunnene:

- På nettsiden: «Lagre bakgrunnen som PNG» under «HD-grafikk» lagrer den som vises,
  med riktig navn.
- Uten vindu: `moonstone-headless --lag-dump MAPPE` skriver hver ny bakgrunn som
  `MAPPE/HASH.png` når den har stått i 50 bilder (og på nytt hvis den blir lysere).
  `--lag F:PREFIKS` skriver begge lagene i bilde F.

Når spillet toner med paletten, tones HD-bakgrunnen, HD-figurene og posene like mye:
lysstyrken til fargene bakgrunnen bruker, mot fullt lys. For en scene (se under) er fullt
lys summen med PIV-filens egen palett, så det er kjent fra første bilde, også når
skjermen toner inn. Ellers er fullt lys det lyseste som har stått stille i minst ti
bilder for den bakgrunnen. Toner skjermen inn før det er kjent, vises originalen til
lyset har stått stille (ellers ville HD-bildene lyst fullt over en mørk skjerm). Posene
avvises ikke lenger mens skjermen toner: uten skjermens palett godtas fargene når de er
posens farger ganger lysstyrken (med ett 4-bits Amiga-trinn slingringsmonn).

**Utsnitt.** Noen bakgrunner dekker bare en del av skjermen: Highwood og kroen
(`bg/438c8bc2`, `bg/44898895`, venstre 256 kolonner) og Waterdeep (`bg/d097d0ff`,
kolonne 66-319). De vises bare når en scene har gitt rektangelet (`rect` i scenen). Står
bakgrunnskopien på en av dem uten scenetreff (en meldingsskjerm over byen), vises
originalbakgrunnen i stedet for at bildet strekkes over hele skjermen. Hvilke bakgrunner
som er utsnitt, leses av scenene i `manifest.json` (et `rect` mindre enn 320 x 200), eller
av `"partial": true` på filoppføringen (`StandardHd.utsnitt()`,
`Visning.settUtsnittBakgrunner`).

### Scener som bare finnes på skjermen

En scene (`manifest.scenes`, `web/src/scenes.js`) kjenner igjen en PIV ut fra indeksene.
Vanligvis sammenlignes med bakgrunnskopien. Med `"compare": "screen"` sammenlignes med
det skjermen viser, for bilder spillet tegner rett på skjermen uten å legge dem i
kopien. En slik scene går foran en som bare stemmer med kopien, og brukes ikke når kopien
selv er bildet (da gjelder den vanlige bakgrunnen). Med `"copy_scene": true` brukes scenen
også da, sammenlignet med kopien (banneret message.piv i meldinger og Prepare yourself).
Alt som avviker fra PIV-en (teksten), blir forgrunn med sine indekser, så tekst og logo
kan få HD over scenen.

Dekker forgrunnen mer enn halve skjermen uten scenetreff, vises ikke HD-bildet av
bakgrunnskopien: da er det ikke kopien som vises, og HD-bildet ville skinne gjennom der
meldingen og kopien har samme indeks (svart).

Målt med `--tegneliste` og `LAG_SPOR=1` (11. oktober 2026):

| Skjerm | Bakgrunnskopien | Det som vises | HD |
|---|---|---|---|
| Lasteskjermen etter introen (også med Esc i introen) | portalen 6e5a5c07, eller månen 8dbce956 | `ch.piv` (trærne fra tittelen) som forgrunn, logoen `bold.f` 73 (y 20), copyrightlinjene `bold.f` 74 og 75, «created by Rob Anderson» og «Loading...» i `bold.f` | Scene `loading` (ch.piv, `bg/55bb9767`). Tekst og logo er figurer. Copyrightlinjene mangler PNG |
| Prepare yourself (før hver kamp) | tittelen 55bb9767, så tom (045a1ac5) | banneret `message.piv` (Stonehenge i lilla) og teksten i `bold.f`, tegnet 44-52 bilder etter valget i tittelmenyen | Scene `message` (931f9b1d) er lagt inn, men `bg/931f9b1d.png` finnes ikke. Utkastet `art/photoreal` message er ikke godkjent. Teksten er figurer og får HD |
| Select a Knight | tom (045a1ac5) | «Select a Knight» i `bold.f` (y 5) og portrettene `sel.cel` 1-5 | Alt er figurer. Det finnes ikke noe eget banner |

Logoen `bold.f/073.png` er 2172 x 724 med tom kant. Innholdet er 2172 x 414 (5,2:1), mens
kilden er 305 x 54 (5,65:1), så beskjæring retter ikke sideforholdet. I `text.json` har den
`"fit": "width"` og et utsnitt rundt innholdet: den fyller figurens bredde og sentreres i
høyden (ca. 59 i stedet for 54 linjer), uten å strekkes. En ny tegning i 5,65:1 er bestilt.

### Tekst i HD

Bokstavene tegnes også av `tegn_figur`, som figurer i fontfilene `bold.f` (den store
fonten; bilde 73 er hele MOONSTONE-logoen) og `Small.font` (den lille, på
statusskjermene). HD-bilder for dem, f.eks. `bold.f/015.png`, gir derfor tekst i HD.

Tekst tegnes bare én gang, mens figurene i kamp tegnes på nytt hele tiden. Med lagene
blir en HD-figur derfor stående så lenge forgrunnen der den ligger er uendret
(sammenlignet med fargeindeksene, så fading ikke teller som en endring), og den
forsvinner når spillet tegner noe annet der. For bokstavene sjekkes det hvert bilde om
de fortsatt står der, og det samme gjelder alle figurer når bakgrunnen byttes: hver
kildepiksel må ha samme indeks, være lik bakgrunnen, eller være dekket av en annen
plassert figur med den indeksen (nabobokstaven over skyggen). Figurene som står, beholdes. Det trengs fordi Prepare yourself tegner teksten mens kopien ennå er
tittelen, og bytter kopien 35 bilder senere. Uten lagene vises en klynge til det har
gått 50 bilder uten nye tegninger, som før.

En tekstrad kan stikke en linje under vinduet («Loading...» på y 182, 19 høy). Da
kontrolleres bare linjene som vises.

### Figurer i flere deler

Mange figurer tegnes i flere deler som overlapper: ridderen er føttene, kroppen og
sverdet (`kn1.ob` og `kn4.ob`), og blod og sår tegnes oppå. HD-figurene tegnes i samme
rekkefølge som i tegnelisten, så en senere figur ligger over en tidligere også når
begge har HD-bilde.

For hver piksel finner renderen eieren: den siste figuren i listen som har en
ikke-gjennomsiktig piksel der i originalen. En figur får HD bare hvis hver piksel i
rektangelet stemmer med eieren sin (samme fargeindeks i forgrunnen, eller lik
bakgrunnen), og hvis ingen figur uten pålitelig kilde ligger i rektangelet. En
forgrunnspiksel ingen figur eier, gir originalen. Bare piksler som eies av en figur med
HD, fjernes fra forgrunnslaget. Piksler som eies av en senere figur uten HD, ligger
foran HD-bildene under (vern), og piksler fra en tidligere figur uten HD blir stående
under. `Visning.hdFigurer(true)` viser hvilke figurer som har HD i bildet som vises.

### Farge fra paletten (masker)

Ridderne deler figursett, og fargen kommer fra paletten: `kn*.ob` bruker indeksene
6-8 og `he*.ob` 9-11 til rustningen, og spillet setter fargene etter hvilken ridder som
kjemper. Spilleren i øvingskampen er blå (6-8) og motstanderen grønn (9-11); i en duell
på kartet er motstanderen oransje eller rød med de samme `he1.ob`-bildene. Et HD-bilde
med faste farger blir derfor feil for alle unntatt én ridder.

Et HD-bilde kan ha en maske ved siden av seg, med samme navn og `.mask.png`, for
eksempel `kn1.ob/012.png` og `kn1.ob/012.mask.png`. Masken legges over bildet med samme
utsnitt (helst samme mål som bildet) og leses piksel for piksel uten utjevning:

| Kanal | Betydning |
|---|---|
| R | 0 = behold fargen i bildet. 1-32 = palettindeks + 1 (7 betyr indeks 6) |
| G | lysstyrke: 128 gir fargen i paletten, 0 svart, 255 nesten dobbelt så lyst |
| B | hvor mye av palettfargen som brukes: 255 helt, 0 ingenting (myk overgang) |
| A | brukes ikke (la den være 255) |

Fargen hentes fra skjermens palett på den linjen pikselen ligger, mens spillet kjører,
så den følger ridderfargen, hiet og toningen. Resten av bildet tones med lysstyrken som
før. Bildets egen farge der masken er satt spiller ingen rolle når B er 255, så det går an
å tegne rustningen i grått og la masken gi fargen, med skyggene i G. Uten gyldig
skanout (HAM, hires, mer enn fem plan) vises figuren som originalen.

`kn1.ob` og `he1.ob` er samme tegning med ulike indekser. Ett HD-bilde kan derfor
brukes for begge: kopier PNG-en, og la masken ha R = 7-9 (indeks 6-8) for `kn*.ob` og
R = 10-12 (indeks 9-11) for `he*.ob`. Prøvd med en syntetisk pakke (originalene 4x med
rød rustning i PNG-en og maske): samme `he1.ob`-bilder ble grønne i øvingskampen og
oransje og røde i dueller på kartet, og den blå ridderen ble blå.

Posene i `poses.json` bruker samme palett, men uten egen maske: originalens indekser
(lowres) er masken, og `palette` i posen er fargene bildet er tegnet med. Fargen flyttes
fra den fargen til skjermens farge (forholdsvis, og som forskjell der referansen er nær
null), så posene virker også når paletten er en annen enn i øvingskampen. I øvingskampen
er fargene like, og bildet vises uendret.

### Glatt (Scale4x) og automatiske HD-pakker

Filteret «Glatt (Scale4x)» runder av trappetrinnene i all grafikken uten HD-bilder:
Scale2x (EPX) brukes to ganger i shaderen for Amiga-lagene. Det lager ingen nye
farger, så paletten og fadingen er spillets egen, og kantene på figurene rundes også
(alfa er med).

`tools/hd_skaler.py INN UT` gjør det samme med PNG-filer og lager en HD-pakke i fire
ganger størrelse av alt `tools/gfx.py extract` gir (og bakgrunner i `INN/bg`). Det er
et utgangspunkt for å tegne over for hånd. Merk at fargene i de utpakkede bildene er
fra paletten `gfx.py` velger, ikke alltid den skjermen bruker.

### Det som gjenstår

- **HD-bilder med spillets palett.** Masker (se over) gir farge fra paletten der de
  er laget. Ingen ekte ridderbilder har maske ennå.
- **Bakgrunner som endres litt.** Skriver spillet noe inn i selve bakgrunnskopien
  (for eksempel en markør som blir stående), får den en ny hash, og HD-bildet passer
  ikke lenger. Det kan løses med å godta små forskjeller og legge dem over.
- **Ting som ligger foran figurene.** Figurer fra tegnelisten ligger i riktig
  rekkefølge. Tegner spillet noe over en figur med en annen rutine, er pikselen ikke eid
  av noen figur, og figuren vises som originalen.
- **Andre tegnerutiner.** Noe grafikk tegnes ikke med `tegn_figur` (f.eks. tekst og
  menyrammer). `--blit-log` viser hvor Blitteren startes fra, og er et godt sted å
  begynne for å finne dem.

Nettspill: listen lages lokalt hos hver spiller (alle kjører samme maskin), så
HD-pakken kan være forskjellig fra spiller til spiller.

## Standardgrafikk i nettutgaven

Nettutgaven laster standardgrafikken automatisk. Pakken har 320 PNG-ruter: 68 bakgrunner, 142 fontglyfer, HD-logo, 20 faste tekstfelt, seks kartlandemerker, fem blå stå-/gangposer, fire riddervalg, menypilen, fem månefaser og ikonene (se nederst). Bakgrunnene omfatter de 24 hulebakgrunnene (fol, gll, swl og wal 1-6), healeren, Mythrid og druidene. Kartet, Waterdeep, Highwood, kroen og fire introscener (steinsirkelen, alteret, portalen og steinringen sett ovenfra i bg3) er koblet til kildevaliderte PIV-lag, til sammen åtte scener. Bakgrunnen 045a1ac5 er en helt tom skjerm og får aldri HD (vakt i `web/src/hd.js` og `web/pakk.py`). Se [leveransen med bilder og kontroller](../art/hd-backgrounds-2026-10-11/README.md). Andre figurer, scener og animasjoner bruker originalgrafikk til deres nye deler er rettet og kontrollert.

Velg **Grafikk → Original** i sidemenyen for å sammenligne. Valget lagres. **Standardgrafikk** henter standardpakken igjen etter at egne filer er valgt eller HD er fjernet. Egne HD-mapper støttes fortsatt; de stopper automatisk innlasting slik at brukerens bilder får overta.

Bildene ligger i `web/hd/`, og alle filstørrelser og SHA-256-hasher er bundet i `manifest.json`. Kjernen og spilltilstanden endres ikke av HD. Bakgrunner hentes først når den tilhørende scenen vises; høyst fire standardbakgrunner holdes i minnet. Hvis en fil mangler, er ødelagt eller ikke kan lastes, beholdes originalgrafikken.

`web/pakk.py` kontrollerer manifestet og kopierer HD-filene ved siden av den bygde HTML-filen. Pages og web-artifaktet inneholder begge deler. Ved direkte `file://`-åpning virker originalspillet; åpne mappen gjennom en lokal HTTP-server for automatisk HD, for eksempel `python3 -m http.server 8000 --directory web/build`.

Alle produserte råbilder og tidligere revisjoner ligger under `art/photoreal/candidates`, med prompter og et lokalt original-/fotogalleri. Arkivets 616 valgte oppføringer er ikke det samme som 616 ferdige spillruter. Se `art/photoreal/README.md` for status og kreditering.

Trofaste ikoner: [kilder, metode og kontroll](../art/hd-icons-2026-10-11/README.md). Den oppdaterte standardpakken har 320 PNG-ruter. 69 ikonruter bygger direkte på originalens fargeflater og faktiske palett.
