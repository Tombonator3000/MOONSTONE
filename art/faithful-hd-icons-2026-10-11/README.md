# Tre motivrettede HD-landemerker

Leveransen inneholder Math sitt tårn, Valley of the Gods og tre trilitter i skogklaringen. Se [motivbeskrivelsen](../../docs/hd-ikonmotiver.md) og [sammenligningen](semantic-correction/comparison.html).

De tidligere utkastene misforstod motivene. De er ikke del av den aktive leveransen. Den lokale arbeidsmappen inneholder bevarte eldre kandidater med egne pending-registre; de er ikke godkjent grafikk og inngår ikke i dette inncheckede settet.

`assets.json` har bare de tre valgte bildene. `semantic-correction/*.png` er urørte generatorresultater. JSON-filene ved siden av lagrer prompter og opphav. `references/landmark-crops/` inneholder originalutsnittene. Brukerens originale tårnscene ligger i `references/user/`.

Bildene pakkes i 8x størrelse til `packed/` og `web/hd/map-landmarks/001..003.png`. Dalen og skogklaringen bruker hele originalutsnittet og myk kantblanding i renderer. Tårnet har transparent bakgrunn. Originalens kildefil og palett kontrolleres; fading og den kjente vannsyklusen tillates. Andre paletter beholder originalutsnittet.

Gjenta pakking uten ny bildegenerering:

```sh
python3 tools/hd_ikoner_landemerker_rett.py
node tools/hd_ikoner_raster_pakk.cjs
python3 tools/hd_ikoner_raster_aktiver.py
python3 web/pakk.py web/build/moonstone-core.js web/build/moonstone.html
```

Verifikasjon ligger i `verification/`. Rastertesten kontrollerer bildefilbevaring og paletter. Landemerketesten kjører en naturlig karttur, fjerner og gjenoppretter hvert bilde for å bevise at det faktisk tegnes, og kontrollerer originalfallback og uendret emulert tilstand. Skjermbildene er faktiske spillbilder. Generatormasterne er ikke spillbilder.

Bakgrunner, figurer og de øvrige ikonene er fortsatt ikke ferdig konvertert. Se [dekningskontrollen](../../docs/hd-status-2026-10-11.md).
