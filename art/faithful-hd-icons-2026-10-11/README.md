# Motivrettede HD-landemerker og Stonehenge-porter

Leveransen inneholder Math sitt tårn, Valley of the Gods, tre trilitter i skogklaringen og én Stonehenge-port for 23 gjentatte interaksjonssteder. Brukerens siste foto presiserer to oppreiste støtter og en overligger med åpen passasje. Math har loddrette vegger og brystning. Se [motivbeskrivelsen](../../docs/hd-ikonmotiver.md), [sammenligningen](place-correction/comparison.html) og [siste faktiske kartbilde](verification/corrected-map-hd.png).

De tidligere utkastene misforstod motivene. De er ikke del av den aktive leveransen. Den lokale arbeidsmappen inneholder bevarte eldre kandidater med egne pending-registre; de er ikke godkjent grafikk og inngår ikke i dette inncheckede settet.

`assets.json` har 26 godkjente ruter for fire motiver. `place-correction/tower.png` og `trilithon.png` er urørte generatorresultater. Portmasteren brukes ved alle 23 steder av denne typen, og brukerens nye foto ligger i `trilithon-reference.jpg`. `standing-stone.png` er det bevarte, avviste enkeltsteinutkastet. `semantic-correction/` inneholder dalen, skogklaringen og den bevarte, avviste tårnkjeglen. JSON-filene ved siden av lagrer prompter og opphav. `references/landmark-crops/` inneholder originalutsnittene. Brukerens originale tårnscene ligger i `references/user/`.

Bildene pakkes i 8x størrelse til `packed/`, `web/hd/map-landmarks/001..003.png` og `web/hd/map-icons/000..022.png`. Dalen og skogklaringen bruker hele originalutsnittet og myk kantblanding i renderer. Tårnet og portene har transparent bakgrunn, også gjennom portåpningen. Originalens kildefil og palett kontrolleres; fading og den kjente vannsyklusen tillates. Andre paletter beholder originalutsnittet.

Portene har et eget `draw_rect` på 9x11 kartpiksler, med samme midtpunkt og fotpunkt som den gamle 9x5-markøren. Matching og fjerning bruker fortsatt originalens uendrede `rect` og 45 forventede indekser. Endret status eller ridder over originalmarkøren hindrer erstatning. Forgrunnsvernet beskytter også figurer i portens visningsfelt. Landsbyene og spillerikonene beholdes.

Gjenta pakking uten ny bildegenerering:

```sh
python3 tools/hd_ikoner_landemerker_rett.py
python3 tools/hd_stedsporter_rett.py
node tools/hd_ikoner_raster_pakk.cjs
python3 tools/hd_ikoner_raster_aktiver.py
python3 web/pakk.py web/build/moonstone-core.js web/build/moonstone.html
```

Verifikasjon ligger i `verification/`. Rastertesten kontrollerer bildefilbevaring og paletter. Landemerketesten kjører en naturlig karttur, fjerner og gjenoppretter hvert bilde for å bevise at det faktisk tegnes, og kontrollerer originalfallback og uendret emulert tilstand. Skjermbildene er faktiske spillbilder. Generatormasterne er ikke spillbilder.

Bakgrunner, figurer og de øvrige ikonene er fortsatt ikke ferdig konvertert. Se [dekningskontrollen](../../docs/hd-status-2026-10-11.md).
