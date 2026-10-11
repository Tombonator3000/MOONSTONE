# Fotografisk HD-grafikk

807 urørte rå-PNG og tilhørende prompter er bevart i dette repoet. `catalog.json` og `index.html` viser 506 valgte planoppføringer og 110 valgte bildefliser. Tidligere revisjoner er beholdt i `candidates/`. De ti svarte konstante bg1b-flisene er beskrevet i flismanifestet og telles ikke som nytegnede fotografier.

Dette arkivet inneholder også uferdige kandidater. Status og konkrete avvik er bevart, inkludert feil palettvarianter, konturer, alpha og sammensettingsskjøter. `production-plan-2026-10-03.json` er historisk kildedokumentasjon med enkelte lokale bevisstier; det selvstendige katalogformatet bruker de innsjekkede filene i `references/` og `candidates/`.

Spillet bruker `web/hd/manifest.json`: 327 bilder, av dem 75 bakgrunner. 48 av radene i `catalog.json` er slått på (`enabled_in_game`), det vil si at råfilen ligger byteidentisk i standardpakken. Hulebakgrunnene, healeren, Mythrid, druidene og stedsskjermene kommer nå fra `art/hd-all-locations-2026-10-11` (PR #26); utkastene her er merket som erstattet. De fem hele blå metodeposene er ikke en erstatning for separat nytegning av alle originalruter. Uferdige figurdeler er ikke automatisk aktivert.

Bakgrunner lastes ved behov og høyst fire av standardpakkens bakgrunner holdes på GPU-en. Rå-PNG-ene i standardpakken er byteidentiske med masterne. Ingen bildebehandling eller ny bildegenerering ble brukt ved integrasjonen.

Originalspillet er Moonstone: A Hard Days Knight, Mindscape 1991. Rob Anderson laget spillet; Richard Joseph laget musikk og lyd; originalgrafikk er kreditert Todd Prescott, Dennis Turner, Kevin Hoare og Steve Leney. Bildereferansene her kommer fra originalarkivet som eieren allerede har lagt i repoet. Ny grafikk er laget med den innebygde bildegeneratoren; et eksakt modellnummer ble ikke oppgitt av verktøyet.

For neste produksjonsøkt: bruk `catalog.json`, promptene og de bevarte flis-checkpointene. Fullfør gjenstående ruter og rett de registrerte avvikene før flere figurdeler aktiveres i spillet. De gamle lokale eksperimentene og alle skjermbilder ligger fortsatt i den opprinnelige arbeidsmappen `moonstone-hd`.
