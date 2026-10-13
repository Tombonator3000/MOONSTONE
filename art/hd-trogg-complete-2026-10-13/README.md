# Hele Trogg-serien

Produksjonen dekker alle225 ruter i TROGGAxe1.CEL, TROGGAxe2.CEL, TROGGSpear1.CEL og TROGGSpear2.CEL.30 tidligere leverte våpenruter bevares byteidentisk.195 ruter legges til, med62 eksakte originalaliaser. Det gir163 unike kildeformer.

Det er laget to nye materialatlas med den innebygde bildegeneratoren. Hud, ull, hår, lær, stål, tre og blod bindes til originalens materialfelt, lysformer og avrundede konturer. Det er en kildebundet materialkonvertering, ikke225 uavhengige anatomiske nytegninger. Originalens åpne stålkappe, kroknese, mørke hår, drakt, våpen, fragmentdeling og ankere bevares. De tre avviste kroppsutkastene brukes ikke. Ni unike svarte skygge-/skaftformer bevares uten fotografisk erstatning. Eksakt modellversjon eksponeres ikke av verktøyet.

151 ruter har egne levende masker. Troggens klær9..11 og hud12..14 følger de tre originale terrengpalettene. Ridderofrenes6..8 følger spillervalg.15 er blod.5 er svart kontur, hår, skygge eller skaft avhengig av kilden. Farge5 tolkes derfor ikke automatisk som bare skygge. Løse beindeler er eksplisitt klassifisert som lærstøvler, slik at de ikke får hjelmens metallmateriale.

| Bank | Ruter | Innhold |
|---|---:|---|
| TROGGAxe1.CEL |37| Kropp, kast-/bevegelsesdeler, liggende fragmenter og fire gangretninger |
| TROGGAxe2.CEL |80| Treff, blod, skade/død000..049, sving050..054, øks055..068 og hammer069..079 |
| TROGGSpear1.CEL |41| Bevegelse000..013, spydets offer-/angrepsdeler, blod og svarte former |
| TROGGSpear2.CEL |67| Delte treff-/dødsdeler000..049 og spydangrep/kropp/vaapen050..066 |

`source/contracts.json` binder alle ruter til originalZIP, bankSHA, planmaske, indekser og dimensjoner. `pack.py`, `sprites.json`, `packing/`, `generation.json` og `prompts/` dokumenterer produksjonen. `atlas.py` eksporterer fire atlaspar og225 byteeksakte ruteutsnitt. Spillet bruker individuelle PNG-er, ikke inspeksjonsatlasene. `index.html` viser alle original-/HD-par og har bankfilter. Lokalt galleri: http://127.0.0.1:8799/.

Kontroller ligger i `verification/`. `runtime.cjs` prøver alle225 normal/speilet, fire klippkanter, retur til Original/HD og full save. `palettes.cjs` prøver alle151 maskerte ruter med de relevante terreng-/spillerfargene. Forventet antall ulike terrengbilder kommer fra originalpaletten; indeks11 er svart i to terrengtyper. `standard.cjs` kontrollerer alle225 gjennom vanlig standardlasting, normal/speilet, og gjentar separate originale øks-/hammer-/spydkamper. Originalkampene bruker tre dokumenterte initializer-/aktiv-ridder-/terrengskrivinger før kamp og vanlig joystickinput. Kandidaten beveger ridderen mot høyre, mens standard-/offentlig prøve beveger den mot venstre for å få flere treff- og dødsdeler. Native originalreferanse med samme venstreinput ligger i source/native-left. Ingen direkte skriving til liv, palett, animasjon eller frontbuffer under disse CPU-kampene.

Faktisk CPU-dekning rapporteres separat fra frontendprøvene. Ingen full naturlig kampanje eller fysisk mobilprøve påstås. Kjernen, originalZIP, spilleregler, input og lagringsformat endres ikke av grafikkleveransen.

Kandidat3273/3273, alle151masker638/638, kildekontroll489 og brukerflyt53/53 består. Kamphelperens bakgrunnslasting er rettet til appens korrigerte scenehash; tidligere råhash-bevis er bevart og er ikke grunnlag for å påstå en produktregresjon. Endelig standard-/publiseringskvittering arkiveres i verification/. Galleriets225 kort/450 bilder og fire filtre er kontrollert på desktop- og mobilbredde; dette er nettleserbredder, ikke fysisk enhetstest.


Bakgrunn og bakte lik er nå kildebundet i render.js/scenes.js. Bare originale Trogg-banker med riktig SHA,087b34-kall og0a2cd6-buffer kan forklare kroppsdeler i kampkopien. Senere087bf0-tegninger får bare samme rett etter et observert bakekall med samme kilde, mål, posisjon og speiling. Hele originalkomposisjonen og faktiske palett-/bakgrunnspiksler kontrolleres; ukjente data beholder Original. Originalens regler, CPU, input og save er urørt.

Endelig lokal standard1128/1128 observerer57 øks-,59 hammer- og68 spydruter. Alle72 lagrede kampbilder beholder HD-bakgrunn. Bakeprøven80/80 dekker også feil caller/buffer/geometri/kilde/piksel, reset og full uendret save. Sluttregresjon: brukerflyt53/53, BLO619/619 og Ratmen26/26. delivery.json bevarer den historiske aktiveringen før bakerettelsen; delivery-active.json og verify_active.py kontrollerer alle225 allerede installerte ruter og151masker mot endelig kode/standardbevis uten ny aktivering. Pakke2381PNG/2387filer; ingen Trogg-ruter gjenstår i bestillingen. Øvrig spillgrafikk har586mastere/587ruter igjen.
