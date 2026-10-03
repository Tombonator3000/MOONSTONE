# memory.md

Varige fakta om prosjektet. Oppdateres når vi lærer noe nytt.

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
- Introen ser på den siste tastaturkoden uten slipp-biten, og bare mellom trinnene.
  Esc huskes, men det kan gå opp mot 200 bilder før mog lastes. En annen tast etter Esc
  (Return som slippes) gjør at introen ikke slutter. Målt med moonstone-headless
  `--press F:esc:4`: alltid mog innen +200 bilder, aldri med Return i tillegg.
- app.js `introTaster`: fire, Enter, mellomrom og trykk på skjermen blir Esc i 4 bilder;
  Enter og mellomrom sendes ikke til spillet i introen. Det første trykket slår bare på
  lyden (nettleseren krever det), unntatt med invitasjon. Esc er ikke en brukerhandling
  for nettleseren, så lyden prøves på nytt ved neste trykk.
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
- Testtilstanden $S/hv/kart.sav må lages på nytt når H eller M2 endres (STATE_VERSION 8,
  ikke sluppet ennå). Uten tilstand: --press 1400 med --hver før return i 1500, så turen
  starter med de fjerne ridderne.
- Valgene på kartet venter på tastene 1-9 (`--press 1900:2:4` velger nummer 2).
- Nettlesertest: $S/test26.js (vert og Kari, Separate, gange, farger, verten går).
  Playwright ligger i /opt/node-tools/node_modules (NODE_PATH).
- Dueller (steg 3): HVER_BLOB (hele ridderen som heks, 312 tegn), HVER_MEG (inn paa plass 0
  etter duellen), HVER_DUELL (maske: kan naas), HVER_AI (datamaskinen tar over), hendelser
  HVER_EV_DUELL / HVER_EV_DUELL_SLUTT via ms_hver_hendelse. Nettsiden: D i app.js (rolle 'a'
  angriper / 'b'), Nett.duellKoble (direkte PeerJS med metadata.duell), sendTilstandTil,
  tilstandsMottaker. Protokollversjon 3.
- Kampposisjonene: +$04 x og +$08 y (ord) i ridderstrukturen. Kampen laster i om lag 8 s.
- Tester: $S/test27.js (duell, verten angriper, testspiller styrer etter posisjonene),
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
  SLIPPES; $9B716 er tabellen over tastene som er nede.
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
- Nettlesertest for Turns-kontrollene: $S/test35.js.
