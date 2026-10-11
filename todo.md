# todo.md

## Neste
- [x] HD-retting av Math og stedene: loddrett rundt murtaarn og 23 gjentatte Stonehenge-porter. Siste brukerfoto presiserer to stoetter og en overligger; enkeltstaaende soeyle er erstattet. Portene er skalert proporsjonalt ned til originalens fem kartpiksler i hoeyden. Originale posisjoner, statusmoenstre og spillregler beholdes.
- [x] HD-troskap: KI-rankene034-036, mys.cel000-001 og seks DragonDice-symboler000-005 er separat generert, kildebundet og aktivert.141 runtimekontroller består.
- [ ] HD-troskap: fullføre1779 separate figur-/animasjonsmastere med2040 konkrete PNG-ruter og264 masker. Math, KN4, hen1-flammer og TROLL er under produksjon; kandidater regnes ikke som ferdige. Hele ridderposer erstatter ikke separate ruter.
- [x] HD-troskap: fem bakgrunnsrevisjoner, kildeformet gulllogo og begge komplette rullestriper er aktivert.81 bakgrunner,411 PNG/417 filer.47+35+58 berørte runtimekontroller består; figurene gjenstår.
- [ ] HD-bakgrunner etter filnavn (bg1a.PIV/0.png) i tillegg til hash, for bildene som vises som de er.
- [ ] Valgene paa kartet i PC-versjonen: LB, RB, X og Y velger 1-4 i dag; mangler valg 5-9 og en liste paa skjermen. Nevn det i windows/LES_MEG.txt.
- [ ] Options paa mobil: oppsett av styrekorset og knappene (storrelse, venstrehendt).
- [ ] Options-siden også i PC-versjonen (SDL): taster og knapper i spillets meny. PC slår ikke på menylappen i dag.
- [ ] Options: velge spillkontroller nummer 2 og hvilken kontroller som er spiller 1.
- [ ] Duell: la den som blir angrepet få se et kort varsel før kampen («Tom utfordrer deg») i spillets egen stil, ikke bare i statuslinjen.
- [ ] Hver for seg, steg 4: motstanderen er opptatt (by, kamp), to utfordrer hverandre samtidig, årstidene går hver for seg.
- [ ] Hver for seg: vise navnet til spilleren (ikke bare riddernavnet) når man står ved siden av, og en melding når noen kommer inn på kartet.
- [ ] Veien mot en native port (brukeren sa ja 2026-10-02): 1) grafikken ut i lag (bakgrunn og forgrunn er ferdig; gjenstår menyrammer i HD og bakgrunner som endres litt), 2) logikken til C del for del (kamp og kart først) med check_hooks, 3) fjerne 68000 og Amiga-brikkene når originalkoden ikke kjører lenger.
- [x] HD-bilder som får fargene fra skjermen: maske <navn>.mask.png (docs/hd-grafikk.md), 2026-10-11.
- [ ] HD-bakgrunner som tåler små endringer i bakgrunnskopien (legg forskjellene over).
- [ ] Effektene og HD-laget også i PC-versjonen: trenger en PNG-leser (png.c kan bare skrive) og HD-tegningen skrevet i C (SDL_Renderer holder).
- [x] Prøve «Run workflow» for hånd én gang: bygg.yml på main26b6f86, kjøring38159533435, Linux/Windows/web/Pages grønne 2026-10-11.
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

- [ ] Klikk der man peker også i Select a Knight (ingen peker der; feltene for figurene er ikke kartlagt) og for forsvareren i en duell.
- [ ] Et trykk på kartet blir fire og kan åpne et sted; la det bare gi retning når man drar (observatør på \$0AACFA).

## HD: kodeendringer så bildene i docs/hd-bestilling-chatgpt.md blir brukt
- [ ] Prøve HD-figurer i en ekte monsterkamp i et hi og i en kamp med fire riddere (ikke målt etter at figurer i flere deler kom).
- [x] Banneret i Prepare yourself: bg/931f9b1d.png kom med PR #26.
- [x] Introen og slutten: originalbundet programtrace, målbuffer og rullekompositt.385 figurruter kan nå vises;329 uavhengige nytegninger er fortsatt på restlisten.
- [x] bg1b.PIV og komplette intro-/sluttrullestriper er kildevaliderte. Alle synlige atlasfliser dekkes av rekonstruerte320x1200-kompositter.
- [ ] Lasteren (render.js lastHdPakke) skal bare godta NAVN/NNN og bg/HHHHHHHH og si fra om resten (i dag tar den alt, ca 4 MB per ubrukt bilde).
- [ ] tools/hd_skaler.py skal hoppe over bildemappene (PIV) og test/, bare figurmapper og bg.
- [ ] HD-pakken skal huskes (IndexedDB) og kunne være en zip.
- [ ] --lag-dump skal lage mappen eller si fra, og prøve igjen når en bakgrunn ikke ble skrevet.
- [ ] Et skript som spiller gjennom spillet med --lag-dump og knytter hver bakgrunnshash til et skjermnavn.
- [ ] Sjekke CEL-navnene med --tegneliste (sti foran?) og om MAX_CELS glemmer filer som fortsatt tegnes.
- [x] Inntoning av HD-bakgrunnen første gang den vises (beregnLys, lysRef i scenene), 2026-10-11.
- [ ] Rette docs/hd-grafikk.md (knappens navn, skala høyst 4) og grafikklisten (hen1.p = bg5.piv, Klift1.CEL = hen1.c).

## Fra gjennomgangen 2026-10-11 (docs/hva-mangler.md)
- [ ] Separate: hverKart() er sann hele spillet (hver.c setter H.kart = 0 bare i tittelmenyen), så en spiller i by eller monsterkamp sier ja til dueller automatisk.
- [ ] Turns: gjesten kan ikke lagre, og mister kopien når verten forsvinner.
- [ ] PC: innstillinger i spillet (volum, beskjeder som vises i fullskjerm), spiller 2 uten talltastatur. --online-meny blir stående på «Creating Room...».
- [ ] Nettspill på PC, eller et vedtak om å la det være.
- [ ] Noen av nettlesertestene (tests/kjor.sh) i en egen CI-jobb, og de nye testene fra 11. oktober inn i tests/nettleser (slutt1, skjult1, fs1, gl1; de ligger i scratchpad).
- [ ] Separate: et rom som forsvinner kan ikke samles igjen, og en død forbindelse blir stående som ridder på kartet.
- [ ] Et lagret Turns-spill fordeler ridderne etter rekkefølgen gjestene kommer inn i.

## Ferdig
- [x] Klikk og trykk treffer der man peker i inventaret, byen, tavernaen og butikkene (MENY_CMD_PEKER).
- [x] Tapt WebGL-kontekst: lagres med en gang, tegnes igjen, eller siden lastes på nytt og fortsetter.
- [x] --skriv avviser verdier som ikke kan leses; test av sluttscenen (slutt1.js, lagring laget med --skriv).
- [x] Mobil: fullskjermknapp, ikon og manifest for hjemskjermen, Wake Lock.
- [x] Tur for tur: en gjest med skjult fane fjernes etter ett minutt (verten får beskjed i chatten).
- [x] Sluttscenen kjennes igjen på nettsiden (\$080190 bit 7) og hoppes ikke over av et trykk.
- [x] Nettlesertestene inn i repoet: tests/nettleser (Playwright) med felles hjelpefil og lokale PeerJS- og MQTT-servere, tests/kjor.sh og tests/README.md. Tilstandene lages med moonstone-headless når testene kjøres.
- [x] Lagringer som tåler nye versjoner (MOONSAV2 med deler og standardverdier), går mellom PC og nett, forklarer hvorfor de avvises, automatisk lagring (nett og PC), eksport og import, PC-lagring i brukermappen (atomisk, UTF-8 på Windows).
- [x] Nettspill: lagringsformatet sendes med i 'hei' og i romlisten; en gjest med annen versjon får beskjed, og en gjest som ikke kan laste tilstanden, går ut med grunnen.
- [x] Bakgrunnsmusikken i hele spillet fjernet igjen (eieren ville ikke ha den).
- [x] Lyden startes i selve trykket på mobil og følger ikke lydløs-bryteren på iPhone. (Bakgrunnsmusikken i hele spillet ble fjernet igjen 2026-10-11 etter ønske fra eieren.)
- [x] Nedlastbare utgivelser: Actions lager utgivelsen «siste» med moonstone-linux.zip og moonstone-windows.zip ved push til main. CI bruker actions på Node 24 og kjører tools/check_hooks.py.
- [x] Musikk i hele spillet: introsangen (music.cmp) spilles også i menyen, på kartet og i kampene (port/src/musikk.c), med bryter og styrke i sidemenyen. Originalen har musikk bare i introen og sluttscenen. Lyden startes i selve trykket på mobil og følger ikke lydløs-bryteren på iPhone.
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
- [x]144 originale fontformer inklusive opphavsrettsfeltene,21 palettstyrte UI-konturer, pergamentpanel og fire nye bakgrunner koblet til standardpakken. Nye materialutkast som mister originalsilhuetten holdes utenfor.
- [x] Publisere UI-/font-/bakgrunnsoppfølgingen via PR #30. Offentlig filkontroll og99 runtimekontroller består; fire nye bakgrunner og naturlig kart/inventar er visuelt kontrollert.
- [x] Rette bestillingens CEL-planmasker, grånormalisering, prioritering og mappeimport for kildevaliderte scener.
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

## Alle steders bakgrunner, 11. oktober 2026
- [x] Nytegne og koble inn de 24 manglende kamp-/hulevariantene i skog, gressland, sump og fjell.
- [x] Legge til helbreder, mystiker, Math utenfra/innenfra, druidenes Stonehenge og terningbord med beskyttet dialog/forgrunn.
- [x] Kontrollere alle 56 sammensatte kampbakgrunner i faktisk WASM, og de tolv nye PIV-koblingene med originalfixturer.
- [x] Bevare små kartporter, Original-valg, spilltilstand, originalfiler og fungerende HD-import/cache.
- [x] Lage galleri, master-/promptarkiv og kildeoversikt for alle 75 aktive bakgrunner.
- [x] Fullføre selvstendige PIV-fliser/rulling og rullende sluttsekvenser; dette inngår ikke i de 56 faste kampvariantene.
- [ ] Nytegne de resterende figurrutene separat etter bakgrunnsarbeidet, som avtalt med brukeren.
- [x] Koble inn de fem øvrige faste intro-/meldingsbildene med bevarte originalfigurer, symboler, stjerner og logo.

## Resterende objektikoner, 11. oktober 2026
- [x] Identifisere inventar-/kart-/kroikoner mot nettmanual, originale bilder og originalkode.
- [x] Nytegne inventargjenstander, statussymboler, bylandemerker, krosekker og pekere med original plassering og størrelse.
- [x] Bevare de tidligere godkjente små 9x5-portene og Math-tårnet.
- [x] Legge til manglende statiske ridder-, Gem of Seeing-, Hawk-, port-, grav- og paddemarkører.
- [x] Fullføre samlet runtime-/import-/integrasjonskontroll for ikonpakken.
- [x] Publisere ikonpakken via PR, grønn CI og offentlig kontroll.
- [x] Fullføre originaltro fontformer, meldingspanelet, riddervalgrammen og valgkonturene som egne oppgaver.
- [x] Fullføre de tre vinrankefragmentene034-036; avviste kandidater beholdes som negative eksempler.
- [ ] Ta figur- og drageanimasjoner, separat forgrunn, effekter og rulling etter ikon-/bakgrunnsarbeidet.

## Separate figurruter, 11. oktober 2026
- [x] Nytegne og kontrollere alle26 KN4-sverd-/bevegelsesruter,7 identiske kopier og025-masken.
- [x] Nytegne18 flammer separat og kontrollere dem i original Stonehenge-scene og sluttsekvens;18 identiske Klift-kopier.
- [x] Publisere og kontrollere den første figurruteleveransen etter grønn CI (PR #33, offentlig70PNG, faktisk kamp og Stonehenge).
- [ ] Fullføre1654 resterende figurmastere/1824 konkrete ruter;118 mastermasker og57 HE-kopier står på restlisten.
- [ ] Gjøre Math-ansikt, kropp, hår og kappe visuelt sammenhengende i statisk WI1.P-plate og separate Wi1.C-ruter.
- [x] Fjerne hudskjøter fra de to separate MYS-øyefragmentene før aktivering; aktivert lokalt etter14 scene- og30 rutekontroller.
- [ ] Publisere og kontrollere MYS006/007 i standardpakken.
- [ ] Fullføre tavernahansker006..009 og tre kastede terninger010..022; rette også innbygd TAV-figur med aktiv spillerfarge.
- [x] Kontrollere og aktivere16 TROLL-ruter, inklusive øyefarge og adskilt fotskygge.
- [x] Aktivere129 KN3-/HE3-/RATMEN-ruter og90 masker etter1928 rutekontroller og visuell sammenligning. Fire rene svarte skygger bevart.
- [ ] Publisere og kontrollere den andre figurleveransen med237 nye PNG-filer.
- [ ] Fullføre øvrige TROLL- og KN1-ruter med samme separate bilde-/runtimekrav.
