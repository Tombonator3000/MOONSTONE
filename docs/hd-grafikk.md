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

Når spillet toner ut med paletten, tones HD-bakgrunnen og HD-figurene like mye
(lysstyrken til fargene bakgrunnen bruker, mot den lyseste som er sett).

### Tekst i HD

Bokstavene tegnes også av `tegn_figur`, som figurer i fontfilene `bold.f` (den store
fonten; bilde 73 er hele MOONSTONE-logoen) og `Small.font` (den lille, på
statusskjermene). HD-bilder for dem, f.eks. `bold.f/015.png`, gir derfor tekst i HD.

Tekst tegnes bare én gang, mens figurene i kamp tegnes på nytt hele tiden. Med lagene
blir en HD-figur derfor stående så lenge forgrunnen der den ligger er uendret
(sammenlignet med fargeindeksene, så fading ikke teller som en endring), og den
forsvinner når spillet tegner noe annet der eller bakgrunnen byttes. Uten lagene
vises en klynge til det har gått 50 bilder uten nye tegninger, som før.

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

- **HD-bilder med spillets palett.** Bilder med fargeindekser (PNG med palett) kunne
  fått fargene fra skjermen når de tegnes, så de alltid passer.
- **Bakgrunner som endres litt.** Skriver spillet noe inn i selve bakgrunnskopien
  (for eksempel en markør som blir stående), får den en ny hash, og HD-bildet passer
  ikke lenger. Det kan løses med å godta små forskjeller og legge dem over.
- **Ting som ligger foran figurene.** HD-figurene legges over forgrunnen. Tegner
  spillet noe over en figur med en annen rutine, vil HD-figuren dekke det.
- **Andre tegnerutiner.** Noe grafikk tegnes ikke med `tegn_figur` (f.eks. tekst og
  menyrammer). `--blit-log` viser hvor Blitteren startes fra, og er et godt sted å
  begynne for å finne dem.

Nettspill: listen lages lokalt hos hver spiller (alle kjører samme maskin), så
HD-pakken kan være forskjellig fra spiller til spiller.
