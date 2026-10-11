# Motivkontroll av kart, kro og pekere

Kontrollert 11. oktober 2026 mot originalarkivet, originalens relokerte kode og nettmanualen. Denne mappen dokumenterer research og kontroll av råmastere. Ingen aktive bilder eller spillfiler er endret av denne deloppgaven. Tidligere genererte kandidater er ikke brukt som motivfasit.

## Avgjørende rettinger

| Aktiv rute | Korrekt identitet | Sikkerhet og grunnlag |
| --- | --- | --- |
| `map-landmarks/000` | **Highwood**, nordvest i Misty Moors. Borg/by med konsentriske murer og høye tårn. | Høy. Arbeidsnavnet Waterdeep var feil. Manualens plassering, originalskissen merket HIGH WOOD og originalens faste karttabell stemmer. |
| `map-landmarks/005` | **Waterdeep**, sørøst i Wetlands. Kystby med lyse, slanke tårn, røde tak og klippeform under byen. | Høy. Arbeidsnavnet Highwood var feil. Manualens plassering, originalskissen merket WATER DEEP og originalens faste karttabell stemmer. |
| `map-landmarks/004` | **Unavngitt kartdekorasjon ved elven**, tidligere kalt Tower2. | Høy sikkerhet om at den ikke er et eget interaktivt sted. Lav sikkerhet om den konkrete avbildede natur-/ruinformen. Verken manualens stedsliste eller originalkodens karttabell navngir den. Ikke tegn et nytt trollmannstårn eller finn på et stedsnavn. Bevar originalens smale, mørke brun/grønne silhuett og plassering dersom materialdetaljer forbedres. |
| `map-icons/023..025` | **Tre forekomster av kartets ridderhjelm**, med datamaskinens `mi.c/009`-form. | Høy. De er ikke landsbyer. Originalen laster `mi.c` i banken `$08E7BE`; `$0810A6` tegner figurnummer + 5. Figur 4 gir rute 9. Hjemlandsbyene ligger i kartets fire hjørner. |
| `scene-icons/000` | Brun pengesekk med et rektangulært, tomt tallfelt for spillerens gullsum. | Høy. Original `tav.piv`; `$08A478` leser ridderens gull ved +$4A og `$08A490..$08A4A4` tegner det ved (282,14). Feltet må stå åpent for variabel tekst. |
| `scene-icons/001..005` | Samme knyttede brune pengesekk, gjentatt for innsats på 1, 2, 3, 4 og 5 gull i Dragon Dice. | Høy. Fem ulike objekter skal ikke oppfinnes. Manualen beskriver innsats 1 til 5; originalkodens valgfelt tildeler disse verdiene i radrekkefølge. Tallene/ordet GOLD ligger utenfor selve ikonutsnittene. |
| `po.cel/000` | Skrå dolk/lite sverd som peker øverst til venstre. Rett blad, korsvern og grep nederst til høyre. | Høy. Originalens 16x18 hardware-sprite og manualens pekertype stemmer. Bevar spissen, vinkelen og originalens treffpunkt. |
| `sel.cel/000` | Bred gullfarget høyrepil. | Høy. Originalens 38x19 menypil. Den er ikke en hånd eller et våpen. Bevar samme bredde/høyde, pilretning og fotavtrykk. |

## Kilder

- [Originalmanual, transkripsjon](https://www.freegameempire.com/games/Moonstone-A-Hard-Days-Knight/manual): Highwood i Misty Moors, Waterdeep i Wetlands, Math i Northern Wastelands, landsbyfunksjon, Dragon Dice-innsats og dolkpeker. Manualen er primærtekst selv om den er lagret hos et arkiv.
- [Originale skisser fra David O'Connor](https://moonstonetavern.co.uk/box-art-music-more/): skissene er merket med bynavn og er presentert som materiale fra Rob Anderson. Det er disse skissene som ble brukt i kartet.
- [Highwood-skisse](https://moonstonetavern.co.uk/wp-content/uploads/2026/01/highwood-sketch-576x1024.jpg).
- [Waterdeep-skisse](https://moonstonetavern.co.uk/wp-content/uploads/2026/01/waterdeep-sketch-1024x576.jpg).
- [Skaperintervju](https://spillhistorie.no/2024/12/11/interview-with-the-creator-of-moonstone/): Rob Anderson bekrefter at O'Connors byskisser ble brukt i spillets kartgrafikk.
- [Stedsside](https://moonstonetavern.co.uk/settlements-other-locales/): krysskontroll av stedstekst. Bildene som lenkes der har nå `updated` i filnavnet, og er derfor ikke brukt som geometrisk originalfasit.

Original `Moonstonecd32-AMIGA.zip` er den tekniske fasiten. `evidence.json` inneholder arkiv-/bankhash, karttabell og kildekontrakter. `references/` inneholder bare uttak av originalgrafikk, og kopier av de navngitte originalskissene. Ingen av disse referansebildene er nye produksjonsassets.

## Begrensning og praktisk kunstretning

Byene kan nytegnes trygt med riktige navn og originalsilhuetter. Tre hjelmruter må samordnes med `mi.c/009` slik at kartet ikke får hus på riddernes plasser. Kroens fem innsatssekker kan dele én master; den øverste tellersekken trenger et eget åpent felt. Unavngitt elvedekorasjon har ingen bekreftet konkret identitet. Kildetro overflateforbedring er mulig, men en ny arkitektur ville være en tolkning. Ikke kall denne identiteten avklart som Tower2.

## Råmastere levert til integrasjon

Ti valgte mastere dekker 17 ruter: tre landemerker, tre kartforekomster av hjelmen, seks kroikoner, to pekere, den aktive `mi.c/009`-hjelmen, inventarsøylen `ki.cel/026` og gullsekken `ki.cel/037`. Samme hjelm er gjenbrukt for fire ruter; samme innsatssekk er gjenbrukt for fem ruter. Alle har egne `asset-*.json`-records i kunstmappens rot med kilde, prompt og `review_status: reviewed_for_runtime` etter visuell kontroll av motivet. Dette betyr klare til pakking og spillkontroll, ikke at runtime eller publisering allerede er verifisert.

Masterne er urørte kopier av resultater fra den innebygde bildegeneratoren. `art-review.json` inneholder SHA-256, dimensjoner, alfagrenser, kontroll av ekte RGBA-transparens og bekreftelse på at råfilene er byteidentiske med generatororiginalen. Promptene ligger under `prompts/`; kildeuttakene ligger under `references/` og `research/inventory/references/`.

- Highwood bruker `raw/map-landmarks/000-v2.png`, der bannere uten originalgrunnlag er fjernet. Første revisjon er bevart, men velges ikke av noen record.
- Tellersekken bruker `raw/scene-icons/counter-sack-v2.png`, der en ekstra knott er fjernet. Første revisjon er bevart, men velges ikke av noen record.
- `mi.c/009` bruker hjelmlegemet uten den palettstyrte kanten. Recorden har nå `preserve_indices: [19,31]` slik at originalens mørke ytterkant og pulsering bevares i renderer.
- Tellersekkens variable gulltekst tegnes ved (282,14). Integrasjon må verne minst verdensrektangelet `[281,12,302,24]` mot HD-overtegning. Tall og ordet GOLD ved innsatssekkene ligger utenfor ikonutsnittene.
- `ki.cel/026` beholder én smal, flutete steinsøyle med vinranke, ikke en bred ramme. `ki.cel/037` beholder skrå sekkemunn øverst til venstre og slapp sekk nedover mot høyre, med mynter bare i åpningen.

Pakking, palettkontroll, gullfeltvern, sammenligning i faktisk spill, aktivering og publisering utføres av integrasjonsagenten. Den konkrete identiteten til elvedekorasjon 004 er fortsatt ubekreftet; råmasteren forbedrer bare materialene innen den originale formen.

## Fullstendig statisk MI-omfang

Den avsluttende gjennomgangen av de 55 tidligere ukoblede KI-/MI-rutene fant 26 flere statiske objektruter etter den allerede planlagte MI009. De skal med i ikonleveransen: MI000..008 ridderhjelmer, MI010..014 Gem of Seeing, MI015..018 Hawk-målmarkører, MI020/031 små trilitter, MI033/042 gravkors og MI043..046 de fire statiske Math-padde-kartmarkørene. Med MI009 blir dette 27 MI-ruter. `static-mi-scope.json` angir hver nøkkel, hvor den brukes, originalkodens valg og gjenbruksmulighet. Resten av de 55 er ti tekst-/rammedeler, ni rene valgkonturer, ett meldingspanel og åtte drageanimasjonsruter. Summen er 27 +10 +9 +1 +8 =55. De tomme MI019/029 var ikke med i de 55.

Gem of Seeing er en krystallkule, ikke en hånd eller hjelmstatus. [Originalmanualens Gem of Seeing-avsnitt](https://www.abandonwaredos.com/docawd.php?idg=957&sf=moonstone_manual.txt&sg=Moonstone%3A+A+Hard+Days+Knight&st=manual) sier at ridderens kartikon byttes til en kule som kan brukes over hi for å se skatten. Kodevalget fra inventargjenstand2 til flagg08e7ae og deretterMI010..014 bekrefter sammenhengen. Den femte sokkelen er olivengrønn, selv om den femte hjelmen er mørk plomme. Kulens mørkebrune indeks19 er en intern hals ved y6,x2..5 og skal ikke vernes som bakgrunn eller ytterkant.

Scroll of the Hawk gir valg av teleporteringssted ifølge [samme originalmanual](https://www.abandonwaredos.com/docawd.php?idg=957&sf=moonstone_manual.txt&sg=Moonstone%3A+A+Hard+Days+Knight&st=manual). Kodevalget fra inventargjenstand12 til flagg08e7a6 ogMI015..018 viser at den asymmetriske korsformen er målmarkøren. Formen skal beholdes; det skal ikke tegnes en hauk, et smykke eller et gravkors. De fire kroppsfargene er blå, gul/oransje, grønn og rød.

Ni nye råmastere forMI010..018 er visuelt kontrollert mot hver sin fullstendige originalreferanse og klare til pakking. `raw/mi.c/010.png` er den runde cyan kulen på blå sokkel;011..014 er fargevarianter som bare bytter sokkelen. `raw/mi.c/015.png` er den nøkterne, asymmetriske målformen;016..018 er kroppsfargevarianter. Alle ni bruker `preserve_indices: [31]`, så den levende originalpulsen tegnes separat. Originalreferansene har kun0/31 gjort transparente, med opprinnelig8x10-plassering bevart.

`mi-extra-art-review.json` dokumenterer ekte RGBA-alfa, SHA-256 og at alle ni råfiler er urørte kopier av generatorutdata. Ett forkastet kuleforsøk er bevart som010-v1-rejected: det fulgte pikseltrappene bokstavelig og ble et glasskors. Det ble ikke brukt som referanse for den korrigerte kulen eller valgt av noen asset-record. Pakking, palettvern, faktisk spillvisning og publisering må kontrolleres av integrasjonsagenten før levering.

## Rettet klassifisering av paddemarkørene

MI043..046 er fire statiske kartmarkører for riddere som Math har forvandlet til padder. De er ikke fire animasjonsruter og skal med nå. Originalkoden tester ridderens forvandlingsfelt ved +$52 i 0aab38 og legger 43 til ridderens fargevariant i 0aab3e før markøren tegnes i 0aab4a. Den samme 10x12-formen brukes med blått, gult/oransje, grønt eller rødt felt på kroppen. De fire eksisterende fargede paddemasterne kan derfor gjenbrukes med egne MI-kildekontrakter. Inventoryagenten håndterer recordkoblingene og routeaudit kildekontraktene. Denne dokumentrettingen endrer ingen råbilder eller records.

KI045..049 er allerede aktive PNG-/poseruter i `web/hd/manifest.json`, kontrollert direkte i manifestet. De trenger ingen ny ikonmetadata og legges ikke til som manglende ruter i denne statiske MI-kompletteringen.
