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
