# Trogg: HD-vaapen og materialer, 13. oktober 2026

Denne pakken lager 30 kildebundne ruter i TROGGAxe2.CEL/050..079: fem bevegelsesspor, oeksens vinkler, hammerens vinkler og fire ruter med synlige grep. Fire palettmasker bevarer hud-/ermfargene som originalen skifter med terrenget. Dette er ikke hele Trogg-figuren eller 30 uavhengige AI-tegninger.

Tre separate mastere er laget med den innebygde ChatGPT-bildegeneratoren: kompakt oeks, lang oeks med haand og rektangulaer hammer. Eksakt modellversjon eksponeres ikke. Prompt og urørt PNG ligger i prompts/ og raw/. weapons.py henter dokumenterte metall-, tre- og hudutsnitt og tilpasser dem de originale materialfeltene og alfaformene. Den bruker ikke oppskalert original RGB. Samme materiale gjenbrukes for stabil identitet gjennom vinklene. weapons.json binder hver originalrute, PNG, maske og materialmaster til SHA256. weapon-comparison.png viser alle 30 original-/HD-par.

Original kilde bestemmer rutemaal, hull, tegneanker, skaft-/hodeform og bevegelsesspor. Alfa er laget med prosjektets eksisterende avrundede kildekonturer. Hvert opakt/gjennomsiktig kildepikselmidtpunkt kontrolleres. Originalens indeks5 er skaftmateriale i disse rutene, ikke en fotskygge. Grepene i062/063/065/066 bruker levende Trogg-indekser9..14; de er ikke ridderofre.

Kroppsforsoekene ble avvist. 025-v1/v2 avviker for mye i bein og kroppskontur. V3 tolker hjelmen og ansiktet feil. De er bevart i rejected/ som negative referanser og aktiveres ikke. pack.py og packing/ dokumenterer formproeven; weapons.py er den faktiske vaapenproduksjonen. Nye kroppsposer maa loeses foer full Trogg-konvertering.

## Gjenskap

Fra reporoten: python3 art/hd-trogg-2026-10-13/weapons.py. Dette validerer original ZIP/bank/indekser foer pakking og krever de tre eksisterende genererte masterne. Det genererer ingen ny kunst og endrer ikke standardpakken.

runtime.cjs bruker faktisk WASM, standardlaster og WebGL. Kandidatmodus importerer de30 PNG-ene og fire masker separat. MOONSTONE_TROGG_STANDARD=1 bruker bare standardpakken. MOONSTONE_URL kan velge offentlig nettspill; HTML og alle nye assetbytes kontrolleres mot lokale hasher. Node krever prosjektets eksisterende Playwright og Sharp.

Frontendfixturer kontrollerer alle30 ruter normal/speilet, fire kanter, eksakte Original/HD-returer og uendret full lagring. Grepet testes med tre opprinnelige terrengpaletter. En fremmed forgrunnspiksel skal beholde Original. Egne originalkamper initialiserer oeks083e6e og hammer083f2c, velger aktiv ridder og terreng0c og lar deretter original CPU styre alle tegninger. Dette er kontrollerte kamper, ikke naturlig kampanjereise eller full animasjonsdekning. Kontrollerte faktiske kampbilder holdes atskilt fra frontendfixturene.

Status og faktisk antall bestaaette kontroller foeres i verification/ og log.md etter utfoert kontroll. Ingen tidlig kandidatrapport er en produksjonsgodkjenning.


Lokal standardkontroll:483/483 bestaar uten JS-feil. De samme30 PNG-ene og fire masker er brukt i kandidat og ordinær standardlasting. Alle2011 eldre manifestfiler er SHA-uendret.264 kilde-/maskekontroller og30/30 pikseleksakte atlasutsnitt bestaar. Standardpakken har2039PNG/2045filer. Gjenstående719mastere/782ruter/59mastermasker er dokumentert i docs/hd-status-2026-10-13. UI og publisering registreres separat etter faktisk kontroll.

UI-regresjonen bestaar53/53 med faktiske valg og inventarklikk. Galleri med30kort/60bilder er kontrollert paa desktop/mobil. Standardens faktiske oeks-/hammerbilder er visuelt kontrollert etter ordinær innlasting. Publisering og offentlig kontroll dokumenteres separat.
