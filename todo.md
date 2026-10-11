# todo.md

## Neste
- [ ] HD-bakgrunner etter filnavn (bg1a.PIV/0.png) i tillegg til hash, for bildene som vises som de er.
- [ ] Valgene paa kartet i PC-versjonen: LB, RB, X og Y velger 1-4 i dag; mangler valg 5-9 og en liste paa skjermen. Nevn det i windows/LES_MEG.txt.
- [ ] Options paa mobil: oppsett av styrekorset og knappene (storrelse, venstrehendt).
- [ ] Options-siden også i PC-versjonen (SDL): taster og knapper i spillets meny. PC slår ikke på menylappen i dag.
- [ ] Options: velge spillkontroller nummer 2 og hvilken kontroller som er spiller 1.
- [ ] Duell: la den som blir angrepet få se et kort varsel før kampen («Tom utfordrer deg») i spillets egen stil, ikke bare i statuslinjen.
- [ ] Hver for seg, steg 4: motstanderen er opptatt (by, kamp), to utfordrer hverandre samtidig, årstidene går hver for seg.
- [ ] Hver for seg: vise navnet til spilleren (ikke bare riddernavnet) når man står ved siden av, og en melding når noen kommer inn på kartet.
- [ ] Veien mot en native port (brukeren sa ja 2026-10-02): 1) grafikken ut i lag (bakgrunn og forgrunn er ferdig; gjenstår menyrammer i HD og bakgrunner som endres litt), 2) logikken til C del for del (kamp og kart først) med check_hooks, 3) fjerne 68000 og Amiga-brikkene når originalkoden ikke kjører lenger.
- [ ] HD-bilder med fargeindekser (PNG med palett) som får fargene fra skjermen.
- [ ] HD-bakgrunner som tåler små endringer i bakgrunnskopien (legg forskjellene over).
- [ ] Effektene og HD-laget også i PC-versjonen: trenger en PNG-leser (png.c kan bare skrive) og HD-tegningen skrevet i C (SDL_Renderer holder).
- [ ] Prøve «Run workflow» for hånd én gang (rettelsen a998217 er på main, men ikke prøvd).
- [ ] HD-grafikk: bakgrunner i HD (PIV, og .t for kampene), fargeeffekter (fading) på HD-bildene, andre tegnerutiner enn tegn_figur (tekst, menyer).
- [ ] Lage en liten HD-pakke som eksempel (f.eks. ridderne i fire ganger størrelse).
- [ ] Finne ut hvordan .t-filene bygger kampbakgrunnene.
- [ ] Spille gjennom hele spillet (butikker, taverna, Waterdeep, dragen, vokteren, Stonehenge, Game Over) med --coverage, og lage coverage.bin og functions.txt på nytt (de er fra 2. oktober).
- [ ] Assembler-utgave av disassemblyen som bygger byte for byte like filer (vasm).
- [ ] Teste nettspill (også «Online Game» i tittelmenyen) mot PeerJS Cloud og HiveMQ fra en vanlig nettleser (proxyen i skymiljøet stopper WebSocket; lokalt testet med egne servere).
- [ ] Teste den nye oppstarten på en ekte mobil (lyd ved første trykk, også med lydløs-bryteren på iPhone, trykk på skjermen hopper over introen, navnefeltet med skjermtastatur).
- [ ] Klikk i menyene også i PC-versjonen (meny_row_at finnes; PC slår ikke på menylappen i dag).
- [ ] Mus på andre skjermer enn tittelmenyen: velge ridder, butikker og inventar med klikk (krever å finne valgvariablene for hver skjerm).
- [ ] Teste moonstone.exe på ekte Windows.
- [ ] Nettspill over et ekte nett med to maskiner: hvor mye forsinkelse gjesten og forsvareren i en duell merker i kamp, og om bufferen på tre bilder bør justeres.

## HD: kodeendringer så bildene i docs/hd-bestilling-chatgpt.md blir brukt
- [ ] Lasteren (render.js lastHdPakke) skal bare godta NAVN/NNN og bg/HHHHHHHH og si fra om resten (i dag tar den alt, ca 4 MB per ubrukt bilde).
- [ ] tools/hd_skaler.py skal hoppe over bildemappene (PIV) og test/, bare figurmapper og bg.
- [ ] HD-pakken skal huskes (IndexedDB) og kunne være en zip.
- [ ] --lag-dump skal lage mappen eller si fra, og prøve igjen når en bakgrunn ikke ble skrevet.
- [ ] Et skript som spiller gjennom spillet med --lag-dump og knytter hver bakgrunnshash til et skjermnavn.
- [ ] Sjekke CEL-navnene med --tegneliste (sti foran?) og om MAX_CELS glemmer filer som fortsatt tegnes.
- [ ] Inntoning av HD-bakgrunnen første gang den vises (render.js lysMaks).
- [ ] Rette docs/hd-grafikk.md (knappens navn, skala høyst 4) og grafikklisten (hen1.p = bg5.piv, Klift1.CEL = hen1.c).

## Fra gjennomgangen 2026-10-11 (docs/hva-mangler.md)
- [ ] Separate: hverKart() er sann hele spillet (hver.c setter H.kart = 0 bare i tittelmenyen), så en spiller i by eller monsterkamp sier ja til dueller automatisk.
- [ ] Turns: gjesten kan ikke lagre, og mister kopien når verten forsvinner.
- [ ] Trykk og klikk i inventar, by, butikker og Select Knight gir fire der spillets peker står ($098092/$098094), ikke der man trykker.
- [ ] Reserve når WebGL-konteksten mistes (svart skjerm på mobil).
- [ ] Mobil: fullskjerm, manifest for hjemskjermen og Wake Lock.
- [ ] Utgivelser for PC (GitHub Releases) i stedet for Actions-artefakter, og krav (libSDL2, glibc 2.34) i README.
- [ ] PC: innstillinger i spillet (volum, beskjeder som vises i fullskjerm), spiller 2 uten talltastatur. --online-meny blir stående på «Creating Room...».
- [ ] Nettspill på PC, eller et vedtak om å la det være.
- [ ] Testene (test26-36, mus, mobil, Options) og tilstandene de bruker inn i repoet, og check_hooks.py i CI.
- [ ] CI: actions på Node 20 er utfaset.
- [ ] Separate: et rom som forsvinner kan ikke samles igjen, og en død forbindelse blir stående som ridder på kartet.
- [ ] Et lagret Turns-spill fordeler ridderne etter rekkefølgen gjestene kommer inn i.
- [ ] Fast test av sluttscenen. --skriv leser heks uten 0x som 0 uten melding.
- [ ] Rette memory.md (STATE_VERSION 8) og README (mappen spill/).

## Ferdig
- [x] Tur for tur: en gjest med skjult fane fjernes etter ett minutt (verten får beskjed i chatten).
- [x] Sluttscenen kjennes igjen på nettsiden (\$080190 bit 7) og hoppes ikke over av et trykk.
- [x] Lagringer som tåler nye versjoner (MOONSAV2 med deler og standardverdier), går mellom PC og nett, forklarer hvorfor de avvises, automatisk lagring (nett og PC), eksport og import, PC-lagring i brukermappen (atomisk, UTF-8 på Windows).
- [x] Nettspill: lagringsformatet sendes med i 'hei' og i romlisten; en gjest med annen versjon får beskjed, og en gjest som ikke kan laste tilstanden, går ut med grunnen.
- [x] Bakgrunnsmusikken i hele spillet fjernet igjen (eieren ville ikke ha den).
- [x] Lyden startes i selve trykket på mobil og følger ikke lydløs-bryteren på iPhone. (Bakgrunnsmusikken i hele spillet ble fjernet igjen 2026-10-11 etter ønske fra eieren.)
- [x] Turns testet headless: beskyttelsesrullen styres av den angrepne (og kampen unngås når den brukes), og når datamaskinens ridder angriper, styrer den angrepnes spiller ridderen med port 2.
- [x] Nettspill tur for tur: joysticken følger rekkefølgen ridderne ble valgt i (ikke figuren), bare den som velger styrer Select a Knight og navnet, møtet mellom to riddere gir portene til riktig spiller (rullen, kampen, plyndringen), Players settes opp til antallet i rommet, og korte trykk fra nettet blir ikke borte.
- [x] Mobil i spillets menyer: valgene paa kartet som knapper (trykk, styrekors og Fire, Enter), navnet til ridderen med tekstfelt. Sidemenyen, knappene og meldingene i spillets stil (font, pil, logo og nattehimmel fra spillfilen). Bryter mellom HD og original grafikk. docs/grafikkliste.md og .csv over all grafikken.
- [x] Duell: beskyttelsesrullen ($080C1A) og inventaret etterpå styres av forsvareren (port 1 flyttes til port 2 mens spillet venter).
- [x] Options i tittelmenyen (nettsiden): Online Game, Keyboard (fire og bevegelse for begge spillerne), Gamepad (fire, inventar, Pass, Esc), Default Controls. Lagres i nettleseren. Korte fire-trykk mens menyen tegnes, blir husket.
- [x] Flerspiller «Hver for seg» steg 3: dueller over nettet (direkte forbindelse, den andre får maskinen og styrer port 1, tar ridderen med tilbake), hele ridderen sendes, datamaskinen tar over om den andre ikke kan.
- [x] Flerspiller «Hver for seg» steg 1 og 2: Mode Separate i Online Game, alle spiller sitt eget spill, de andre vises på kartet og flytter seg mens du har turen, turene deres hoppes over, kamp mot dem styres foreløpig av datamaskinen.
- [x] Varige HD-figurer (står så lenge forgrunnen er uendret), HD-tekst via bold.f og Small.font, filteret Glatt (Scale4x), tools/hd_skaler.py.
- [x] Lagrenderer: bakgrunn og forgrunn fra spillets egen bakgrunnskopi, HD-bakgrunner etter hash, effekter (skygger, uskarp bakgrunn, glød, farger, vignett), HD-bilder tones med paletten.
- [x] Mus og berøring i spillets menyer (klikk paa valg, Enter), fire og retning med musen i spillet, jevnere lyd, tegning bare ved nye bilder.
- [x] Ingen startside: nettsiden starter i introen, som kan hoppes over, og nettspill og navn velges i spillets tittelmeny.
- [x] Spillfilen bygget inn i programmene og nettsiden; startsiden uten filvalg.
- [x] Spillbart på GitHub Pages: https://tombonator3000.github.io/MOONSTONE/
- [x] Navnene på spillerne i romsiden i spillets meny.
- [x] Tekstverktøy: tools/tekst.py og tekster.txt i porten, også lengre tekster og avsnitt.
- [x] «Online Game» i spillets tittelmeny: Host Game, Join Game, Copy Invite Link, Public Room, Enter Code.
- [x] HD-lag for figurene i nettleseren: tegneliste fra tegn_figur, speiling, klynger, tools/hd_sjekk.py.
- [x] GitHub Actions for Linux, Windows og nettsiden, med Pages-jobb.
- [x] Verktøy: bilder og figurer som PNG (rundtur byte for byte lik), lyder som WAV, musikk som .mod.
- [x] Disassembly av program og mog med relokeringer, kodedekning og symboler.
- [x] Hook-system med syklusregnskap og check_hooks.py. Første funksjoner i C (joystick).
- [x] Joystick etter tur i nettspill (game.c).
- [x] PC-frontend med SDL2 (vindu, lyd, tastatur, joystick, spillkontrollere, lagring). Windows-bygg med MinGW.
- [x] Nettleserversjon: WASM-kjerne, visning med three.js, WebAudio, IndexedDB.
- [x] Nettspill: PeerJS (vert og opptil tre gjester), invitasjonslenke, romliste via HiveMQ.
- [x] Pakket ut ISO-en og funnet ut hvordan WHDLoad-slaven starter spillet.
- [x] Emulatorkjerne: 68000, Copper, Blitter, bitplan og sprites, Paula, CIA, WHDLoad-funksjoner.
- [x] Introen og tittelmenyen kjører med grafikk og lyd.

## HD-integrasjon, 11. oktober 2026
- [x] Nytegne kart, byer og kro; aktivere tre bevarte introbakgrunner med kildevalidering og beskyttet originalforgrunn.
- [x] HD-logo, 142 konturglyfer, 20 faste menytekster og seks separate kartlandemerker; Original-valget bevares.
- [x] Kontrollere stor/liten font i tittel og inventar, naturlig intro/kart, PIV-fixturer og faktisk HTML-menys HD-bryter.
- [x] Legge produserte råbilder, revisjoner, prompter og selvstendig original-/fotokatalog i repoet.
- [x] Aktivere48 kildevaliderte standardbilder i nettspillet uten manuelt mappevalg.
- [x] Beholde Original-valg og egen mappeimport, avbryte lasting sikkert og begrense bakgrunnscachen.
- [x] Kontrollere auto-HD i tittel/Practice og71 gangbilder samt lasting/feil/gjenoppretting i faktisk HTML.
- [ ] Fullføre nytegning og dokumenterte feil i resterende figurruter, palettvarianter og PIV-fliser før videre spillaktivering.

## Trofaste ikoner, 11. oktober 2026
- [x] Bygge75 ikonruter fra originalkonturer, uten nye motivdetaljer eller bildegenerering.
- [x] Bruke virkelig palett, korrekte CEL-planmasker og source-hash; bevare Original og usikre treff.
- [x] Identifisere sverdpekeren som hardware-sprite og bevare dens overlapping.
- [x] Kontrollere alle26 557 kildepikselmidtpunkter i eksporterte HD-filer mot originalvisningene.
- [x] Avvise ugyldige scene-/mønsterfelt og kontrollere egne ikonbilder uten gamle standardkonturer.
- [x] Bevare øvrige ikoners palett, kildekontroll og HD-peker ved delvis import og ødelagt PNG.
- [x] Bevare originalmarkører under treg HD-kartlasting og kontrollere samlet bytte til HD.
