# HD-grafikk til Moonstone: bestilling

Alt under streken er en ferdig melding. Lim den inn til ChatGPT og legg ved `docs/hd-bestilling-liste.csv`. Listen lages på nytt med `python3 tools/hd_bestilling.py Moonstonecd32-AMIGA.zip docs/hd-bestilling-liste.csv`, og tallene under er fra den kjøringen (12. oktober 2026). Bakgrunnen for listen, med belegg, står i `docs/hd-mangler.md`.

Meldingen viser til filer som kommer med samme PR som denne bestillingen (listen, `tools/hd_bestilling.py`, `docs/hd-mangler.md`, maskeformatet i `docs/hd-grafikk.md` og kildebildene i `art/photoreal/references/runtime_background/`). Send den når PR-en er flettet, og sjekk at filene finnes på https://github.com/Tombonator3000/MOONSTONE/tree/main.

---

Hei! Jeg vil ha hjelp til å tegne HD-grafikk til et gammelt Amiga-spill. Vedlagt er en liste med en rad per bilde. Under står hva spillet er, hvordan bildene skal se ut, nøyaktig hvilket format nettsiden trenger, og hvor du finner originalbildet til hver rad. Repoet er https://github.com/Tombonator3000/MOONSTONE (grenen main). Kommandoene kjøres fra roten av repoet og krever Python 3 med Pillow.

## 1. Spillet og stilen

Moonstone: A Hard Days Knight kom på Amiga i 1991, fra Mindscape. Det er mørk og brutal fantasy: fire riddere på jakt etter en magisk stein, kamper mot troll, demoner og drager, blod, steinsirkler, skoger om natten. Originalen er pikselgrafikk i 320 x 200 med 32 farger. Nettsiden kjører det originale spillet i en emulator og legger HD-bildene oppå, rute for rute, der spillet tegner originalen.

Stilen skal være fotografisk, med materialer, lys og farger som følger originalbildet. Dagens HD-bilder er støtte for materialkvalitet, men originalen bestemmer motivet. Logoen er gullmetall. De statiske objektikonene er kildebundne rasterbilder fra art/hd-remaining-icons-2026-10-11. Behold originalens motiv, størrelse og dokumenterte palettvarianter.

Det viktigste: **samme motiv, samme form, samme plassering, bare skarpere.** Ikke legg til ting, ikke flytt noe, ikke endre posen. Et sverd som peker opp til høyre i originalen, skal peke opp til høyre i HD-bildet, og det skal slutte på samme sted. Spillets treffsoner følger originalens piksler.

## 2. Listen

`docs/hd-bestilling-liste.csv` har 991 gjenstående rader, skilt med semikolon. Kolonnene:

| Kolonne | Hva |
|---|---|
| prioritet | Lavest tall tas først. Ikoner og bakgrunner er levert; figurene har prioritet 3 eller 4 |
| gruppe | Hva slags grafikk |
| fil, bilde | Originalfilen i spillet og bildenummeret i den |
| hd_fil | Eksakt sti i HD-pakken. Bruk den uendret |
| kilde_bredde, kilde_hoyde | Originalens størrelse i piksler |
| hd_bredde, hd_hoyde | Størrelsen HD-bildet skal ha |
| farger_fra_palett | ja: spillet bytter noen av fargene (rustningen til ridderne). Se punkt 3.5. Aktive UI-ikoner har egne palettkontrakter i icons.json |
| trenger_maske | ja: lever også en maske. Se punkt 3.5 |
| hvor_i_spillet | Hvor bildet vises |
| merknad | Hva som er spesielt: like bilder, utkast som finnes, kilde til bakgrunner |

Antall per gruppe, i rekkefølgen du bør ta dem:

| Pri | Gruppe | Rader | Filer |
|---|---|---|---|
| 3 | Monstre | 677 | Balok, beistet, Demon, DRAGON, Mudmen, RATMEN, TROGGAxe, TROGGSpear, TROLL |
| 4 | Blod og sår | 41 | blo.cel |
| 4 | Intro og slutt | 273 | au1, co1, da1, dg1, dw1 |

Listen har bare figur- og animasjonsarbeid igjen. De 11 ikonmaterialene, fem bakgrunnsrevisjonene og logoen er aktivert etter kilde- og runtimekontroll. To komplette rullestriper for intro og slutt er også koblet inn. Pakken har 82 aktive bakgrunner, inkludert den kildebekreftede Guardian-bakgrunnen og alle 56 sammensatte kampvarianter, og 1741 PNG-ruter i 1747 manifestfiler. 991 selvstendige mastere gir 1055 konkrete PNG-ruter med eksakte kopier. Kildebekreftede rene kampbakgrunner kan naa beholde HD naar originalen bare legger til eksakte rode indeks15-celler; disse originalcellene tegnes foran HD. Ukjente bakgrunnsendringer gir fortsatt Original-fallback.

79 gjenstående masterrader trenger maske for innbakte ridderdeler i indeks6..8. Originalens fargevalg ved088c4a..088caa gjelder også Balok, Mudmen, Ratmen, Trogg, beistet og enkelte Demon-ruter. De konkrete107 kilderutene er bundet i tools/hd_bestilling.py; identiske kopier og allerede aktiverte ruter gir færre selvstendige maskebestillinger. To tidligere leverte ruter, Balok1/010 og RATMEN2/058, er etterlevert med maske uten PNG-endring. Alle HE-kopier er aktivert; ingen HE-kopimasker gjenstår. KN1-5, HE1-3, Math/Wi1.C og dice.cel006/007 er levert med kildebundne fargemasker. LI1 og de oppstigende HEN/Klift-rutene har egne kildebundne blinkmasker. Math015-020 og tavernaspilleren følger aktiv ridderfarge i indeks6-10. Normal standardlasting er kontrollert i alle fire tavernaspillerfarger, uten kandidatimport eller palettskriving.

Ni palettstyrte valgkonturer, MI032-meldingspergamentet, alle ti KI-fragmenter034-044, sel.cel/001 og mys.cel/000-005 er aktive, sammen med seks DragonDice-symboler. De tidligere erstatningsfontene er byttet til 144 originale kildeformer: 142 glyfer og to opphavsrettsfelt. Logoen bruker fotografisk gullmateriale i originalens nøyaktige bokstav- og skyggeformer.

Alle KN1-5-/HE1-3-ruter, åtte kartdrager, alle DICE-ruter, Math, de fire OV1-forgrunnene, 22 HA1-ruter og hele LI1 er aktivert etter original- og runtimekontroll. Alle HEN/Klift-ruter, inkludert flammer, ritualridder, lyn og oppstigning, er også aktive. DRAGON1 har16 nye ruter, DRAGON2 har26 og DRAGON5 har44 aktive ruter. Sistnevnte inkluderer åtte konservative flate kildeeffekter, som ikke telles som fotografiske tegninger. Balok1 har65 aktive ruter, Balok2 har19 og Balok3 har4. Guardian demon1 og demon2 har48 hver, RATMEN1 har24 og krigsbeistet har39. Math har en ekstra fastfigur i WI1.PIV, og tavernaen har en innbakt spillerfigur utenfor CEL-listen. Begge er levert. TAV-bakgrunnen er renset for den gamle spilleren, mens øvrige tavernagjester er bevart. TROLL har fortsatt enkelte ruter som må fullføres.

De fem eldre helfigurprøvene er tatt ut av standardpakken. De er bevart i produksjonsarkivet og telles ikke som separat nytegning. Aktiv riddergrafikk bruker nå hver originalrute og tilhørende fargemaske. [Sjuende figurleveranse](../art/hd-completion-figures-2026-10-11/delivery-progress-007.json) binder aktive bilder, originale kilder og kontrollresultater. Rutekontroll og kontrollerte scener er dokumentert. Sjuende pakke har 15 beistruter og ett kildeidentisk alias som er kontrollert i strenge frontendfixturer, uten synlig fangst i originalkampen. Disse er merket separat i leveransen. Full naturlig gjennomspilling av alle animasjoner er ikke påstått.

Rekkefølgen følger brukerens bestilling: **ikoner og UI først, så alle bakgrunner og logoen, deretter figurer og animasjoner**. Nytegn og kontroller hver figurrute separat. I standardpakken (`web/hd/`) må hver ny eller erstattet fil føres i `web/hd/manifest.json` med sha256 og størrelse. Math, terningspillet og de aktiverte introscenene har allerede scenekoblinger. Nye bakgrunnsnøkler må få en passende scenekobling ved levering. Ridderne, monstrene og blodet har støtte i koden for figurer i flere deler og fargemasker. Lasteskjermen og Prepare yourself-banneret har aktive HD-scener og er ikke med i bestillingen. Skjermbilder fra faktisk spillvisning skal sammenlignes med originalen før en ny del kalles ferdig.

## 3. Format

### 3.1 Mappe og filnavn

Bruk stien i kolonnen hd_fil, for eksempel `KN1.ob/012.png` eller `bg/3a38d016.png`. Legg alt i én mappe med de samme undermappene. Nettsiden lager nøkkelen av de to siste leddene i stien (mappen og filnavnet uten .png), og store og små bokstaver spiller ingen rolle. Derfor:

- Figurer: mappen heter som originalfilen, filnavnet er bildenummeret med tre sifre: `KN1.ob/012.png`, ikke `KN1.ob/12.png`.
- Bakgrunner: `bg/` og åtte heksadesimale sifre, som er en hash av innholdet. Navn etter PIV-filen (`hea.piv/0.png`) blir aldri lest.
- Ikke legg til noe i navnet (`012@4x.png`, `012_v2.png`). Da treffer det ikke.

### 3.2 Størrelse: 4 ganger originalen

Lag hvert bilde i nøyaktig 4 ganger originalens bredde og høyde, slik kolonnene hd_bredde og hd_hoyde sier. En bakgrunn blir 1280 x 800. Logoen blir 1220 x 216.

Hvorfor 4: nettsiden setter sammen bildet i høyst 4 ganger spillets oppløsning. Med et helt tall svarer hver originalpiksel til nøyaktig 4 x 4 HD-piksler, så kanter, ankerpunkt og masken (3.5) ligger likt med originalen. Det er også tallet i `docs/grafikkliste.csv` (hd_4x). Bildene som allerede ligger i pakken, er laget i andre skalaer (de fleste bakgrunnene er 1586 x 992, fontene 8x, ikonene 8x). Bevar skalaen til eksisterende UI-kontrakter; nye bilder i CSV-en skal være 4x. Sideforholdet må være det samme som originalen. Logoens tegneområde er hele 1220 x 216. Ved levering må også oppføringen for `bold.f/073` i `web/hd/text.json` få riktig utsnitt og dimensjoner; gamle koordinater fra en større PNG kan ikke gjenbrukes.

### 3.3 Ett bilde per rute, samme rektangel

Hver rad er én rute i originalen, og HD-bildet strekkes over nøyaktig samme rektangel som den. Altså:

- Lerretet er hele originalruten ganger 4. Ikke beskjær til motivet, og ikke legg til marg.
- Motivet skal ligge på samme sted i lerretet som i originalen. Øverst til venstre i originalen er øverst til venstre i HD-bildet.
- Mange figurer er deler av en større figur (ridderens kropp i ett bilde, beina i det neste, sverdet i et tredje). Delene settes sammen av spillet. Tegn hver del for seg, og la kantene slutte der originalen slutter, så delene passer sammen. Ikke tegn hele ridderen i én rute.
- Ikke lag speilede varianter. Nettsiden snur bildet selv når spillet tegner figuren andre veien.

### 3.4 Gjennomsiktighet

- Figurer: RGBA-PNG. Det som er gjennomsiktig i originalen (fargeindeks 0), skal ha alfa 0. Myke kanter går fint.
- HD-bildet må dekke hele originalens silhuett. Der HD-bildet er gjennomsiktig innenfor originalens figur, synes bakgrunnen og ikke figuren.
- Bakgrunner: helt dekkende, ingen gjennomsiktige deler.
- Lever figurer som RGBA, ikke som palett-PNG med gjennomsiktig farge. Nettleseren gjør riktignok den om til alfa, men da får du ingen myke kanter, og det er lett å miste gjennomsiktigheten når bildet redigeres.

### 3.5 Maske for figurer som får fargen fra paletten

Ridderne (KN1-5.ob og HE1-3.ob) har ikke fast farge på rustningen. Spillet gir hver ridder sin farge ved å bytte fargene i paletten: KN-bildene bruker indeksene 6, 7 og 8 til rustningen og HE-bildene 9, 10 og 11. Den samme tegningen skal derfor kunne vises i alle ridderfargene (blå, grønn, oransje, rød og så videre). Radene med trenger_maske=ja har slike piksler. For dem leverer du to filer:

1. Tegningen, `KN1.ob/012.png`, som vanlig. Bruk originalens faktiske palettfarger etter at CEL-planmasken er utvidet (punkt 4). Alternativt kan rustningen tegnes i grått med et uttrykkelig valgt referansegrånivå (kommandoen under). Fargen på rustningen kommer fra masken; lys, skygge og detaljer må overføres til G-kanalen.
2. Masken, `KN1.ob/012.mask.png` (navnet i hd_fil uten .png, pluss .mask.png). Samme størrelse som tegningen, RGBA, og den leses piksel for piksel uten utjevning:

| Kanal | Betydning |
|---|---|
| R | 0 = behold fargen i tegningen. 7, 8, 9 = palettindeks 6, 7, 8 (indeksen + 1); 10, 11, 12 = indeks 9, 10, 11 |
| G | lysstyrke: 128 gir palettfargen, 0 svart, 255 nesten dobbelt så lyst |
| B | hvor mye av palettfargen som brukes: 255 helt, 0 ingenting |
| A | brukes ikke, la den være 255 |

Bare rustningen skal ha R satt. Alt annet (hud, lær, sverd, kanter) har R = 0, G = 0, B = 0, og vises med tegningens egne farger. Der R er satt og B er 255, spiller tegningens farge ingen rolle; da bestemmer G hvor lyst det blir. Skyggene og detaljene i HD-rustningen må derfor ligge i G. Mykere overgang mot resten av tegningen får du med B under 255 langs kanten.

Masken lages med

```
python3 tools/hd_bestilling.py --maske assets/gfx/KN1.ob/012.png hd/KN1.ob/012.mask.png hd/KN1.ob/012.png
```

Første fil er det uendrede originaluttrekket (punkt 4), andre er masken som lages, og tredje er tegningen din. Behold `assets/gfx/index.json`: maskekommandoen trenger CEL-planmasken derfra fordi PNG-indeksene er pakkede. Hvis sidecaren mangler, leses originalbanken fra repoets spill-ZIP, eller en eksplisitt `--spill STI`. Ukjente bank-/bildenavn avvises i stedet for å gjette. Et viktig eksempel er `HE3.ob/031`: pakket PNG-indeks 3 betyr faktisk palettindeks 10.

Kommandoen utvider indeksene, forstørrer dem med nærmeste nabo, setter R og B der originalen har indeksene 6-11, og regner ut G av tegningens lysstyrke delt på lysstyrken til den faktiske kildefargen. G blir 128 når lysstyrken er lik. Uten tegning blir masken 4x originalen med G = 128. Ved grå rustning som bruker grånivå 128 som nøytral referanse, bruk:

```
python3 tools/hd_bestilling.py --maske assets/gfx/KN1.ob/012.png hd/KN1.ob/012.mask.png hd/KN1.ob/012.png --graa-referanse 128
```

Da gir grått 128 G = 128, mørkere grått gir skygge og lysere grått gir lys. Ikke bruk standardnormaliseringen mot en farget original på en vilkårlig grå tegning: da forskyves rustningens lysstyrke. Etterpå kan kantene rettes for hånd. Bevar R-indeksene uten utjevning.

Mange bilder i HE1-3.ob er de samme som i KN1-3.ob, bare med indeksene 6, 7 og 8 byttet til 9, 10 og 11. De står ikke som egne rader. Merknaden på KN-raden sier hvor tegningen også skal ligge: legg samme tegning der, og legg ved KN-masken med R byttet fra 7, 8, 9 til 10, 11, 12. G og B skal være uendret. Ikke normaliser den samme fargede KN-tegningen på nytt mot HE-palettens andre lysstyrker. `HE3.ob/031` inngår nå som en slik kopi av `KN3.ob/031`, med egen HE-maske.

### 3.6 Like bilder

Noen bilder finnes i flere filer, byte for byte like (troggen med øks og troggen med spyd deler 62 bilder, hen1.c og Klift1.CEL er like, sverdene i KN4.ob brukes også av noen monstre). De står bare én gang i listen. Merknaden sier hvor tegningen også skal ligge. Lag en tegning og kopier filen dit.

## 4. Slik finner du originalbildet

Figurer:

```
python3 tools/gfx.py extract Moonstonecd32-AMIGA.zip assets/gfx
```

Det gir en mappe per fil med ett PNG per bilde, med samme navn som i hd_fil: `assets/gfx/KN1.ob/012.png` er originalen til raden med hd_fil `KN1.ob/012.png`. PNG-ene er indekserte og skal beholdes uendret som kilde. `tools/gfx.py` lagrer de pakkede CEL-indeksene for å bevare byteidentisk rundtur; de er ikke alltid de faktiske skjermindeksene. Bruk CEL-planmasken fra `assets/gfx/index.json` ved visuell kildebygging og maskering. Bestillingsgeneratoren og maskekommandoen gjør denne utvidelsen. Paletten fra skogkampen er bare en forhåndsvisning; faktisk originalskjerm avgjør motivfargen. Størrelser og filbeskrivelser står i `docs/grafikkliste.md`.

Bakgrunner: merknaden på hver bakgrunnsrad sier hvor kilden ligger.

- Butikken og inventaret: `art/photoreal/references/runtime_background/e868fda9.png` og `94e65527.png`, lagret fra emulatoren.
- De andre er bildefiler i spillet: `assets/gfx/hen1.p/0.png`, `assets/gfx/bg3.PIV/0.png` og så videre etter kommandoen over.

Bakgrunnene er 320 x 200. Det finnes eldre utkast i `art/photoreal/candidates/` for mange rader. Ingen av dem er godkjent. De er feilarkiv, og skal ikke vedlegges som positive tegnereferanser eller brukes som utgangspunkt. Bruk det uendrede originalbildet og kontroller resultatet direkte mot det.

## 5. Figurer som fortsatt skal tegnes

- **Hver figurrute** i CSV-en tegnes separat, også kroppsdeler, våpen, øyne, flammer og blod. En helfigur erstatter ikke separate fragmenter.
- **Trollet** er blått i spillet. Eldre brune og gylne utkast er avviste referanser. 13 originale kampkontekster er nå målt med originalens palettrutiner, inkludert trogg-økse/spyd i skog, sump og ørken; se `art/hd-completion-figures-2026-10-11/palettes/`.
- **Intro og slutt** har tegneliste og rullestøtte. Hver nytegnet rute må likevel prøves med sin faktiske palett, målbuffer og plassering.

## 6. Levering og test

Lever PNG-filene i en mappe med samme oppbygning som hd_fil (for eksempel `hd/KN1.ob/012.png`, `hd/KN1.ob/012.mask.png`, `hd/bg/3a38d016.png`). Legg ved kilde, prompt og original-/HD-sammenligning. Aktivatorens separate oppgave er å oppdatere manifest og nødvendig ikon-, scene- eller tekstmetadata.

Enkeltfigurer og eksakte bakgrunnshasher kan prøves med «Velg HD-mappe» i sidemenyen. Slå på «Gult felt der HD-bilde mangler» og sammenlign «HD / Original». Sceneavhengige bakgrunner, palettstyrte ikoner og logoen krever også riktig metadata. Test dem i en integrert pakke, bygg nettsiden (`make -C port web`) og kjør de berørte runtimeprøvene. Mappevalg alene er ikke bevis på at en ny eller revidert scene fungerer. Ved riddertesting skal samme tegning vises i minst blå og grønn rustning, med korrekt lys og overlapping. Kontroller også Original-retur, endret palett og alle leverte animasjonsruter.

## 7. Dette skal du ikke lage

- `bg/045a1ac5.png`. Det er hashen av en helt tom skjerm, og bildet ville vist seg på alle tomme skjermer og i overganger.
- `bg/8dbce956.png` (månen) og `bg/c234c097.png` (stjernene). De ligger bak lasteskjermen og synes aldri.
- Bitene i `test` (bilde 0-7). Kampbakgrunnene settes sammen av dem, men bare den ferdige bakgrunnen kan byttes. Alle 56 ferdige kampvarianter har nå HD.
- Ikke lag nye hele skjermer for lasteskjermen («MOONSTONE ... Loading») eller «Prepare yourself»; de har aktive HD-scener fra ch.piv og message.piv. «Select a Knight» bruker eksisterende HD-tekst og valggrafikk. Menyrammen sel.cel/001 er nå aktivert og utelatt fra listen.
- Separate PIV-atlasfliser bestilles ikke ved siden av de komplette rullestripene. Introens bg1a/bg1c/bg1b og sluttens bg7 rekonstrueres fra originalens fliskart til to320x1200-kilder, som har1280x4800-HD-ruter. Ukjente kilder faller tilbake til originalen.
- KI034-044 og de åtte materialikonene i kro/by er ferdige. Fritt genererte utkast som mistet originalens silhuett er avvist som geometrigrunnlag; hvert fotografiske materiale er bundet til originalkonturene.
- De 144 originale kildeformene for fontene, logoen og de fem bakgrunnsrevisjonene er aktive. KI045-049 er aktive via poseruten selv om de ikke står i icons.json. Manifestdekning alene betyr fortsatt ikke visuell godkjenning av andre motiver.

## 8. Det som ikke er sikkert

- Riddermasken er prøvd med syntetiske palettvarianter. Hver ny fotografisk ridderrute krever fortsatt egen kontroll. Math015 er prøvd med separat fotografisk nytegning i faktisk blå og rød originalscene.
- Flere ridderbanker har nå kildebekreftede draktindekser og målte palettvarianter. Hver ny bank må likevel kontrolleres separat; masken bygges fra originalens indekser, ikke fra en forhåndsvisningsfarge.
- KN5.ob er nå kontrollert i original dragekamp. Alle65 ruter har separate HD-mastere og normal-/speilingsprøver; de sju brennende ridderrutene058..064 er også observert i originalens tegneliste. Dette er ikke en påstand om naturlig bruk av alle65 ruter. De41 blo.cel-masterne gjenstår.
- Math (WI1.P, WI2.P), terningspillet og de aktiverte introscenene har allerede scener i `web/hd/manifest.json`. De skal ikke bestilles på nytt for å løse en manglende scenekobling. Nye eller reviderte bakgrunnsbilder må fortsatt testes mot originaltekst, markører og forgrunn ved levering.
- Monstre kan ha andre farger i et hi enn ute. De 13 målte kampkontekstene er kildebelegg, ikke full dekning av alle ruter og steder. Kontroller hver levert monsteranimasjon i riktig sammenheng.

### Nytt bakgrunnshull funnet ved faktisk kampkontroll

Guardian-kampens originale bakgrunnshash cbc31cbf finnes ikke blant de81 aktive bakgrunnsfilene. Figurleveransen bruker trygg Original-fallback. Bakgrunnen er en separat gjenstaaende oppgave utover figur-/effekt-CSV-en. Full bakgrunnsdekning er ikke bekreftet.
