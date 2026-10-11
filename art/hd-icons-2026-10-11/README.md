# Trofaste HD-ikoner

[Åpne spillet](https://tombonator3000.github.io/MOONSTONE/) og velg **Grafikk > HD**. **Original** viser originalbildet. Dette settet erstatter den genererte menypilen og gir de små ikonene en kildefast konturbehandling. Bakgrunner, portretter og fotoposer fra de tidligere leveransene er beholdt.

Det er 75 ikonruter: 35 inventarbilder (`ki.cel/000..033` og `037`), sverdpekeren (`po.cel/000`), menypilen (`sel.cel/000`), seks faste ikoner i kroens pergamentmeny 26 kartmarkører og seks landemerker på kartet. Av disse er 68 nye PNG-ruter; menypilen og seks tidligere fotoikoner erstattes. Hele standardpakken har 292 PNG-ruter.

## Utseende og kilder

Dette er konturer fra originalens faktiske fargeflater, ikke nye motivtolkninger eller genererte fotografier. Åpninger i nøkler og ringer, rullenes symboler, originalens små refleksflater, retning og proporsjoner bevares. Ingen ekstra glød, ornamenter, teksturer eller tilfeldig detalj er lagt til. Kurvene har myke overganger med høyst 0,12 originalpiksel avrunding. HD-eksporten er åtte ganger originalmålene.

[Original-/HD-sammenligning](index.html) viser alle 75. [SVG-kildene](svg/) er redigerbare. [Originalvisningene](source/) gjengir de samme originale indeksdataene uten konturbehandling. [icons.json](icons.json) binder hver rute til originalfil, SHA-256, mål, planmaske og indeksdata. Paletten til arbeidsvisningen er målt i et naturlig inventar ved ramme 2150. Kartmarkørene kommer fra en naturlig originalramme ved ramme 2000; dens tilstand og indekser er bevart som referanse. Spillrendereren bruker den aktuelle skjermpaletten, også ved fading og fargebytte.

De seks landemerkene er utsnitt av originalkartet med dokumenterte kildeavgrensninger. Konturer, farger og plassering kommer fra kartet; de større fototolkningene brukes ikke lenger. Avgrensningene og kildepikslene finnes i `icons.json`.

Ingen bildegenerator eller genereringsprompter er brukt til dette settet. Oppskriften er [hd_ikoner_bygg.py](../../tools/hd_ikoner_bygg.py) og [hd_ikoner_eksporter.cjs](../../tools/hd_ikoner_eksporter.cjs).

## Integrasjon

`icons.json` lastes med standardpakken. Inventarbilder krever identisk originalbank, indeksdata, mål og planmaske, og alle synlige kildepiksler valideres før de fjernes fra originalforgrunnen. Usikre treff beholder originalen.

CEL-filer kan lagre færre plan enn skjermen bruker. Masken `$17` betyr for eksempel plan 0, 1, 2 og 4. Disse bitene utvides korrekt i visningsanalysen. Originalfilene og spillkjernen endres ikke.

Sverdpekeren bruker hardware-spritefargene 17..19 og finnes derfor ikke i `tegn_figur`-listen. HD-laget identifiserer dens kildeverifiserte form i skanout, bevarer skjulte deler og fjerner bare faktisk synlige originalpiksler. Kartmarkører erstattes bare når hele det dokumenterte mønsteret stemmer. Andre markørstatuser og markører som dekkes av en ridder, beholder originalen.

## Kontroll

[Kildefiltesten](verification/source-test.json) sammenligner eksportert PNG med uavhengige pikselriktige originalvisninger. Alle 75 bilder og 26 557 kildepikselmidtpunkter har identisk farge og alfa. [Nettlesertesten](verification/background-text-test.json) består 59 kontroller og dekker naturlig inventar, kart og intro, Original > HD > Original, endret originalbank, forsinket kartlasting med bevarte originalmarkører, tekstoverlapp, mobilmenyen og eksplisitte PIV-visningsfixturer for byer/kro. Det er ingen full gjennomspilling eller måling på fysisk telefon i denne leveransen.

[Inventar](verification/inventory-hd.png), [kart](verification/journey-frame2000-hd.png) og [kro](verification/fixture-tavern-hd.png) er faktiske nettleserbilder. Krobildet er en tydelig avgrenset visningsfixtur. Kildene og de gamle genererte kandidatene er bevart.

[Standardtesten](verification/standard/standard-test.json) består25 kontroller med71/71 gangbilder. [Faktisk inndata](verification/input-test.json) består4/4. Alle298 standardpakkefiler er kontrollert på lengde og SHA-256.

[Importtesten](verification/import/import-test.json) består 17 kontroller. Et eget ensfarget testikon lastes gjennom mappevalget og vises med sine egne piksler. Ni ugyldige scene-/mønsterfelt avvises. Delvis bakgrunns- og ikonimport bevarer de øvrige standardikonene, deres palett og HD-pekeren. En ødelagt PNG beholder eksisterende bilde og metadata. Standardpakken kan gjenopprettes.
