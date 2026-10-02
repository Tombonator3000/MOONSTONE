# Slik er Moonstone bygget

Notater om hvordan spillet er laget, ut fra filene, disassemblyen og emulatoren.
Adressene gjelder hovedspillet `mog` lastet til $80000 (som i `disasm/mog.s`).
Oppdateres etter hvert som vi finner ut mer.

## Filene

CD32-ISO-en er en WHDLoad-installasjon. Mappen `Moonstone` har slaven, en tekstversjon
av manualen og to IFF-bilder (joystickoversikten og månefasene). Selve spillet ligger i
`data`:

| Fil | Hva det er |
| --- | --- |
| `program` | Introen (Mindscape-logoen, månen, druidene, Stonehenge). Hunk-fil, 34 hunker. |
| `mog` | Hovedspillet. Hunk-fil, 46 hunker, 52 kB kode i første hunk. |
| `Test` | Ni bilder i én fil: delark til kampbakgrunnene, ferdige bakgrunner (skog, klipper, sump, åker) og verdenskartet. |
| `*.piv`, `*.p`, `mindscape` | Bilder i 320 x 200 (byer, tavernaen, terningspillet, tittelbilder). |
| `*.cel`, `*.c`, `*.ob` | Figurer: ridderne, monstrene, druidene, gjenstander. Hver fil har mange små bilder. |
| `bold.f`, `Small.font` | Skrifttypene, i samme format som figurene. |
| `*.a` | Lydeffekter, 8SVX i en hunk-fil, én fil per figurtype (kn.a ridder, ba.a Balok, dr.a drage ...). |
| `music.cmp`, `vmusic.cmp` | Musikken: ProTracker-moduler (Richard Joseph), pakket. |
| `*.t` | Oppsett for kampbakgrunner per terreng: fo = skog, sw = sump, gl, wa, med lair-utgaver (fol, swl, gll, wal). |
| `collide.hit` | Tekstfil med treffsoner per figurfil. |
| `intro.stile`, `co.stile` | 960 byte hver, brukes av introen. |

Formatene er beskrevet i `tools/moonfiles.py`. Kort:

- **LZ**: spillets egen pakking. En kontrollbyte med åtte flagg. 0 = en byte som den er,
  1 = to byte med 5 bit lengde (3-34) og 11 bit avstand bakover. Utpakkeren ligger i slaven,
  der Wepl flyttet og optimaliserte den.
- **PIV**: ord antall bitplan, long pakket lengde, palett (32 farger i Amiga-format
  med bit 15 satt), og LZ-pakkede bitplan, plan for plan.
- **CEL**: ord antall bilder, long pakket lengde, long minnebehov, så 10 byte per bilde
  (offset, bredde, høyde, flagg, planmaske), og LZ-pakkede bitplan, plan for plan for
  hvert bilde. Figurene settes sammen av flere bilder (kropp, bein, våpen) mens spillet går.
- **.cmp**: hodet sier `RNC\x01`, men metoden er en annen enn vanlig RNC. Bitene leses
  bakfra. Utpakkeren er oversatt fra introen til `tools/lyd.py`.

## Oppstarten

1. WHDLoad (her: `port/src/whdload.c`) laster `Moonstone.Slave` og kaller den.
2. Slaven laster `program` til $80000, relokerer den og lapper den med patchlisten
   (tastatur, lyd, lasting av filer, pauser), og hopper inn.
3. Introen viser logoen og historien. Når den er ferdig (eller du trykker Esc), hopper
   den til slaven, som laster `mog` til $80000 på samme måte og starter hovedspillet.
4. Alle filer spillet laster senere, går gjennom slaven (`resload_LoadFileDecrunch`).

Slaven fjerner også gullgrensen på 150 (blir 999), og den har en juksekode.

## Skjermen

Spillet bruker en lowres-skjerm på 320 x 200 med fem bitplan (32 farger), satt opp med
Copper. Bakgrunnene er PIV-bilder som pakkes rett inn i skjermminnet. Figurene tegnes
med Blitteren som "bobs" av biblioteket *IMAGEXCEL Code Module: SPRITE* (1988), som
ligger både i introen og i hovedspillet. Kampbakgrunnene settes sammen av biter fra
delarkene i `Test` etter oppsettet i `.t`-filene.

## Ridderne og turene

Fire strukturer på $84 byte fra $8D5B4:

| Offset | Innhold |
| --- | --- |
| +$0B | hvem som styrer: 1 = joystick i port 1, 2 = joystick i port 2, 4 = datamaskinen |
| +$36 | spillernummer 0-3, eller 4 for en ridder datamaskinen spiller |
| +$6C | peker til navnet |

Langordet på $8D9AC peker på ridderen som har turen (også når datamaskinen spiller).
På kartet styres ridderen som har turen med joysticken i port 2. I kamp mellom to riddere
får den andre ridderen port 1. Alle menneskelige spillere velger ridder og spiller på
kartet med samme joystick (port 2), etter tur, slik manualen beskriver med "1 eller 2
joysticker". Etter at alle har hatt tur, kommer "Next Day" og månen går videre.

`les_joysticker` ($81F92) leser begge portene hvert bilde til $8D9A2 (port 2) og $8D9A0
(port 1). `joystick_for_figur` ($81F6A) gir joysticken til en figur ut fra +$0B.

Dette er det nettspillet bruker for å gi joysticken til den som har turen
(`port/src/game.c`).

## Lyd

Hver figurtype har sin egen `.a`-fil med 8SVX-lyder (steg, grynt, sverdslag, treff).
Navnene står i filene, f.eks. `knitestep3C`, `headchop`, `SwordClash3.snd`. Musikken er
to ProTracker-moduler: `introx5` (introen) og `vict0ry6yy` (seier).

## Ting å se nærmere på

- `.t`-filene: nøyaktig hvordan kampbakgrunnen bygges.
- Tegnerutinen i IMAGEXCEL-modulen (for HD-grafikk, se `docs/hd-grafikk.md`).
- Kampsystemet: de åtte angrepene, treffsonene i `collide.hit`, monstrenes oppførsel.
- Testmenyen for monstre på $82D82.
