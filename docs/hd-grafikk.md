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

På nettsiden: Meny, «HD-grafikk (eksperimentelt)», velg mappen. Kryss av for gule
felt, så vises et gult felt der spillet tegner en figur som ikke har HD-bilde. Da er
det lett å se hva som mangler.

### Sjekk av plasseringen

`tools/hd_sjekk.py` kjører emulatoren uten vindu fra en lagret tilstand, legger de
utpakkede figurbildene der tegnelisten sier, og måler treffet mot skjermbildet:

```
python3 tools/hd_sjekk.py --gfx assets/gfx --state kamp.sav --press 5:left:40
```

I kamp og på kartet treffer alle figurene (1,00, eller litt under der noe annet
enn en figur ligger over).

### Det som gjenstår

- **Bakgrunnene.** Navnet på bakgrunnen (siste PIV fra slave+$5F2) er med i
  tegnelisten, men HD-bakgrunner tegnes ikke ennå. Kampbakgrunnene (`.t`-filene) er
  ikke dekodet.
- **Ting som ligger foran figurene.** HD-figurene legges alltid øverst. Tegner
  spillet noe over en figur med en annen rutine (tekst, deler av landskapet), vil
  HD-figuren dekke det.
- **Fargeeffekter.** Fading og fargeskift gjøres med paletten. HD-bildene følger ikke
  med ennå; det kan tas fra paletten i kjernen.
- **Andre tegnerutiner.** Noe grafikk tegnes ikke med `tegn_figur` (f.eks. tekst og
  menyrammer). `--blit-log` viser hvor Blitteren startes fra, og er et godt sted å
  begynne for å finne dem.

Nettspill: listen lages lokalt hos hver spiller (alle kjører samme maskin), så
HD-pakken kan være forskjellig fra spiller til spiller.
