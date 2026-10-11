# KN1: separate originalbundne figurmaterialer

60 masterruter er generert separat med den innebygde bildegeneratoren, hver med sin egen originale rute som formreferanse. 59 mastere har nytt synlig fotomateriale. KN1.ob/038 er en ren svart originalskygge og telles som bevart skygge, ikke som synlig nytegnet foto.

Originalbanken KN1.ob har SHA256 `96bdcf5e73b4ebaaba4f3809bdc85eaa15808cc9173556bfb438080d171de7b5`. `source-contracts.json` binder hver originalrutes planmaske, ekspanderte fargeindekser, utsnitt, ankret størrelse og original-PNG. `generation-records.json` og `prompts/` binder hvert separat generatorkall til den rå PNG-en. Avviste/ubrukte varianter er bevart i `rejected/`.

`packed/` inneholder 105 figur-PNG-er og 97 palettmasker: 60 KN1-mastere, 45 kildebeviste HE1-aliaser, 55 KN1-masker og 42 HE1-masker. Alle ruter pakkes i 4x originalstørrelse. HE1 deler eksakt RGB-master med KN1, men egen kildebasert maske flytter originalens draktindekser 6–8 til 9–11. Det finnes bare 45 eksakte HE1-aliaser; andre HE1-ruter legges ikke til uten kildebevis.

Ny steel-/ulltekstur er klippet til originalens form. Alle opprinnelig dekkede pikselmidtpunkter, transparente hull, mørke skygger og avkuttede deler beholdes. Dette gir trofast form og kontakt med originalens øvrige tegnede deler. Den originale blå drakten er nøytral i RGB-masteren og får faktisk ridderfarge fra masken i rendererens shader.

`verification/packing-test.json` kontrollerer alle 60 mastere, 45 eksakte aliaser, kilde-PNG/SHA, form, transparente hull, materialfarger, maskekanaler og 4x mål. Fem kontaktark `verification/comparison-000-011.png` til `comparison-048-059.png` sammenligner ferdige PNG-er med originalen.

`runtime-first-fixtures.cjs` viser alle 105 ruter normal/speilet med original palett i faktisk WASM-frontend, kontrollerer ankere, maskebruk og eksakt Original/HD-retur, samt fem originale ridderpaletter på rute000. Dette er kildebaserte tegneliste-/scanout-fixturer, ikke naturlig gameplay for hver rute.

`runtime-composed-first-pair.cjs` og `runtime-composed-walk.cjs` bruker original CPU-kamp med tre dokumenterte scenetestskrivinger fra `palettes/cases/troll.json`; ingen palett eller figurtegneliste skrives. Original inndata gir fem kropp/fot-par000/001,002/003,004/005,006/007,008/009 med KN4-sverd, helt innenfor bildet. Håndkontakt, kropp/fot-grense, speiling og begge returer kontrolleres. `verification/composed-walk/comparison.png` viser utsnitt fra de faktiske spillbildene.

`runtime-standard-retired-poses.cjs` beholder den fulle standardpakken og erstatter bare testens innlastede posemanifest med det eksplisitt tomme `retired-poses.json`. Samme fem gangpar kontrolleres med individuelle KN1/KN4-ruter og uten de gamle helposeprøvene. Ingen aktiv posemetadata endres av denne testen.

Den endelige `delivery.json` og `activation-set-kn1-001.json` opprettes først når alle aktuelle runtimebevis er bundet til samme frosne HTML, WASM, renderer, scenekode, originale kilder og ferdige PNG-er. Rotagenten håndterer aktivering og pensjonering av tidligere poseprøver. Ingen delt metadata eller frontend er endret her.

Rute001 hadde en tidlig feilaktig tekstlig tolkning av tåretningen. Kildepikselkontroll viste at originalens støvler peker mot høyre, og den valgte referansebundne genereringen beholder dette. Den eksakte opprinnelige prompten bevares; `source_review_correction` i generatorkvitteringen dokumenterer rettingen. Den tidlige varianten er ubrukt, ikke bevis for at originalens tåretning skulle endres.

Frosset sluttkontroll: 1 514 641 pakkekontroller og 2 153 runtimekontroller bestått (105 ruter/1 580, første faktiske par/18, fem gangpar/276, standardpakke uten gamle poser/279). Baseline-HTML har SHA256 `8cb9c45be6ae724b054bcdceee7438b7d08f11da934273630f62134661d69466`, renderer `9d0e6a66a7597e745d23b0a0516f0c6f8b06f97cb92189613938c14f40aef8bd`, scenekode `f96ca11802910e3291ec7ee4128299f68b73957b3f5f1d0b1435141e1a08ebcd`, WASM-kjerne `c56094d8b992cbd7ed7e4a8ef65709c435156072124874b26bce7cf02cb8e633`. Standardtesten lastet588 assets og5 posekontrakter før testimport, deretter688 assets og0 posekontrakter uten feil. Kampbakgrunnen i denne målrettede testen er original; kontrollen gjelder figurene og pensjoneringen av poseprøvene.
