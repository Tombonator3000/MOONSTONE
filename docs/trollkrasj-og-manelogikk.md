# Undersøkelse av trollkrasj og månelogikk

Dette er gjennomføringsplanen for B01 og måneundersøkelsen i
[funnregisteret](kuttet-innhold-og-feil.md). Kodekontrollen er gjort mot
main `f3103ebb` 12. oktober 2026. Testene nedenfor er ennå ikke implementert
eller kjørt. Trollkrasjet er rapportert, og spillvirkningene av månen må måles
før eventuelle rettinger eller nye regler innføres.

**Status 12. oktober, kveld:** begge delene er kjørt. Resultatene står i
[undersokelser/b01-troll.md](undersokelser/b01-troll.md) og
[undersokelser/maane.md](undersokelser/maane.md). Verktøyene fikk navnene
`tools/b01_troll.py`, `tools/maane.py` og `tools/maane_kamp.py` i stedet for
navnene foreslått under. Kort: denne utgaven slipper bare ut ett troll om gangen,
og med to tvunget fram låser kampen seg (ikke et CPU-krasj). Månen skifter hvert
fjerde døgn, ingen monsterkode leser den, og manualens regler finnes nå som valg.

## Bekreftet støtte i porten

| Funksjon | Kilde og betydning |
| --- | --- |
| Lagring, lasting, inndata, minnedumper og PNG-bilder uten vindu | [main.c](../port/src/main.c) har `--save-state`, `--load-state`, `--press`, `--dump`, `--shot-every` og `--shot-dir`. |
| Instruksjonsobservasjon | [hooks.c](../port/src/hooks.c) har `hook_trace`. En begrenset CPU-/stacklogger må bygges rundt denne. Intersepterte resload-kall returnerer før callbacken og trenger egen hendelseslogging. |
| C-erstatninger | [decomp.c](../port/src/decomp/decomp.c) registrerer joystickrutinene `$082008` og `$081F92`. Kampmotoren er ikke C-erstattet av disse. |
| Avgrensning av `--nohooks` | C-erstatningene slås av. Lapper registrert med `hooks_register_patch` kjører fortsatt og styres av tilstanden. |
| Eksisterende paritetsprøve | [check_hooks.py](../tools/check_hooks.py) sammenligner chipminne og sluttbilde med og uten C-hooks, men bruker en fast meny-/kartrute. Den tar ikke en egen B01-lagring eller avspillingsfil. |
| Versjonert maskinlagring | [state.c](../port/src/state.c) bruker `MOONSAV2` med separate deler for blant annet minne, CPU, brikker og WHDLoad. Kompatibiliteten må kontrolleres før gjenbruk på andre spill-/slaveversjoner. |

Bildetelling må normaliseres i testverktøyet: `--press` bruker absolutt
`M.frame` før bildet kjøres. `--dump` bruker absolutt `M.frame` etter bildet,
mens `--save-state` og skjermbildenes intervall/navn bruker kjøringens relative
bildetall. En avspilling etter lasting må registrere startverdien og konvertere
relative inndata til absolutte bilder. Logg begge tallene ved kontrollpunkter.

`run_headless` returnerer også 0 etter `M.aborted`. Testen må kontrollere
stoppmeldingen, oppnådd bildetall og forventede artefakter i tillegg til
prosessens returkode.

## Gjenskap B01

Foreslått nytt verktøy er `tools/check_troll_repro.py`. Navnet beskriver en
planlagt fil, ikke et eksisterende testprogram.

1. Lag en tilstand rett før en naturlig kamp med to troll. Bevar den opprinnelige
   tilstanden uendret. Et kontrollert, innskrevet kampoppsett kan brukes til å
   finne utløseren, men merkes syntetisk til samme symptom er vist i vanlig spill.
2. Registrer SHA-256 for spillarkiv, `mog`, `program`, `Moonstone.Slave`,
   lagringen og emulatorbinæren, samt repo-commit og eventuelle lokale endringer.
   Oppgi CRC-algoritme og byteområde. Prosjektets kjente CRC-16/ARC-verdier gjelder
   de første `$1000` bytene, ikke hele filene. Ta med maskinoppsett, aktive lapper,
   spillmodus, startbilde og inndata med knapp, start og varighet.
3. Kjør samme tilstand, inndata og innstillinger med C-hooks og med `--nohooks`.
   Bruk hookrapporten til å kontrollere at C-rutinene faktisk treffes. Sammenlign
   minne og bilder ved identiske kontrollpunkter, og registrer første avvik.
   Instruksjonssporene vil naturlig være forskjellige der C erstatter 68000-kode.
4. Registrer den rapporterte utløseren: to troll vender mot hverandre og slår
   over hodet samtidig. Sammenlign med ett troll og med de to angrepene forskjøvet
   noen bilder. Bevar tilfeldighetstilstanden og reduser avspillingen til det
   korteste forløpet som gjentar symptomet.
5. Legg til en ringbuffer, eksempelvis siste 4096 instruksjoner, med PC, SR,
   D0-D7, A0-A7 og relevante USP/SSP-verdier. Ta avgrensede stackutdrag fra
   gyldig RAM uten å lese maskinregistrene som har sideeffekter. Observasjonen
   skal ikke endre emulert tilstand eller syklustall, og brukes i begge kjøringer.
6. Lagre CPU-spor, stack, siste ferdige bilde og maskinlagring ved kontrollert
   stopp. Skill CPU-feil, prosesskrasj, manglende spillprogresjon og venting på
   spillerinndata. Bruk tidsgrense på vertsprosessen og periodiske bevisfiler,
   slik at en hard heng ikke gjør hele undersøkelsen tom. Et statisk bilde eller
   en gjentatt PC er alene utilstrekkelig til å fastslå heng.

Hver kjøring skal bevare metadata, eksakte inndata, logger, kontrollpunkter og
SHA-256 for bevisfilene. Ved første avvik skal rapporten vise begge tilstander
og det siste like kontrollpunktet. Manglende reproduksjon rapporteres med
forsøkt scenario og varighet; det betyr ikke at feilen er avkreftet.

### Tolkning av resultatene

| Observasjon | Forsvarlig konklusjon |
| --- | --- |
| Samme symptom med og uten C-hooks | Feilen kan ligge i en felles kodevei, emulatoren, WHDLoad eller øvrige lapper. Dette beviser ikke feil på original maskinvare. |
| Avvik bare med C-hooks | Undersøk første avvik i inndata, returverdier og syklustall før kampkoden får skylden. |
| Samtidige slag utløser symptomet, forskjøvede slag gjør det ikke | Samtidigheten er en kandidat til utløser. Kodeårsaken må fortsatt vises. |
| Stackdata er ødelagt | Finn den konkrete skrivingen og stackgrensen før årsaken kalles stack overflow. |
| Ulik oppførsel mellom WHDLoad-versjoner | Gjenta fra kompatibel oppstart og knytt forskjellen til en konkret patch. |

WHDLoad-sammenligningen er et eget forsøk. Innebygd slave v1.4 og dokumentert
v1.6 har ulike endringer, blant annet i tilfeldig initialisering fra v1.5.
Ikke flytt lagringer ukritisk mellom versjonene. Registrer binæridentitet og
initialbetingelser for hver utgave, og gjenta samme spillforløp. Versjonsloggen
navngir ikke B01 som rettet. Spisemanøveren og stack overflow er ikke etablerte
forklaringer på det rapporterte samtidige slaget.

## Mål månelogikken

Foreslått nytt verktøy er `tools/check_moon_logic.py`. Finn først lesere og
skrivere av dagteller, tur og faseindeks. Det kjente visningssporet er
`$082B8C`, med tabellen `45,46,47,48,49,48,47,46` ved `$08F147` og
`ki.cel/045..049`. Adressene gjelder den undersøkte utgaven. Tabellen viser
fasebilder, men identifiserer ikke alene dagtelleren eller spillvirkningene.

Logg dag, aktiv ridder/tur, faseindeks, KI-bilde, gjeldende HP, maks-HP,
kampverdier, gjenstander og sykdomsstatus. Dokumenter adresse, datastørrelse og
betydning for hver variabel etter at kodebruken er identifisert. Ikke fyll inn
ukjente adresser som antakelser.

| Forsøk | Kontroll og måling |
| --- | --- |
| Hele faseomløpet | Følg vanlig turavslutning gjennom minst ett helt omløp, helst to. Skill riddertur fra spilldøgn, også med flere riddere. Manualens forventning er tre døgn per fasetrinn, åtte trinn og 24 døgn per omløp. Logg faktisk overgang og tegnet KI-bilde. |
| Ratmen | Bruk samme kampoppsett, spillerverdier, utstyr, terreng og tilfeldighetstilstand ved hver fase. Mål fiendens HP/styrke, skade per treff og angrepsintervall. Skill voksende og avtakende måne også når grafikken er den samme. |
| Moonstone | Bruk redusert gjeldende HP, slik at dobling av gjeldende HP kan skilles fra endret maks-HP. Sammenlign uten stein, med matchende stein og med ikke-matchende stein ved samme fase. Logg før og etter den identifiserte aktiveringen, eventuell grense og varighet. |
| Sykdom | Mål smitte, periodisk virkning, varighet og helbredelse i egne forsøk. Bruk flere dokumenterte tilfeldighetstilstander for smittesannsynlighet. Test faseavhengighet separat fra skade og øvrige Ratmen-verdier. |

En kontrollert endring av fasetilstanden skal logges som et testinngrep og bare
brukes etter at feltet er identifisert. Den naturlige omløpsprøven skal også
gjennomføres, slik at en kunstig fase ikke skjuler andre dagavhengige verdier.

Resultatrapporten skal skille tre forhold:

| Manualens påstand | Målt originaloppførsel | Ønsket endring |
| --- | --- | --- |
| Kildeutsagn med relevant avgrensning | Spill-/slaveidentitet, måleverdier og bevisfiler | Eget forslag med regler og begrunnelse, dersom en endring ønskes |

Avvik mellom manualen og én utgave er et måleresultat. Det etablerer ikke alene
at innhold ble kuttet, eller at nye multiplikatorer er en restaurering. Sykdom
som bevisst er fjernet i en annen port er heller ikke fasit for originalen.

## Fullføringskrav

- B01 har en gjentakbar avspilling med dokumentert symptom, eller en presis
  rapport om hvilke forsøk som ikke gjenskapte det. Årsak merkes uavklart til
  sporene viser den.
- Faseomløpet er målt og koblet til KI-bildet. Ratmen, Moonstone og sykdom har
  separate kontroller med identifiserte variabler og bevart forsøksgrunnlag.
- Eventuelle spillendringer får egne paritets-/regresjonsprøver og en tydelig
  beskrivelse av om de retter et påvist avvik eller innfører nye regler.

Historiske kildeutsagn, manualen og WHDLoad-loggen er samlet med lenker i
[funnregisteret](kuttet-innhold-og-feil.md#kilder-og-sporbarhet).
