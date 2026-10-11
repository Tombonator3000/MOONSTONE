# HD-bakgrunner og tekst, 11. oktober 2026

Velg Grafikk > HD i [nettspillet](https://tombonator3000.github.io/MOONSTONE/). Original gir tilbake originalgrafikken. Menyer, bevegelse, spillfiler og lagret spilltilstand følger originalen.

Standardpakken har nå 224 aktive PNG-ruter: 40 bakgrunner, 142 fontglyfer, en logo, 20 faste tekstfelt, seks kartlandemerker og de 15 tidligere figur-/meny-/månebildene. De tidligere 48 rutene er beholdt. 184 basisbilder lastes automatisk, bakgrunner ved behov med høyst fire i GPU-cachen.

| Bilde | Aktiv rute | Hva som bevares |
| --- | --- | --- |
| [Verdenskart](world-map.png) | bg/2c1e0fa5.png | Bevegelige markører og alle avvik fra kildekartet |
| [Kartlandemerker](map-landmarks.png) | map-landmarks/000..005.png | Seks faste posisjoner; markører tegnes over landemerkene |
| [Waterdeep](waterdeep.png) | bg/d097d0ff.png | Venstre meny og dens valg; scenen fyller x66..319 |
| [Highwood](highwood.png) | bg/438c8bc2.png | Høyre meny og dens valg; scenen fyller x0..255 |
| [Kroen](tavern.png) | bg/44898895.png | Priser, valg og høyre meny; scenen fyller x0..255 |
| [Steinsirkel](stone-circle.png) | bg/93153ff2.png | Originale introfigurer, flammer, løv og bevegelige deler |
| [Alter](altar.png) | bg/64e5c054.png | Originale introfigurer og bevegelige deler |
| [Portal](portal.png) | bg/6e5a5c07.png | Originale introfigurer og bevegelige deler |

Kartet, byene, kroen, landemerkene og logoen er produsert med den innebygde ChatGPT-bildegeneratoren. Verktøyet bekreftet ikke et bestemt modellnummer. [Promptsettet](prompts/) inneholder nytegning fra originalreferanser og en retting av kartet. world-map-v1.png og begge logorevisjoner er bevart; v1 er ikke aktiv. Steinsirkel, alter og portal bruker bevarte, tidligere genererte råbilder fra art/photoreal/candidates/piv. PNG-råbildene er kopiert urørt. Utsnitt, alpha-cutoff og plassering gjøres i spillrendereren. Landemerkene er én transparent atlas med seks faste utsnitt.

HD-tekst er konturtekst i originalens glyphmål, med seks ganger oppløsning. [Tekstkatalogen](../hd-text-2026-10-11/glyphs.json) oppgir tegn, kildebank, mål og hash. [Faste tekstfelt](../hd-text-2026-10-11/panels.json) erstatter bare de målte feltene i de tre kildevaliderte pergamentmenyene. Uncial Antiqua og IM Fell English er OFL-lisensiert; originalfiler og lisenser ligger i [fonts](../hd-text-2026-10-11/fonts/). Konturfonten til HTML-menyen bygges inn i selve HTML-filen.

Bygg tekst på nytt med `python3 tools/hd_tekst_bygg.py` og `python3 tools/hd_paneltekst_bygg.py`, deretter `make -C port web`. Verktøyene oppdaterer manifestets hashverdier og bevarer rålogoen. Den gamle 48-bilders arkivimporten nekter å overskrive den utvidede pakken.

## Kontroll

[background-text-test.json](verification/background-text-test.json) har49 beståtte kontroller og dekker naturlig intro ved bilde2940/4240/4480, inndata fra tittel via riddervalg til kart og inventar, samt eksplisitte visningsfixturer fra originale PIV-data for byer og kro. Fixturene skriver ikke i WASM-minnet og regnes ikke som en naturlig reise gjennom de tre stedene. Original > HD > Original gir identiske originalbilder og uendret spilltilstand. Svarte skjermer avvises. Tittel har42 godkjente tekstglyfer, inventaret29. Mobilmenyen har synlig konturtekst uten vannrett overløp.

[Standardtesten](../photoreal/verification/2026-10-11-background-text/standard-test.json) dekker oppstart,71 gangrammer, bakgrunnscache, Original-preferanse, egen mappe, gjenoppretting, feil hash, manglende filer, avbryting og file://. [Inndatatesten](verification/input-test.json) bruker faktisk museklikk i Practice, tastaturbevegelse og sidemenyens bryter. Native check_hooks har25/25 byteidentiske sammenligninger. Det er ingen ny full gjennomspilling eller måling av FPS på telefon.

Dette fullfører den valgte bakgrunns-/tekstleveransen. Resterende figurtegning, øvrige PIV-scener, rulletekst/flisbanker og fast tekst innebygd i andre bakgrunner er fortsatt uferdige og beholder originalen.
