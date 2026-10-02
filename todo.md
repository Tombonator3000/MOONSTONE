# todo.md

## Neste
- [ ] Slå på GitHub Pages (Settings, Pages, Source: GitHub Actions) og flette til main. Privat repo krever betalt GitHub for Pages.
- [ ] HD-grafikk: logge tegnekallene til IMAGEXCEL-modulen og tegne HD-lag i three.js (docs/hd-grafikk.md).
- [ ] Finne ut hvordan .t-filene bygger kampbakgrunnene.
- [ ] Flere funksjoner i C: hovedløkken på kartet, kampsystemet.
- [ ] Spille gjennom mer av spillet med --coverage (kamper, byer, Stonehenge) for bedre disassembly.
- [ ] Assembler-utgave av disassemblyen som bygger byte for byte like filer (vasm).
- [ ] Teste nettspill mot PeerJS Cloud og HiveMQ fra en vanlig nettleser (proxyen i skymiljøet stopper WebSocket).
- [ ] Automatisk joystick etter tur i nettspill: finne variabelen for hvem som har turen, og hvem som kjemper.
- [ ] Teste moonstone.exe på ekte Windows.

## Ferdig
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
