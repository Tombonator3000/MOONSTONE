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
- [x] Riddervalg med portrettklikk, Enter og mellomrom. Butikker og inventar har egen pekerkommando.
- [ ] Teste moonstone.exe på ekte Windows.
- [ ] Nettspill over et ekte nett med to maskiner: hvor mye forsinkelse gjesten og forsvareren i en duell merker i kamp, og om bufferen på tre bilder bør justeres.

- [x] Klikk der man peker i Select a Knight, med spillereierskap i Turns.
- [ ] Klikk der man peker for forsvareren i en duell.
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
- [ ] Fullføre749 resterende figurmastere/812 konkrete ruter; 59 mastermasker for kildebekreftede innbakte ridderdeler og ingen HE-kopier står på restlisten.
- [x] Gjøre Math-ansikt, kropp, hår og kappe visuelt sammenhengende i statisk WI1.P-plate og separate Wi1.C-ruter (PR #35).
- [x] Fjerne hudskjøter fra de to separate MYS-øyefragmentene før aktivering; aktivert lokalt etter14 scene- og30 rutekontroller.
- [x] Publisere og kontrollere MYS006/007 i standardpakken (PR #34).
- [x] Fullføre tavernahansker006..009 og tre kastede terninger010..022, samt innbygd TAV-figur med aktiv spillerfarge (PR #35).
- [x] Kontrollere og aktivere16 TROLL-ruter, inklusive øyefarge og adskilt fotskygge.
- [x] Aktivere129 KN3-/HE3-/RATMEN-ruter og90 masker etter1928 rutekontroller og visuell sammenligning. Fire rene svarte skygger bevart.
- [x] Publisere og kontrollere den andre figurleveransen med237 nye PNG-filer (PR #34).
- [x] Fullføre øvrige TROLL-ruter med samme separate bilde-/runtimekrav; KN1/HE1 er levert i PR #35.

- [x] Tredje lokale figurleveranse: KN1/HE1, KN2/HE2, Math, TAV/DICE, kartdrage, OV1, HA1 og ytterligere TROLL,1145PNG/1151filer. Standard- og originalkontroller bundet.
- [x] Publisere og kontrollere tredje figurleveranse (PR #35, alle433PNG samt281 KN1-/158 KN2-kontroller paa offentlig side).
- [x] Fullføre LI1/30, HEN/Klift/74, KN5/65, DRAGON1/16, Balok1/28 og TROLL2/2 nye ruter lokalt:178 mastere,215 kilderuter og68 masker,283 nyePNG. Palettblink, LI1-haandens retensjon og eksakt TROLL-likbuffer er kontrollert.
- [x] Publisere fjerde figurleveranse via PR #36 og groenn CI. Alle283 nyePNG samsvarer offentlig; slutt1507 og LI1/98 kontroller bestaar.
- [ ] Fortsette resterende drager, Balok, Guardian og resten av749-masterlisten. Uavklarte TROLL-bruksruter beholdes som originalgrafikk til de kan kontrolleres.

- [x] Femte lokale figurleveranse: DRAGON2/26, Balok1/15, Guardian/18 og krigsbeist/6, med to manglende riddermasker rettet.1498PNG/1504filer; alle tidligere publiserte PNG-er uendret.
- [x] Publisere femte figurleveranse: PR #37, groenn CI, alle70PNG offentlig og Guardian220/krigsbeist76/slutt1577 bestaar.

- [x] Nytegne og lokalt aktivere Guardian-bakgrunn cbc31cbf fra original test005.220 faktiske standardkontroller bestaar;1499PNG/1505filer/82BG lokalt.
- [x] Publisere ny Guardian-bakgrunn cbc31cbf (PR #38, offentlig006).
- [x] Kontrollere alle32 originale terrengkompositter mot aktive HD-hasher; test000..003 er flisark, ikke manglende bakgrunnsbilder. Senere dynamiske monster-/blodendringer kartlegges separat.

- [x] Sjette lokale leveranse:125 nyePNG og122 ruter, med112 egne fotomastere,aatte konservative flate originaleffekter,en bevart svart skygge,ett eksakt alias,to masker og Guardian-bakgrunn.1623PNG/1629filer; alle1504 tidligere filer uendret.
- [x] Standardproever006: Guardian550,demon2/187,drage97,krigsbeist49 og slutt1702. Samlet5092fil-/kildekontroller og255bestillingskontroller bestaar.
- [x] Publisere sjette leveranse via PR #38/groennCI og kontrollere alle125nyePNG/femfaktiske offentlige scener.
- [ ] Fullfoere kildebundet retensjon for Dragon2/005, Balok067/068 og dynamiske originale kampbakgrunnsdeltaer. Bevar Original ved ukjent kilde.

- [x] Sjuende lokale rutegruppe:93 separate fotomastere,fem aliaser,98 ruter og20 masker. Standard4436 og fil/kilde5449 bestaar.
- [x] Rette synlige bakgrunnsblokker over Balok1/004 og002 ved pose2200.008 er kontrollert visuelt i samme Original/HD-pose; historisk007-feilrapport beholdes.
- [ ] Beholde HD-bakgrunn ved eksakte Ratmen-bakinger med svart5 og roedt15, uten aa godta ukjente bakgrunnsendringer.

- [x] Aattende lokale kohort:202 ruter/222 PNG,195 egne fotomaterialmastere,sju bevarte originalruter,20 masker.1963 PNG/1969 filer/82 bakgrunner. Alle1747 tidligere filer uendret.
- [ ] Publisere008 etter komplett standard-/fil-/kildekontroll og kontrollere samme offentlige HTML, manifest og bilder.
- [ ] Fullfoere749 resterende mastere,812 konkrete ruter og59 masker; paagaaende009-kandidater telles foerst ved kildeverifisert aktivering.

## Oppstart og riddervalg, 12. oktober 2026
- [x] HD som standard, med bevart uttrykkelig Original-valg.
- [x] Ett trykk over introen, ogsaa under lasting og toning.
- [x] Fire direkte portrettvalg, Enter/mellomrom, mobil og eierkontroll i Turns.
- [x] Dobbeltklikkvern og faktisk lasting av eldre PEKR-lagring.
- [x] Nettleser81/81, inklusive faste porter, og check_hooks25/25. Fysisk mobil og full gjennomspilling er fortsatt egne oppgaver.
- [x] Beholde engangstegnede portretter under forsinket HD-lasting, med seks faktiske nettleserkontroller.

- [x] Publisert oppstartsrettelsene i PR40/41 med groenn CI og faktisk offentlig HD/riddervalg/intro/omstart10/10.

## Grafikk og mus, 12. oktober 2026
- [x] Rette firkant rundt Next Day-maanen og kontrollere alle fem faser.
- [x] Klar tekst i HD, inklusive navn og verdier paa karakterarket.
- [x] Inventarmarkoer foran HD-soeylene, med original pekerposisjon.
- [x] HD-bakgrunner under foerstegangslasting, scenebytter og forbigaaende nettfeil.
- [x] PC-klikk paa kartet gir original bevegelse, med tur- og netteierkontroll.
- [x] Vurdere brukerens innlimte referansetekst mot aktuelle primaerkilder og gjeldende kode.
- [x] Samlet lokal kontroll, groenn CI, Pages og offentlig kontroll av berorte scener (PR #42;108 nettlesersjekker og13+41 offentlige kontroller).

## HD-oppdatering, kartsteder og logo, 12. oktober 2026
- [x] Dokumentere faktisk aktiv HD-restliste og separate lokale kandidater.
- [x] Beholde HD-portretter og karakterark ved klikk, rammer, verdier og ikonoppdatering.
- [x] Verifisere riktige KI-ikoner, inklusive alternative liv/utstyr og små kartporter.
- [x] Skjule kildebekreftet vunnet lair i HD uten å slette loot eller endre originalregler.
- [x] Lage, pakke og kontrollere ny glatt Moonstone-logo i faktisk tittelbilde.
- [x] Rette Ratmen063-lauvets grove interne fargelegging og kontrollere faktisk kampvisning.
- [x] Fullføre relevant regresjon, PR43, grønn CI, Pages og111 offentlige nettleserkontroller.

## Blod og sår 2026-10-12
- [x]41 separate BLO-materialer generert og kildebundet pakket i4x; KN5/65 eksisterende skadefragmenter beholdt.
- [x] Hele serien visuelt kontrollert,619 kandidatkontroller inklusive normal/speilet, fire klippkanter,13 rødnivåer, fremmed kilde/palett, full lagring og originalkodekamp.
- [x] Aktivert41 nye PNG-er,2005 PNG/2011 manifestfiler. Restliste749 mastere/812 ruter/59 mastermasker.
- [ ] Endelig standardpakke, regresjon, PR, grønn CI, Pages og faktisk offentlig BLO-kontroll.

## Undersøkelser av originalen (docs/undersokelser)
- [x] Månefasene målt og lest i kode (maane.md, tools/maane.py).
- [x] Skaden med og uten passende Moonstone målt i en ekte Ratmen-kamp (tools/maane_kamp.py): 3 mot 6.
- [x] Sykdom: Ratmens bitt (type 4) smitter, og sykdommen tar ett livsnivå per faseskifte, ikke per dag.
- [x] Månereglene fra manualen som valg (av som standard): fase hvert tredje døgn, Ratmen sterkere med månen, M1 rettet.
- [ ] Hva som skjer med en syk ridder på livsnivå 0 ved neste faseskifte.
- [ ] B01: trollkrasjet, med tools/b01_troll.py (utgave, inndata, CPU/stakk, siste bilde, med og uten C-erstatninger).
