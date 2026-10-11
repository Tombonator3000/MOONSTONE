# Innebygd TAV-spiller

Denne kandidaten er en ekstra figur i `TAV.PIV`, utenfor listen med separate CEL-mastere. Den rene tavernabakgrunnen og den originalankrede spilleren skal aktiveres sammen med de 17 separate DICE-masterne. Root eier aktiveringen.

Originalfeltet er `[90,65,225,188]`, 135×123 originalpiksler og 540×492 HD-piksler. Kildemasken velger 7431 figurpiksler. Spillerens 3682 levende kappe-/fjærpiksler følger palett6..10. De 16 andre levende pikslene i barmaidens skygger tilhører ikke spilleren og er utelatt. Indeks11 er en fast mørkerød kappeskygge.

`raw/player-v3.png` er den separate innebygde bildegenereringens master. `generation-record-player-v3.json` binder master, prompt og kildereferanse. `material/player-v3-registered.json` beskriver tilpasningen av nedre armens fotomateriale til originalens uendrede maske. `material/fixed-material-v2.json` beskriver fjerning av feilblå farge i faste originalmaterialer. Alle RGBA-piksler med kildeindeks6..10 og hele alfaen er byteidentiske før/etter denne siste normaliseringen. Hver DICE-rute har sin egen master; kildeidentisk, stillestående kappemateriale deles i210 originalpiksler i006/007.

Den siste kandidaten er `packed/embedded/tav-player.png` med tilhørende NN-maske. `check-player.py` kontrollerer originalindeksene, alle kildepikselmidtpunkter, hver maskepiksel, fotografisk luminans og de uendrede levende feltene. Testen avviser en feil R-kanal i et levende felt.

`runtime.cjs` kjører originalinngang08a1f0 og originalt bettrykk gjennom menykommando14. Det er en kontrollert sceneinngang, ikke en naturlig kartreise. Sluttprøvene ligger i `verification/runtime-v11-0` til `runtime-v11-3`. De binder de faktiske19 DICE-PNG-/maskebytene, spillerplaten, spillermasken, ren bakgrunn, frontend, originalZIP, WASM og lastetHTML. Bakgrunnens siste faktiske import observeres for å unngå en eldre standardbakgrunn over kandidaten. Hver farge prøver manglende/lastet maske, alle17 DICE-ruter, eksakt Original/HD-retur og uendret emulert tilstand.

`verification/runtime-v9-package` bevarer HTML5b59aed4 og manifestet fra den fryste976-filspakken som sluttprøvene bruker. Det midlertidige snapshotet kan gjenopprettes fra de samme hashbundne filene; det brukes bare som egen lokal testvert.

Eldre v6-bilder har feilaktig gammel standardbakgrunn; v7/v8 stopper på det senere rettede poseantallkravet. V9 er før material-/skjøtrevisjon. V10 er diagnostikk med for bred mørkning av original0. Ingen av disse eldre bildene er sluttgodkjenning.

`freeze-delivery.py` lager `activation-set-001.json` bare når alle fire v11-prøver har bestått med samme kandidatfiler og kildehasher. Visuell vurdering skal bygge på de faktiske v11-bildene; en teknisk bestått prøve alene er ikke visuell godkjenning.

Root har godkjent v11-bildene i alle fire farger. Indeksen er fryst med `--visual-reviewed`. `tools/hd_tavern_aktiver.py` kontrollerer denne indeksen og `--dice-delivery` samlet. Uten `--activate` skriver den ingenting. Den kontrollerer originale PIV/CEL-indekser,7431 figurpiksler,3682 levende spillerpiksler,16 utelatte barmaidpiksler, alfamidtpunkt, alle NN-maskekanaler, fotografisk luminans,17 egne DICE-mastere og210 byteidentiske kappefelt. Frontend, WASM, originalZIP, alle fire faktiske runtimeprøver, HTML, pakkelogg, fotografier, prompter og materialderivasjoner må passe. `verification/activation-gate/test.json` dokumenterer20 porter, inklusive avvist feil kandidat ved faktisk `--activate`, en full isolert installasjon og tilbakeføring av alle egne bildefiler hvis siste manifestbytte feiler. Dette verktøyarbeidet aktiverte ingen spillfiler.

WI2 trenger ingen ekstra fastfigur. `../hd-embedded-wi2-2026-10-11/source-audit.json` korrigerer den tidligere skjermtolkningen: WI2.P har bare bakgrunn. Hele trollmannen tegnes av de allerede leverte Wi1.C015/017/019 og tilhørende fragmenter016/018/020.
