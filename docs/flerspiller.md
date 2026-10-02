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
   eget spill.
4. **Resten:** hva som skjer om den andre er opptatt (i en by eller kamp), om to
   utfordrer hverandre samtidig, og at årstiden og månedene går hver for seg.
