# Resterende objektikoner, 11. oktober 2026

Trofaste nytegninger for HD-valget. Original-CEL/PIV, faktisk bruk i originalkoden og nettmanualen bestemmer motivet. Retningen, antallet gjenstander, fargefamilien og originalens visningsfelt beholdes. Råbilder fra den innebygde bildegeneratoren er bevart urørt, også forkastede revisjoner. Pakkingen bruker browsercanvas; spillets originale data og emulerte tilstand endres ikke.

Pakken erstatter 49 konturruter og legger til 27 statiske kartikonruter. Det gir 102 rasterkontrakter totalt, inkludert de 26 tidligere godkjente rutene. De 76 nye rutene bruker 62 valgte råmastere inkludert fargevarianter og én gjenbrukt godkjent stedsport. De fire livsymbolrutene har dessuten 16 ekstra palett-PNG-er. Standardpakken har 370 PNG-er og 376 manifestfiler.

## Hva ikonene forestiller

| Originalruter | Betydning |
|---|---|
| KI000..002 | Halv, hel og ny Moonstone |
| KI003..004 | Ring of Protection og Potion of Healing |
| KI005..008 | De fire geometrisk forskjellige nøklene til Valley of the Gods |
| KI009..010 | Gem of Seeing og Talisman of the Wyrm |
| KI011..015 | Scroll of Haste, Hawk, Acquisition, Wyrm og Protection, i originalkodens rekkefølge |
| KI016 | Gjentatt smal side av en ekstra rull |
| KI017..020 | Livsymboler som hjelm eller Math-forvandlet padde, begge paneler og fem ridderfarger |
| KI021..025 | Kastedolk, long sword, broad sword, claymore og Sword of Sharpness |
| KI026 | Smal inventarsøyle med vinranke |
| KI027..030 | Padded armour, chainmail, platemail og battleplate |
| KI031..033 | Tre deler av samme åpne skattekiste |
| KI037 | Åpen sekk med gullmynter |
| MI000..009 | Ridderhjelmer på kartet, fem farger og vanlig/valgt status |
| MI010..014 | Gem of Seeing gjør kartbrikken til en krystallkule med ridderfarget sokkel |
| MI015..018 | Hawk-rullens fargede teleportmål, abstrakt asymmetrisk kors |
| MI020/031 | Vanlig/valgt liten stedsport med to steinstøtter og overligger |
| MI033/042 | Vanlig/valgt gravkors for død ridder |
| MI043..046 | Fire statiske Math-paddemarkører på kartet, med ridderfarget stripe |
| map-landmarks000/005 | Highwood i nordvest og Waterdeep i sørøst |
| map-landmarks004 | Smalt elvedetaljmotiv. Det er ikke kildebekreftet som et eget besøksted eller et andre trollmannstårn |
| scene-icons000..005 | Kroens gulltellersekk og samme innsatssekk gjentatt for 1..5 gull |
| po.cel000/sel.cel000 | Skrå dolkpeker og gullfarget høyrepil |

KI045..049, de fem månefase-statusskivene, er fortsatt aktive via tidligere PNG-/poseruter og trenger ikke duplisert ikonmetadata.

Den tidligere navngivingen hadde byene omvendt. David O'Connors originale byskisser, kartets besøkstabell og nettbildene bekrefter navnene. De tre mørke hjelmene i den gamle kartbakgrunnen er riddermarkører, ikke landsbyer. «55 ekstra ikoner» omfattet også rammefragmenter, tekst, valgkonturer og figuranimasjon; det var ikke 55 forskjellige gjenstander.

## Kilder

- [Originalmanualen, Free Game Empire](https://www.freegameempire.com/games/Moonstone-A-Hard-Days-Knight/manual)
- [Magical Equipment med originale spillbilder](https://moonstonetavern.co.uk/magical-equipment/)
- [Quest, Knights & Dragons](https://moonstonetavern.co.uk/quest-knights-dragons/)
- [Settlements & Other Locales](https://moonstonetavern.co.uk/settlements-other-locales/)
- [Originale byskisser og produksjonsmateriale](https://moonstonetavern.co.uk/box-art-music-more/)

Detaljert kobling til originalbank, palett, rutinenummer og bilder ligger i `research/inventory/`, `research/map-tavern/` og `research/runtime/`. Kilden avgjør identiteten; genererte detaljer brukes ikke som bevis for hva originalen forestiller.

## Filspor og kontroll

- `asset-*.json`: valgte råbilder, prompt, referanse, plassering og motivgjennomgang.
- `raw/`, `prompts/`, `revisions/`: urørte generatorresultater, fullstendige prompter og forkastede revisjoner.
- `packed/`, `candidate-icons.json`, `packing-report.json`: kildebundet pakking og SHA-256-spor.
- `index.html`, `review/`: original/HD-galleri og kontaktark. De er diagnosebilder, ikke ekstra spillgrafikk.
- `research/runtime/`: faktisk frontend med originale CEL-fixturer, speiling, kildeavvisning, paletter, pulskanter og gullteller. Fixturer skriver ikke i spillminnet og er ikke en naturlig gjennomspilling.
- `verification/`: samlet integrasjonskontroll og leveransekvitteringer.

Skattekisten pakkes én gang i originalens 59x53-union og klippes til de tre opprinnelige CEL-feltene. Rullene deler en nytegnet pergamentflate, mens symbolenes transparente hull og røde/brune blekk følger originalens nøyaktige konturer. Livsymbolene velger separate genererte fargebilder kun ved de fem dokumenterte palettparene. Kartets originale levende indeks 31 og enkelte dokumenterte skygge-/høylyspiksler tegnes foran HD-kroppen. Ukjent kilde, palett eller variant beholder originalgrafikken.

## Avgrensning

Arbeidet gjelder statiske objektikoner. De tre vinranke-/rammefragmentene, originale fontformer, meldingsrammer, valgkonturer, separat forgrunn, effekter, rulling og figur-/drageanimasjoner er fortsatt egne oppgaver. Tidligere godkjente små kartporter og Math-tårn beholdes, og denne leveransen endrer ingen bakgrunner. Figurrutene tas til sist, som avtalt.

## Verifikasjon før fletting av PR #27

Uavhengig leveransekontroll bekrefter 102 rasterkontrakter, 76 nytegnede ruter, 27 nye statiske MI-ruter, 370 PNG-er og 376 manifestfiler. Alle 283 tidligere filer utenfor de erstattede ikonene er identiske, inkludert de 75 bakgrunnene. Originalarkivet og spillkjernen er uendret. Raster-/kildekontrollen består 3774 kontroller for alle 102 rutene.

De 58 opprinnelige nye CEL-rutene bestod 780 runtimekontroller; de fire siste paddemarkørene bestod 53. Dette er historiske prøver fra før flettingen av PR #27, ikke bevis for den nye tegnekoden. Bevisene binder hver kilde, råmaster, prompt, record og pakket PNG til kontraktsettet. Rendererrettingen gjaldt utskifting av en fargevariant ved uendret palett: 15 faktiske importkontroller bekreftet ny PNG, riktig blå retur, eksakt gjenoppretting og uendret spilltilstand.

Den naturlige kartkontrollen avdekket at Waterdeep og elvedetaljen manglet originalens vannsyklus i metadata. Originalkoden roterer bare indeks 21..23; disse to rutene godtar nå akkurat den gruppen. Alle 92 nye PNG-er og de øvrige 100 ikonkontraktene er uendret av rettingen.

Samlet spillkontroll før flettingen bestod 59 intro-/inventar-/by-/krokontroller, 27 importkontroller, 106 kartkontroller og 25 standardpakkekontroller med 71 av 71 gangrammer. Math-besøket bevarte 84 HD-glyfer, alle 8705 figurpiksler og eksakt Original-visning. Alle hadde null nettleserfeil. Kartets palettretur var eksakt uten ekstra stabiliseringsrammer etter at testens framebuffer ble korrigert til samme palett som skanout. De tidligere mislykkede testdiagnosene er bevart og regnes ikke som beståtte.

## Nye prøver etter fletting av PR #27

Main 74ceafb er flettet inn med figurdeling, pikseleierskap, palettmasker, tekst og lys bevart. Ikonets beskyttede originalpiksler respekteres også i den nye felles forgrunnstømmingen. Koden er frosset med SHA-256 i `research/runtime/post-main-merge/runtime-contract.json`.

Alle 62 CEL-ruter er prøvd på nytt i åtte batcher, uten gjenbruk av gamle runtimeprøver: 828 kontroller består, inkludert vanlig/speilet tegning og alle 20 livfargevalg. Eiervern, pulskanter, faktisk variantimport og kroteller består ytterligere 162 kontroller. Den samlede rapporten `research/runtime/post-main-merge/merged-runtime-coverage-test.json` binder disse prøvene til kode, kilde, råmaster, prompt og aktive PNG-er.

Kjør `python3 tools/hd_resterende_ikoner_dekning_sjekk.py` fra repoet for å validere den leverte dekningen. Standardkommandoen bruker post-main-merge-checkeren og viderefører dens exitkode. Den tidligere 833-rapporten beholdes som historisk bevis og sammenlignes ikke med dagens tegnekode. Dette retter P2-funnet i kodegjennomgangen av PR #28; grafikken og produksjonskoden er uendret.

Friske integrasjonsprøver ligger i `verification/post-main-merge/`: 3774 rasterkontroller, 59 intro-/inventar-/by-/krokontroller, 27 importkontroller, 106 kartkontroller og 25 standardpakkekontroller med 71 av 71 gangrammer består. Math-besøket bevarer 84 HD-glyfer, alle 8705 figurpiksler og eksakt Original-visning. Ingen nettleserfeil. Inventar, kart og kro er visuelt inspisert i faktisk spillvisning. Dette er avgrensede runtimeprøver, ikke en full gjennomspilling eller fysisk telefontest.
