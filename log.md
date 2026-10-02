# log.md

Logg over alt som er gjort i prosjektet, nyeste nederst. Tid i UTC.

- 2026-10-02 09:07 UTC: Startet arbeidet. Lest instruksjonene i Moomesa-repoet (AGENTS.md, memory.md, todo.md) og nettverkskoden i guild-life-adventures (PeerJS, HiveMQ-romliste) for å bruke samme oppskrift her.
- 2026-10-02 09:12 UTC: Pakket ut `Moonstone CD32.iso` fra zip-filen. Det er en WHDLoad-installasjon (Moonstone.Slave av Wepl) med kjørbare filer `program` og `mog` og 150 datafiler.
- 2026-10-02 09:20 UTC: Disassemblert slaven. Fant lasterutinen, patchlistene for program og mog, CRC16-sjekken og spillets egen LZ-utpakker. Sjekket at hunkene legges rett etter hverandre (patchadressene treffer riktige instruksjoner).
- 2026-10-02 09:22 UTC: Opprettet prosjektstrukturen og kopierte Musashi (68000) fra Moomesa.
- 2026-10-02 09:40 UTC: Skrev emulatorkjernen i C: minnekart, Copper, Blitter (flate, fylling og linjer), Denise (bitplan, sprites, dual playfield, EHB, HAM), Paula (DMA og manuell), CIA (tidtakere, TOD, tastatur), WHDLoad-funksjonene (LoadFile, Relocate, Patch, Control, Delay, CRC16 m.fl.), filsystem fra zip/ISO/mappe, RNC-utpakker og tilstandslagring.
- 2026-10-02 09:41 UTC: Første kjøring: svart skjerm, CPU-en ventet på slave+$1C4. Årsak: SR $2700 ved start. Med SR $2000 kjører introen. music.cmp har et eldre RNC-hode som ikke kan pakkes ut av WHDLoad; nå lastes den som den er, slik WHDLoad gjør.
- 2026-10-02 09:42 UTC: Introen (månen, druidene, Stonehenge, tittelteksten) og tittelmenyen i mog kjører med riktige farger og lyd. 9000 bilder tar 16,5 s.
- 2026-10-02 09:47 UTC: SDL2-frontend (port/src/frontend.c): vindu med skarp skalering, lyd, tastatur til Amiga, joystick på piltaster/Ctrl og talltastatur, spillkontrollere som CD32-padden, lagring av tilstand. Testet i Xvfb. Windows-bygg (moonstone.exe) kryssbygget med MinGW og SDL2 2.30.8.
- 2026-10-02 09:49 UTC: Fant hvordan spillet leser joystickene: $81F92 leser JOY1DAT til $8D9A2 (port 2) og JOY0DAT til $8D9A0 (port 1). Kampfigurene har en byte på offset $B: 1 = port 1, 2 = port 2, 4 = datamaskinen. Manualen på ISO-en sier 1-4 spillere med 1 eller 2 joysticker.
- 2026-10-02 09:50 UTC: Brukeren sa at Moonstone er abandonware, så vi kan være enklere med spillfilene. Nettsiden laster nå spill/Moonstonecd32-AMIGA.zip automatisk hvis den ligger ved siden av siden.
- 2026-10-02 09:55 UTC: Nettleserversjonen: kjernen som WebAssembly (port/src/web.c), three.js-visning med filtrene skarp, rene piksler, myk og CRT, lyd med AudioWorklet, tastatur, spillkontrollere og berøringsknapper, lagring i IndexedDB. three.js (r186, bare delene vi bruker), PeerJS 1.5.5 og MQTT.js 5.16 ligger i web/vendor. web/pakk.py lager én HTML-fil.
- 2026-10-02 10:05 UTC: Nettspill med PeerJS: verten kjører spillet, gjestene får hele tilstanden (gzip) og deretter inndata per bilde, og filer spillet laster videresendes. Sjekksum hvert 120. bilde. Romliste via HiveMQ (MQTT over WebSocket). Testet med to nettleservinduer mot en lokal PeerJS-server (proxyen her slipper ikke WebSocket til PeerJS Cloud): gjesten styrte menyen, valgte ridder og kom til kartet, 10 av 10 sjekksummer like.
