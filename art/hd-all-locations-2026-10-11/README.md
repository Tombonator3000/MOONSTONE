# HD-bakgrunner for alle steder, 11. oktober 2026

Denne leveransen legger til 35 ulike bakgrunnsbilder og 36 kildekoblinger. Standardpakken har nå 327 PNG-ruter, derav 75 bakgrunner. Originalens ZIP, WASM-kjerne, figurruter, kartmarkører og spillregler er uendret.

## Innhold

- 24 nye kampvarianter: `fol1..6.t`, `gll1..6.t`, `swl1..6.t` og `wal1..6.t`. Sammen med de 32 tidligere aktive variantene har alle 56 sammensatte kampbakgrunner en egen HD-rute.
- Seks nye stedsskjermer: helbreder, mystiker, Math utenfor tårnet, Math på balkongen, druidenes Stonehenge og terningbordet. `hen1.p` og `bg5.piv` deler originalbilde og HD-bilde.
- Fem nye materialkoblinger til faste intro-/meldingsbilder: ridderen foran Stonehenge, steinsirkelen ovenfra, stjernehimmelen i sluttscenen, meldingsbanneret og Mindscape-logoen. Originalfigur, altermarkering, stjerner, logosilhuett og ordmerke bevares.
- Tidligere kart, Waterdeep, Highwood, kro, tittel og tre introbakgrunner er fortsatt aktive.

29 av de nye aktive bildene er produsert med den innebygde ChatGPT-bildegeneratoren. En ekstra Math-revisjon er bevart, men brukes ikke i spillet. Seks mastere gjenbrukes fra tidligere produksjon, inkludert Stonehenge. De fem øvrige er dokumentert med tidligere vurdering i `reused-masters.json`; de påpekte avvikene i figurer, symboler, stjerner og logosilhuett skjules nå av eksakte kildeindeksmasker. Verktøyet oppgir ikke eksakt modellversjon. Urørte mastere ligger i `raw/`, de konkrete promptene i `prompts/`, og kilde-/PNG-hasher i `assets.json`. Produksjonskopiene i `web/hd/bg/` er byteidentiske med masterne. Ingen oppskalering, filtrering eller ettertegning er brukt på disse PNG-ene.

## Motiv og integrasjon

Originalene styrer oppsett, perspektiv, antall kister, ruiner, trær, kjeder og åpent kampområde. Math har et rundt mursteinstårn med loddrette vegger. Materialer er tegnet som tre, stein, bark og jord. Små runetegn følger kildens grupper og plassering, men er ikke garantert identiske strek for strek.

Bakgrunner lastes ved behov når HD er valgt. Steds-PIV valideres med kildehash og faktisk viste indekser. Dialogfelter og alle avvik fra originalbakgrunnen beholdes i forgrunnen. Vernerektangelet er adskilt fra UV-feltet: de nye masterne viser hele originalrammen og skaleres derfor over hele 320x200, uten å presses inn i dialogutsnittet. Maths nye råbakgrunn inneholder bare arkitekturen. Originalens ansikt, kappe og hender bevares fra PIV-kilden med avgrensede indeksmasker; animert hår og skjegg bevares fra den faktiske spillrammen. Ingen ny statisk Math-figur brukes. I sluttbildet med ridderen gjenkjennes de faste pikslene i hele rammen, siden den animerte rustningsarmen dekker omtrent en fjerdedel av rammen. BG2a-indeks 0 er et hull til programmets underlag og separate forgrunnsfigurer; disse originaldelene beholdes, ikke fylles med et oppdiktet landskap. Terningbordets tekstfelt bevares. HD-lysstyrken følger kildens fulle palett og inn-/uttoning fra første bilde, også på banneret med svart midtrad. Høyst fire standardbakgrunner ligger på GPU samtidig.

[Original/HD-galleri](index.html) viser alle 75 aktive bakgrunner. [Dekningslisten](coverage.json) binder hver rute til originalfil og bilde. Råbakgrunnsgalleriet viser ikke separate figurer, dialog eller animasjon.

## Verifikasjon

- `verification/combat/combat-test.json`: alle 56 varianter kjørt i faktisk WASM til bilde 1200. Originalkoden velger scenen fra kontrollerte terreng-, teller- og filpekerverdier. Originalfilens SHA-256 og bakgrunnspiksler samsvarer med referansen. Aktiv HD-tekstur samsvarer med riktig PNG. Original/HD/Original bevarer spilltilstand og gjenoppretter originalbildet eksakt.
- `verification/places/places-test.json`: 110 kontroller av tolv PIV-koblinger i frontendfixturer. Kildegjenkjenning, dialogvern, forgrunn på både én piksel og 3072 piksler, og begge grafikkbytter består uten endring i emulert minne. Dette er ikke naturlig besøk til alle stedene.
- `verification/math/math-animated-test.json`: Math besøkes med original navigasjon og animasjon etter kontrollert kartplassering. Originalens figur og animasjon kontrolleres separat mot skanout. Alle 84 synlige dialogglyfer godkjennes, og Original-bildet samsvarer eksakt med kjernens opprinnelige lag. Faktiske bilder ligger i `verification/math/math-animated-*.png`.
- `verification/intro/intro-test.json`: alle fem faste bilder vises i original intro og sluttsekvens. Sluttgrenen aktiveres med kontrollert seiersflagg, ikke med en full gjennomspilling. Faktiske inn-/uttoninger måles mot kildens lysstyrke fra første bilde.
- Regresjon under `verification/regression/`: 49 bakgrunn/tekst-kontroller med naturlig intro/kart/inventar og PIV-fixturer, 88 faktiske kart/ikon-kontroller samt 25 standardpakke-kontroller med 71 av 71 gangrammer. Ingen nettleserfeil.

Testens skjermutsnitt må stabiliseres over minst 25 tegninger før PNG-sammenligning. Den første fixturtesten kunne ellers sammenligne ulike lerretstørrelser. Dette ble rettet i testen. Frontenden beholder nå samme kilde-PIV-identitet ved Original/HD-bytte, slik at engangstegnet dialog ikke mister HD-font. Tekstvalideringen tillater kildebekreftede originalmotiver bak transparente glyffelt. WASM-kjernen er uendret.

## Avgrensning

Dette kobler inn stedsskjermene, alle 56 faste kampvarianter og de faste intro-/meldingsbildene. Det er ikke en påstand om at all grafikk i spillet er HD-ferdig. Individuelle PIV-fliser og andre sammensetninger ved rulling, rullende sluttbilder, dynamiske effekter, butikkfigurer og resterende figurruter må fortsatt behandles. Ingen full gjennomspilling eller telefonmåling av ytelse er utført her.
