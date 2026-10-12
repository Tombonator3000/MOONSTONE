# Lair-markører etter seier

HD skjuler portikonet til en beseiret lair når originalspillets første-seier-flagg er `1`. Gull og gjenstander blir liggende og kan hentes senere. Original-grafikk beholder originalens visning. Byer og andre faste landemerker følger sine eksisterende regler.

## Originalens regler

Lair-tabellen inneholder 24 poster à 22 byte. Pekeren ligger ved `$08CDB2`; hver post har loot-peker ved `+0`, gull ved `+8`, kartposisjon ved `+10/+12` og første-seier-flagg ved `+20`.

Originalkoden skriver første-seier-flagget ved `$080D1C` og åpner loot ved `$080D2E`. Etter at spilleren går ut av loot, sjekker `$080D50` både gull og de 24 gjenstandsbyte. Bare når alt er tomt, skriver `$080D80` `FFFF,FFFF` til kartposisjonen. Karttegningen ved `$0AAB8C` hopper deretter over posten. Seier og full tømming er dermed to forskjellige tilstander i originalen.

HD-regelen i `web/src/scenes.js` er bare presentasjon. Den krever kjent original `mog`/`mi.c`, verifiserte opcodes, gyldig lair-tabell, seier-flagg nøyaktig `1`, korrekt original MI-bilde 20 og et eksakt pikselmatch i hele portens 9×5-felt. Portens gjennomsiktige hjørner sammenlignes med originalterreng. Overlappende riddere eller annen markørstatus avviser skjulingen for dette bildet. Terrenget må være lastet i HD før originalporten frigis.

De 24 lair-portene bruker `map-icons/000..022` og `026`. `023..025` er bymarkører og omfattes ikke. `026` dekker den opprinnelig utelatte porten ved `(24,24)`; den bruker samme eksisterende portbilde og kildekomposisjon som de andre portene.

## Reproduserbar kontroll

```sh
make -C port headless
python3 tools/lag_lair_fixture.py --out /tmp/moonstone-lairs
node tools/check_cleared_lairs.cjs --out /tmp/moonstone-lairs-check --fixtures /tmp/moonstone-lairs
# Krever Playwright og Chrome. MOONSTONE_BUILD kan peke til et fryst webbygg.
MOONSTONE_LAIR_FIXTURES=/tmp/moonstone-lairs node tools/hd_lair_sjekk.cjs
```

Generatoren lager en ny starttilstand og går via originalkode til kamp, seier, loot, exit og kart. Det er en kontrollert kampfixtur: oppsettet plasserer ridderen ved lairen, nullstiller lairens ventetid og setter sluttkampens aktører til beseiret. Den skriver ikke loot, seier-flagg, lair-posisjon, bakgrunn eller palett. `fixture.json` inneholder alle kommandoer, minneinngrep og SHA-256 for lagringene. `*-natural.sav` bevarer ridderposisjonen etter kamp. Separate `*-view.sav` flytter bare ridderen 16 kartpiksler før original kartredraw, slik at porten kan inspiseres uten ridderoverlapp.

Tre tilfeller kontrolleres: lair 20 har 27 gull igjen, lair 18 har en nøkkel igjen, og lair 19 er helt tom. De to første beholder originalport og loot, mens HD skjuler porten. Den siste får `FFFF,FFFF` fra originalkode ved `$080D80` og forsvinner i begge visninger. Den målrettede WASM-kontrollen har 34 sjekker, inklusive uendret CPU/lagring ved grafikkbytte, andre markører/byer, kildeendringer, ugyldig tabell, ukjent flagg, overlapp og manglende HD-terreng. Denne kontrollen bruker virkelig original WASM og scanout, men en adapter for GPU/HTTP.

Nettleserkontrollen bruker faktisk WebGL og et avgrenset, SHA-verifisert kartutvalg fra standardpakken. Den lagrer bilder av før seier, HD/Original/HD-retur med loot igjen og tom lair. En egen sekvens laster den opprinnelige loot-tilstanden og går tilbake til kartet med et virkelig PC-museklikk. Den erstatter ikke den separate testen av hele standardlasteren.

Kontrollert 12. oktober 2026: 34/34 WASM-sjekker og 14/14 nettlesersjekker bestod, uten nettleserfeil. Bildene av begge porter, tom lair og faktisk muse-exit er åpnet og visuelt kontrollert. Nettleseren brukte HTML SHA-256 `013a3d5087a6fbd84eb038cb0ea5cbed7b86cde4c7d99f0da239e3eb57baeb5e` og manifest `09576ba453efbc3c26bb9716116c6e4ef3e8920d751b84192c06d952e0fd7eab`. CPU-sjekksummene var uendret gjennom Original/HD-rundturene: `1776287379` for lair 20 og `1034196009` for lair 18. WASM-kontrollen kontrollerte også uendret SHA-256 for komplette serialiserte lagringer.
