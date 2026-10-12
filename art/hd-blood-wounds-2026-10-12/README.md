# HD-blod og sår, 12. oktober 2026

41 nye uavhengige `blo.cel`-materialer er aktivert. De 65 allerede leverte `KN5.ob`-skadefragmentene er beholdt. Pakken har 2005 PNG-er/2011 manifestfiler. Det gjenstår 749 kildemastere/812 konkrete ruter i resten av spillet.

[Briefen](BRIEF.md) beskriver identiteten. [Kildekontrakten](source/contracts.json) binder alle 41 opprinnelige ruter til originalbankSHA `d83857454db7f5113598c6a41a46e45f62ecb4936637372b4807e22125bf699e`. Hver rute har egen innebygd ChatGPT-bildegenerering i `raw/NNN.png` og egen full prompt i `prompts/NNN.txt`. Verktøyet eksponerer ikke eksakt modellversjon. Ingen avviste utkast er brukt som nye referanser.

`tools/hd_blod_pakk.py` bruker hvert råbildes væskeoverflate, tilpasset kildens opake boks. Den eksisterende avrundede originalkonturmetoden klipper bort tillegg utenfor kilden og bevarer alle kildepikselmidtpunkter, hull, fulle4x-rutemål og origo. Nærmeste genererte overflate fyller områder hvor generatoren etterlot transparente hull. Det er ikke anatomisk nytegning eller oppskalering av originalens røde RGB. Konturene følger bevisst originalens diskrete små dråpefelt. `packing/NNN/record.json` registrerer hver rå-/prompt-/PNG-SHA, kontur-IoU, utfylling og kildeindeksSHA. `comparison.png` viser original, råmateriale og pakket resultat. Begge kontaktark og faktiske kampbilder er visuelt kontrollert i [visual.json](verification/visual.json).

Den nye smale rendererporten krever kjent BLO-bank, planmaske15, riktige rutemål og kun kildeindeks0/15. Synlige opake rader må ha samme rødnivå i palettindeks15: R=0..204 i steg17, G=B=0. Dette er de13 originale min/subtract-falmenivåene for `c00`. BLO får dette absolutte lysnivået, uavhengig av terrengpalettens maksimum. Ukjent kilde eller fremmed radpalett beholder Original. Eierskap, klipping og original tegnerekkefølge kontrolleres fortsatt før HD. Ingen original ZIP, WASM-kjerne, spillregler eller lagringsformat er endret.

## Kontroll

[619 kandidatkontroller](verification/candidate/report.json) og [standardkontrollen](verification/standard/report.json) bruker faktisk WASM og WebGL. Standardkontrollen laster hele pakken fra manifestet uten manuell BLO-import. Alle 41 ruter prøves normal/speilet, ved fire skjermkanter, med eksakt Original/HD-retur og uendret full lagring. Rute13 prøves ved alle 13 rødnivåer samt fremmed palett og bank. Feil bank skal gå tilbake til Original og korrekt bank gjenopprette HD.

En egen kontrollert Troll-initialisering lar original CPU og vanlige joystickinnsendelser produsere blod. [Native tegneliste](source/native-observations.json) har27 unike ruter; nettleserprøven får18 synlig HD-godkjente ruter. Seks kampbilder, inklusive Original/HD-par, lagres med SHA i rapporten. De tre initializer-/terrengskrivingene under setter opp kampen; ingen skriver direkte til blod, palett eller liv. Fragmentfixturene over endrer bare frontendobservasjoner. Dette beviser ikke naturlig bruk av alle 41 ruter eller en full gjennomspilling.

Gjenskap den native originalprøven:

```sh
./port/moonstone-headless --headless --frames 2600 \
 --press 100:esc:4 --press 700:down:4 --press 760:down:4 --press 820:fire:4 \
 --skriv 900:80172:0x84924:4 --skriv 900:8d9ac:0x8d5b4:4 --skriv 900:8015c:0xc:4 \
 --press 1280:right:500 --press 1310:fire:900 --press 1310:up:900 \
 --tegneliste 1300:1300 --log 0
```

Original kode laster BLO via082502..08250e til08cdd4;0875c8 fordeler bankpekeren i effekttabellene, og087bf0 tegner. Kampens palettsetter088c86..088c92 setter indeks15 til `c00`. Gore Off er originalflagg08f2cc og styres fortsatt av originalen.

## Produksjon og levering

```sh
python3 tools/hd_blod_pakk.py --frames 0:41
MOONSTONE_BLOOD_CANDIDATE=1 MOONSTONE_OUT=art/hd-blood-wounds-2026-10-12/verification/candidate node tools/hd_blod_sjekk.cjs
# Visuell kontroll og dens SHA-kvittering opprettes etter faktisk inspeksjon.
python3 tools/hd_blod_aktiver.py
python3 web/pakk.py web/build/moonstone-core.js web/build/moonstone.html
MOONSTONE_OUT=art/hd-blood-wounds-2026-10-12/verification/standard node tools/hd_blod_sjekk.cjs
```

Node trenger Playwright og Sharp, slik de øvrige repo-verktøyene gjør. Aktiveringen krever bestått full kandidatrapport, kilde-/kode-/materialhasher og visuell kvittering. [activation.json](activation.json) binder 41 nye PNG-er til manifestet. Alle 1970 tidligere manifestfiler er uendret. Bestillingsgeneratorens255 kilde-/maskekontroller og den [oppdaterte filauditen](../../docs/hd-status-2026-10-12/audit.json) kontrollerer hele pakken. Publisering, CI og faktisk offentlig kontroll registreres i log.md og leveringskvitteringen etter at de er utført.

Endelig lokal kontroll:619 standard-,53 UI- og26 Ratmen-kontroller består uten nettleserfeil. Kampsekvens, speilvendt41-serie og alle fire inventarfarger er visuelt kontrollert. [Samlet lokal kvittering](verification/local-delivery.json).
