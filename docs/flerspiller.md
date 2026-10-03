# Flerspiller: tur for tur, og «Hver for seg»

## Hvorfor nettspillet i dag føles tregt

Moonstone er laget for å spilles ved samme maskin, tur for tur. På kartet styrer
bare ridderen som har turen; de andre venter. Nettspillet kjører originalen
nøyaktig likt hos alle (verten kjører spillet, gjestene får knappetrykkene), så
det arver dette: når det ikke er din tur, kan du ikke gjøre noe.

## Målet: «Hver for seg»

Hver spiller spiller sitt eget spill samtidig, som alene, og ser de andre ridderne
på kartet. Når to riddere møtes, kan de slåss, og den kampen spilles over nettet
med begge styrende hver sin ridder.

Status: steg 1, 2 og 3 er ferdige (Mode Separate i Online Game, standard). Kamp mot en
annen spiller er en duell over nettet der begge styrer sin ridder. Steg 4 gjenstår.

## Det vi vet om spillet

Ridderne: fire plasser à $84 byte fra $8D5B4 (`ridder_1` til `ridder_4`, se også
`port/src/game.c`). Plasser uten menneske styres av datamaskinen (+$36 = 4).

| Felt | Betydning |
| --- | --- |
| +$0B | joystickporten (2 på kartet, 1 for den andre ridderen i kamp) |
| +$36 | spillernummer 0-3, 4 = datamaskinen |
| +$49 | liv; 0 eller mindre = død (tegnes med bilde $21/$2A) |
| +$4D | settes til 12 ved turstart |
| +$52 | større enn 0: turen hoppes over |
| +$56 | antall trekk per tur / 16 (`$8E7C2 = +$56 << 4`) |
| +$64 | nullstilles ved turstart (svart ridder følger) |
| +$6C | peker til navnet |
| +$7E, +$80 | posisjonen på kartet (skjermkoordinater) |

Turene (`$0AAC14` til `$0AAF54`):

- `$8E79E` er hvilken plass som har turen (0-3). `$0AAF54` setter `aktiv_ridder`
  ($8D9AC) til `ridder_1 + $84 * $8E79E`, port 2, +$4D = 12 og `$8E7C2`.
- `$0AAC14` starter turen til en levende ridder (tegner kartet osv.), og løkka
  `$0AAC8C` leser joysticken (eller kunstig intelligens for +$36 = 4).
- `$8E7A0` teller trekkene. Tasten E setter den til `$8E7C2`, mellomrom viser
  inventaret, Q avslutter.
- Ved `$0AAE62` slutter turen når `$8E7A0 >= $8E7C2`: neste plass (`$8E79E + 1`,
  modulo 4). Når den går rundt til 0, er det ny runde (`$08064A`, `$082B46`, og
  `vent_paa_fire`).
- Kartet: `$0AAB0A` tegner de andre ridderne (mi.c bilde +$36 + 5) på +$7E/+$80,
  `$0AAAB0` den som har turen.
- Det du kan gjøre der du står, bygges ved `$080F56`: andre riddere i nærheten
  (avstand med `$080E00`, D5 = 2), den svarte ridderen og steder. Velger du en
  ridder, blir det kamp mellom to riddere.
- Kartet tegnes slik: når turen starter, kopieres kartet til bakgrunnen ($8CDE8),
  stedene tegnes (`$0AAB60`), så de andre ridderne (`$0AAB0A`, rett etter
  `$0AAC54`). I lokka (`$0AAC8C` til `$0AAF50`) tegnes ridderen som har turen, så
  vises bildet og bakgrunnen kopieres inn i skjermbufferet på nytt (`$0AAF38`). Alt
  som står i bakgrunnen, vises altså hvert bilde.
- Valget der du står (fire på kartet): `$0ABB76` viser listen ($8EEEC, peker og
  type: 1 levende ridder, $21 død ridder, 2 sted) og venter på tastene 1-9. En
  ridder gir `$080AB8` med a0 = den som angriper og a1 = den andre. Er begge
  datamaskinens (+$36 = 4), blir det ingen kamp. Ellers får mennesket port 2 og den
  andre port 1 (+$0B), og kampen kjøres (`$083CEE`). Alle veier ut går via
  `$080BD8`.
- Turen hoppes over når +$52 er større enn 0 (`$0AAEEC`). En død ridder som ikke er
  datamaskinens, telles som en død spiller (`$0AAF08`), og når alle spillerne er
  døde, er spillet over.

## Slik er «Hver for seg» laget (port/src/hver.c, web/src/app.js)

- Verten velger **Mode Separate** (meny.c, `M2.spill`); rommet sier det til gjestene
  i lobbymeldingen (`spill: 'hver'`). Gjestene får ingen tilstand og ingen bilder.
- Hver nettleser sender sin ridder (+$7E, +$80, +$49, +$36 og navnet) til de andre via
  verten når den endrer seg (høyst sju ganger i sekundet) og ellers hvert andre
  sekund, eller `borte` når den ikke er på kartet.
- De andre i rommet får plass 2, 3 og 4 i rekkefølgen i rommet. `hver_frame` skriver
  dem inn før hvert bilde: posisjon, liv, figur (+$36, ikke 4, ellers styrer
  datamaskinen den på kartet), +$0B = 4, navnet (i ledig chip-minne fra $FC000) og +$52 = 1 hvis
  den er død (ellers ender spillet ditt når den dør). Datamaskinens ridder på plassen
  lagres og får plassen tilbake når spilleren går.
- Har to valgt samme ridder, får den andre en ledig farge hos deg.
- En plass tas ikke over mens datamaskinens ridder på den har turen (`aktiv_ridder`) eller
  er i et møte med en annen ridder (`i_kamp`, satt ved `$080AB8` for begge, nullstilt ved
  `$080BD8`): ellers venter spillet på joysticken din midt i datamaskinens tur. På samme
  måte gis en plass ikke tilbake midt i en kamp, men når kampen er over.
- Turen til en fjern ridder hoppes over (`$0AAC14`, se under Plan).
- Kopi av bakgrunnen ved `$0AAC54` (kart og steder, uten ridderne). Har en fjern
  ridder flyttet seg, legges kopien tilbake øverst i lokka (`$0AAC8C`, høyst hvert
  fjerde bilde), og en liten rutine i chip-minnet ($FC080) tegner ridderne på nytt
  med `$0AAB0A` og setter tegnemålet ($9E202) tilbake. Slik ser du de andre gå.
- Hele ridderen sendes med: strukturen ($84 byte) og tingene (+$60 peker på $18
  byte med antall av hver ting), som heks (`b` i meldingen, `HVER_BLOB`). Felt som
  hører til plassen, skrives ikke over: +$0B, +$36, +$42/+$44 (ruten på kartet),
  +$52, +$60/+$64 og +$6C (pekere) og +$7E/+$80 (posisjonen kommer for seg).
  Stats: +$46 STR, +$47 END, +$48 CON, +$49 liv, +$4A gull, +$4E XP, +$50/+$54 HIT.
- I kamp er +$0B den som styrer figuren (`joystick_for_figur` $081F6A: 1 port 1,
  2 port 2, 4 datamaskinen), så fjerne riddere har +$0B = 4 utenom dueller.
- Duell: angriper du en fjern ridder som kan nås (`HVER_DUELL`, alle som er på
  kartet), lar `$080AB8` +$36 være figuren, så spillet gir ridderen port 1, og
  frontenden får `HVER_EV_DUELL`. Spillet ditt stopper etter bildet. Nettsiden
  kobler seg direkte til den andre (PeerJS, `metadata.duell`) og sender
  `utfordring`. Den andre lagrer sitt eget spill (hele maskinen, i minnet), svarer
  `ja`, får maskinen din og svarer `klar`. Så kjører du kampen og sender
  inndataene for hvert bilde (`f`, med sjekksum hvert 120. bilde), og den andre
  kjører de samme bildene og sender joysticken sin (`inn`, port 1). Ved `$080BD8`
  (eller tittelmenyen) kommer `HVER_EV_DUELL_SLUTT` hos begge i samme bilde: den
  andre tar ridderen sin fra plassen i ditt spill (`hver_blob`), henter sitt eget
  spill tilbake og legger ridderen inn på plass 0 (`HVER_MEG`). Hos deg skrives
  plassen ikke over før den andre har sendt ridderen sin på nytt.
- Kampen laster grafikk i om lag 8 sekunder før den begynner (posisjonene i +$04 og
  +$08 settes før det). Filene kampen trenger, lastes i bildet duellen starter i,
  altså før maskinen sendes. Laster kampen filer senere, sendes de med bildet når
  en av dem har andre filer enn de innebygde (`egne` i `ja`), og den andre får sine
  egne filer tilbake etter kampen.
- Den som angripes, gir opp etter 20 sekunder uten melding fra den andre, og
  angriperen etter 12 sekunder (den andre sender joysticken minst hvert halve
  sekund). Da henter den andre sitt spill tilbake, og hos angriperen styrer
  datamaskinen ridderen.
- Etter duellen er plassen hos angriperen slik kampen endte (liv og hele ridderen leses
  fra minnet ved `$080BD8`, i samme bilde hos begge) til den andre sender ridderen sin på
  nytt. En død ridder får dermed +$52 = 1, så spillet ditt ikke ender med «Game Over».
- Duell bare mot en levende ridder (+$52 = 0 og +$49 > 0). En grav er type $21 i
  valgene og går også til `$080AB8`, men til plyndringen (`$080BA4`).
- Plyndring (`$080BA4`, a0 plyndrer a1): en fjern ridder som ikke var med i en duell
  over nettet (en grav, eller datamaskinen styrte den), plyndres ikke. Tingene er i
  den andres eget spill og ville blitt doble. Mennesket hopper til `$080BBC` (byttet
  tilbake etter plyndringen), datamaskinen til `$080BD8`.
- Angriperen lukker forbindelsen først når den andre sier `ferdig` (eller etter et
  minutt), og mister den andre forbindelsen, kjører den ferdig bildene som alt er
  kommet, så resultatet ikke går tapt når fanen har vært skjult. En utfordring godtas
  bare fra noen i rommet og for plass 1-3. Under en duell kan ingen av dem lagre,
  laste eller ta pause, og tastene til den som forsvarer seg, går ikke til hans eget
  spill etterpå.
- Sier den andre nei (i sidemenyen, ikke på kartet, i en annen duell) eller svarer
  ikke på 15 sekunder, styrer datamaskinen ridderen i kampen (`HVER_AI`: +$36 og
  +$0B = 4). Under en duell endres ingenting i kjernen utenfra (de andre ridderne
  oppdateres etterpå), ellers kommer maskinene ut av takt.
- Med `Mode Separate` av (Turns, eller alene) gjør ingen av lappene noe, og
  `tools/check_hooks.py` gir samme minne byte for byte.

Testes uten nettleser med `moonstone-headless --hver F:1:MASKE` (plassene) og
`--hver F:2:0:"plass x y liv figur NAVN"`.

`tools/check_hooks.py` dekker ikke lappene (de kjøres også med `--nohooks`). At de ikke
gjør noe når flerspilleren ikke er i bruk, sjekkes ved å bygge en kopi der
`hver_register_hooks` returnerer med en gang, kjøre begge med trykkene fra
check_hooks og `--online-meny`, og sammenligne minnedumpene (like byte for byte
2026-10-02).

Beskyttelsesrullen: har den som angripes en rull (ting $12), viser `$080C1A` en
beskjed og venter på fire i port 2, og inventaret som åpnes etterpå styres også
derfra. I en duell ville det vært angriperens joystick. hver.c setter derfor
`H.rulle` fra `$080C52` til `$080C98` når den angrepne er motstanderen i duellen,
og `hver_frame` flytter port 1 (forsvareren) til port 2 så lenge (2026-10-03).

## Plan

1. **Hver sitt spill.** Alle starter et spill med like mange spillere som er med i
   rommet. Spiller N styrer ridder N hos seg. Turen til en ridder som spilles på en
   annen maskin, hoppes over med en gang (hook ved `$0AAC14`: hopp til
   `$0AAE62` med `$8E7A0 = $8E7C2`). Ridderne til datamaskinen spiller som vanlig,
   hos hver.
2. **De andre på kartet.** Hver maskin sender posisjonen (+$7E/+$80) og livet til
   sin ridder noen ganger i sekundet, og de skrives inn hos de andre. Spillet
   tegner dem selv.
3. **Møtes og slåss.** Velger du en annen spillers ridder, blir kampen en kort
   lockstep-økt som nettspillet i dag: utfordreren kjører kampen, den andre lagrer
   sitt eget spill, får tilstanden og styrer sin ridder med port 1. Når kampen er
   over, tar den andre med seg ridderen sin (liv, gull, ting) tilbake til sitt
   eget spill. Kroken er `$080AB8` (a1 er den fjerne ridderen), og kampen er over ved
   `$080BD8`. Ferdig, se over.
4. **Resten:** hva som skjer om den andre er opptatt (i en by eller kamp), om to
   utfordrer hverandre samtidig, og at årstiden og månedene går hver for seg.
