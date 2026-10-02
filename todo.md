# todo.md

## Neste
- [ ] Flette rettelsen av workflowen (a998217 på grenen) til main, så «Run workflow» også publiserer.
- [ ] HD-grafikk: bakgrunner i HD (PIV, og .t for kampene), fargeeffekter (fading) på HD-bildene, andre tegnerutiner enn tegn_figur (tekst, menyer).
- [ ] Lage en liten HD-pakke som eksempel (f.eks. ridderne i fire ganger størrelse).
- [ ] Finne ut hvordan .t-filene bygger kampbakgrunnene.
- [ ] Flere funksjoner i C: hovedløkken på kartet, kampsystemet.
- [ ] Spille gjennom mer av spillet med --coverage (kamper, byer, Stonehenge) for bedre disassembly.
- [ ] Assembler-utgave av disassemblyen som bygger byte for byte like filer (vasm).
- [ ] Teste nettspill (også «Online Game» i tittelmenyen) mot PeerJS Cloud og HiveMQ fra en vanlig nettleser (proxyen i skymiljøet stopper WebSocket; lokalt testet med egne servere).
- [ ] Teste den nye oppstarten på en ekte mobil (lyd ved første trykk, trykk på skjermen hopper over introen, navnefeltet med skjermtastatur).
- [ ] Klikk i menyene også i PC-versjonen (meny_row_at finnes; PC slår ikke på menylappen i dag).
- [ ] Mus på andre skjermer enn tittelmenyen: velge ridder, butikker og inventar med klikk (krever å finne valgvariablene for hver skjerm).
- [ ] Teste moonstone.exe på ekte Windows.

## Ferdig
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
