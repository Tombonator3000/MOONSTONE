# Moonstone: decomp og port til PC og nettleser

Arbeidsprosjekt for *Moonstone: A Hard Days Knight* (Mindscape 1991, Amiga), fra
CD32-utgaven i `Moonstonecd32-AMIGA.zip`. Målet er å spille det på PC og i nettleseren,
også sammen over nettet, og å lære hvordan spillet er bygget, slik at vi kan endre kode
og grafikk og på sikt bytte til grafikk i høy oppløsning.

Porten kjører originalkoden til spillet på en emulert Amiga 500 skrevet i C. Spillets
regler og turer er derfor helt som før. Funksjoner i spillet kan byttes ut med C en og
en (decomp), og hver erstatning sjekkes mot originalen.

## Spille i nettleseren

`web/build/moonstone.html` er hele spillet i én fil: emulatoren som WebAssembly, bildet
med three.js og lyden med WebAudio. Den lages med `make -C port web` og legges ut på
GitHub Pages av Actions. Det finnes ingen egen startside: spillet starter med introen
med en gang siden er lastet, og alt annet velges i spillets egen tittelmeny.

Nettleseren slipper ikke ut lyd før du har trykket på noe, så det første trykket slår på
lyden. Deretter hopper Esc, fire, Enter, mellomrom eller et trykk på skjermen over
introen. Det kan ta et par sekunder før den slutter, for introen gjør ferdig overgangen
den holder på med.

Spillfilen (`Moonstonecd32-AMIGA.zip` fra repoet) er bygget inn i siden. En annen
spillfil, f.eks. «Moonstone CD32.iso», kan velges i menyen (Home eller knappen oppe til
høyre) under «Spillfil og egne filer». Der ligger også bilde og lyd, lagring og
HD-grafikk.

### GitHub Pages

Når Pages er slått på, ligger spillet på **https://tombonator3000.github.io/MOONSTONE/**.
Hver push til `main` bygger siden på nytt og legger den ut (jobben `pages` i
`.github/workflows/bygg.yml`), med spillfilen innebygd.

Slik slås det på (bare eieren av repoet kan gjøre det):

1. Pages krever at repoet er offentlig, eller et betalt GitHub-abonnement.
   Offentlig: Settings, General, nederst under «Danger Zone»: «Change repository
   visibility» til Public.
2. Settings, Pages, «Build and deployment»: Source = **GitHub Actions**.
3. Actions, «Bygg», «Run workflow» på `main` (eller push noe til `main`).

Selve siden er alltid offentlig, også om repoet er privat med betalt abonnement.

### Nettspill

Nettspillet ligger i spillets egen tittelmeny, under **Online Game**, tegnet med
spillets font og pil:

- **Host Game** lager et rom. Siden viser romkoden og navnene til de som er med,
  med spillernummer (1 er den som velger ridder først). **Copy Link** kopierer
  invitasjonslenken, og **Public** legger rommet i listen over offentlige rom.
- **Join Game** viser de offentlige rommene. Velg ett, eller **Enter Code** for å
  skrive inn en romkode eller lime inn en lenke.
- **Choose Name** (eller **Name** med navnet ditt) åpner et lite felt der du skriver
  navnet de andre ser. Spør spillet om navnet første gang du lager et rom eller blir
  med, om du ikke har valgt det før. Spillets font har bare engelske bokstaver, så
  æ, ø og å blir ae, o og a i menyen.
- **Back** fra romsiden setter **Players** i tittelmenyen til antallet som er med.

En invitasjonslenke åpner spillet på samme måte. Hopp over introen (her holder ett
trykk), så åpnes **Join Game** med rommet øverst og pilen på det. Trykk fire for å bli
med. Gjestene trenger ikke spillfilen. Velg så antall spillere og la hver spiller
velge ridder etter tur.

Lukker verten fanen, får gjestene beskjed og havner i introen igjen. Har verten
forsvunnet uten å si fra (tapt nett), gir gjestene opp etter 20 sekunder uten svar.

Menyvalget finnes bare på nettsiden, siden PC-versjonen ikke har nettspill
(`moonstone-headless --online-meny` viser det for testing).

Verten kjører spillet og styrer turene. Gjestene får hele tilstanden til maskinen når de
kobler seg til, og deretter knappetrykkene for hvert bilde, så alle kjører nøyaktig det
samme spillet. Filer spillet laster underveis, sendes med. Hvert 120. bilde sammenlignes
en sjekksum, og en gjest som har kommet ut av takt får tilstanden på nytt.

Joysticken følger turen i spillet: på kartet styrer den som har turen, og i kamp mellom
to riddere får begge sin joystick. Spiller 1 er den som velger ridder først, spiller 2
den neste osv. Verten kan endre rekkefølgen, eller bytte til faste porter, i menyen.
Bare den som har turen kan trykke tastene (mellomrom, E).

PeerJS Cloud kobler nettleserne sammen gratis, og dataene går så direkte mellom dem
(WebRTC). Offentlige rom vises i en liste via den gratis MQTT-megleren til HiveMQ hvis
verten slår på **Public**. Lagring skjer i nettleseren til verten. Begge deler er samme
oppskrift som i Guild Life.

Egen PeerJS-server eller MQTT-megler: legg `?peer=vert:port` eller `?mqtt=wss://vert/sti`
til adressen.

## Spille på Windows og Linux

Ferdige bygg ligger under **Actions** (filene `moonstone-windows` og `moonstone-linux`).
Spillfilen er bygget inn i programmet, så det trengs ingen andre filer. På Windows:
dobbeltklikk `start.bat` eller `moonstone.exe`. Windows kan si at programmet er ukjent
fordi det ikke er signert; velg «Mer informasjon» og «Kjør likevel».

Med `--game sti` bruker programmet en annen spillfil: zip-filen, ISO-en eller en mappe
med `Moonstone.Slave` og `data/`. `moonstone --help` viser alle valgene.

## Taster

| | Spiller 1 (joystick i port 2) | Spiller 2 (joystick i port 1) |
| --- | --- | --- |
| Bevegelse | piltastene | talltastaturet 8 2 4 6 (7 9 1 3 på skrå) |
| Fire | Ctrl | talltastaturet 0 |
| Spillkontroller | nummer 1 | nummer 2 |

Resten av tastaturet går til Amigaen som det er: **mellomrom** viser inventaret, **E**
avslutter turen, **Esc** hopper over introen, og du skriver navnet til ridderen. I
nettleseren hopper også fire, Enter, mellomrom og et trykk på skjermen over introen.
Mens introen går, sendes ikke Enter og mellomrom videre til spillet, for introen ser
bare på den siste tasten, og da ville de skjult Esc.
I kamp holder du fire og trykker en retning for de åtte angrepene (se manualen på ISO-en).
På spillkontrollere er A fire, B mellomrom, Start E og Back Esc, som CD32-padden.

### Mus og berøring i nettleseren

Originalspillet bruker bare joystick. Det leser musen i avbruddet sitt, men ingen del av
spillet bruker det den finner. I nettleseren er musen derfor koblet inn slik:

- **Menyene** (tittelmenyen og nettspillsidene): klikk eller trykk på et valg. Pilen
  flytter seg dit, og valget utføres. Pekeren blir en hånd over valg som kan klikkes.
  Enter og mellomrom velger også, i tillegg til fire (Ctrl).
- **I spillet** er venstre museknapp fire så lenge den holdes. Hold den og dra i en
  retning for fire og retning samtidig (angrepene i kamp). Høyre knapp og dra er bare
  retning.
- **Styrekors og knapper på skjermen** vises på mobil og nettbrett, og kan slås på for
  mus i menyen under «Bilde og lyd».

### Effekter og HD-grafikk i nettleseren

Nettsiden deler bildet i to lag: bakgrunnen spillet holder for seg selv, og det som
tegnes over den (figurer, tekst, piler). Lagt oppå hverandre er de nøyaktig
originalbildet, men hvert lag kan byttes ut eller få egne effekter. I menyen under
«Effekter» finnes skygger under figurene, uskarp bakgrunn, glød, sterkere farger og
vignett. Filteret «Glatt (Scale4x)» under «Bilde og lyd» runder av kantene i all
grafikken, med spillets egne farger. Under «HD-grafikk» kan du velge en mappe med egne bilder for figurene (også bokstavene, i `bold.f` og `Small.font`) og for
bakgrunnene (`bg/HASH.png`; «Lagre bakgrunnen som PNG» gir deg den som vises, med
riktig navn). `tools/hd_skaler.py` lager en HD-pakke automatisk av de utpakkede bildene. Se `docs/hd-grafikk.md`.

Første gang tittelmenyen vises, står det øverst at valgene kan klikkes.


| Tast | PC | Nettleser |
| --- | --- | --- |
| Meny | | Home |
| Lagre / laste tilstand | Page Up / Page Down | Page Up / Page Down |
| Bytt lagringsplass | End | End |
| Pause | Pause | Pause (alene) |
| Fullskjerm | F11 eller Alt+Enter | nettleserens egen |
| Skjermbilde | F12 | |
| Filter | Print Screen | menyen |
| Spol fremover | Home (hold) | |
| Avslutt | F10 (som i WHDLoad) | F10 |

## Status

| Del | Status |
| --- | --- |
| Emulator (C) | 68000 (Musashi), Copper, Blitter (flater, fylling, linjer), bitplan og sprites, Paula, to CIA, tastatur. Introen og hele spillet kjører. |
| WHDLoad | Slaven kjøres som på en ekte Amiga. resload-funksjonene den bruker er skrevet i C. |
| PC | SDL2 for Linux og Windows. Windows-bygget gir byte for byte samme minne som Linux (testet i Wine). |
| Nettleser | WebAssembly, three.js med filtrene skarp, rene piksler, myk og CRT, lyd, spillkontrollere, berøringsknapper, lagring i IndexedDB. Testet i Chromium. |
| Nettspill | PeerJS med opptil fire spillere, joystick etter tur, romliste via HiveMQ. Testet med to nettlesere mot en lokal PeerJS-server og MQTT-megler. |
| Grafikk | Alle bilder og figurer ut som PNG og inn igjen. Rundturen er byte for byte lik. |
| Tekster | Alle tekster ut til en fil og inn igjen (`tools/tekst.py`), også lengre enn originalen. |
| Nettspill i spillet | «Online Game» i tittelmenyen: lage rom, navnene på spillerne, kopiere lenke, offentlige rom, bli med. Testet med tre nettlesere. |
| HD-grafikk | Eksperimentelt i nettleseren: figurer kan byttes med PNG-er i høyere oppløsning. Plassering og speiling er sjekket mot emulatorbildet i kamp og på kartet. Bakgrunner gjenstår. |
| Lyd | Lydeffektene som WAV, musikken som ProTracker-moduler. |
| Disassembly | 13 775 instruksjoner og 412 funksjoner i mog, styrt av relokeringer og kodedekning. |
| Decomp | Hook-system med syklusregnskap. `les_joysticker` og `joydat_til_bits` er i C og gir samme spill som originalen. |

## Endre grafikk og lyd

```
python3 tools/gfx.py extract Moonstonecd32-AMIGA.zip assets/gfx
# rediger PNG-ene (indekserte, behold fargeindeksene)
python3 tools/gfx.py build Moonstonecd32-AMIGA.zip assets/gfx mod
port/moonstone --mod mod
```

`build` lager bare filene du har endret, og de pakkes med samme metode som spillet.
På nettsiden velger du dem i menyen under «Spillfil og egne filer». I nettspill får
gjestene dem fra verten.

```
python3 tools/lyd.py extract Moonstonecd32-AMIGA.zip assets/lyd
```

gir lydeffektene som WAV og musikken som `.mod`. Verktøyene trenger Python 3 og Pillow
(`pip install pillow`), disassembleren også capstone.

### Tekstene i spillet

```
python3 tools/tekst.py extract Moonstonecd32-AMIGA.zip tekster.txt
# endre tekstene i anførselstegnene, f.eks. 8f130 "Practice" -> "Practice Battle"
python3 tools/tekst.py check Moonstonecd32-AMIGA.zip tekster.txt
port/moonstone --mod MAPPE           # med tekster.txt i MAPPE
```

`extract` gir alle de 361 tekstene i hovedspillet med adressen der de ligger. Porten
bruker filen når spillet er lastet, så spillfilen endres ikke. Tekster kan bli lengre;
da legges de i ledig minne og pekerne rettes, og avsnitt flyttes samlet. `check` viser
hva som endres, og sier fra om en tekst blir for bred for skjermen, har tegn fonten
ikke har (æøå finnes ikke), eller ikke kan bli lengre. På nettsiden velges
`tekster.txt` i menyen under «Spillfil og egne filer», og i nettspill får gjestene den
fra verten.

### HD-grafikk (eksperimentelt)

Nettsiden kan tegne figurene med egne bilder i høyere oppløsning. Lag en mappe med
samme navn som `tools/gfx.py extract` gir, f.eks. `kn1.ob/012.png`, tegn bildene i
den størrelsen du vil, og velg mappen i menyen under «HD-grafikk». Spillet selv er
uendret; HD-bildene legges oppå der spillet tegner figuren. `--tegneliste F[:N]` i
PC-versjonen viser hvilke figurer som tegnes hvor, og `tools/hd_sjekk.py` sjekker
plasseringen. Mer i `docs/hd-grafikk.md`, og det vi vet om hvordan spillet er bygget
står i `docs/slik-er-spillet-bygget.md`.

## Decomp

```
port/moonstone-headless --headless --frames 13000 --coverage disasm/coverage.bin ...
python3 tools/disasm.py Moonstonecd32-AMIGA.zip disasm
```

gir `disasm/mog.s` og `disasm/program.s` (lages lokalt, sjekkes ikke inn) og
`disasm/functions.txt`. Navn og kommentarer settes i `disasm/symbols.txt`. Kodedekningen
legges sammen for hver kjøring, så jo mer du spiller med `--coverage`, jo mer kode blir
funnet.

Slik bytter du en funksjon ut med C:

1. Finn den i `disasm/mog.s` og gi den et navn i `disasm/symbols.txt`.
2. Skriv den i `port/src/decomp/decomp.c` med originalkoden som kommentar, og registrer
   den i `decomp_register_all()`. Husk registre, flagg og det originalen skriver på
   stakken.
3. `port/moonstone-headless --headless --frames 12500 --hook-cycles ...` viser hvor
   mange sykluser originalen bruker. C-versjonen sier det samme med `hook_cycles()`.
4. `python3 tools/check_hooks.py` kjører spillet med og uten C-versjonene og
   sammenligner minnet og bildet. Alt skal være likt.

## Bygge selv

Linux:
```
sudo apt install build-essential libsdl2-dev
make -C port              # moonstone med vindu
make -C port headless     # moonstone-headless, uten SDL, for testing
```

Spillfilen bygges inn (`port/bin2c.py` lager `port/src/spilldata.c` fra
`Moonstonecd32-AMIGA.zip`). `make -C port MED_SPILLET=nei` bygger uten; da ser programmet
etter filen i `spill/` og mappen det startes fra.

Windows fra Linux (krever mingw-w64 og SDL2-devel-2.30.8-mingw):
```
make -C port windows SDL2_MINGW=/sti/til/SDL2-2.30.8/x86_64-w64-mingw32
```

Nettleser (krever emscripten): `make -C port web` gir `web/build/moonstone.html`.

## Mappene

```
port/src/         emulatoren og PC-delen (C)
  amiga.c         minnekart, CPU og tidsstyring        custom.c   registrene og Copper
  blitter.c       Blitteren                             video.c    bitplan, sprites, farger
  paula.c         lyd                                   cia.c      tidtakere, tastatur
  whdload.c       slaven og resload-funksjonene         files.c    zip, ISO og mapper
  game.c          det vi vet om spillets data (ridderne, turen, tegnelisten)
  patch.c         lapper i spillet: tekster.txt, lengre tekster   meny.c  «Online Game» i tittelmenyen
  hooks.c         C-erstatninger og kodedekning         decomp/    funksjonene i C
  frontend.c      SDL2-vinduet                          web.c      grensesnittet til nettsiden
port/ext/musashi  68000-kjernen (MIT)
web/src/          nettsiden: core, render (three.js), audio, input, store, net (PeerJS), rooms (MQTT), app
web/vendor/       three.js, PeerJS og MQTT.js (MIT)
tools/            gfx.py, lyd.py, tekst.py, disasm.py, check_hooks.py, hd_sjekk.py, moonfiles.py
disasm/           symbols.txt, functions.txt, coverage.bin
docs/             hvordan spillet er bygget, HD-grafikk
windows/          start.bat og LES_MEG.txt til Windows-pakken
```

## Lisenser

Egen kode i prosjektet er laget for Tom. Musashi er MIT (Karl Stenerud). three.js,
PeerJS og MQTT.js er MIT (lisensene ligger i `web/vendor`). SDL2 er zlib-lisens.
Moonstone tilhører Mindscape og rettighetshaverne. Spillfilen ligger i repoet fordi
eieren la den der; Moonstone regnes som abandonware, men det er ingen juridisk lisens.
WHDLoad-slaven er laget av Wepl.
