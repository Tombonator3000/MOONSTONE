# KN4: separat nytegnet våpenbank

Dette er en isolert kandidatleveranse. `delivery.json` opprettes først når pakkekontroll og alle runtimeporter er bestått mot samme frosne PNG-er og produksjonskode. Aktive manifest, `icons.json`, dokumentbestilling og spillkode er ikke endret her.

26 originalruter er generert separat med innebygd ChatGPT-bildegenerering. `generation-records.json` har hele prompten, originalreferansen, verktøyargumentene, kvitteringen og råbildets SHA. `raw/KN4.ob` bevarer alle nye originalmastere. Syv kildeidentiske aliaser får byteidentiske kopier.

`packed` har 4× originalmål. Den faktiske nye fotomaterialtegningen klippes til den frosne kildeformen, med dekning fra nærmeste genererte kantfarge. Alle originale opake og transparente pikselmidtpunkter bevares. Dette er en kildebundet oppdatering med nye fotoaktige stål-/lærmaterialer og bevegelsesspor. Konturen skal ikke beskrives som en fritt nytegnet form.

`comparison.png` viser hver original ved siden av den ferdige ruten i samme størrelse. 011–023 er små bevegelses-/refleksfragmenter. Åpne ditherfelt bevares, de fylles ikke som nye massive sverd. Opake mørke indeks4/5-felt bevares slik at de ikke blir ekstra sølvstreker. Rute025 har en liten ridderfarget draktbit, ikke blod; positiv tegnereferanse bruker original TROLL-kamppalett. Den generiske eldre forhåndspalettens røde felt er ikke fargegrunnlag.

`025.mask.png` bruker faktisk ny drakttekstur mot gråreferanse128, med originalens levende indeks6/7. Originalens fem ridderpaletter er kontrollert fra `disasm/mog.s` $088ca0–$088d14. Verktøyet eksponerer ikke et sikkert modellnavn; ingen bestemt modellversjon påstås.

## Verifikasjon

- `verification/packing-test.json`: original-PNG, råkvitteringer, 4×-mål, alle pikselmidtpunkter, sluttalfa-IoU minst0,90, mørke kildefelt, palettmaske og aliasenes originale bank/indeksdata.
- `verification/all-routes/test.json`: alle26 + syv aliaser normal/speilet i faktisk WASM-frontend. Kontrollerer godkjenning, ankre/mål, maskemodus, eksakte Original/HD-returer, fem kildebekreftede ridderpaletter og uendret spilltilstand. Dette er kontrollerte kildebaserte tegneliste-/scanout-fixturer, ikke naturlig gameplay for hver rute.
- `verification/first-route`: ekte original TROLL-kamp og inndata viser000 sammen med original kropp og hånd. `contact-001` viser speilet001 etter at ridderen er inne på skjermen. Tre dokumenterte testskrivinger velger kampgrenen, ingen palettskriving. Originale kroppsdeler og fiender er bevart her.
- KN3/001 i kontakt000 er et blodsprut-/draktfragment, ikke en separat arm. Hånden ligger i KN3/000-kroppen.

## Gjenskaping

Kjør `prepare.py`, `pack.cjs`, originalens `tools/hd_bestilling.py --maske` med `--graa-referanse 128` for025, deretter `verify.py`. Kjør `runtime-all.cjs` og `runtime-first.cjs`, samt sistnevnte med `KN4_ROUTE=1`, mot frossen isolert HTML. `delivery.py` avviser utdaterte kode-, HTML-, WASM-, kontrakt- og PNG-hasher.
