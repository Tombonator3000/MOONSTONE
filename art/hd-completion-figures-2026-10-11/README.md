# Kildekø for alle resterende figurer

Dette er produksjonsforberedelse. Ingen eksport, kontaktflate, maske eller nærmeste-nabo-forstørrelse her er en nytegnet HD-figur. Ingen fil kobles inn i spillet av disse verktøyene.

Køen fryser bestillingen med 1796 rader. De 11 ikonmaterialene, fem bakgrunnsrevisjonene og logoen er skilt ut i `outside-scope.json`. Der ligger også de separate rullekildene og de 38 tomme CEL-rutene som skal bevares.

## Nøyaktig omfang

| Type | Antall |
|---|---:|
| Selvstendige CEL-nytegninger | 1779 |
| Eksakte kopier av en master | 159 |
| HE-kopier med egen indeksmaske | 102 |
| Konkrete figur-/animasjonsruter | 2040 |
| Banker med konkrete ruter | 45 |
| Selvstendige ruter med maskebehov | 164 |
| Samtlige maskemaler, inkludert HE | 266 |

Dette er CEL-inventaret, ikke en påstand om at alle innbakte PIV-figurer er ferdige. `additional-non-cel-work.json` fører en separat reell oppgave: Maths statiske ansikt, kropp og hender som er bakt inn i `WI1.P`. Den oppgaven ligger hos `art/hd-math-figures-2026-10-11`, med egen kilde-/regionkontrakt og runtimekontroll; den er ikke en av de 1779 CEL-masterne.

Intro/slutt har 385 konkrete kilder. 329 bestilles som selvstendige tegninger; 55 `Klift1.CEL`-ruter kopieres fra `hen1.c`, og én `au1.cel`-rute er en annen eksakt kopi. Intro/slutt har teknisk HD-støtte. Kopiene har fortsatt egen port for rutenes kunst, palett og animasjonskontroll i køen. En master som også brukes i hovedspillet, er fortsatt forberedt for hovedspillet.

## Tre selvstendige arbeidspakker

Rekkefølgen under prioriterer visuell risiko. Filnøklene mellom pakkene overlapper ikke. Hver pakke omfatter sine mastere og de dokumenterte kopiene deres.

| Pakke | Selvstendige | Målruter | Viktigste risiko |
|---|---:|---:|---|
| `01-monstre` | 1050 | 1120 | Store figurer bygget av fragmenter, kropp/våpen-overlapping, demonens pisk og drageild. Trollets blå originalpalett er kilde-/CPU-bekreftet; hver ny rute må fortsatt prøves samlet i kamp. |
| `02-riddere` | 195 | 330 | Kropp og separate våpen, samme rustning over alle ruter, levende spillerfarger, 102 HE-varianter og korrekt maske med lysdetaljer. |
| `03-steder-effekter-intro` | 534 | 590 | Math og øyefragmenter, hender/terningkast, blod og magi. Inkluderer intro/slutt med teknisk støtte og egne palett-/animasjonsporter; kartdragens åtte ruter tas sist etter brukerens prioritet. |

Begynn med én representativ master i hver pakke og før den helt gjennom kildekontroll, nytegning, pakking, speiling og faktisk spillvisning før tilsvarende bilder multipliseres. Nummererte nabobilder er kildekontekst, ikke dokumentasjon på en bekreftet animasjonssekvens.

## Filer

- `queue.csv` har én rad for hver av de 2040 målrutene, med master, rolle, bank, 4x-mål, maskebehov og runtimeport.
- `queue.json` og `routes/<bank>/<rute>.json` binder hver rute til originalbankens SHA256, bitplandata, pakkede og utvidede indekser, flagg, planmaske, palettkilde og eksportbilder.
- `source/banks/` inneholder de urørte originale CEL-bankene. `source/programs/` bevarer `program` og `mog`, som begrunner skillet mellom hovedspill og intro.
- `source/packed/` er indekserte PNG-er med originalens pakkede CEL-indekser. De er beregnet på datakontroll og maskebygger, ikke som fargefasit.
- `references/original/` utvider planmasken til faktiske skjermindekser før visning. `references/nearest4x/` er tydelig merkede arbeidsreferanser, ikke nye tegninger.
- `source/alpha/` bevarer hvert originalt gjennomsiktighetsmønster. `mask-templates/` inneholder 4x runtime-maskemaler med nøytral G=128; de mangler HD-tegningens lysdetaljer.
- `prompts/` og `reviews/` har én forberedt prompt og QA-post per selvstendig master. Eksport overskriver ikke eksisterende reviewposter.
- `contact-sheets/` og `index.html` gjør kildebankene lettere å gjennomgå.
- `packs/` blir først brukt når en faktisk nytegnet kandidat pakkes. Tidligere kandidater bevares i egne SHA-mapper.

## Kildebundne farger og gjenstående kontroll

CEL-bankene inneholder indekser, ikke egne fargepaletter. `combat-preview` er originalens palett fra `test`, bilde 4. Den er en datatro arbeidsvisning, men beviser ikke monsterets eller spillerens farger i den aktuelle kampen. Bruk ikke et generisk brunt trollbilde som tegnereferanse for det blå trollet.

`palettes/` har nå13 kontrollerte monsterkontekster med originalpalettkode,32 runtimeord, bank-/ZIP-/native-SHA og komplette bankreferanser. Trollet bruker blå55a/347/123/001, med rødt øye/blod. Troggene har terrengvarianter. Dette bekrefter de undersøkte originalpalettgrenene, ikke hver animasjon eller HD-runtime. Bruk disse referansene foran den gamle `combat-preview`.

Math har 17 kildeeksporterte ruter med målt WI1-/WI2-scene. 015..020 bruker levende indeks 6..10, dokumentert i `source/runtime-palette-contracts/math.json`. 000..014 har faste scenefarger.

`dice.cel/006..009` er ridderens stålhanske og arm over tavernabordet. `010..022` er tre kastede DragonDice; den frosne køens feilaktige hanskeetikett er korrigert additivt i `source/identity-corrections.json`. De bruker `tav.piv`, ikke terningspillets `dice.piv`. `palettes/capture_tavern.py` kontrollerer originalstarten og setterens kode `$08a3b2→$08a9b6`; fire faktisk målte ridderfarger i tre dumper hver bevarer alle andre palettindekser. Den blå kontrakten brukes i kildeeksporten. Bare 006/007 har levende draktindekser 6..10 og trenger maske. Den frosne bestillingen manglet disse to og Maths seks maskeflagg; masketotalen er derfor 266. Kontrakten ligger i `source/runtime-palette-contracts/tavern.json`. Dette er kontrollert originalstart, ikke en naturlig kartreise eller en ferdig HD-runtimeprøve.

Øyefragmentene får paletten fra sine originale PIV-scener. Kartdragen bruker en bevart faktisk kartpalett. Også disse må prøves i den scenen der ruten brukes. `Klift1.CEL` har samme indeksgeometri som `hen1.c`; en palett fra hen1-scenen bekrefter ikke fargene i introen.

Fargeporten står derfor som en separat QA-sak. Ingen palettoppføring eller teknisk PNG-kontroll er automatisk kunstnerisk godkjenning.

## Gjentakbar eksport og kildekontroll

Utpakkede originaler, nearest4x-referanser, alfa og maskemaler lages lokalt med eksportkommandoen. Disse gjentakbare filene sjekkes ikke inn. Kildekontrakter, egne genererte fotomastere, prompter, ferdige HD-filer og prøver bevares i repoet.

Fra reporoten, med Python 3 og Pillow:

```sh
python3 art/hd-completion-figures-2026-10-11/prepare.py export
python3 art/hd-completion-figures-2026-10-11/prepare.py check
```

Første eksport fryser CSV, manifest og de tre originale parserfilene som kilder. Senere eksport bruker disse kopiene, slik at nye ikonleveranser ikke flytter figurkøen. Originalbanken, ZIP-en, palettkildene og parserfilene har SHA256 i kontraktene. Kildekontrollen sammenligner eksporten med de faktiske originalbankene og kontrollerer alle 266 maskemaler. Den utfører ingen generering eller runtimeprøve. `preparation_check.py` kontrollerer byteidentisk gjenbygging, 266 aliasmasker og ni negative porter, inkludert en palettendret pikseloppskalering og en uttrykkelig avvist geometridiagnose. Uavhengig pågående kunstproduksjon holdes utenfor eksportens byteinventar.

Den separate program-observatøren har nå målt faktiske intro-/sluttkall. `prepare.py observe` fryser disse bevisene og lager `runtime-observations.json`, som kobler observerte ruter, plasseringer, speiling og kallsteder til køen. Observerte kall kan ligge i bakgrunns-/dobbelbuffer. Rektangelskjæring mot320x200 er ikke bevis på faktisk synlige piksler. Denne målte delmengden er ikke full dekning av alle385 intro-/sluttkilder, og bekrefter ikke nytegningenes farger eller hver HD-animasjon. Køen beholder derfor alle originalrutene.

Rulleoversikten eksporterer de tre originale `bg1a`, `bg1b` og `bg1c`-atlasene og et separat inspeksjonsrutenett på 80 celler per atlas, 32x25 piksler. De 240 cellene er ikke nye bekreftede runtime-ruter. `intro.stile` og `co.stile`, 960 byte hver, bevares med hash. Sammensetningen og hele rulleforløpet dekodes eller sluttgodkjennes ikke her.

## Pakking av én nytegnet master

Lever ett ubeskåret RGBA-bilde i nøyaktig 4x-målet. Bildets venstre øvre hjørne er originalens ruteorigo; ikke flytt figuren til et nytt midtpunkt eller fotpunkt. De separate kropp-/våpenfragmentene skal forbli separate. Ikke bruk automatisk oppskalering som erstatning for nytegning.

Fyll ut masterens reviewpost med faktisk kandidat-SHA, `authoring_method: "individual_redraw"`, kildeindeks-SHA, prompt og generatoropplysninger. Oppgi bare et modellnavn som faktisk er bekreftet. QA-feltene kan stå `pending` mens en kandidat pakkes; pakkerapporten sier alltid at dette er en uaktivert kandidat.

```sh
python3 art/hd-completion-figures-2026-10-11/prepare.py pack \
  --key KN1.ob/012.png --candidate /absolutt/sti/nytegnet.png \
  --art-record art/hd-completion-figures-2026-10-11/reviews/KN1.ob/012.json \
  --gray-reference 128
```

Bruk `--gray-reference 128` bare når grå rustning bruker grånivå 128 som nøytralt lys. Uten dette normaliseres maskens G mot rutens valgte fargede scenepalett, via en separat `mask-source` med samme pakkede kildeindekser. En farget master som kopieres fra KN til HE skal beholde G og B; bare R-indeksen endres etter den kildeverifiserte indekskoblingen. Pakkeren gjør dette for alle dokumenterte HE-kopier.

Pakkeren avviser feil størrelse, feil PNG-modus, feil kilde-/kandidatbevis, for stor silhuettendring og en ren nærmeste-nabo-forstørrelse. Den måler formtreff, kopierer masteren til de dokumenterte aliasene og lager masker med kandidatens skyggedetaljer. Dette beviser ikke fotografisk kvalitet eller faktisk animasjonsflyt. Gjennomgå kilde og kandidat visuelt, og kjør original/HD, speiling, lys, palettbytte og overlapp i faktisk WASM-spill før en separat aktivator får endre produksjonspakken.

KN5 har nå en egen originalkode-/palettkontrakt og65 separate HD-mastere. Draktfelt6..8 er levende; faste drage-/ildfarger følger sin kildepalett. Alle ruter har normal-/speilfixturer og de sju brennende ridderrutene er sett i faktisk original dragekamp. Dette gir fortsatt ikke naturlig animasjonsdekning av alle65 ruter. `blo.cel` gjenstår.

## Tredje figurleveranse, 12. oktober 2026

`delivery-progress-003.json` binder206 håndterte originalmastere,269 konkrete ruter,160 masker og tre ekstra innbakte figur-/maskefiler.201 mastere har eget nytt fotomateriale; fem er bevarte svarte originalskygger. TAV-bakgrunnen er renset og revidert. Fem gamle helfigurprøver er pensjonert i standardpakken. Nye totaler:1145PNG/1151filer,81bakgrunner. Restlisten:1448mastere/1555ruter.

Standardlasting er kontrollert i de leverte scenene uten kandidatimport. TAV/DICE følger alle fire spillerpaletter. HA1 har sju naturlig observerte introruter og44 normal-/speilfixturer; øvrig dekning og begrensninger står i de frosne bevisene. Original/HD-returer og emulert tilstand er kontrollert. Full naturlig reise gjennom alle animasjoner er ikke påstått.

Original-PNG-er, bankeksporter, kildeindeks-/maskebinærfiler og kompilert HTML er regenererbare lokale data. De sjekkes ikke inn. Bruk de relevante `prepare.py`-/`prepare-static.py`-skriptene, original-ZIP-en og `web/pakk.py` ved reproduksjon. Rå genererte bilder, prompts, kildekontrakter, pakkemetoder og bevis beholder egne hasher. Gamle avviste forsøk er lokale diagnosefiler og er ikke aktive spillassets.

## Fjerde figurleveranse, 12. oktober 2026

`delivery-progress-004.json` binder178 nye, separat genererte fotomastere til215 originalruter og68 masker. Dette gir283 nye PNG-filer: KN5/65, Balok1/28, TROLL2/2, HEN/Klift/74, LI1/30 og DRAGON1/16 ruter. Standardpakken har1428PNG/1434filer og81 bakgrunner. CSV-restlisten er1270 selvstendige mastere/1340 konkrete ruter, fordelt på monstre956, blod41 og intro/slutt273 mastere.

LI1 og den oppstigende HEN-ridderen bruker kildebekreftede fullindeksmasker for normalfarger, lynblink og svart toning. En ny fotoimport får aldri en gammel maske. LI1/012 beholdes gjennom originalens kopier over transparente hull; ukjent forgrunn avvises fortsatt. Tre eksakt identifiserte TROLL2-likfragmenter kan følge originalens bakgrunnsbuffer, også etter at tegnelisten blir tom. Ukjent kilde, kall, buffer eller pikseleierskap gir originalgrafikk.

Den ferdige standardpakken har egne faktisk kjørte intro-/sluttprøver uten privat import, nøyaktige Original/HD-returer og uendret emulert tilstand. Historiske bevis beholder sine opprinnelige kodehash; de eksakte presentasjonskildene er bevart i `verification/source-freezes-004`. Nye totaler og begrensninger står i kvitteringene. Guardian-kandidater og andre uferdige animasjoner er ikke med i denne leveransen.
