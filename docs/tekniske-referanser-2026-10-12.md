# Tekniske referanser vurdert 12. oktober 2026

Brukerens innlimte kildevurdering er nyttig som grunnlag for undersøkelser. Den
endres ikke til nye spillregler eller en utskifting av motoren. Dagens feil gjelder
HD-visning og musekontroll. Den delte ChatGPT-adressen viste «Shared chat not found»;
vurderingen nedenfor bygger på den innlimte teksten, repoet og kildene som ble åpnet.

| Referanse | Bekreftet i kilden | Bruk i vårt prosjekt |
| --- | --- | --- |
| [WHDLoad Moonstone](https://www.whdload.de/games/Moonstone.html) | Dokumenterer blant annet synkronisering, minnefeil, tastatur, lyd og introhopp. Oppgir også endret gullgrense og tilfeldig startfordeling. | Bruk endringsloggen til å formulere konkrete regresjonsprøver. Den dokumenterer ikke påstanden om Black Knight-sporing eller save/restore. Ingen udokumentert AI-retting innføres. |
| [OpenMoonstone](https://github.com/joetsoi/OpenMoonstone) | Rust/Python, DOS-data, kampmodus og kampanjekart under utvikling. Siste commit kontrollert via GitHub API: 60b253ec, 15. mai 2023. | Mulig sammenligningsgrunnlag for kamp og dataformater. Det er ikke en komplett C++-port som kan erstatte vår Amiga-kjerne. |
| [moonstone-ace](https://github.com/Jarskih/moonstone-ace-public) | C++-rekonstruksjon for Amiga 1200/WinUAE, med originaldata og rutinesammenligninger. Kontrollert hovedrevisjon: 2bc43a2e. | Modul- og rutinekart kan hjelpe ved senere dekompilering. Plattformkode og regler må vurderes hver for seg før eventuell gjenbruk. |
| [Undines Moonstone 2026](https://github.com/Undine1/Moonstone-A-Hard-Days-Knight-2026) | Windows-versjon med innebygd 68000/OCS-kjerne. README oppgir troll-/Moonstone-rettinger og at sykdom bevisst er fjernet. Nettspill er ikke testet. Kontrollert hovedrevisjon: 74f7fde0. | Interessant teknisk referanse for konkrete krasj. Dokumenterte regelendringer overføres ikke til vårt originalspill. Påståtte rettinger er ikke verifisert ved egen kjøring. |

Vår gjeldende kode er C99/SDL2, Amiga-kjerne og WebAssembly/Three.js. `decomp.c`
registrerer to C-erstatninger: joystickrutiner ved $082008 og $081F92. De øvrige
spillrutinene kjøres fortsatt som originalkode. `tools/check_hooks.py` sammenligner
samme inndata med C-erstatningene og originalrutiner byte for byte.

Det mest nyttige rådet er å gjøre hvert avvik repeterbart: lagre originaltilstanden,
gi samme inndata, sammenlign minne og bilde, og kontroller faktisk visning etterpå.
Månefaser, Black Knight-jakt og rapporterte krasj er egne undersøkelser før en
eventuell retting. Nye multiplikatorer, sideoppdrag eller endret kampbalanse krever
et eget oppdrag. Museklikk på kartet skal bruke originalens bevegelse og terreng,
med samme turer, i den eksisterende deterministiske kommandooverføringen.

Ingen kode eller binærfiler fra referanseprosjektene er kopiert eller kjørt.
