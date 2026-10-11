# Elleve kildebundne HD-ikonmaterialer

Alle elleve mastere er generert hver for seg med innebygd image_gen og riktig originalrute som positiv referanse. Ingen av de tidligere avviste rankene brukes som formreferanse.

KI-rankene og Dice-symbolene bruker fotografisk materiale fra hvert enkelt generatorresultat innen originalens sammenslaatte blad/stengel eller lys/moerk-konturer. Fritt genererte ranker mistet deler av originalformen og ble avvist som geometrigrunnlag. MYS-pungene er separate nytegninger klippet til originalsilhuetten; sma hull ved kanten fylles fra naermeste genererte materialpiksel. Dette er materialoppgradering paa kildegeometri, ikke nye fritegnede motivtolkninger.

| Original | Motiv | Originalmaal | PNG 8x | Original indeks-SHA256 |
| --- | --- | --- | --- | --- |
| ki.cel/034 | Hoyt separat rankefragment | 27x60 | [216x480](packed/ki.cel/034.png) | 6f6cb423c062bfaf400a581c42f09c183a4453f912a14c4d454a16a0e1cc39f8 |
| ki.cel/035 | Lite rankehjorne | 15x12 | [120x96](packed/ki.cel/035.png) | 39d713f93759029426bae4aebe87dc6141674535ff3cd581e86a20faea8c9303 |
| ki.cel/036 | Ovre bredt rankefragment | 53x19 | [424x152](packed/ki.cel/036.png) | 9fa974e60bfd150e8098af13e23a7bfaa968d31fdb74708379b7915ecaa75e8a |
| mys.cel/000 | Mystikerens donasjonssekk | 46x26 | [368x208](packed/mys.cel/000.png) | 8f23c745fc2737d8d47c9c47a02f828447089d2976caf8774f3ce61b0599c538 |
| mys.cel/001 | Healerens donasjonssekk | 47x26 | [376x208](packed/mys.cel/001.png) | ef65b66c34c98e05a725c3b29f280110c87d0aac27e314dac792657e73be79b4 |
| dice.cel/000 | Dragesymbol | 53x23 | [424x184](packed/dice.cel/000.png) | 2042f654c979b5d40476268657797615466124a8b1b94304ded587cca0992686 |
| dice.cel/001 | Kranium | 53x24 | [424x192](packed/dice.cel/001.png) | 935875aacc97d58176d45efeaccd938b3ab0391a485110a59822ea58ce85749e |
| dice.cel/002 | Tiltaegende maane, lyst felt mot hoyre | 53x23 | [424x184](packed/dice.cel/002.png) | b5951cec991e8e399e15e91e9b85651aa35d5887c970be8bd3b958a89a04a36a |
| dice.cel/003 | Fullmaane | 53x23 | [424x184](packed/dice.cel/003.png) | 204e7d13bacd650edcda777bf25eb33e80d25ed6bc2b945f49ec3ebb4dac441c |
| dice.cel/004 | Avtaegende maane, lyst felt mot venstre | 53x23 | [424x184](packed/dice.cel/004.png) | 1d2e2e7facd0bc78acead3c8cf5a10d654b64aac74f63e8afc70b2b1f74de7aa |
| dice.cel/005 | Nymaane | 53x23 | [424x184](packed/dice.cel/005.png) | becaf5ab873424dbafe1d4b9a3acb3966a65037ab4a6a82a0637f71f51035173 |

Pakkekontrollen bestod 18 911 sjekker: original ZIP/CEL, ekspanderte bitplan, riktige mys/hea/dice-paletter, 8x PNG, alle 7 349 opake og 5 243 transparente kildepikselmidtpunkter samt blad/stengel og lyse/moerke symbolomraader. Se `verification/packing-test.json`. Maskesjekken viser geometrisk dekning, ikke alene fotografisk kvalitet.

Visuelt er motivene kontrollert ved samme visningsstoerrelse i `comparison.png`. Pungene beholder tomme tallfelt. Rankene beholder sine sma, separate fragmenter og alle originale aapninger. Dice beholder de projiserte ellipsene, den originale drageglyfen, kranium og de fire maanefasene. Det er ikke lagt til terningkuber, nye dragehoder eller pynt.

Nettkontroll: [Moonstone Tavern, Settlements & Other Locales](https://moonstonetavern.co.uk/settlements-other-locales/) viser originalens gevinsttabell for Dragon Dice. Tabellbildet er lagret i `references/manual-gambling.gif` og PNG-kopi. Det bekrefter drage, kranium og fire maanefaser; hvilke maane-ruter som er tiltaegende/avtaegende er lest fra de originale lyse feltenes retning. Direkte PDF-henting fra OpenRetro feilet; ingen PDF er brukt som grunnlag.

Reproduser kandidaten med `python3 material-geometri.py`, deretter Node `pack.cjs`, `material-pack.cjs` og `python3 verify.py` fra dette omraadet. `generation-records.json` har alle elleve eksakte prompter, originalreferanser og generatorens kvitteringer. Alle elleve materialene er senere aktivert av `tools/hd_completion_activate.py` etter bundet runtimekontroll.

Runtime bestod med 11 ikoner og 141 kontroller, uten nettleserfeil. Normal og speilet Original/HD-retur er pikseleksakt; endret kildebank og ukjent forgrunn avvises, emulert spilltilstand forblir uendret. Fersk WASM SHA256: `c56094d8b992cbd7ed7e4a8ef65709c435156072124874b26bce7cf02cb8e633`. Isolert HTML-identitet står i den endelige bundne runtimekvitteringen. Se `verification/bound-runtime/ui-fixtures-test.json`. Dette er kontrollerte frontendlagsfixturer, ikke en naturlig gjennomspilling av mystiker/healer/Dragon Dice.

Kanonisk `source-contracts.json` er nøyaktig den testede kontraktfilen. To redundante selvpalettoppføringer er fjernet; full historisk kontrakt er bevart i `source-contracts-full-provenance.json`. Alle CEL-felt, indekser og faktiske paletter er identiske. `verification/material-proof-binding.json` binder testen og alle elleve uendrede PNG-er til materialpakken.
