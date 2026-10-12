# Tester

Nettlesertestene ligger i `tests/nettleser/`. De styrer nettsiden (`web/build/moonstone.html`)
i Chromium med Playwright, trykker taster og leser spillets minne gjennom `window.moonDebug`,
og skriver en linje per sjekk: `OK   ...` eller `FEIL ...`. Nettspillet testes med flere sider
i samme nettleser mot en lokal PeerJS-server og en lokal MQTT-megler i stedet for PeerJS Cloud
og HiveMQ.

## Slik kjores de

```
tests/kjor.sh                 # alle testene
tests/kjor.sh lag1 ver1 test35
```

`kjor.sh` bygger nettsiden (`make -C port web`) og `port/moonstone-headless` om de mangler,
installerer serverne i `tests/nettleser/servere` med npm første gang, starter en HTTP-server
(python3), PeerJS og MQTT på 127.0.0.1, kjører testene og skriver OK eller FEIL per test.
Serverne stoppes etterpå. Logger, skjermbilder og tilstander havner i en midlertidig mappe
som skrives ut (eller i `MOONSTONE_UT`).

Valg (miljøvariabler):

| Variabel | Standard | Hva |
|---|---|---|
| `CHROME` | Playwrights Chromium | Valgfri sti til installert Chrome/Chromium |
| `SIDE` | `web/build/moonstone.html` | nettsiden som testes (f.eks. en nedlastet utgave fra Pages) |
| `MOONSTONE_PORT` | 8765 | HTTP-serveren |
| `PEER_PORT` | 9000 | PeerJS |
| `MQTT_PORT` | 8883 | MQTT over WebSocket |
| `TIDSGRENSE` | 900 | sekunder per test |
| `MOONSTONE_UT` | ny mappe i /tmp | logger, skjermbilder, tilstander |
| `MOONSTONE_GAMLE` | (ingen) | mappe med lagringer fra eldre versjoner til `lag1` |

En test kan også kjøres for seg når serverne går: `node tests/nettleser/test35.js --port 8765`
(eller `--url http://...`, og `--ut MAPPE` for skjermbildene). `MOONSTONE_PEER` og
`MOONSTONE_MQTT` sier hvor serverne er (standard `127.0.0.1:9000` og `ws://127.0.0.1:8883/mqtt`).
En test gir exit 1 når en sjekk feiler eller testen stopper.

## Det som trengs

- Node 18 eller nyere og Playwright med Chromium: `npm install -g playwright` og
  `npx playwright install chromium` (i skymiljøet ligger Playwright i `/opt/node-tools/node_modules`,
  og `kjor.sh` finner det selv).
- python3 (HTTP-serveren) og npm (serverne).
- Emscripten for å bygge nettsiden, og en C-kompilator for `moonstone-headless`.

Chromium kjører uten skjermkort med SwiftShader (`--use-angle=swiftshader`). Det er tregt, så
testene venter i sekunder mellom trykkene: menyene tegnes på nytt i opptil et sekund, og en kamp
laster i om lag åtte.

## Tilstander

`lag1` trenger to lagringer. De lages med `moonstone-headless` i testens mappe første gang
(oppskriftene står i `felles.js`) og sjekkes ikke inn:

- `kart_ny.sav`: et spill på kartet, lagret i bilde 2000 (`--online-meny`, Esc i 100, ned i 700,
  760 og 820, fire i 880 og 1300, Return i 1500).
- `ny.sav`: samme vei, lagret i bilde 1600, like før kartet.

To sjekker trenger lagringer fra eldre versjoner som ikke kan lages på nytt: `kamp6.sav`
(versjon 4) og `gml.sav` (versjon 13 fra PC, 64 bit). Legg dem i mappen `MOONSTONE_GAMLE` for å
ta dem med; ellers hopper testen over dem med en melding.

## Testene

| Test | Hva den sjekker | Tid |
|---|---|---|
| `test12` | Flyten uten startside: introen, ett trykk slår på lyden og hopper over, navnet fra menyen, Host Game, Public og Copy Link. Kari blir med via lenken, Ola via den offentlige listen med musen. Tre i Turns, sjekksummer, og gjestene havner i introen når verten lukker. | 2 min |
| `test17` | Mus i menyene: klikk på radene, hånd over et valg, Enter og mellomrom, Mode Turns og Separate, Back, klikk utenfor radene, Practice med klikk. | 1 min |
| `test26` | Separate: verten og Kari spiller hvert sitt spill og ser hverandre på kartet (plass, navn, farge), Kari går og verten ser det, verten lukker og Kari spiller videre alene med SIR DWAIN tilbake. | 2 min |
| `test27` | Duell i Separate: verten angriper Kari, kan ikke laste under duellen, Kari styrer sin ridder over nettet, verten slår til kampen er over, Kari tar ridderen med tilbake, sjekksummene i kampen. | 4 min |
| `test28` | Duell der Kari har sidemenyen åpen og ikke kan ta imot: ingen duell, datamaskinen styrer ridderen hennes. | 2 min |
| `test29` | Duell motsatt vei: Kari angriper verten. | 4 min |
| `test30` | Duell der verten blir stille: Kari gir opp og har ridderen sin uendret, verten får datamaskinen til å styre. Til slutt en fil inn og ut av kjernen. | 2 min |
| `test31` | Duell der Kari blir stille: verten gir opp og datamaskinen tar over. | 2 min |
| `test32` | Laste et spill fra kartet mens tittelmenyen vises: menyen og menyhintet henger ikke igjen. | 1 min |
| `test33` | Options i tittelmenyen: Keyboard og Gamepad (en falsk spillkontroller), binding av taster og knapper, Esc avbryter, oppsettet huskes, Default Controls, Online Game fra Options. | 2 min |
| `test34` | Turns med gjest: gjesten styrer menyen til Keyboard > Fire, men ingen begynner å vente på en tast, begge får forklaringen, og Default Controls fra gjesten endrer ikke verten. | 2 min |
| `test35` | Turns: hvem styrer i Select a Knight og på kartet når verten velger SIR RICHARD (rekkefølgen, ikke figuren), portrettklikk med automatisk fordeling og faste porter, statuslinjen, E avslutter turen bare for den som har den. | 2 min |
| `test36` | Turns med tre: Copy Link og F10 fra en gjest, gjest som laster på nytt, kopi av fanen, fane som forsvinner og kommer tilbake på samme plass, nummer uten hull, og en side som stopper mens en retning holdes. | 4 min |
| `lag1` | Lagringene: ingen autolagring i tittelmenyen, autolagring når fanen skjules, nedlasting som PC-versjonen laster, Fortsett etter omlasting, en PC-lagring inn på nettet, meldinger for feil fil og gamle lagringer. | 1 min |
| `ver1` | Versjonssjekk i nettspill: romlisten viser bare rom med samme lagringsformat, og en gjest med et annet format får beskjed og blir ikke stående og vente. | 2 min |
| `fullt2` | Fullt rom: verten og tre gjester, en femte får beskjed om at rommet er fullt uten at spillet hans startes på nytt. | 3 min |
| `start1` | HD som standard, ett trykk over introen, alle fire portrettklikk, Enter/mellomrom, lagret Original-valg og mobiltrykk. | 2 min |
| `m1` | Mobil (berøring, stående telefon): trykk hopper over introen, styrekorset flytter pilen, Fire går til kartet. | 1 min |
| `m2` | Mobil: spillets grafikk på siden, sidemenyen med trykk, navnet til ridderen med tekstfelt (æøå blir ae, o, a), valgene på kartet som knapper med styrekorset og Fire. | 1 min |

Testene heter som de het da de ble laget (test12 til test36, lag1, ver1 og så videre), så de
stemmer med `log.md`.
