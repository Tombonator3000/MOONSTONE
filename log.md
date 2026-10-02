# log.md

Logg over alt som er gjort i prosjektet, nyeste nederst. Tid i UTC.

- 2026-10-02 09:07 UTC: Startet arbeidet. Lest instruksjonene i Moomesa-repoet (AGENTS.md, memory.md, todo.md) og nettverkskoden i guild-life-adventures (PeerJS, HiveMQ-romliste) for å bruke samme oppskrift her.
- 2026-10-02 09:12 UTC: Pakket ut `Moonstone CD32.iso` fra zip-filen. Det er en WHDLoad-installasjon (Moonstone.Slave av Wepl) med kjørbare filer `program` og `mog` og 150 datafiler.
- 2026-10-02 09:20 UTC: Disassemblert slaven. Fant lasterutinen, patchlistene for program og mog, CRC16-sjekken og spillets egen LZ-utpakker. Sjekket at hunkene legges rett etter hverandre (patchadressene treffer riktige instruksjoner).
- 2026-10-02 09:22 UTC: Opprettet prosjektstrukturen og kopierte Musashi (68000) fra Moomesa.
- 2026-10-02 09:40 UTC: Skrev emulatorkjernen i C: minnekart, Copper, Blitter (flate, fylling og linjer), Denise (bitplan, sprites, dual playfield, EHB, HAM), Paula (DMA og manuell), CIA (tidtakere, TOD, tastatur), WHDLoad-funksjonene (LoadFile, Relocate, Patch, Control, Delay, CRC16 m.fl.), filsystem fra zip/ISO/mappe, RNC-utpakker og tilstandslagring.
- 2026-10-02 09:41 UTC: Første kjøring: svart skjerm, CPU-en ventet på slave+$1C4. Årsak: SR $2700 ved start. Med SR $2000 kjører introen. music.cmp har et eldre RNC-hode som ikke kan pakkes ut av WHDLoad; nå lastes den som den er, slik WHDLoad gjør.
- 2026-10-02 09:42 UTC: Introen (månen, druidene, Stonehenge, tittelteksten) og tittelmenyen i mog kjører med riktige farger og lyd. 9000 bilder tar 16,5 s.
