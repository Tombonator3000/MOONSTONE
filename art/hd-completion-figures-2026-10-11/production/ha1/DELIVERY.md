# HA1: egne fotografiske materialmastere med originalgeometri

22 separate råbilder fra den innebygde bildegeneratoren, ett kall og én originalreferanse per rute. `generation-records-v1.json` binder generatorfil, råbilde og prompt. Ingen bestemt modellversjon påstås.

`geometries-build.py` kontrollerer de faktiske utvidede CEL-indeksene mot den uendrede ZIP-en og `source-contracts.json`. Fargene kommer fra gyldig skanout i naturlig intro4912. `pack.cjs` registrerer hvert fotografi til sin originale alfagrense, beholder glatte kildekonturer og alle hull og former, og bruker fotografiets materialdetalj innenfor originalens belysning. Dette er materialnytegning med kildefast geometri, ikke en påstand om fritt nytegnet kontur.

Stål bruker originalens1..7 og de mørke18/19/24/27-feltene. Rutene012/019 beholder den avrundede fiolette moonstonen12/15/23; bare hvite1-komponenter ved steinen er steinhøylys. Vanlige stålreflekser på1 er fortsatt stål. Ingen levende palettmaske trengs her.

`verification/demo-v1.png` viser000/006/012 før bred pakking. Den pakkeretningen er visuelt godkjent av rotagenten. `verification/all-v1.png` viser alle22 mot originalen. `check.py` kontrollerer alle34207 alfamidtpunkter, sammenhengende forgrunn og hull samt fiolett stein/lysere hvitt høylys uavhengig av pakkeren.

`runtime.cjs` bruker en uforanderlig kopi av den faktisk bygde standard-HTML-en8ec46e4a og manifest a05ba348. Kandidatimporten legger bare inn HA1 og fire eksisterende bakgrunnsfiler som scene-kontekst. Original intro kjøres uten hopp, emulert minneskriving eller palettskriving. Rutene000..006 skal ses i faktisk komposisjon; alle22 testes dessuten normalt og speilvendt som klart merkede frontend-fiksturer. Rutene007..021 påstås ikke naturlig observert. Original/HD-returer og uendret spilltilstand kontrolleres, og ukjent forgrunn skal avvise den berørte HD-figuren.

`freeze.py` binder alle PNG-er, egne fotografier, prompts, kilder, verktøy og faktiske runtimebevis. Visuell sluttkontroll er separat fra teknisk pass. Ingen aktivering, felles frontendendring eller commit utføres av denne leveransen.
