# B01: trollkrasjet

Undersøkt 12. oktober 2026 (punkt 1 i planen i
[kuttet-innhold-og-feil.md](../kuttet-innhold-og-feil.md)). Rapporten [S4]: to troll
vender mot hverandre og slår over hodet samtidig, og spillet krasjer.

Verktøy: `tools/b01_troll.py`. Det lager kampen, kjører faste inndata med og uten
C-krokene og melder stopp, adressefeil og fastlåste kamper. Emulatoren har fått
`--unntak N` til dette (se under).

## Utgave

| Fil | SHA-256 | CRC32 |
|---|---|---|
| Moonstonecd32-AMIGA.zip | 35b7d4c67b9fae6019e257780050d0f421d6ec4c250cdde48a8f296086d67a02 | |
| Moonstone.Slave (v1.4) | cfd615e6ec063a7f111604eaf8ab804cb6b35a050513bb5622fc7d5989240fb8 | 2a894f7c |
| data/mog | d8cc4ec9f848ee30032f1e0c0db4e37c2484114910d314760956da9fee96da81 | 3b7f8bbd |
| data/program | b0a84503c0664515ef8b31072098acd62dbf50de3a36fe4ffe9492b094f593a6 | 22988186 |

Rapporten i [S4] sier ikke hvilken utgave den gjelder. Alt under gjelder bare
denne.

## 1. Denne utgaven slipper aldri to troll ut samtidig

Trollene er monstertype `$30` (hulene 6, 7 og 8 i kartlagringen). Oppsettet
`$084780` setter antallet på skjermen (`$08CFBE`) til 1 og kaller `$084180`, som
øker det for en sterk ridder (`+$46` over 3, maks liv `+$54` på minst 60). Så
kommer en egen sjekk:

```
0841fc  cmpi.l   #$847ee, $8cfc4.l     ; er dette trollene?
084206  bne.b    $84210
084208  move.w   #$1, $8cfbe.l         ; da bare ett på skjermen
```

Den samme sperren gjelder én annen monstertype (`$0848a8`). Neste troll kommer
først når det forrige er dødt (`$080398`). Målt: med `+$46 = 4` og maks liv 90 går
telleren til 3 og så tilbake til 1 på `$084208`, og bare ett troll kommer ut.

**Det naturlige scenarioet i rapporten kan altså ikke oppstå i denne utgaven.**
At sperren finnes, tyder på at utviklerne kjente til et problem med to troll.
Om den var med i utgaven rapporten gjelder, vet vi ikke.

## 2. Testvariant: to troll tvunget fram

For å prøve scenarioet endrer `tools/b01_troll.py` den ene byten på `$08420a`
fra 1 til 2 før hulen åpnes. Det er en endring av spillkoden, bare for testen.
Da kommer to troll ut samtidig. Ridder 1 får 90 i liv så kampen varer, og står
ved hule 6 før han går inn. Alt annet er originalt.

Hvert forsøk kjøres fra den samme lagringen med faste, tilfeldige inndata (frø
1 til N), én gang med C-krokene og én gang med `--nohooks`. Etter kampen kjøres
1500 bilder til der ridderen slår mot trollene. Står liv og ridderens plass helt
stille, regnes kampen som låst.

Resultat med `--forsok 10` (3000 bilder per forsøk):

| Start | Med C-krokene | Med `--nohooks` | Stopp eller adressefeil |
|---|---|---|---|
| Naturlig, ett troll | 0 av 10 låst | 0 av 10 låst | ingen |
| Testvariant, to troll | 9 av 10 låst | 9 av 10 låst | ingen |

De to kolonnene er like forsøk for forsøk, også i ridderens liv og plass når det
låser seg. I alle de låste kampene står minst ett troll i angrep `$20` (32).

## 3. Hva som skjer når det låser seg

Frø 2 med to troll, fulgt med `--vakt` (bildetall fra lagringen):

| Bilde | Hva | Belegg |
|---|---|---|
| 3085 | troll 0 starter angrep `$08` | `$40` på trollet, pc `$086bfe` |
| 3130 | troll 0 går over i angrep `$20`, spiseangrepet | pc `$086c20` |
| 3244 | ridderen settes til `$40 = 8` og blir borte fra skjermen | pc `$08547a` |
| 3300 og videre | troll 0 står i `$20` for alltid, troll 1 veksler mellom `$08` og `$20` | |
| 9300 | fortsatt det samme: ridder 80 i liv, begge troll 30, ridderen usynlig | 5000 bilder med slag fra ridderen |

Ridderen er spist og blir aldri sluppet. Animasjonen går, musikken går, men
kampen kommer aldri videre. For en spiller ser det ut som at spillet har hengt
seg, og det er nok det rapporten kaller et krasj.

## 4. Symptom, årsak og versjon holdt fra hverandre

| Spørsmål | Svar | Belegg |
|---|---|---|
| Krasjer CPU-en (unntak, adressefeil)? | Nei. Ingen hopp til vektorene og ingen ord- eller langordtilgang på oddetallsadresse i noen kjøring. | `--unntak` |
| Er det C-krokene våre? | Nei. Identisk utfall med og uten C-krokene, bilde for bilde. | `--nohooks` |
| Symptomet | Kampen låser seg med ridderen spist av ett troll mens det andre også går i spiseangrepet. Ikke et ekte krasj. | målt |
| Årsaken | Ikke funnet ennå. Det som er sikkert: spiseangrepet (`$20`) slipper ikke ridderen når to troll er i kampen. Neste steg er å følge trollets angrepsskript fra `$086c20` og se hva som avslutter `$20` med ett troll. | |
| Stack overflow? | Ikke sett. Påstanden i [kuttet-innhold-og-feil.md](../kuttet-innhold-og-feil.md) er fortsatt udokumentert. | |
| WHDLoad | Sperren på `$084208` står i spillfilen `mog`, ikke i slaven. Slaven (v1.4) lapper 21 steder, blant dem åtte kall i `$08530e`-`$085538`, ett kall på `$086b58` (`btst #1,$8D97C`, trolig knapp på joysticken) og én byte på `$086a71`, alle i nærheten av kampkoden. Ingen av dem er på `$084208` eller i trollets spiseangrep. Vi kan ikke kjøre spillet uten slaven, så om en annen WHDLoad-utgave oppfører seg annerledes, er ikke prøvd. | `--log 2` skriver patchlisten |

## Adressefeil og vår emulator

Emulatoren er en 68000 uten adressefeil (`M68K_EMULATE_ADDRESS_ERROR` er av i
Musashi). En ekte 68000 (A500) stopper med Address Error når et ord eller langord
leses fra en oddetallsadresse. CD32 har en 68020, som tillater det. En krasj av den
typen ville derfor gått upåaktet her. `--unntak N` skriver ut de N første slike
tilgangene med registre og stakk, og stopper maskinen om PC havner i
unntaksvektorene (de er 0 i denne utgaven, så et unntak hopper dit). I
trollkampene ble det ikke funnet noen.

## Neste

1. Følg angrep `$20` hos trollet fra `$086c20` til det slipper ridderen med ett
   troll, og finn hvilken tilstand som mangler med to.
2. Prøv en identifisert A500-utgave med den samme lagringen hvis den finnes, for
   å se om sperren på `$084208` mangler der.
