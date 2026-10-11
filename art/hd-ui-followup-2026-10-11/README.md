# Originaltro UI-fragmenter

Dette er originalens bokstavformer, rammer og kartkonturer med utjevnete
kanter i aatte ganger kildestoerrelsen. Ingen erstatningsfont eller nye
symboler er brukt. Dette er ikke fotografisk nytegning av materialer.

## Utvalg og kilde

- `mi.c/021..028` og `030`: ni konturer for kartsteder/hjemsteder.
  De bestaar bare av indeks 31. Originalkoden velger dem i
  `disasm/mog.s`, adresse `080e8e..080f56`. Direkte konturpalett lar
  originalens fargepuls fortsette uten en statisk RGB-maske.
- `mi.c/032`: pergamentfelt for tur/valg paa kartet. Originalen tegnes
  ved `(50,100)` i `0abc5c..0abc92`; tekst/valg kommer etterpaa i
  `0abc98..0abd6c`. Konturfilen her er et materialutkast. Den aktive
  pakken bruker egen naturtro pergamentnytegning fra bakgrunnsleveransen.
- `ki.cel/034..036`: tre separate vinrankefragmenter med original
  speiling. Fragmentlisten og speilingen ligger i `08ae50..08af24`.
  Egen naturtro materialnytegning gjenstaar.
- `ki.cel/038..043`: originaltekstene `STR:`, `CON:`, `END:`, `XP:`,
  `GOLD:` og `HIT:`. `ki.cel/044` er `NEXT KNIGHT`. Bokstavene og
  deres originale skyggefarger er bevart. Se `08af44..08b34a` og
  `08cace..08cbd6`.
- `sel.cel/001`: rektangulaer markeringsramme paa 64 x 76.
  Valgt ridder bruker rute 1 ved y=80 i `081e3e..081e5e`.

`source-contracts.json` inneholder originale utvidete palettindekser,
planmasker, bankhash, palett og ruteidentitet. `references/` er eksplisitte
originalreferanser. `source/` og `svg/` er redigerbare original- og
konturkilder; `packed/` har de eksporterte PNG-filene.

## Visuell og teknisk kontroll

Foerste pakking avdekket at den eldre konturhjelperen skilte diagonale
enkeltpiksler som separate perler. Den separate `ui_contours`-funksjonen
forbinder derfor originalens diagonale pennestroek. Eksisterende raster-
og konturkode i de andre ikonverktøyene er ikke endret.

`tools/hd_ui_pakk.cjs` kontrollerer alle 21402 kildepikselmidtpunkter,
dimensjoner, aapne hull og sammenhengende stroek. Dette gir 21507
pakkeprøver. `comparison.png` viser original og utjevnet UI side ved side.

`tools/hd_ui_sjekk.cjs` importerer kandidaten i en faktisk WASM-side og
kontrollerer normal/speilet visning, eksakt Original/HD-retur, levende
31-palett paa alle ni kartkonturer, endret kildebank og ukjent forgrunn.
Rapporten i `verification/ui-fixtures-test.json` gjelder bare den oppgitte
produksjonskoden og kandidaten. Den beviser ikke naturlig bruk av alle
steder eller en full gjennomspilling.

## Integrasjon

Ingen aktiv metadata endres av byggeren eller pakkeren.
`fragment-icons.json` har bare de 21 nye rutene. `candidate-icons.json`
inneholder ogsaa de 102 eksisterende rasterkontraktene uendret.

`python3 tools/hd_ui_aktiver.py` kontrollerer standardutvalget paa 17
UI-ruter. `--activate` aktiverer dette utvalget etter godkjent kontroll.
De fire materialutkastene holdes utenfor standardaktivering.
`--include-material-drafts` tar dem med uttrykkelig som uferdige utkast.

Eksisterende PNG-er, metadata og manifestruter som ikke er del av dette
utvalget skal bevares ved integrasjonen.

## Tillegg: donasjon og Dragon Dice

`additional/` er en separat kandidat, slik at den bestaatte hovedpakken
og dens bevis ikke endres ved neste bestilling. Bygg den med
`python3 tools/hd_ui_bygg.py --additional` og sett `MOONSTONE_UI_ART` til
`art/hd-ui-followup-2026-10-11/additional` for pakkeren og runtimeproeven.

- `mys.cel/002..005` er originaltekstene Exit/OK og to retningspiler.
  Disse fire UI-rutene er standardutvalget ved `--additional`-aktivering.
  Runtimeproeven bruker baade MYS- og HEA-paletten, siden originalens
  donasjonsdialog deles av mystikeren og healeren.
- `mys.cel/000` er mystikerens donasjonssekk med MYS-paletten.
  `mys.cel/001` er healerens sekk med HEA-paletten. Begge trenger egen
  naturtro materialnytegning foer aktivering.
- `dice.cel/000..005` er seks faste Dragon Dice-utfall, valgt som
  tilfelldig tall 0..5 i `08a600..08a690`. Det er spillets symbolflater,
  ikke vanlige terninger med prikker. Disse seks materialutkastene
  aktiveres ikke i denne leveransen.
- `mys.cel/006` og `007` er healerens og mystikerens oeyefragmenter med
  lukkede oeyne. De tilhoerer figuranimasjonene og ligger bare som
  originalreferanser, uten kandidatmetadata eller PNG-aktivering.
  `references/mys-corrected-identities.png` viser riktig HEA/MYS-palett.

Tillegget har tolv statiske kandidater: fire UI-ruter og aatte
materialutkast. De to oeyefragmentene inngaar ikke i disse tolv.

## Aktivert og kontrollert i felles pakke

De 17 opprinnelige UI-rutene og de fire donasjonsrutene er aktivert.
Aktivereren verifiserer hash og alle originale rasterkontrakter fra
`source-contracts.json`, og bevarer ogsaa rasterkontrakter lagt til etter
kandidaten ble bygget. De 102 tidligere rasterikonene er uendret; den
naavaerende pakken har i tillegg det separat produserte pergamentet.

Hovedkandidatens 21 ruter bestod 522 runtimeproever, inkludert utkastene
som ikke ble aktivert. De fire donasjonsrutene bestod 64 runtimeproever
med begge vertspalettene. Tilleggets tolv kandidater bestod 10531
pakkeproever. Materialutkastene godkjennes ikke som fotografisk grafikk
av disse tekniske proevene.

`verification/integration/` er den foerste naturlige integrasjonsproeven
mot felles HTML-pakke med 398 PNG-er. Den bestod 60 sjekker.
`verification/integration-final/` bestod 65 sjekker, med eksplisitt kontroll av den
naturlig synlige MI021-valgkonturen og lastet HD-bakgrunn i inventaret.
Originale synlige KI-ruter bestemmer forventningen: 23 plasseringer i
standardinventaret. `NEXT KNIGHT` vises i et annet forloep.

Aktiveringsporten krever fersk runtimeproev fra
`verification/bound-runtime/ui-fixtures-test.json`. Denne proeven binder
de faktisk importerte PNG-bytene, kildekontraktene og de lokale
`render.js`-/`scenes.js`-filene med SHA-256. Proeven verifiserer ogsaa at
den serverte HTML-siden inneholder akkurat disse produksjonskildene,
og at ingen av filene endres under kjoringen.

Byggeren kan kjores igjen etter aktivering. Den verifiserer og gjenbruker
den frosne baselinen, og endrer ikke aktive metadata eller det senere
fotografiske pergamentet. `verification/build-idempotency-test.json`
dokumenterer byteeksakt gjenbygg av begge kandidatene og bevaring av den
aktive pakken. `tools/hd_ui_aktiver_sjekk.py` prover aktiveringsporten i
en midlertidig kopi, inkludert avvisning av utdatert kode- og PNG-bevis.

Den bundne sluttproeven bestod 549 sjekker for 21 hovedruter og 82
sjekker for de fire donasjonsrutene, uten nettleserfeil. Begge
aktiveringsutvalg bestod deretter full dry-run mot fersk proof.
Aktiveringsportens seks positive/negative sjekker bestod; se
`verification/activation-gate-test.json`.
