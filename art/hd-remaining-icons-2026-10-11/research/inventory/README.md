# Inventarikoner: kildekontroll 11. oktober 2026

`inventory-identities.json` dekker alle 95 ikke-tomme ruter i originalbankene `ki.cel` og `mi.c`. Feltet `kind` skiller selvstendige gjenstander fra tekst, rammedeler, animasjon og kartstatus. `confidence` skiller bekreftet identitet fra uavklarte konturer.

Originalmanualen og originale spillbilder på Moonstone Tavern er kontrollert på nett; URL-er finnes per rute og i `sources.json`. Eksakt CEL-rute bestemmes av originalgrafikken og kallet i `disasm/mog.s`. Nettsidenes rekkefølge alene er ikke CEL-rekkefølge: KI012 er Hawk, KI013 er Acquisition.

`references/` og `*-sheet.png` er dekodet fra originale indekser med original palett og utvidet ikke-sammenhengende planmaske. `references-large/` er bare nærmeste-nabo-forstørrelser av disse originalene for bildeverktøyet. `*-raw-sheet.png` er en tidlig diagnose av feil upakket palett og skal ikke brukes som kunstkilde. `online/` inneholder urørte nedlastede originalbilder for identitetskontroll, ikke ny runtimegrafikk.

De fire logiske Moonstones bruker bare tre forskjellige KI-bilder: halv (000, delt av to varianter), full (001) og ny (002). KI016 er en ekstra rull i stabel, ikke en sjette rulltype. KI031,032,033 er tre deler av ett åpent skattekistebilde. KI017/018 er livshjelmer; KI019/020 er paddestatus. MI005..009 er aktive ridderhjelmer, MI010..014 er Gem of Seeing-status, MI015..018 er Hawk-målmarkører. MI034..041 er åtte drageanimasjonsruter og hører til figurfase.

MI021..028 er glødende stedskonturer, ikke åtte nye bygninger. Presis stedstilknytning er ikke sikkert etablert i denne kartleggingen. MI019 og029 er tomme plasser, eksplisitt registrert utenfor listen over ikke-tomme ruter.

Denne mappen dokumenterer kildeidentitet og produksjonsreferanse. Den bekrefter ikke integrasjon, byggekontroll eller publisering.

## Valgte produksjonsbilder

`production-selection.json` er den presise listen over valgte råbilder, tilhørende asset-records, kildereferanser, prompter og SHA-256. Den dekker KI000,001,002,004..010 og017..020 samt MI043..046: 18 ikonruter og24 unike råbilder, inkludert fire statiske MI-paddemarkører. Filene under `raw/` er kopiert urørt fra den innebygde bildegeneratoren. Ingen ekstern generator eller kredittjeneste er brukt.

De ti enkeltgjenstandene bruker `raw/ki.cel/NNN.png` og `prompts/ki.cel/NNN.json`. Mellomvariantene med `-v1` er bevart som revisjonsspor og er ikke valgt. Nøkkelvarianter ble korrigert for fysiske trappetrinn/materialfargeblokker fra pikselkanter; talismanen fikk glatte armtipper og den lille originale røde detaljen.

Livsikonene bruker `raw/life/helmet-{blue,orange,green,red,purple}.png` og `raw/life/toad-{blue,orange,green,red,purple}.png`, med ett konkret promptdokument per råbilde under `prompts/life/`. KI017/018 deler hjelmfamilien, KI019/020 deler paddefamilien. Originale venstre/høyre indeksmasker er like etter28/29→30/31-remap, kontrollert av runtime-ruteauditen. `purple` betegner originalens femte svært mørke marineblå spillerpar, ikke en ny lyslilla palett.

KI018/020s blå produksjonsreferanser ligger i `references-blue/ki.cel/`; disse bruker originale ruteindekser med en gyldig blå spillerpalett i30/31. De eldre hvite palettfangstene er bevart under `references/ki.cel/` og skal ikke tolkes som en permanent hvit høyrespalte. Metadata i `asset-ki-017.json` til020.json har alle fem originale palettpar.

Paddens `toad-blue-v1.png` og `-v2.png` er forkastede mellomvarianter: v1 hadde leketøyliknende ansikt/hud, v2 fikk beige buk. Valgt `toad-blue.png` har realistiske paddeøyne/hud og original grønn kropp; bare den korte bukmarkøren endres i de fire fargevariantene. Hele paddekroppen skal ikke farges med spillerfargen.

Alle24 valgte råfiler er visuelt kontrollert og teknisk validert som RGBA med ekte alpha0 rundt motivet. `reviewed_for_runtime` beskriver bildegjennomgangen; denne mappen påstår ikke at alle ruter er sett i kjørende spill. Integrasjon, normal spillstørrelse og publisering krever prosjektets sluttkontroll. MI-kontur/glød styres av original indeks31, bekreftet i ruteauditen, og er ikke permanent rosa grafikk.


## Statiske paddemarkører på kartet

MI043..046 er fire statiske Math-forvandlingsikoner med blå, oransje, grønn og rød bukmarkør. Disse hører til objektikonarbeidet, ikke den utsatte figuranimasjonen. Originalens10×12-kroppsgeometri er lik KI019 uten tom kant, kontrollert mot `research/runtime/map-toad-contracts.json`. Original31 finnes ikke; indeks19 er interne øyne og munn, slik at ingen originalindekser bevares som ytterkant.

De fire nye `raw/mi.c/043.png`..`046.png` gjenbruker KI-paddens naturtro form gjennom små fargeendringer i den innebygde generatoren. Øvre to tredjedeler av markøren følger kartets originale fargetone, og nederste tredjedel er fast brun18 `[136,102,34]` i alle fire; KI-masterens mørke spillerfarge ville vært feil her. Konkret prompt og urørt råfil spores i `prompts/mi.c/NNN.json`, `asset-mi_c-NNN.json` og `production-selection.json`. Alle fire er visuelt sammenlignet med originalreferansen under `research/runtime/references/mi.c/`.

Gem of Seeing har fem kartvarianter MI010..014. Den femte (MI014) bruker olivengrønn sokkel, indeks12 `[102,119,68]`; den skal ikke forveksles med femte hjelms mørklilla identifikasjonsfarge. KI045..049 er månefase-HUD; manglende oppføring i `icons.json` alene betyr ikke manglende HD, siden disse allerede har egne aktive PNG-er og originalpose-rute.
