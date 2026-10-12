# Ny Moonstone-logo, 12. oktober 2026

Logoen er nygenerert med den innebygde bildegeneratoren. Verktøyet eksponerte ikke et bestemt modellnavn. Originalens `bold.f/073` er formreferansen: hovedordet MOONSTONE, de tre O-enes diamantformer og undertittelen A Hard Days Knight. Brukerens avviste HD-logo er ikke formgrunnlag.

Den valgte gullmasteren ligger i `raw/logo-black-master-v3.png`, og den endelige prompten i `prompts/logo-black-master-v3.txt`. To transparente utkast ble forkastet på grunn av urene mattekanter. Den valgte masteren har ensartet svart bakgrunn. Assetpakkingen fjerner bare matten, klipper til innholdet og skalerer uten å endre bokstavformene. Dette er en ny tolkning med glatte kurver, ikke den tidligere originalpikselmasken med gullmateriale.

`packed/bold.f/073.png` er en RGBA-fil på 2440 × 581. Samme bytes er aktivert i `web/hd/bold.f/073.png`. Originalens kildebredde305, anker og originalgrafikk beholdes; eksisterende `fit: width` bevarer bildets sideforhold og sentrerer det i kildefeltet. Logoen og undertittelen er kontrollert i den faktiske tittelskjermen. Hjelpeteksten skjules når HD-logoen vises, slik at den ikke dekker bokstavene.

`verification/packing.json` binder råmaster, kildebank, utsnitt, alfamatte, mål og PNG-hash. `verification/runtime/report.json` dokumenterer åtte faktiske nettleserkontroller, med naturlig introhopp, standardlaster, HD-logo før resten av pakken, komplett tekstur, riktig sideforhold, Original/HD-retur og uendret CPU-tilstand. Bildene i samme mappe er visuelt kontrollert. Den første helperprøven feilet fordi den hentet en tømt WebGL-buffer; tegning og PNG-henting skjer nå i samme tick.

Gjenbygg uten aktivering:

```sh
node tools/hd_logo_2026_10_12_pack.cjs
```

Aktiver den kontrollerte pakken:

```sh
node tools/hd_logo_2026_10_12_pack.cjs --activate
```

Verktøyet bruker allerede tilgjengelig `sharp` i utviklingsmiljøet. Det legger ingen ny avhengighet til spillet. Logoen erstatter den eldre logo-pakkingen fra11.oktober; historiske packing-/aktiveringsverktøy skal ikke brukes til å gjeninnføre den avviste logoen.
