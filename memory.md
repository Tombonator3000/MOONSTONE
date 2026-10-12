# Motivretting av HD-ikoner, 11. oktober 2026

26 rasterruter er aktive: Math sitt taarn (map-landmarks/001), dalens steinsirkel med elv/fossefall (002), tre trilitter i skogklaring (003), og 23 steder (map-icons/000..022) med samme Stonehenge-port: to oppreiste stoetter og en overligger, aapen passasje. Brukerens siste foto presiserer denne formen; den enkeltstaaende soeylen var feil. Math har loddrette runde murvegger og brystning; den avviste kjeglen er bevart som eldre utkast. 49 ikonruter har fortsatt konturbehandlet originalgrafikk. Dette er fire motiver, ikke 26 forskjellige nytegninger. Detaljert motivgrunnlag: docs/hd-ikonmotiver.md.

Stedsportene er redusert til originalens 9x5 kartpiksler, uten eget draw_rect. Portmasteren pakkes proporsjonalt i 72x40 PNG med transparent sidemarg, sentrert og med samme fotpunkt. Hoeyden er fem kartpiksler mot elleve i den forrige HD-leveransen. Opprinnelig rect, expected, indeks- og bankhash styrer fortsatt kildematching og fjerning av originalmarkoeren. Palett leses ved kilderektangelet; sceneVern beskytter figurer og andre avvik. Endret markoerstatus eller overlapp beholder originalgrafikk. Originalmodus er uendret.

# memory.md

Varige fakta om prosjektet. Oppdateres når vi lærer noe nytt.

## Korrigert HD-status, 11. oktober 2026

Brukeren presiserte at HD skal være en trofast nytegning med naturtro detaljer. De 75 ikonrutene fra 11. oktober er kun kildebasert konturbehandling, ikke ferdige HD-nytegninger. Tidligere leveringsomtale av ferdige ikoner var misvisende. 26 kartmarkørruter bruker fire ulike kildemønstre. Fontene bruker andre skrifttyper enn originalen. Fem blå helposer erstatter begrensede kildekombinasjoner, ikke separat tegning av alle figurruter.

docs/hd-status-2026-10-11.md og den tilhørende CSV-listen gir kontrollert status for alle 2361 originalruter ved main f446d32. Av 2291 ikke-tomme figur-/fontruter har 189 direkte PNG og 11 bare blå posekontrakter; 2091 mangler aktiv kobling. Ingen monsterbanker har aktive HD-bilder. Pakken har 292 PNG-ruter / 298 filer, ikke 292 ferdig konverterte originalruter. Offentlige manifest- og ikonfiler samt alle 75 ikon-PNG-er er kontrollert på nytt mot hash og lengde. Ingen nye bilder eller ny runtimegjennomspilling i denne vurderingen.

## Spillet og filene
- Moonstone: A Hard Days Knight, Mindscape 1991. Laget av Rob Anderson, musikk og lyd
  Richard Joseph, grafikk Todd Prescott, Dennis Turner, Kevin Hoare og Steve Leney.
- `Moonstonecd32-AMIGA.zip` inneholder `Moonstone CD32.iso` (ISO 9660, volumnavn CDTV_TEST).
  ISO-en er en WHDLoad-installasjon som startes med cd32load:
  `S/startup-sequence` kjører `cd32load moonstone.slave` med CD32-knappene koblet til taster
  (blå = mellomrom $40, play = E $12, bwd/fwd/grønn/gul = 1, 2, 3, 4).
- `Moonstone/Moonstone.Slave` er WHDLoad-slaven av Wepl, versjon 1.4 (22.08.2002),
  ws_Version 11, BaseMem $B1000, ExpMem $79000, CurrentDir "data", QuitKey F10 ($59).
- `Moonstone/data/` har 150 filer. `program` (intro, 60 472 byte) og `mog` (selve spillet,
  170 932 byte) er AmigaDOS hunk-filer. CRC16 (CRC-16/ARC) av de første $1000 byte:
  program $D35C, mog $BAB5. Det er versjonen slaven støtter uten resload_Delta.

## Hvordan slaven starter spillet
- GameLoader på $7C. resload-basen lagres på $100, ExpMem på $108, ExpMem+$70000 på $10C
  (buffer for innlasting av pakkede filer). Stakken flyttes til ExpMem+$78FF0.
- Rutinen $632 laster en fil til $80000 (LoadFileDecrunch), sjekker CRC16, relokerer
  (resload_Relocate, hunkene rett etter hverandre uten mellomrom, bare longword-justert)
  og returnerer med A0 = ExpMem, A1 = $400, D1 = $6AC00.
- "program" lappes med patchlisten på slave+$EE og "mog" med listen på slave+$234.
  Mog-listen fjerner gullgrensen 150 (PL_W $03E7 = 999 på tre steder) og retter tastatur,
  lyd og lasting. Program+$11A hopper til slave+$1D0, som laster mog.
- Slaven bruker tag $88000005 i resload_Control for å sjekke registrert WHDLoad. Er den 0,
  stopper spillet etter introen (TDREASON_MUSTREG = 15). Vi svarer 1.
  Tag $88000006 er ButtonWait.
- Slaven inneholder spillets egen utpakker (slave+$50E), en LZ77-variant. Se decrunch.c.
- Filinnlasting i spillet er lappet: slave+$496 lagrer filnavnet, $49C laster filen,
  $4B4 regner ut minnebehov for CEL-filer, $58E laster og pakker ut CEL, $5D8 pakker ut
  vanlige filer, $5F2 laster PIV-bilder (palett til tabell, bitplan til skjermbuffer).

## Filformater (foreløpig)
- PIV (bakgrunner): ord antall bitplan (5), long pakket lengde, (1 << plan) palettord
  (bit 15 satt), deretter LZ-pakkede bitplan.
- CEL / .c / .p / .ob / .f / .font (figurer og fonter): ord antall bilder, long pakket
  lengde, long utpakket lengde, så 10 byte per bilde (long offset, ord bredde, ord høyde,
  byte flagg, byte planmaske), deretter LZ-pakkede data. Bredden rundes opp til hele ord.
- .a: hunk-filer med 8SVX-lyder (FORM....8SVXVHDR).
- music.cmp og vmusic.cmp: RNC metode 1 med et eldre hode på 12 byte (uten CRC-feltene).
  WHDLoad lar dem være, og introen pakker dem ut selv (RNC-rutine på $85968 i program).
- Spillet bruker biblioteket "IMAGEXCEL Code Module: SPRITE, Copyright 1988" for figurer.
- Tekster i mog: ridderne SIR BANNER, SIR DWAIN, SIR BALAIN, SIR GUNTHER. Det finnes en
  monstermeny for testing (B - Balok, A - Trogg with Axes osv.) på $82D82.

## Emulatoren (port/src)
- PAL A500 med 1 MB chip: 68000 7,09 MHz, 227 CCK per linje, 313 linjer, 49,92 Hz.
- WHDLoad-oppsett: chip 0-$FFFFF, ExpMem $200000, slaven $300000, resload-tabellen
  $3F0000 (bare RTS, fanges i instruksjonshooken), stakk $3FFF00.
- Slaven må kalles med SR = $2000. Med $2700 tar CPU-en aldri avbrudd og introen henger
  på slave+$1C4 (venter på at palettfaden på $99B96 blir ferdig).
- resload_Delay kjøres som en løkke i 68000 (tst.b flagg / bne), så avbrudd og musikk går
  videre mens vi venter. Flagget nullstilles når tiden er ute eller fire trykkes.
- Kjernen kjører ca. 11 ganger raskere enn sanntid på én kjerne (9000 bilder på 16,5 s).

## Tegning av figurer og HD-laget
- Alle figurer tegnes av `tegn_figur` ($9DCEC i mog): A0 = CEL i minnet, D0 = bilde,
  D1 = x, D2 = y. Tegner i figurbufferen (peker på $9E87E, fem plan à $12C0 byte).
- Slaven laster CEL-filer med slave+$58E (A0 navn, A1 hvor). Bakgrunn: slave+$5F2 (A0 navn).
- Bildetabellen i en CEL (fra +10, 10 byte per bilde): +4 bredde, +6 høyde, +8 flagg.
  Flagg 1 = vanlig. `speil_figur` ($9DB16) speilvender bildet i minnet og skriver
  (utfylling << 4), bit 0 = 0. `tegn_figur` trekker flagg >> 4 fra x, så speilet figur
  havner på samme sted. Speiltabellen (256 byte) ligger på $9DBEC, lages av $9DBC6.
- Figurene tegnes ti ganger i sekundet, ofte fordelt på to bilder på rad (i kamp He1.ob
  i ett bilde, resten i det neste). Synlig to bilder etter det siste bildet i klyngen.
- `--tegneliste F[:N]` skriver listen, `tools/hd_sjekk.py` måler treffet mot skjermbildet.
- three.js: `ImageBitmap` snus ikke av WebGL (flipY virker ikke). Tegn på et lerret først.
- Tilstander lagret før STATE_VERSION 3 virker ikke lenger.

## Tekster og tittelmenyen
- `mog` ligger upakket i spillfilen, og tekstene står som vanlig ASCII med 0 på slutten
  (f.eks. "Players" på fil-offset 70727, $8F123 i minnet). Samme lengde eller kortere kan
  byttes rett i fila og brukes med `--mod`. Testet: Spiller, Blod, Trening, Velg ridder.
- `skriv_tekst` ($89052) skriver en lenket liste (som $8F060), 14 byte per linje: long
  tekst, ord x, ord y, ord flagg (bit 0 = sentrert), long neste. Tegn - 32 slås opp i
  tegntabellen på $96210 (96 byte) som gir bildenummer i fonten (bold.f har 76 bilder).
  24 koder er ubrukte (gir bilde 69), blant annet [ ] { | } ^ @ ` ~. Der kan æøå kobles inn.
- Tittelmenyen ($8188C): valg 0-3 i $8F2D2, pilens y per valg i $8F2D4 ($55, $6E, $94, $A8),
  grensen 3 står i `cmpi.w #3` på $81916 og $819A6/$819B0. Fire på valg 2 = Practice,
  3 = Select Knight. Antall spillere i $8CDFC (1-4), Gore av i $8F2CC.

## Tekstverktøy, lapper og nettspill i tittelmenyen
- `tools/tekst.py extract` gir 361 tekster i mog. Porten bruker `data/tekster.txt` i
  `game_mog_ready()` (patch.c), som kalles fra resload_Patch når mog er lappet.
  whdload.c husker hvilke langord resload_Relocate rettet (`whd_relocs`), så pekere til
  flyttede tekster kan rettes. Avsnitt: byte med antall linjer (1-31) og linjene.
- Spillet bruker aldri chip over $B1000. Porten: $E0000 tegnelister (255 plasser),
  $F0000 flyttede tekster, $F8000 menysidene.
- Grenser i originalen: tegnelistene har 45 plasser ($8DE4A/$8DFB2) og tekst sjekker
  ikke grensen; sentrert tekst over 320 piksler gir x utenfor skjermen ($890BC/$890EA);
  D0 har tekstbredden etter skriv_tekst og $8B132 leser STR/CON/END med move.b (257).
- Fonten skriv_tekst bruker, ligger i ExpMem ($2433A2), pekeren på $8CE94+$A.
- En hook rett etter et kall til en C-erstattet funksjon kalles ikke (hook_return setter PC,
  og Musashi kjører instruksjonen uten ny hook). Derfor $8190E og ikke $8190C i meny.c.
- Lapper registreres med `hooks_register_patch`; de kjøres også med --nohooks og bestemmer
  selv ut fra tilstanden (texts_patched, M2.enabled) om de gjør noe.
- Tittelmenyen med nettspill: rader på y $53, $6C, $88, $9C, $B0. «Online Game» er valg 4.
  Nettspillsidene har seks rader: $50, $64, $78, $8C, $A0, $B4. Romsiden: «Room KODE»,
  to linjer med navn («1 Tom   2 Kari», kommando 7 med ett navn per linje), «Copy Link»,
  «Public  On/Off», «Back». Linjer man kan velge holdes under 158 piksler, ellers går
  teksten inn under pilen (x 50). Navn kuttes ved siste mellomrom.
  Sidene bygges av meny.c og tegnes av tegn_tittelmeny ($81942 = tegn på nytt og tilbake
  til løkka). Online-siden: Host Game, Join Game, «Name  Tom» eller «Choose Name», Back.
  Hendelser: 1 Host, 2 Join-side, 3 rom valgt, 4 Enter Code, 5 kopier lenke,
  6 offentlig, 7 forlot Join, 8 Back, 9 navn. Kommandoer: 1 rom (kode), 2 spillere,
  3 offentlig, 4 romliste (linjer «navn<tab>1 of 4», en invitasjon er bare «Room KODE»),
  5 melding, 6 slutt, 7 navn, 8 mitt navn, 9 side (Join Game for en invitasjon).
  STATE_VERSION er 6 (myname kom inn i M2; layout_id ser ikke på M2, så versjonen må
  økes når M2 endres).
- Options (2026-10-03): valg 4 i tittelmenyen heter nå «Options» og åpner en side med
  Online Game, Keyboard, Gamepad, Default Controls og Back. Back fra Online-siden går
  til Options; Back fra romsiden går fortsatt til tittelmenyen. Hendelse 11 (BIND,
  arg 0 = standard, 1-4 tastaturet, 5-8 spillkontrolleren) og kommando 12 (CONTROLS,
  åtte linjer med navn) i M2.ctrl. En verdi som begynner med '*' vises alene på
  linjen («Press a Key»). Linjene på kontrollsidene bruker label_value: maks 190
  punkter, to mellomrom, ett når det ikke er plass. Pilen står til venstre for linjer
  opp til ca 196 punkter (målt: «Default Controls» = 195 går så vidt klar).
  STATE_VERSION 11.
- Tittelmenyen tegner seg på nytt i ca 15 bilder etter hvert flytt, og løkka leser ikke
  joysticken så lenge. Spillet ser også joysticken ett bilde etter IN (et trykk i bilde F
  leses i F+1). meny_frame (før hvert bilde, i web.c, main.c og frontend.c) husker nye
  fire-trykk i M2.fire_seen, og hook_input gir dem når løkka leser igjen, så lenge ingen
  retning holdes og trykket er under 30 bilder gammelt. wait_release slippes bare i
  hook_input, ellers gir et fire som holdes i 20 bilder to valg.
- Beskyttelsesrullen ($080C1A, i møtet før kampen): er den angrepne (a1 = $8CE94+4) et
  menneske med en rull (tingtabellen +$12), vises «NAVN may use their Scroll of
  protection», så vent_paa_fire (port 2), så inventaret til den angrepne ($08AAC4 med
  d0 = 9, pekeren styres med port 2). $8BEA4 = $12 etterpå betyr at rullen ble brukt.
  I en duell setter hver.c H.rulle fra $080C52 til $080C98, og hver_frame flytter
  port 1 (forsvareren) til port 2 så lenge.
- Fontbredder (skriv_tekst): mellomrom 15, A 20, B 17, C 13, D 17, E 13, F 16, I 9,
  K 19, M 24, N 19, P 17, S 13, T 16, W 24, a 13, e 11, i 9, l 8, m 19, n 14, o 12,
  r 12, s 11, t 11, tall 7-12. Mangler: " & ( ) * + - : ; < = > ? @ [ ] ^ _ ` { | } ~.
- Pages: repoet er offentlig og Pages bruker GitHub Actions (eieren slo det på
  2026-10-02). Spillet ligger på https://tombonator3000.github.io/MOONSTONE/. Før
  spillfila ble bygget inn, lå spill/Moonstonecd32-AMIGA.zip ved siden av. Før det var repoet privat, og deploy ga
  404 «Ensure GitHub Pages has been enabled». GITHUB_TOKEN kan ikke slå på Pages.
- «Run workflow» (workflow_dispatch) publiserte ikke før rettelsen a998217, fordi
  pages-jobben krevde push. Ny kjøring av en push-kjøring på main publiserer.
- Chromium i skymiljøet kommer ikke gjennom proxyen til github.io (ERR_TOO_MANY_RETRIES),
  men curl gjør det. Test de publiserte filene ved å laste dem ned og servere dem lokalt.
- `/` og `\` i fonten er understrek (bilde 71), `-` og `:` har ikke noe bilde.

## Spillfilen er bygget inn
- `port/bin2c.py` gjør `Moonstonecd32-AMIGA.zip` om til `port/src/spilldata.c`
  (`spill_innebygd`, `spill_innebygd_storrelse`) som strengkonstanter med \xNN; gcc
  bruker et par sekunder, emcc litt mer. Fila skrives bare når innholdet endres.
- `MED_SPILLET ?= ja` i Makefile (CI setter det også). Med `nei` blir tabellen tom.
- PC: `--game` først, så den innebygde, så `spill/` og mappen programmet startes fra.
- Nettsiden (4,3 MB) laster kjernen når siden åpnes; `ms_has_embedded()` sier om
  fila er der, og `ms_open_embedded()` åpner den. Annen spillfil under «Spillfil og egne
  filer» i sidemenyen. `Kjerne.last()` deler ett løfte, så kjernen lastes bare en gang.

## Nettsiden uten startside
- Eieren vil ikke ha en HTML-startside. Siden starter rett i introen, og alt valg skjer i
  spillets tittelmeny. Sidemenyen (Home, knappen oppe til høyre) har bilde og lyd,
  HD-grafikk, lagring, spillfil og egne filer, taster og «Start spillet på nytt».
- Teksten på nettsiden er engelsk som standard; norsk velges øverst i sidemenyen
  («Language / Språk», innstillingen `sprak`: 'en' eller 'no'). Kildeteksten i JavaScript
  er norsk, og `web/src/sprak.js` har ordboken til engelsk. `T(tekst, ...verdier)`
  oversetter ({0}, {1} er plassholdere), `Sprak.sett(el, tekst, ...)` husker kilden så
  elementet tegnes på nytt ved bytte. Nye tekster på siden må inn i ordboken.
  De faste tekstene i index.html er engelske (første bilde, søkemotorer, lenkeforhåndsvisning),
  og `Sprak.start` finner den norske kilden ved å slå opp den engelske teksten baklengs i
  ordboken. En fast tekst i index.html må derfor være lik den engelske teksten i ordboken.
  Feilmeldingene fra kjernen (state.c, files.c, whdload.c) er norske og står også i
  ordboken; navnene på delene i en lagring (`deler[]`) står i `DELER` i sprak.js.
  Tester som leser norsk tekst, setter `sprak: 'no'` i `moonstone.innstillinger`.
- HD-grafikken er på som standard fra 12. oktober. Valget lagres som `hd` sammen med
  `hdValgt: true`; en gammel lagret `hd` uten `hdValgt` gir HD. Et uttrykkelig valg av
  Original beholdes. Standardpakken lastes automatisk fra HTTP(S).
- Introen ser på den siste tastaturkoden uten slipp-biten, og bare mellom trinnene.
  Esc huskes, men det kan gå opp mot 200 bilder før mog lastes. En annen tast etter Esc
  (Return som slippes) gjør at introen ikke slutter. Målt med moonstone-headless
  `--press F:esc:4`: alltid mog innen +200 bilder, aldri med Return i tillegg.
- app.js `introTaster`: fire, Enter, mellomrom og første skjermtrykk ber om introhopp.
  Esc gjentas hvert bilde frem til mog er lastet og slippes deretter. Originalens
  lasting/toning kan slette et enkelt tastetrykk. Enter/mellomrom sendes ikke videre
  i introen; lydstart og introhopp kan skje ved samme brukerhandling.
- `ms_in_intro()` = mog er ikke lastet (whd_mog_loaded, nullstilles i whd_boot).
  `ms_menu_ready()` = tittelmenyens løkke har kjørt (meny_title_seen). amiga_reset kaller
  patch_reset, som nullstiller tekstlappen og menyen, så en omstart starter rent.
- Invitasjon (`?rom=KODE`): når tittelmenyen er nådd, sendes kommando 9 (Join Game) og
  rommet legges først i listen, og `rom` fjernes fra adressen. Lenken beholder `peer`,
  `mqtt` og `mqttv`.
- WebRTC merker ikke at verten lukker fanen. Verten sier fra på `pagehide`, og gjesten
  gir opp etter 20 sekunder uten noe fra verten (ping hvert 2. sekund). `Nett.avslutt()`
  tømmer hendelsene først, ellers kaller close-hendelsen `frakoblet` en gang til.
- Verten legger ut rommet på nytt med en gang antallet spillere endres
  (`stoppAnnonse.oppdater()`), ellers står det «1 of 4» i opptil ett minutt.

## Mus, lyd og ytelse i nettleseren
- Spillet bruker ikke musen: `les_mus` ($9B4FC) kalles fra VBL-avbruddet ($9B2D4) og
  legger posisjonen i $9B7CC/$9B7CE og knappen i $9B7D0, men ingenting leser dem.
- Tittelmenyens lokke ($81906) leser joysticken hele tiden (ingen venting på VBL), men
  å tegne menyen på nytt (tegn_tittelmeny) tar rundt 20 bilder. Et kort fire fra
  nettsiden kunne derfor komme mens den tegnet og bli borte.
- Klikk på en rad: kommando 10 (VELG, arg = rad, -1 = raden pilen står på) setter
  M2.pick og pick_fire. hook_loop setter VALG ved neste tegning, og hook_input ($8190E)
  gir spillet fire en gang når menyen er tegnet: D1 |= $10 og PC = $81910 (forbi beq).
  Gamle klikk (over 25 bilder) kastes. STATE_VERSION er 7.
- meny_in_menu(): sann fra hook_title/hook_loop til Practice ($8194A) eller Select Knight
  ($81952), også mens menyen tegnes. Bare for frontenden, lagres ikke.
- meny_row_at(y): tittelradene har y $53, $6C, $88, $9C, $B0 (treff fra y-3 til y+21),
  sidene $50 + 20 * i (19 piksler høye). Klikket regnes om med Visning.utsnitt() og
  Kjerne.vindu() (y = utsnitt-y0 + andel * høyde - diw-y0).
- Lyd: målet for bufferen starter på 80 ms og økes med 20 ms (til 200 ms) hver gang
  den går tom. Tom buffer tones ut og fylles halvveis før avspillingen fortsetter.
  Pause, sidemenyen og skjult fane tømmer bufferen, så det ikke regnes som et hull.
  Kjernen tar volumet opp til 1 (over det klipper int16); resten forsterkes i workleten
  med myk begrensning over 0,9.
- Tid per bilde i Chromium (4 kjerner, swiftshader): kjernen 2-3 ms, visningen 2,8 ms,
  sjekksummen 5,6 ms (bare hvert 120. bilde hos verten). Visningen tegner nå bare når
  det er et nytt bilde, og tegnelisten hentes bare når en HD-pakke eller rammene er på.

## Lagene (bakgrunn og forgrunn) og renderen
- Den rene bakgrunnen: peker på $8CDE8 (i kamp $000400), fem plan à $1F40 byte (40 x 200).
  Bufferet det tegnes i: peker på $AA948. Skjermbufferne i kamp: $75A3C og $6BDFA.
- Tilbakestilling under figurene: $882E2 går gjennom en liste med rektangler (8 byte:
  x, y, b, h) og kopierer fra bakgrunnen til tegnebufferet med $9E252 (A0 kilde, A1 mål,
  D0/D1 modulo, D2 bredde i ord, D3 høyde), ett plan om gangen.
- Figurene: $9E130 kopierer bildet til figurbufferet ($A2CD6, plan à $12C0), $9DF50 og
  $9DF92 lager masken ($A8A96), $9E0AA blitter med maske til skjermen (minterm F2/22).
- lag.c: bakgrunn = kopien med paletten på hver linje (video_line_pal), forgrunn =
  video_fb der skjermens indeks eller farge er annerledes enn bakgrunnens. Sammen lik
  originalen (0 av 614 400 piksler i test). Gyldig bare med fem plan lowres 320 x 200,
  modulo 0 og plan $1F40 fra hverandre. Hash: FNV-1a av de fem planene. 0,3 ms per bilde.
- `--blit-trace F:N` viser hver blit med pekere og skjermens bitplan; `--lag F:PREFIKS`
  og `--lag-dump MAPPE` skriver lagene. Gamle .sav-filer i scratchpad virker ikke etter
  STATE_VERSION 7; nye lages med --press-sekvenser (Practice: esc 100, ned 700 og 760,
  fire 820; kart: Select Knight, fire 1300, return 1500, tilstand i 1650).
- render.js: trinn 1 tegner lagene i et rendermål (lowres-koordinater, y nedover,
  DoubleSide, teksturer uten flipY), trinn 2 filter og effekter. HD-teksturer fra lerret
  har flipY = false nå.
- Bokstavene tegnes av tegn_figur som figurer i bold.f (bilde 73 er MOONSTONE-logoen) og
  Small.font. Tittelskjermen toner inn fra svart (lys 0), så HD-figurer må sammenlignes
  på fargeindekser (lag_for_idx: indeks, $FF ingen, $FE bare fargen ulik), ikke farger.
- Glatt-filteret: Scale4x regnet ut per utgangspiksel fra 5 x 5 lowres-piksler (s2 fem
  ganger i s4), rendermål fast 4 x. fragAmiga brukes for rammebufferet (celle 2 x 1),
  bakgrunnen og forgrunnen; modus 0 henter hel texel (også hires).
- LAG_SPOR=1 i miljøet får moonstone-headless til å skrive hash, forgrunn og lys per bilde.


## Flerspiller «Hver for seg» (hver.c)
- Mode Separate (M2.spill = 0) er standard, Turns (1) er det gamle tur for tur. Innstillingen
  heter `innst.spill` ('hver' eller 'sammen') på nettsiden; verten bestemmer for rommet.
- Ridderne: $8D5B4, $84 byte. +$0B port, +$36 figur 0-3 (4 = datamaskinen), +$49 liv,
  +$52 > 0 hopper over turen, +$6C navn, +$7E/+$80 posisjon. aktiv_ridder $8D9AC.
- Kroker: $0AAC14 turstart (fjern ridder: $8E7A0 = $8E7C2, PC = $0AAE62), $08188C tittel,
  $0AAC54 kopi av bakgrunnen før ridderne, $0AAC8C toppen av kartløkka (tegner ridderne på
  nytt via rutinen på $FC080), $080AB8 kamp (a1 fjern: +$36 = 4), $080BD8 kampen slutt.
- Ledig chip: $FC000-$FC0FF (navn på $FC000 + k*16, rutinen på $FC080). Stakken ligger i
  fast-minnet ($3FFF00), og området er null på kartet.
- Kartet bygges fra bakgrunnen hvert bilde ($0AAF38 kopierer $8CDE8 til $AA948), så det som
  tegnes i bakgrunnen vises med en gang.
- Kopien av bakgrunnen er ikke i lagringen; etter lasting tegnes ridderne på nytt først
  neste tur.
- Testtilstanden $S/hv/kart.sav må lages på nytt når H eller M2 endres (gjaldt før lagringsformatet MOONSAV2,
  ikke sluppet ennå). Uten tilstand: --press 1400 med --hver før return i 1500, så turen
  starter med de fjerne ridderne.
- Valgene på kartet venter på tastene 1-9 (`--press 1900:2:4` velger nummer 2).
- Nettlesertest: tests/nettleser/test26.js (vert og Kari, Separate, gange, farger, verten går).
  Playwright ligger i /opt/node-tools/node_modules (NODE_PATH). tests/kjor.sh starter serverne og
  kjorer testene (tests/README.md); felles.js har hjelpefunksjonene.
- Dueller (steg 3): HVER_BLOB (hele ridderen som heks, 312 tegn), HVER_MEG (inn paa plass 0
  etter duellen), HVER_DUELL (maske: kan naas), HVER_AI (datamaskinen tar over), hendelser
  HVER_EV_DUELL / HVER_EV_DUELL_SLUTT via ms_hver_hendelse. Nettsiden: D i app.js (rolle 'a'
  angriper / 'b'), Nett.duellKoble (direkte PeerJS med metadata.duell), sendTilstandTil,
  tilstandsMottaker. Protokollversjon 3.
- Kampposisjonene: +$04 x og +$08 y (ord) i ridderstrukturen. Kampen laster i om lag 8 s.
- Tester: tests/nettleser/test27.js (duell, verten angriper, testspiller styrer etter posisjonene),
  test28.js (Kari sier nei: datamaskinen tar over), test29.js (Kari angriper verten).
- Home-tasten aapnet og lukket sidemenyen paa samme trykk (to lyttere); rettet med
  e.defaultPrevented.

## Mobil, valgene paa kartet og spillets grafikk paa nettsiden (2026-10-03)
- Valgene paa kartet: fire paa kartet ($0AADEE) kaller sub_0ABB76. Tabellen paa $8EEEC har
  8 byte per valg (long maal, long type), slutter med maal 0. Ett valg velges med en gang;
  flere tegnes i en brun boks (sub_0ABCAE: x $963BE+5, y $963C0+15, 6 punkter per linje,
  Small.font) og lokka paa $0ABBBA venter paa $9B684 = '1'-'9'. Tekst: type 1 «Battle with »
  ($9633B) + navnet (+$6C paa maalet), type 2 «Enter Lair» ($96330), ellers $96386 +
  (type - $15) * 4 (Enter Village, Enter the city of Highwood ..., $21 «Pillage knight's grave»).
  Overskriften er navnet til aktiv_ridder + « may ... » ($962A1). AI-ridderne ($8E7AE) velger selv.
- Tastaturet: avbruddet ($9B130) legger tegnet (oversatt via $9B696) i $9B685 naar tasten
  TRYKKES (rettet 2026-10-03: --vakt 9B684 med --press 600:a:30 viser skrivingen i bilde 600,
  ingenting ved slippet); $9B716 er tabellen over tastene som er nede.
- Navnet til ridderen: sub_081B26, lokka paa $081B7C. Fire godtar, Return ($1C) godtar,
  Backspace ($0E) sletter, maks 13 tegn. Bufferen er pekeren paa $8F0B4, lengden ordet $8CE32.
- game.c observerer $0ABBBA og $081B7C (som lapper, hooks_register_patch: de endrer
  ingenting, og vanlige kroker inne i lokker forstyrrer --hook-cycles); web.c:
  ms_valg_antall/tekst/tittel, ms_navn/ms_navn_aktiv/ms_navn_klar. app.js viser valgene som
  knapper og trykker tasten med Inndata.trykk (ned naa, opp to bilder senere). Tekstene leses
  gjennom lea-ene ($0ABD7A, $0ABD8E, $0ABDAC, $0ABCB6), som patch.c peker om for tekster.txt.
  Observatorene nullstilles ved lasting (game_state) og start.
- Navnet: ordet $8CE34 er 1 hele tiden navnet skrives (ogsaa mens det tegnes paa nytt etter en
  tast, 6-7 bilder der lokka ikke leser tastene og $9B684 nullstilles etterpaa). Nettsiden sender
  derfor en tast om gangen: neste naar lokka leser igjen og navnet har endret seg.
- Menyen husker ogsaa opp og ned som kommer mens den tegnes (M2.dir_seen, meny_frame), og gir
  dem ved aa skrive $8D9A2 (opp 8, ned 4) og gaa til $81910 (ikke fire -> tittelmeny_joystick).
  Et nytt fire-trykk mens menyen tegnes slipper wait_release (M2.fire_seen). STATE_VERSION 12.
- bold.f: 76 bilder, 19 punkter hoye: 0-25 A-Z, 26-51 a-z, 52-61 0-9, 62 !, 63 ?, 64 ., 65 ,,
  66 #, 67 $, 68 %, 69 tom (15 bred), 70 ', 71 _ (og /), 72 prikk, 73 logoen (305 x 54),
  74-75 copyright. skriv_tekst flytter bredden minus 3 for bold.f ($089166, flagg bit 3).
- sel.cel bilde 0 er pilen (38 x 19), 1-5 portrettene. Small.font: 5 x 6, A-Z to ganger.
- Paletten i PIV-filene er den spillet viser (de 12 laveste bitene; bit 15 er satt i filene).
  ch.piv er tittelmenyen; fargene 9-12 er gull og krem i bold.f, 5 svart kant.
- Tilstander fra headless (64 bit) kan ikke lastes i nettleseren (32 bit, andre strukturer).
- `.knapp { display: inline-flex }` overstyrer `hidden`; style.css har `[hidden] { display: none !important }`.
- DRAGON1.CEL har seks tomme bilder forst (planmaske 0); er_cel godtar det naa.


## Hvem styrer i nettspill (2026-10-03)
- +$36 er figuren som ble valgt i Select a Knight (0 GODBER, 1 RICHARD, 2 JEFFREY, 3 EDWARD,
  $081ECA), ikke rekkefolgen. Select a Knight (sub_081C82, lokka paa $081CFA) gir plass for
  plass: $8F49C er plassen som faar neste ridder, $8F4A0 hvor mange som gjenstaar (startverdi 1,
  0 naar spillet er i gang), $8F4A2 er figurene som er ledige (bit), $8F51E pilen.
  Navnet (sub_081B26) kalles bare herfra. Turene gaar i plassenes rekkefolge.
- game_port_player gir plassen. Moetet: $080AB8 (start, $8CE94 angriper, $8CE98 den angrepne),
  $080C1A rullen (kalles foer portene settes, vent_paa_fire port 2, saa inventaret med
  $8CE94 = den angrepne), $080B14 portene (menneske som angriper +$0B 2, angrepet menneske 1;
  angriper datamaskinen, faar mennesket 2), $080B40 kampen, $080B94 bytte naar den angrepne
  vant, $080BA4 plyndring (a0 plyndrer), $080BD8 slutt. HIT (+$50) leses naar kampen
  starter; aa endre den midt i kampen gjoer ingenting.
- Pekeren i inventaret og plyndringen ($08C3EA): porten til ridderen i $8E8B6 (= $8CE94,
  sub_08CA1C), port 1 naar +$0B er 1. Hoyre +2 x, venstre -2, ned +2 y, opp -2, fire.
- I en duell i Separate har forsvareren +$0B = 1 etter kampen, saa plyndringen hans gaar
  med port 1 (inndataene hans) uten noe ekstra. Rullen trenger H.rulle fordi fjerne riddere
  har +$0B = 4 foer kampen.
- Select Knight i et Turns-rom (M2.spill 1, SESSION_HOST) setter Players opp til M2.players.
- moonstone-headless --skriv F:ADR:VERDI[:N] skriver i minnet foer bilde F (testoppsett).
  To mennesker i moete: Players 2, ridder 2 flyttes til ridder 1 ($8D6B6/$8D6B8 = 300/5 i
  bilde 2100), fire 2200, tasten 2 i 2300; forsvareren gaar med p2-right 62 og p2-down 42
  fra 2850 og slaar med p2-fire + p2-right (angriperen med HIT 1 via $8D604 i 2250).
- Nettlesertest for Turns-kontrollene: tests/nettleser/test35.js.
- Rullen headless: gi plass 1 en rull med --skriv 2100:8d872:1:1 (tingtabellen til plass 1 er $8D860,
  ting $12), angrip som over; fire i 2450 aapner inventaret, pekeren fra (160,100) til rullen ved ca.
  (110,195) og fire bruker den (ting $12 blir 0, $8BEA4 = $12, ingen kamp).
- Datamaskinen angriper: +$64 i datamaskinens ridder er maalet; sub_0AB6AE angriper (jsr $080AB8 paa
  $0AB710) naar maalet er naer nok. Headless: E i 2200 og 2500 (turene til plass 0 og 1), og i plass 2
  sin tur --skriv $8D720 = $8D5B4 (maalet) og begge posisjonene (160,20), hvert 5. bilde fra 2505.
- Musikken: bare program har en musikkspiller (ProTracker-periodetabellen paa 0x2366 i filen). Introen
  laster music.cmp ($085662) etter bildene, saa de foerste ca. 32 s er stille; sangen aapner med 12 s
  nesten stille, slag til 23 s, hovedtema fra posisjon 4. mog har bare en driver for lydeffekter
  ($0AE0DA, fire kanaler med avbrudd).
- Bakgrunnsmusikk i hele spillet (port/src/musikk.c, PR #14) ble fjernet 2026-10-11 fordi eieren ikke
  ville ha musikk som gaar hele tiden. Koden ligger i git (94049e7) om den skal tilbake som et valg.
- Nettsiden starter kjernen paa nytt i samme WebAssembly-instans (startPaaNytt), saa statiske
  variabler i C beholdes mellom omstarter; noe som lastes fra filene, maa lastes i amiga_init.
- Introen hoppes over headless med --press 200:esc:4 (fire hopper ikke over); tittelmenyen fra ca. bilde 600.
- ffmpeg her har libopenmpt og kan spille .mod til WAV (sammenligning med egen spiller).

## Lagringene (fra 2026-10-11)
- state.c: MOONSAV2 = magi, format 1, CRC for spillfilene, antall deler, og deler med merke (4 tegn),
  versjon og lengde: MEM, MACH (M og IN), CUST (C og B), CIA, CPU, AUD, WHD, GAME, PTCH, MENY, HVT, HVER, BLIT.
  En del maa ha samme versjon og nøyaktig samme lengde. GAME (game_standard: tom tegneliste), MENY
  (meny_standard: menyen paa hvis mog er lappet, rd32(0x8f094) == TITLE_NODE), HVER (hver_standard:
  alt unntatt originalene) og BLIT faar standardverdier ellers. HVT er originalene til datamaskinens
  riddere (H.tatt, o36, o6c, o0b, o49, orig) og maa passe, fordi ridderne er byttet ut i minnet.
  AUD er Paula og maa passe (paula_reset midt i spillet ville gjort kanalene stumme).
- hver_kart() (H.kart) er sann fra en tur har begynt til tittelmenyen, i alle moduser, og foelger med
  lagringen. Den brukes som "et spill er i gang" for automatisk lagring (nett og PC).
- Nettspill: 'hei' har f = state_format_id() (delenes merke, versjon, lengde) og v = 4; verten avviser
  et annet format med beskjed. Romlisten (rooms.js) har f og viser bare rom med samme format.
  Faar en gjest en tilstand den ikke kan laste, gaar den ut av rommet med grunnen. Test: tests/nettleser/ver1.js.
- Det gamle formatet (MOONSTAT, versjon 13) leses fortsatt, men bare paa samme maskintype
  (layout_id tok med sizeof(void *)). Eldre versjoner gir en melding med versjonsnummeret.
- Strukturene er like store paa x86_64, MinGW og wasm32 (M 232, C 280, B 64, AudChan 40, Cia 36,
  Input 6, CPU 488), saa lagringer kan flyttes mellom PC og nett. state_feil har grunnen.
- Nettsiden: autolagring i IndexedDB-noekkelen 'auto' (visibilitychange, pagehide, hvert 120 s,
  bare naar hver_kart() og ikke i introen, tittelmenyen, en duell eller som gjest),
  navigator.storage.persist(), Fortsett, Last ned, Hent fra fil. Test: tests/nettleser/lag1.js (10 sjekker, bruker
  kart_ny.sav, som testen lager selv: --online-meny --press 100:esc:4 700/760/820:down:10 880:fire:10 1300:fire:10
  1500:return:6, lagret i bilde 2000 paa kartet).
- PC: SDL_GetPrefPath ("~/.local/share/Moonstone/Moonstone/", %APPDATA%\Moonstone\Moonstone\),
  moonstone_auto.sav ved avslutning (ogsaa F10: amiga_quit_key, ikke ved resload_Abort), den forrige
  blir moonstone_auto_forrige.sav, Shift+PageDown henter. Filene skrives til .tmp og byttes (atomisk),
  og paa Windows aapnes UTF-8-stier med _wfopen (testet i Wine med "Tøm æøå"). SIGTERM gir SDL_QUIT,
  saa avslutningen kan testes med SDL_VIDEODRIVER=dummy og timeout -s TERM.

## Standard-HD og råarkiv, 11. oktober 2026

Utvidelsen i art/hd-backgrounds-2026-10-11/README.md avløser tallene i den opprinnelige 48-bilders leveransen nedenfor. Pakken har 224 PNG-ruter: 40 bakgrunner, 184 basisbilder. Bakgrunner for kart, Waterdeep, Highwood, kro og tre introscener gjenkjennes fra faktisk viste indekser og kilde-PIV med SHA-256. K.skanout() eksponerer kun analyseutdata: synlig indeks, hardware-sprite-flagg og per-linje-palett. HAM, dual-playfield, hires og over fem bitplan avvises. Dette endrer ikke emulert tilstand.

web/src/scenes.js bygger et beskyttet forgrunnslag med originale markører og sceneavvik. Kartets seks statiske landemerker tegnes fra en transparent atlas under markørene. By/kro har egne bildeutsnitt og 20 faste konturtekstfelt; dynamiske avvik beskytter valgmarkeringer. text.json binder 142 fontglyfer og logoen til de originale fontbankene. Overlappende glyfer valideres som adskilte tekstfelt, og palettavvik $FE kontrolleres mot faktisk skanout. Small.font har mask 1; bold.f har mask 15. Ikke anta at preview-fargene eier tekstens spillpalett.

tools/hd_tekst_bygg.py og hd_paneltekst_bygg.py gjenbygger tekst og oppdaterer manifest. tools/hd_integrer.py er en historisk 48-bilders import og nekter overskriving av den utvidede pakken. Alle råbilder, fonter, OFL-lisenser, prompter, revisjoner og verifikasjonsbilder er bevart. Full gjennomspilling, telefon-FPS og alle resterende figur-/PIV-ruter er ikke sluttgodkjent.

web/hd/manifest.json binder48 bilder med SHA-256:33 bakgrunner,5 blå hele metodeposer,4 riddervalg,menypil og5 månefaser. web/src/hd.js henter basisbildene automatisk og bakgrunner ved behov, med høyst4 standardbakgrunner på GPU. Egne filer/Fjern venter på stopp av standardlasteren, så gamle forespørsler ikke skriver over brukervalg. Standardgrafikk-knappen gjenoppretter pakken. Ved file:// brukes originalgrafikk uten nettforespørsler; HTTP/Pages gir auto-HD.

art/photoreal har807 urørte rå-PNG med revisjoner, prompter og616 selvstendige katalogoppføringer:506 valgte planutdata og110 nytegnede fliser.10 svarte konstante fliser er metadata. Katalogen bevarer faktisk palettreferanse eller tydelig preview-merking. Arkivruter er ikke automatisk aktive i spillet. Historisk produksjonsplan er bevart som production-plan-2026-10-03.json. De tidligere lokale spesialverktøyene og bildebevisene er bevart i moonstone-hd-arbeidsmappen.

Integrasjonstest tools/hd_standard_sjekk.cjs bygger på faktisk HTML og main-CI-kjernen med musikk.25 kontroller bestått,71/71 gangrammer har fotopose. Ingen ny full gjennomspilling, mobil-FPS eller ny månefasesekvens er påstått. Måne-/meny-/bakgrunnsregler og råbilder viderefører de tidligere målte kildekontraktene.

## Trofaste konturikoner, 11. oktober 2026

art/hd-icons-2026-10-11 har75 kildefaste konturikonruter og redigerbare SVG-kilder. Ingen bildegenerering. tools/hd_ikoner_bygg.py leser original CEL/PIV og dokumenterte naturlige inventar-/kartpaletter; hd_ikoner_eksporter.cjs eksporterer8x PNG. icons.json binder originalbank, utvidede indeksdata, mål og planmaske. Standardpakken292 PNG-ruter. Visningsanalysen utvider ikke-sammenhengende CEL-planmasker til riktige skjermbiter. po.cel/000 er en hardware-sprite, fargeindekser17..19, og finnes ikke i tegn_figur-listen. K.skanout bit7 identifiserer synlige spritepiksler; HD-markøren beholder skjult del og originalen ved usikre treff. 26 kartmarkører krever eksakt mønster; nye statuser beholder originalen. Seks landemerker bruker avgrensede originalkartkonturer og originalplassering, som erstatter de tidligere fotoikonene. Hele spillkjernen og lagret tilstand er uendret av denne leveransen.

`Visning.lastHdPakke(filer)` bytter bare ikonmetadata når en tilsvarende PNG er dekodet og erstattet. Egen PNG uten ikonmetadata beholder sine egne piksler. Delvis import og bakgrunnslasting bevarer øvrige ikoners palett, kildekontroll og HD-peker. Feil i PNG eller ikonmanifest endrer ikke de øvrige ikonene. Scenefelt krever gyldig rektangel, originalmål og indeksmønster før de blir tilgjengelige for rendereren.

Dynamiske kartmarkører fjernes først fra originalforgrunnen når valgt HD-bakgrunn finnes i standardpakkens ferdiglastede bakgrunnscache. Dette hindrer at markørene blir usynlige under nettverkslasting.
- Sluttscenen: seierruten i mog ($081834) skriver d7|$80 til $3E0 og hopper til tilbake_til_introen ($081846),
  som laster program. program kopierer $3E0 til $080190 ($08001E) og viser sluttscenen naar bit 7 er satt
  ($080064). Ingen andre hopp til $081846. Headless: --press 200:esc:4 --skriv 800:81942:0x4ef9:2
  --skriv 800:81944:0x0008183c:4 --press 900:down:10 (hex maa ha 0x). Nettsiden: ms_in_ending.
- Pekeren: $098088 paa (1)/av, $098092 x, $098094 y (lowres, spissen), $098096 fire, $09A020 feltlisten ($18 byte:
  +4 b, +6 h, +$C x, +$E y, +$10 kode), $8E8B6 eieren (+$0B porten). VBL $08C3EA flytter 2 piksler/bilde og leser
  eierens port; byen ($081242/$0813B2) og tavernaen leser port 2 selv; tavernaen ser etter fire hvert 14. bilde.
  MENY_CMD_PEKER (14, arg x | y << 16) og game_frame (fire 16 bilder paa begge portene). Test: peker1.js; by.sav i
  $S/peker/agent_b. --save-state F er antall bilder fra start av kjoringen (ikke bildenummeret).
- HD-lysstyrke: lag.c lag_bak_lys er summen av fargene bakgrunnen bruker. Er bakgrunnen helt svart (riddervalget), brukes hele paletten i stedet; render.js gir hdLys = 1 om maks er 0. Uten dette ble HD-portrettene og HD-teksten svarte.
- HD-masker: `<hd_fil uten .png>.mask.png`, R = palettindeks + 1 (0 = behold bildets farge), G = lysstyrke (128 = palettfargen), B = vekt. Ridderne: KN-settet indeks 6-8, HE-settet 9-11. tools/hd_bestilling.py --maske lager utgangspunktet.
- HD-testene i tools/: CHROME=/opt/pw-browsers/chromium-1194/chrome-linux/chrome, MOONSTONE_HD_TEST_OUTPUT for standard-testen, og en server på 127.0.0.1:8769 som serverer web/build (python3 -m http.server 8769 i web/build). De skriver rapporter og skjermbilder i art/*/verification.
- Figurer i flere deler: render.js avgjør eierskap per piksel (siste figur i tegnelisten eier pikselen); bare piksler som eies av en figur med HD fjernes fra forgrunnen.

## Steds- og kampbakgrunner, 11. oktober 2026

`art/hd-all-locations-2026-10-11/README.md` avløser tidligere pakkeantall: 327 PNG-ruter, 75 bakgrunner, 333 manifestfiler. Alle 56 sammensatte kampvarianter er koblet inn; de 24 lair-variantene er nytegnet mot original og tidligere materialutkast. Seks stedsskjermer er lagt til: hea.piv, mys.piv, WI2.P, WI1.P, hen1.p/bg5.piv og dice.piv. hen1.p og bg5.piv er samme originalhash og deler HD-rute. Aktive råbilder er uendret; 29 nye aktive genereringer og seks bevarte materialmastere, inkludert Stonehenge. Fem faste intro-/meldingsbilder har fått kildeindeksvern for tidligere påpekte motivavvik. En ekstra, erstattet Math-revisjon er arkivert. Hele original-/HD-oversikten finnes i coverage.json og index.html.

Maths HD-master inneholder bare arkitektur. WI1.Ps originale figur bevares med preserve_regions, og avviksmasken bevarer originalens Wi1.C-animasjon. Ikke beskytt hele palettindeks 25; den er også brukt i bakgrunnen. PIV-identiteten beholdes i begge grafikkmoduser for å bevare engangstegnet HD-tekst. Kildebekreftet PIV-forgrunn er tillatt bak transparente glyffelt. Alle nye mastere bruker fullramme-UV, uavhengig av verneutsnittet. Kildegjenkjenning krever minst 90 prosent samsvar for å tåle bevegelige forgrunnsfigurer; detaljsamsvar og kildehash må også passe. WI1.P verneutsnitt slutter ved y181; helbreder/mystiker ved y161; terningbordets tekstfelt er vernet. tools/hd_math_sted_sjekk.cjs besøker original Math etter kontrollert ridderposisjon 220,27.

Alle 56 kampvariantene er runtime-testet via tools/hd_alle_kampbakgrunner_sjekk.cjs med kontrollert originalt scenevalg. Det er ikke naturlig gjennomspilling. tools/hd_steder_bakgrunner_sjekk.cjs bruker tolv kilde-PIV-fixturer uten skriving til WASM-minnet. Renderers utsnitt bruker 25 tegninger før nytt vindu aksepteres; varm opp før eksakt PNG-sammenligning. tools/hd_steder_bakgrunner_bygg.py kobler bare eksisterende nye mastere. tools/hd_bakgrunnsgalleri.py dokumenterer alle 75 aktive ruter. PIV-flisbankene, rulling, rullende sluttsekvenser og figurer er fortsatt egne gjenstående oppgaver.

SceneHd beregner kjent full lysstyrke fra PIV-palett og indekshistogram. Faktisk lysstyrke summeres over hele kildebildet, ikke bare y100. Visning bruker lag.lysMaks ved toning; dette forhindrer lyse HD-bilder under originalens første svarte fade og fungerer for message.piv med svart midtrad. bg2a.PIV og bg8.PIV vises i program-sluttgrenen, aktivert av bit7 i ordet på chip $3e0. Denne grenen testes med kontrollert flagg, ikke full gjennomspilling.

BG2a har indeks0-hull til underlag/forgrunn. Kildematching ignorerer bare disse hullene og kontrollerer resten av hele rammen med 85 prosent minimum, inkludert den faste rustningen. Matching av bare venstresiden er avvist fordi en annen Stonehenge-scene kan ha samme venstre bakgrunn. Indeks0-underlaget og animerte avvik forblir originalgrafikk. Kjent PIV-lysMaks brukes direkte, saa en tidligere lys palett ikke senker senere foto permanent.

## Nytegnede objektikoner og kildeidentitet, 11. oktober 2026

Originalmanual, originale spillbilder og disasm/mog.s bestemmer motivet. Highwood ligger i nordvest og Waterdeep i sørøst; eldre ikonnavn var omvendt. KI000..002 er Moonstones. KI011..015 er Haste, Hawk, Acquisition, Wyrm og Protection i kodens rekkefølge. KI019/020 er paddeliv etter Math-forvandling. MI010..014 er Gem of Seeing-kartkuler med ridderfarget sokkel, MI015..018 Hawk-teleportmål og MI043..046 statiske paddemarkører. Sistnevnte er ikke fire animasjonsbilder. MI034..041 er derimot åtte drageanimasjonsbilder. KI045..049 er allerede aktive månefase-PNG-er via poseruten. Fravær i icons.json alene betyr derfor ikke manglende HD.

Rullene bruker nytegnet blankt pergament og originalens nøyaktige hull-/blekkonturer. KI031..033 er samme kiste i 59x53-unionen fra sub_08b810, ikke tre gjenstander. KI017..020 velger separate genererte fargebilder for de fem dokumenterte parene i venstre 28/29 eller høyre 30/31. Kartets 31 er levende valgkant. 19 er dokumentert skygge rundt hjelm/grav, men intern brun hals i Gem of Seeing og øyne/munn i paddemarkører; det må ikke vernes globalt. Kroens faste ikonoverlegg ligger på renderOrder 3.5 under HD-tekst 4.

Kunst-/kildespor og gjeldende leveransebevis ligger i art/hd-remaining-icons-2026-10-11/. Pakkeren bruker immutable originalmetadata fra 4365315 og binder aktivering til faktisk gjeldende manifesthash, slik at samme kildepakke kan gjenbygges etter aktivering. De 26 eldre rasterrutene og alle 75 bakgrunner skal forbli identiske. Nye ikoner krever motivkontroll i tillegg til tekniske hash-/runtimeprøver.

Kartets vannrotering fra mog.s 0aafe4..0aaff4 og 0abef0..0abf30 gjelder indeks 21..23. map-landmarks/004 og /005 må godta akkurat denne reference_palette_cycles-gruppen; /005 trenger også kildepalettens hvite indeks 21. Uten dette faller de tilbake til pikselgrafikk ved vanlig kartanimasjon. Det endrer ingen råbilder eller øvrige kontrakter.

## Originalformet UI og font, 11. oktober 2026

Oppfølgingen i art/hd-ui-backgrounds-2026-10-11 har398 PNG-ruter,404 manifestfiler,79 bakgrunner og124 ikonkontrakter (103 raster,21 kildefaste UI-konturer). MI021-028/030 bruker bare indeks31 og beholder levende valgpalett. MI032 er blankt meldingspergament. KI038-044 er seks statusetiketter og NEXT KNIGHT. sel001 er en64x76 valgramme, ikke riddergrafikk. mys002-005 er Exit,OK og piler; mys000/001 er donasjonssekker; mys006/007 er healer-/mystikerøyne og regnes som figurfragmenter. dice000-005 er seks DragonDice-symboler, ikke prikkterninger.

tools/hd_trofast_font_bygg.py/.cjs bruker originalbanker, utvidet planmaske og kildeformer til142 glyfer pluss bold074/075. Logo073 bevares. Gamle hd_tekst_bygg.py sperres hvis disse fontene er aktive. UI-konturer kobler diagonale strokes og hull uten å endre originalpikselmidtpunktene. Tre KI-rankekandidater ble avvist ved silhuettkontroll og er ikke aktivert.

Butikkhash e868fda9 er to buer med tre søyler, der midtsøylen deles. Inventarhash94e65527 er en bue med to søyler. bg1b.PIV er et sammenhengende skogsbilde, ikke hele den rullende intrografikken. bg7.PIV viser flat vannvirvel i y153-199; regionen over beholdes original. Egne HD-mapper bruker utgivelsens sceneidentiteter med originalbank-SHA selv etter at standardlastingen stoppes. Bare tilgjengelige overlegg får fjerne originalen; lastede egne pakker beholder lag i Original-modus for engangstegnet tekst. Logo-utsnitt utenfor faktisk PNG avvises til fullramme med bevart sideforhold.

Bestillingsgeneratoren utvider CEL-planmasken før deduplisering og maskeflagg. HE3/031 er HE-kopi av KN3/031, ikke en selvstendig maskeløs rute.156 selvstendige maskeoppgaver og102 HE-kopier. Grånormalisering krever eksplisitt --graa-referanse; ukjent eller endret kildebank avvises. Gjeldende CSV har1796 rader etter deduplisering, inklusive11 ikonmaterialer og fem bakgrunnsrevisjoner; kildeformer til fontene er aktive.

## Kompletteringsarbeid, 11. oktober 2026

Den nyere pakken avløser tallene over:411 PNG-ruter,417 manifestfiler,81 bakgrunner.11 separate ikonmaterialer, fem bakgrunnsrevisjoner, gullmateriale i nøyaktig original logoform og to fullstendige rullestriper er aktivert. Materialene er bundet til kildegeometri; frie logo-/rankeutkast med feil form er ikke geometrigrunnlag. Bestillingen har1779 selvstendige figurmastere med2040 konkrete ruter. Math/Wi1.C015-020 bruker aktiv ridderpalett i indeks6-10, så162 mastere og102 HE-kopier trenger maske,264 totalt. Blå og rød Math er målt i originalspillet.

Program-observatøren ved original PC$08c214 registrerer målbuffer og kilde uten å erstatte originalrutinen. Intro/slutt kan levere385 figurruter. Tegnelistens eksisterende24-byteformat og lagringsformat er uendret. Introens .stile bruker10x48 fliser på32x25 fra bg1a/bg1c/bg1b; co.stile bruker bg7. Begge rekonstrueres til320x1200. HD-filer6b258d27 og0df34a83 er1280x4800. Synlig y finnes med kildepiksler, ikke ved blind bruk av programmets fremtidige rulleposisjon. Full bank0-kontroll avviser annen sluttscene; filrevisjon nullstiller kildecachen.

Emcc3.1.74 finnes lokalt i /home/tombonator3000t/.cache/moonstone-emsdk-3.1.74. Ny faktisk WASM er brukt til141 ikon-,47 bakgrunns-,35 import/logo- og58 program/rullekontroller.25 hook-sammenligninger samt27 intro- og27 sluttfiler er byteidentiske mot originalkjøring/kontrollbygg. Sluttprøven bruker eksplisitt originalt seiersflagg, ikke full gjennomspilling. Figurer produseres separat og er fortsatt på restlisten til egne kilde-, palett-, visuelle og runtimeprøver er bestått.


## Foerste separate figurleveranse, 11. oktober 2026

PR #32 er offentlig verifisert, main7bb8c13, bygg38167880982. Neste lokale leveranse har481 PNG-ruter,487 manifestfiler og81 bakgrunner.44 separate nye mastere:26 KN4.ob og18 hen1.c,25 kildeidentiske kopier, en maske paa KN4/025. Bestillingen teller1735 mastere/1971 konkrete ruter;163 mastermasker pluss102 HE-kopier,265 totalt. Dice006/007 bruker levende ridderfarger6..10 fra tav.piv, ikke dice.piv. Math-fastfiguren i WI1.P er en egen oppgave utenfor CEL-listen.

Aktivering krever eksplisitt gjennomgaatt indeks, originalbank/utvidede kildeindekser, eget raabilde/prompt for hver master, eksakt4x-RGBA, kildekorrekt maske og samme PNG i faktisk runtimebevis. tools/hd_figurer_aktiver.py har negativ kontroll i hd_figurer_aktiver_sjekk.py. Kildemasker teller som PNG-importer, men ikke egne GPU-bilder i Visning.hdAntall; standardtesten skiller dette.

Standardpakken prioriterer fem eksisterende hele KN1-poser over KN4/001 i ganganimasjon. Derfor beviser standard-kontakt001 eksisterende helpose og lastet ny tekstur; isolertkontakt001 og alle rute-fixturer beviser selve nytegningen. Faktisk KN3-angrep med KN4/000 viser den separate nye vaapenruten. Naar KN1 er separat ferdig, kan de eldre poseproevene pensjoneres med egne kontroller. Math-tilgjengelighet maa beregnes uavhengig av Original/HD-valg, ellers endres forgrunnsidentiteten og animasjonsfragmenter kan avlyses ved retur til HD.

PR #33 er publisert, main84a8e4e, hovedbygg38169385599. Offentlig HTMLd90dc81f og manifest61fb0076 er byteidentiske med lokal leveranse; alle70 nye PNG-hasher kontrollert. Faktisk offentlig KN4/000 har11 beståtte kontroller, Stonehenge18 ruter har54, uten nettleserfeil. Kvitteringer i art/hd-completion-figures-2026-10-11/verification/public/.

To separate MYS-øyefragmenter006/007 er nå godkjent og aktivert lokalt, men ikke publisert:483PNG/489filer,1733 mastere/1969 konkrete ruter gjenstår. Tavernaens dice006..009 er hanske/arm;010..022 er TRE kastede terninger, ikke hanskefragmenter. Originalsekvens0ad76e tegner009 fast mellom de bevegelige terningrutene. Den frosne queue.json beholdes med separat source/identity-corrections.json; generatoren er rettet. Feil hanskeutkast010/011 skal aldri aktiveres. TAV.PIV har en ekstra innbygd spillerfigur utenfor CEL-listen med levende kappe/fjærindekser6..10; denne må følge faktisk ridderpalett.

Neste lokale figurleveranse har718 PNG/724 filer,81 bakgrunner. Den legger til237PNG fra KN3/HE3/RATMEN129ruter+90masker,TROLL16,MYS2.81 selvstendige kilder er håndtert;77nye fotomaterialer og fire bevarte svarte skygger. Restlisten1654mastere/1824ruter er regenerert. Generic aktiveringsport validerer HE-flytting6..8→9..11, allerede aktiv masterkontekst, frosset materialpost og ekstra råmateriale.72 egne regressjonsporter. DICE010..022 er tre terninger. TAV sin innbakte spiller ligger i[90,65,225,188],7417 kildesilhuettpiksler og3682 levende6..10piksler;16 barmaidpiksler skal ikke følge spillerpaletten. Ny ren bakgrunnskandidat finnes, men spillerplate, DICE og Math må godkjennes samlet før aktivering.

PR #34 er offentlig, main efa5be2, bygg38174386563 grønt. Offentlig718PNG/724filer er kontrollert mot frosset614f803, ikke mot den senere arbeidsmanifesten.237nye PNG eksakte; KN3-kamp15,TROLL16ruter84,MYS-scener15 består. De fire OV1-forgrunnene bruker nattpalett fra naturlig intro3200: efoy indeks24..27 er blaacyan, stein19..22 brun og gress4..7 blaagraa. Global combat-preview med roede blader er ikke deres fargefasit.

Tredje lokale figurleveranse:1145PNG/1151filer/81bakgrunner.206kildemastere håndtert,201med nytt fotomateriale og fem bevarte svarte skygger.269konkrete ruter+160masker+tre ekstra embeddedfiler;432nyePNG, én TAV-bakgrunnsrevisjon, fem hele posePNG pensjonert.1448mastere/1555ruter gjenstår,8KN5-masker, ingen HE-kopier. Source/runtimebinding i delivery-progress-003.json. Standard-Hd antall poser må hentes fra hashkontrollert poses.json; hardkodet fem henger når listen er tom. OV1 nattforgrunn har kjent bakgrunnsindeks3 som intern padding, ukjent forgrunn avvises fortsatt. TAV levende6..10 maskeres i renderOrder2.5 under originalforgrunn3/CEL4, med7431kildemaskepiksler,3682levende og16barmaidpiksler utenfor. DICE006/007 deler210kildefaste draktpiksler med TAV-spillerplaten; hanskefoto/alfa beholdes. WI2.P har ingen ekstra innbakt Math, figuren kommer fra Wi1.C015/017/019.

KN5/058..064 er brennende ridder i original dragekamp:9/11/15 er faste rødfarger,29..31 gul/oransje ild. Bare6..8 følger aktiv ridder. Faktisk original CPU med blå/rød ridder bekrefter dette. Bestilling og masker rettet fra15 til8 masteroppgaver; høye indekser må ikke leses fra global cyan/rosa forhåndspalett.

## Guardian-bakgrunn kontrollert,12.oktober2026

Guardian-kampens rene bakgrunn er `data/test` PIV005, FNV1a `cbc31cbf` over40000 bitplanbyte, kildefil-SHA8e8d950fb3dfb1b24b3a866c42254e8fc76d9f5d4567cef7843a08f61fd072a5. Original kamp1243 bekrefter samme bitplan, indekser, RGBA og200 palettrader fra Guardian-initialisereren. `production/guardian/export-background.py` gjenskaper referansen fra originalZIP. Den manglet blant81HD-bakgrunner iPR37; en egen nytegning er lokalt aktivert som82. bakgrunn med220 faktiske kontroller, foreloepig upublisert. Antall bakgrunnsfiler alene bekrefter ikke full dekning.

## Sjette figurleveranse, 12. oktober 2026

Den lokale pakken har1623PNG/1629filer/82bakgrunner etter125nyePNG,122kilderuter.120 egne genererte figurmastere er112 fotomaterialmastere og aatte flate kildeeffekter Dragon5/023..030 med foreloepig konservativ identitet; dessuten en original svart Ratmen-skygge og ett Dragon5-alias. Alle1504filer fra PR37 er uendret. Guardian demon1/000..047 er aktiv, demon2/000..014 er aktiv; neste banker gjenstaar. Restlisten1084mastere/1153ruter/97masker er fortsatt uferdig.

Alle32rene terrengkompositter fra originalens fire Test-baser og flisark har eksakte aktive HD-hasher. Test000..003 er flisark. Guardian-initialisereren fjerner dekorasjoner og bruker rawTest005/cbc31cbf, som naa har egen HD-fil. Senere originalCEL-skriving til08cde8 kan endre bakgrunnshashen; slike deltaer kan fortsatt gi Original-fallback. Ingen ekstra malerier bestilles bare paa grunn av disse hashene. Audit og begrensninger er frosset i production/guardian/verification/test-background-audit-v1.

Sjette figurleveranse er offentlig verifisert: PR38 flettet som798b926, hovedbygg38191612724 har fem vellykkede jobber.125nyePNG, manifest899a380b og HTMLe79f2dc4 er bytekontrollert offentlig. Guardian550,Demon2-retry187,Dragon97,Beast49 og slutt1702 gir2585 bestaaende kontroller; foersteDemon2-forsok feilet kun paa lastetidsgrense og er bevart. Kvittering verification/public-006/publication.json. Kildebundne visningsrettinger for007 er fryst separat fra006.

Sjuende lokale rutegruppe:1741 PNG/1747 filer/82 BG,98 nye ruter,118 PNG,93 egne fotomastere,fem eksakte aliaser og20 masker.991 mastere/1055 ruter/79 mastermasker gjenstaar. Teknisk standard4436 og fil/kilde5449 bestaar, men publisering er holdt for synlige bakgrunnsblokker over Balok1/004 og002 ved faktisk pose2200. Dette er ikke ny kildegeometri eller aliasfeil. Ratmen-bakgrunnens eksakte sene deltaer er19 svart5+77 roedt15, fra R2/056 og R1/051 med caller087b34/target0a2cd6;007 har forventet Originalfallback der. Ikke kall hele HD-arbeidet ferdig.

Aattende lokale kohort har1963 PNG/1969 filer/82 bakgrunner og202 nye ruter:195 egne fotomaterialmastere,sju kildeeksakte originalruter,20 masker. Alle1747 filer fra007 er uendret. Frontend008 er fryst med render6b93be5b og scenes189eed86, samme originalZIP/WASM/core/hd.js. Balok-glyfvernet fjernes bare ved eksakt akseptert figur-HD og dokumentert eierskap; Ratmen Wa2-bro krever eksakt64000-indekskomposisjon og riktige originale bakecaller/target/ankre. Full opak originalforgrunn bevares. EndeligHTMLb1e3496e og manifest6e8d7646 brukes i standardjobber. Rootvisual008 beviser at007s Balok-blokker er borte. Status er foreloepig lokal, publisering er ikke bekreftet.790 mastere/853 konkrete ruter/59 masker gjenstaar;009-kandidater telles ikke foer aktivering.

## Riddervalg og oppstart, 12. oktober 2026

Standard-HD må samle tegnelisten mens pakken lastes, før hdPakke har bilder. `StandardHd.start` setter tvungetLag, og `Visning.brukerListe` må også følge dette flagget. Portrettene sel.cel2..5 og tittelfonten tegnes bare én gang; uten tidlig innsamling blir de stående i Original ved raskt introhopp og sen HD-lasting. Riddervalget har tom bakgrunn045a1ac5 og får HD gjennom figurene, så hdKontroll().bakgrunn=hd er feil test her. `hdstart1` blokkerer nedlastingen til portrettene er tegnet og krever fire faktisk godkjente HD-portretter etterpå.

Portrettenes x-posisjoner leses fra originaltabellen $8F516, y80..155 og bredde64. Bare ledige figurer i $8F4A2 kan klikkes. MENY_CMD_SELECT (10) gir et ventende portrettvalg utenfor tittelmenyen. Hooken på $081D04, etter btst og før fire-grenen, velger figuren og fortsetter originalens navneflyt. $081D00 ville blitt hoppet over etter C-erstatningen av les_joysticker. Nettlaget sender gjestens betrodde spilleridentitet og port til vertens valgbehandler. Automatisk fordeling følger ridderen som har turen; faste porter krever p2 eller begge uavhengig av spillernummer. Samme kontroll brukes lokalt. PEKR-delen har nå to byte, peker_fire og ridder_klikk. Fe markerer et brukt klikk frem til neste originale valgløkke, så et dobbeltklikk ikke velger for neste spiller. Eldre PEKR-deler får standardverdier, og state_format_id skiller nettutgavene. Originale spillfiler og HD-bilder er uendret.

## Grafikk og kartmus, 12. oktober 2026

StandardHd laster kildeverifiserte bakgrunner uavhengig av hele figurpakken. Tekst,
menypil og deretter portretter prioriteres. Base og bakgrunner har egne
AbortController-objekter; en fatal figurfeil skal ikke sperre senere bakgrunner.
Bare nettfeil/HTTP408,429,5xx proeves inntil tre ganger. SHA-/lengdefeil avvises.
SceneHd maa identifisere baade PIV- og rullekilder under lasting, med de samme
kilde-, palett- og pikselkontrollene som etterpaa. Bakgrunnscachen er fortsatt fire.

Lesbar HD-tekst tegnes fra bekreftede originalglyfer. Bold bruker innebygd
UncialAntiqua med felles grunnlinje; Small bruker innebygd DejaVuSansMono-Bold.
Small.font071 er skraastrek, selv om eldre text.json deler Bold sitt understrektegn.
Unntaket er bundet til bank- og indeks-SHA. KI038..043 er de seks statsetikettene,
ikke fontglyfer; deres klare tekst har egen kildekontrakt. Originalmodus beholder
originalpikslene. Tooltipens palettrad kan gi forIdx=$FE; allerede validerte egne
tekstpiksler maa ikke maskeres igjen av det generelle figurvernet.

Next Day-rutene KI045..049 kan fjerne ensfarget blaafelt bare naar faktisk vist,
kildeverifisert ch.piv-HD-himmel overtar. Ellers beholdes originalfeltet.
Po.cel000 er den kildebekreftede hardwarepekeren. Aktiv originalpekerposisjon kan
brukes til aa vise hele pilen foran HD-soeyler, ogsaa ved klipping mot skjermkant.

MENY_CMD_KART15 setter bare maal og retning ved bildegrensen. Patch$0AAD00 etter
joysticklesingen lar originalkartet styre fart, terreng, grenser og trekkbudsjett.
Klikk gjelder ikonets fotpunkt; hoeyreklikk/manuell input/ny tur/sceneskift avbryter.
PEKR-delen er naa18byte, med maal og heltallskoordinater; eldre1/2byte faar standard.
Netteieren kommer fra betrodd spillernummer eller p2/begge i faste porter, aldri
fra koordinatpakken. Ugyldige koordinater og CEL-pekere avvises foer minnet leses.

## HD-retensjon og lair-visning, 12. oktober 2026

KI000..044 må beholde kildebekreftede instansspor når transparente felt får nye tall eller hardwarepekeren flytter seg. Kandidatretensjon bindes til original KI-bankSHA02287e89 før HD-PNG/ikonmanifest er tilgjengelig. ForberedHd beholder full kilde-/palett-/pikseleierskapskontroll. SEL001-rammen og SEL002..005-portrettene deler mål og posisjon, men må ha separate spor; kjent SEL-bankSHA30f6b154 binder denne regelen. Direkte grønt museklikk kunne ellers slette blå/grønn HD selv etter full lasting.

Original lairseier registreres ved $080D1C i lair+$14. Originalen fjerner posisjonen ved $080D80 først når gull+$08 og alle24 lootbytes er tomme. HD-visningen skjuler etter brukerens ønske den eksakte9x5-portkompositten straks seierflagget er1; ingen loot, originalposisjon eller kjernelogikk endres. SourceMOG/MI/testSHA, opcode, tabellgrenser og faktisk scanout bindes før skjuling. Originalmodus beholder originaloppførselen. Kartet har24 lairs; porten ved24,24 får ny map-icons/026 uten å flytte eksisterende000..025.

Ny Moonstone-logo er generert med innebygd image_gen, med originalen som formreferanse. Den glatte2440x581-RGBA-ruten erstatter den eldre pikselkonturlogoen. Original kildebredde305/anker bevares via fit:width. Råmaster, prompt, pakking og faktisk tittelskjerm ligger i art/hd-logo-2026-10-12. HD-bestillingen godtar bare den nye eksakte PNG-SHA11c779b3 som ferdig logorevisjon.

RATMEN1.CEL063 er et44x35-lauvfragment som gjenbrukes med terrengets globale palett. Wa2 har grønne22/24/25/28, mens Gll3 gir andre farger på de samme indeksene. Den grønne HD-ruten må derfor ha egen kilde-/palettgate. Native originalmåling viser innfade=min(kanal,n) og utfade=max(kanal-n,0) per4bitskanal, med felles n. Hele bladpaletten5/22/24/25/28 kontrolleres på alle synlige opake rader, også når klipping bare viser svart5. Kontinuerlig fotografisk RGB kan ikke bindes til bare de synlige originalcellene. Råfoto og opak alfakontur beholdes ved revisjonen; andre paletter får konservativ Original for063.


## BLO-HD 2026-10-12
- blo.cel har41 uavhengige 0/15-ruter, bankSHA d83857454db7f5113598c6a41a46e45f62ecb4936637372b4807e22125bf699e, planmaske15. Original088c86..088c92 setter kampindeks15 til c00. Native min/subtract-fading gir13 eksakte rødnivåer0..204 i steg17. Alle41 har nå separate genererte væskematerialer med kildekontur4x. KN5.ob sine65 skadefragmenter var allerede HD.
- render.js blodNivaa binder bank, mål og synlig radpalett, gir absolutt blodlys og beholder Original i fremmed kilde/palett. Kjerne/save/input er uendret. lastHdPakke venter på originalbankhash før BLO installeres.
- tools/hd_blod_sjekk.cjs skiller kontrollert original Troll-kamp fra frontendfragmentfixturer. Native CPU ser27 BLO-ruter; nettleserkampen18 synlig HD-godkjente. Hele41 normal/speilet, fire klippkanter,13 fader, fremmed bank/palett og full save/retur prøves. Ingen full naturlig kampanje påstås.
- Produksjon/brief/proveniens: art/hd-blood-wounds-2026-10-12. Aktivering krever full runtime- og visuell SHA-kvittering. Etter denne leveransen:2005PNG/2011filer,749 manglende mastere/812ruter/59mastermasker. Separate009-kandidater er fortsatt uaktivert her.

## Månen, Ratmen og sykdom (12. oktober 2026)
- Alt står i docs/undersokelser/maane.md. Verktøy: tools/maane.py (fasene) og tools/maane_kamp.py (stein, Ratmen, smitte, sykdom i ekte kamp i lair 0).
- Fast mem: Ratmen og de andre kampfigurene ligger over $200000. Bruk mem_read8/16, ikke chip[], når en peker kan gå dit.
- Ratmen: +$4D = $24, slaghandler dat_0855ce. Type 4 bitt smitter ($82), type 8 bare skade. Andre angrep via dat_0858a8 og sub_085ae0.
- Sykdom trekkes i sub_080704, som bare kalles ved faseskifte.
- Valget game_maaneregler lagres i delen MAAN. En lagring vinner over --maaneregler, så fixturer for valget må lages med flagget.
- --vakt tar bare én adresse (siste vinner).
