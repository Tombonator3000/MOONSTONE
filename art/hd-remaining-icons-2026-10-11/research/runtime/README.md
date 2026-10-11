# Originalruter og trygg HD-kobling

Dette er kildekontrakter og runtimebevis for HD-leveransen. Sluttpakken inneholder 102 rasterkontrakter: 26 tidligere rasterruter er bevart, 49 tidligere konturruter er erstattet, og 27 kildeverifiserte statiske MI-objektruter er lagt til. De fire livsymbolrutene har fem faktiske fargebilder hver (16 ekstra PNG-er). `source-contracts.json` har alle 97 rutene i KI og MI med originalbankhash, ekspanderte skjermindekser, planmaske, synlig silhuett og riktige referansepaletter. `source-contract-check.json` bekrefter de 35 eksisterende KI-kontraktene mot den aktive pakken. Referanse-PNG-ene er originalgrafikk med naermeste-nabo-forstoerring.

Den tidligere omtalen av 55 ekstra inventar-/smaagjenstandsikoner var upresis:

| Gruppe | Antall | Behandling |
|---|---:|---|
| KI vinranke-/rammefragmenter | 3 | Sammenhengende dekor, ikke tre gjenstander |
| KI statustekst og NEXT KNIGHT | 7 | Originaltro tekstoppgave |
| MI hjelmbrikker | 10 | Fem ridderfarger, vanlig og valgt status |
| MI Gem of Seeing | 5 | Krystallkule med ridderspesifikk sokkel, ikke hjelmer |
| MI Scroll of the Hawk | 4 | Korsformet teleportmaal, ikke gravkors eller fugler |
| MI stedsmarkoerer | 2 | Samme lille Stonehenge-port, ulik valgstatus |
| MI interaksjonskonturer | 9 | Valg-/treffkonturer, ikke nye bygninger |
| MI meldingsfelt | 1 | Pergamentfelt for tur/interaksjon |
| MI gravkors | 2 | Aktiv/annen doed ridder |
| MI flygende drage | 8 | Egen kartanimasjon, figurer til sist |
| MI Math-paddebrikker | 4 | Statiske forvandlede ridderbrikker; dekkes som ikoner |

MI019 og MI029 er tomme, og skal ikke genereres. SEL001 er en cyan valgramme og inngaar heller ikke i de 55.

## Palett og originalform

KI000 bruker maske 0x17, KI002 0x1b og KI005-008 0x0b. MI002/004 bruker 0x1b, MI032 0x17 og MI033 0x13. CEL-dataene maa utvides til de opprinnelige skjermbitene; sammenhengende fargeindekser fra en preview er feil. Rendererens originalCel gjoer allerede dette riktig.

MI skal vises med kartpaletten. Den eldre MI-kontaktflaten brukte inventarpaletten, og viste for eksempel en roed drage blaatt og ridderfarger feil. `mi.c-correct-palette-sheet.png` er korrigert. Indeks31 er en pulserende valgt-/interaksjonskontur, her lilla, ikke en fast hvit outline. Originalens rutine 0aafcc..0aafda animerer den. Rasterisering maa bevare denne originale indeksen eller kontrollere hele palettanimasjonen. Faste rasterpaletter vil ellers hoppe mellom HD og original.

KI017-020 bruker de fem dokumenterte ridderfargeparene med separate genererte bildefiler. Andre, udokumenterte kroppsfarger beholder originalen. MI-hjelmer, krystallkuler og Hawk-maal har egne kilde- og fargeruter.

`natural-headless-draws.json` dokumenterer faktisk originaltegning via vanlig tastaturreise: kartets MI005/021 og inventarets KI026/034-036/038-043/017/021/022/027. Ingen skriving i spillminnet ble brukt. Dette er tegnelistebevis, ikke visuell HD-kontroll av alle ruter.

## Ny produksjonspipeline

1. Bildemakerne lagrer urorte raw-bilder, prompt og en `asset-*.json` i kunstroten. `review_status=reviewed_for_runtime` krever separat motivkontroll.
2. `tools/hd_resterende_ikoner_pakk.cjs` bruker browsercanvas til aa plassere masterens alfa i originalreferansens bounds. Det skriver bare kandidatmetadata, rapport og packed-PNG. De 26 gamle rasterkontraktene kopieres uendret fra den uforanderlige `source-baseline-icons.json` (git4365315). Etter aktivering kan samme pakke reproduseres ved aa hente kildekontraktene fra denne filen, mens `baseline_icons_sha256` fortsatt binder de faktisk aktive metadataene foer neste aktivering. Andre aktive ruter beholdes.
3. `tools/hd_resterende_ikoner_aktiver.py` kontrollerer hasher uten aa endre spillet. Bare den eksplisitte bryteren `--activate` kopierer gjennomgaatte filer og oppdaterer ikon-/pakkehasher. `--keys` kan velge et smalt utvalg.
4. `tools/hd_resterende_ikoner_sjekk.cjs` importerer kandidatbilder i en egen testnettleser og proever de faktiske rendererfunksjonene med originale CEL-/inventarfixturer. Original, HD, speiling, kildeendring, ukjent forgrunn og uendret kjernetilstand kontrolleres.

Foerste KI003 Ring of Protection bestod 17 kontroller med normal og speilet kilde. De faktiske frontend-PNG-ene er visuelt kontrollert, men dette er en eksplisitt inventarfixture, ikke bevis for at ringen er kjoept og brukt gjennom vanlig spillnavigasjon. Ingen produksjonsfil ble aktivert i denne proeven.

## Gjenbruk av integrasjonstester

De eksisterende ikon-/landemerke-/pakketestene bruker egne utdata i denne leveransen. Kontraktantallet avledes fra aktivt manifest (102); den naturlige inventarskjermen har fortsatt 17 synlige KI-ruter. Rastertesten dekker alle rasterruter og 16 fadingnivaaer, vannpalettsyklus og ukjent palett. Kildemidtpunkttesten brukes bare paa konturruter, ikke paa fotografiske nytegninger. `hd_resterende_ikoner_alle_sjekk.cjs` kjoerer de foerste 58 nye KI-/MI-rutene i avgrensede, sekvensielle frontendnettlesere.

Toppen av kroens pengesekk, scene-icons000, inneholder et gullfelt som originalen tegner dynamisk ved x282,y14. Det maa bevares. De fem innsatssekkene har tekst/tall utenfor utsnittene, saa tekstomraadene skal beholdes. Gamle kroreferanser er opake pergamentfelt: bruk en motivreferanse med korrekt alfa eller en fullcrop-master for aa unngaa aa strekke en transparent sekk til hele pergamentrektangelet.

## Nye kildekontrakter og runtimevern

Skattekisten er ett objekt: originalkoden i sub_08b810 tegner KI031 ved (58,46), KI032 ved (76,33) og KI033 ved (58,60). CEL-bounds gir en 59x53-union og relative fragmentrect [0,13,18,14], [18,0,41,27], [0,27,46,26]. Referansefilen hos motivagenten er et 540x510-diagnosebilde med margin; den bestemmer ikke utsnittet. Pakkeren bruker samme fullmaster og skalering foer de tre utsnittene. `canvas-contract-test.json` bekrefter 163520 identiske fragmentpiksler mot fullmasteren.

Runepergament kan pakkes med `source_clip:true`, `ink_indices:[7,8]` og et kildeavgrenset `ink_rect`. Da beholdes originale transparente index0-hull, mens roedt/brunt blekk tegnes fra de eksisterende kildepaths. Dette er en kildegeometrisk tekst-/symboloperasjon; raw-genereringen endres ikke. Canvasproeven bekrefter eksakt hull, RGB-blekk og uendrede piksler utenfor runeomraadet.

`preserve_indices:[19,31]` beholder den valgte MI009-hjelmens originale moerke ytterkant og pulskant foran rasterkroppen. Den kontrollerte originalindeksen utelates fra kroppens referansepalett, og de samme pikslene beholdes i forgrunns- og vernmasken. Endret kroppspalett eller endret kildemoenster avvises fortsatt. Den foerste faktiske hjelm-body-masteren med bare31vern bestod 108 frontend-/SceneHd-kontroller med 32 forskjellige pulsfarger i `pulse-art-verification/pulse-test.json`. Sluttkontrakten bevarer ogsaa19. Endelig rapport skrives separat etter aktivering.

sub_08ad68..08adfc velger inventarpanelenes ridderfarger: KI017/019 bruker28/29 og KI018/020 bruker30/31. Parene er blaa003f/0028, oransje0fb0/0b60, groenn04c3/0160, roed0f00/0800 og moerklilla0027/0003. KI017/018 og019/020 har identisk pikselgeometri etter bare indeksbyttet. Hvert panel trenger de fem faktiske fargebildene. `palette_variants` velger disse bildene bare ved de dokumenterte indeksparene; ingen fri fargetinting foretas. De fire ekstra fargene per panel ligger under `ki-palettes/`. Uventet fargepalett og manglende variantbilde beholder originalen.

KI037 bruker indeks30 bare ved (10,21) og (16,21). Disse to dynamiske hoeylysene bevares som original forgrunn med `preserve_indices:[30]`; alle andre farger er fortsatt kildevaliderte. Dette unngaar unodvendige sekkevarianter.

Kroens faste scene-ikonoverlegg tegnes paa renderOrder3.5, under HD-glyfer/scene-tekst4 og over original forgrunn3. Eksakt originalforgrunn vernes fortsatt av sceneVern. Dette hindrer at den fotografiske sekkens panel dekker nye HD-tallkanter, uansett hvilken flate som ble opprettet foerst.

## Statiske MI-objekter og riktig kantmateriale

De 27 nye MI-kontraktene er 000..018,020,031,033,042..046. Alle ti hjelmer har identisk kroppsalfa etter at0/19/31 er tatt ut: kroppsbounds[1,1,7,9] i8x10-ruten. Vanlige000..004 bevarer19; valgte005..009 bevarer19og31. De fem kartfargene er de faktiske originalfargene fra kartpaletten. `helmet-body-contracts.json` dokumenterer pikselmaskene.

Gem010..014 er krystallkule paa ridderfarget sokkel. Indeks19 er her en intern brun hals (rad6,x2..5), saa den inngaar i bildet; bare31 bevares. Hawk015..018 er originalens korsformede maalmarkoer med31pulskant. Disse betydningene er sporet i originalkode og originalmanual av motivagenten; `research/map-tavern/README.md` inneholder kildepekerne.

Grav033/042 bruker graakorsmasteren i bodybounds[1,1,7,9]. Begge beholder moerk19ytterkant, og042 beholder ogsaa31puls. De to graa kroppsmaskene er ikke identiske:042 har ni ytterpiksler erstattet med19. Originalforgrunnsvernet dekker forskjellen; `grave-body-contracts.json` dokumenterer den.

Stedsport020/031 gjenbruker byteidentisk, tidligere godkjent trilithonmaster fra stedskorreksjonen. Den pakkes proporsjonalt og bunnforankret (contain) innen originalens9x5-rute, slik at fotoporten ikke strekkes til en bred bjelke. Valgt031 bevarer31. Ingen interaksjonskonturer, tekst-/rammefragmenter eller figur-/drageanimasjoner er nytolket som statiske gjenstander.

De tre faste lilla kart-hjelmene map-icons023..025 har ingen31 i sine kildekontrakter. De bruker samme bodymaster som MI004/009 og bevarer den originale moerkebrune19-ytterkanten. Dette er et eksplisitt unntak for de tre gjennomgaatte rutene; Gem19 er fortsatt internt stativmateriale og inngaar i rasteren.


## Sluttbevis og avgrenset cachekorrigering

`final-cel-verification/cel-fixtures-batches-test.json` dokumenterer58 opprinnelige KI-/MI-ruter og780 frontendkontroller. Alle normale og speilede originalfelt godkjennes med HD, Original/HD-retur er eksakt, endret originalbank og ukjent forgrunn avvises, og emulatortilstanden beholdes. De fire livrutene valgte alle20 faktiske genererte farge-PNG-er eksakt i begge paneler.

Maths fire paddebrikker MI043..046 er statiske10x12-objekter med samme grunnmotiv som KI019s10x12-kropp innen13x15-ruten. De har ingen31kontur;19 er interne oeyne/munn og maa inngaa i bildet. Stripefelt[4,7,2,2] er blaatt30, oransje29, groent8 eller roedt28; nedre[4,9,2,1] er fast brun18. Fire minimale bildevarianter foelger disse kartfargene. `map-toad-contracts.json` dokumenterer kildepikslene, og `additional-toads-verification/inventory-fixtures-test.json` bestod53 kontroller for de fire nye rutene.

Review av delvis variantimport fant en egen cachefeil: ny roed variant-PNG ved uendret roed kildepalett oppdaterte ikke baseteksturen. Bare to cachelinjer i render.js ble rettet: valgt variantteksturobjekt inngaar naa i cacheidentiteten. `variant-import-verification/variant-import-test.json` bestod15 kontroller paa den faktiske siste builden: ny PNG vises straks, korrekt blaa original beholdes, retur til roedt bruker importen, Original/HD-returnering er eksakt, og den genererte roede PNG-en kan gjenopprettes identisk. Kodehashene foer/etter er lagret, og reversering av akkurat de to linjene gir eksakt det opprinnelig testede kodehashet.

`combined-cel-coverage-test.json` binder alle62 nye KI-/MI-ruter og833 kontroller til det endelige102-kontraktsettet. For hver rute valideres metadata, raw/source/record/prompt/packed-hasher og de faktiske normal-/speilskjermbildene. De bestaaette uendrede rutene gjenbrukes med det avgrensede importovergangsbeviset; ingen kilde-, geometri-, palett- eller indeksgodkjenning ble endret av cachekorrigeringen. Dette er eksplisitte frontendfixturer, ikke bevis paa naturlig kjoep/bruk av hver gjenstand i spillet.

Den historiske108-pulsproeven gjelderMI009 med31vern foer19 ble lagt til; den generiske indeksverngrenen er uendret. En egen KI037-femfarge-GPUproeve finnes som verktøy, men er ikke kjoert og paastaas ikke bestått. KI037 har eksakt kildepikselbevis, normal/speilet fixture og samme generiske indeksvern. Kroens22-kontrollproeve, canvasprøvens163520 kistefragmentpiksler og320 fadingproever er separate bevis, med egne rapporter i denne mappen.

## Vannsyklus og konsistent palettfixture

Den naturlige kartturen avdekket at Waterdeep (map-landmarks/005) og elvestedet (004) falt tilbake til originalgrafikken under vannsyklusen. Originalkoden setter startindeks21 ved0aafe4 og sluttindeks23 ved0aafe8, og0abef0..0abf30 roterer hele dette inklusive intervallet. De to nye rasterkontraktene manglet denne kjente syklusen. Kun004/005 fikk `reference_palette_cycles:[[21,22,23]]`;005 fikk ogsaa kildepalettens hvite RGB for21 som kan rotere inn i22/23. Alle andre100 metadata og alle92 nye PNG-er er identiske med foer rettingen. `water-landmark-cycle-contract.json` dokumenterer kildebevis og avgrensning. Pakken er aktivert og bygget; den samlede CEL-rapporten er bundet til dette102-kontraktsettet.

Kartregresjonens syntetiske ukjente palett maa oppdatere baade `Kjerne.skanout().pal` og de tilsvarende RGB-pikslene i `Kjerne.rammebuffer()`. SceneHd kontrollerer at faktisk framebuffer samsvarer med indeks/palett. Endres bare scanpal, blir alle ellers identiske PIV-piksler med den endrede indeksen kunstige forgrunnsavvik. Det kan slette en CEL fra rendererens plasseringscache; dette er ikke en gyldig simulering av et originalbilde. De foerste feilede palettretur-rapportene beholdes som diagnose. Ingen produksjonskode ble endret som foelge av denne testdiagnosen.

Den konsistente kartfixturen bestod 106 kontroller i `../../verification/landmarks/landmarks-test.json`. Alle 32 kartoverlegg er faktisk tegnet og gjenopprettes identisk etter hver enkelt PNG-retur. Ukjent palett beholder originalfeltet, og den opprinnelige paletten gir eksakt samme HD-bilde etter foerste render (`settle_frames:0`), uten aa resende tegnelisten. Begge nye vannsteder er dermed faktisk synlige under originalens aktive vannsyklus.
