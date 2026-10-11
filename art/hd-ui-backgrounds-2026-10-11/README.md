# Originaltro UI, font og bakgrunner

Oppfølging 11. oktober 2026. Standardpakken har 398 PNG-ruter, 404 manifestfiler og 79 bakgrunner. Den nye delen inneholder 22 UI-ruter, 144 originalformede fontbilder og fire bakgrunner. Av fontbildene erstatter 142 tidligere erstatningsglyfer; to opphavsrettsfelt er nye. Logo073 er bevart og står fortsatt til revisjon.

## Det som er lagt inn

| Del | Ruter | Metode |
|---|---|---|
| Valgkonturer | MI021-028 og MI030 | Originale former, levende palettindeks31, kantutjevnet ved8x |
| Meldingspanel | MI032 | Fotografisk blankt pergament, klippet til originalsilhuetten |
| Inventartekst | KI038-044 | Originalens bokstavformer og fargeindekser |
| Riddervalgramme | sel001 | Original ramme, ikke en ny figur |
| Exit, OK og piler | mys002-005 | Originale former, begge stedsvariantene beholder sin palett |
| Stor/liten skrift | 142 glyfer og bold074/075 | Originale CEL-former og skygger ved8x |
| Butikk | bg/e868fda9.png | To buer og tre søyler, med felles midtsøyle |
| Inventar | bg/94e65527.png | En bue, to søyler og opprinnelig plassering |
| Introskog | bg/d744b02e.png | bg1b.PIV, kildevalidert scene |
| Vannvirvel | bg/e2e904b2.png | bg7.PIV, flat vannflate nederst; øvre originalregion bevares |

Nye bakgrunner er 1280x800. Råresultater fra den innebygde ChatGPT-bildegeneratoren ligger uendret i `raw/`, med prompter og kildebilder ved siden av. Verktøyet oppgav ingen eksakt modellversjon. `generation-records.json` skiller kandidatene som brukes fra de avviste. Pakking med browser-canvas gjør bare fullrammeskalering eller klipping til originalkonturen.

Tre nye KI-rankekandidater034-036 mistet for mye av originalsilhuetten og er ikke aktivert. Fire-søyleversjonen av butikken og en logokandidat er også avvist. De er negative eksempler, aldri tegnereferanser. To donasjonssekker og seks DragonDice-symboler er kartlagt, men trenger fortsatt fotografiske materialer. mys006/007 er øyefragmenter og tas sammen med figurene.

## Kontroller

- `verification/backgrounds/backgrounds-test.json`: 34 kontroller av fire bakgrunner i faktisk WASM-frontend, Original/HD-retur, bevegelig forgrunn, beskyttede regioner og uendret tilstand. PIV-/PNG-fixturer, ikke naturlige besøk til alle steder.
- `verification/panel/ui-fixtures-test.json`: 14 kontroller av pergamentet, normal/speilet, kildevern og Original/HD-retur.
- `../hd-ui-followup-2026-10-11/verification/`: 549 hashbundne UI-fixturekontroller, 82 ekstra MYS-kontroller, 65 naturlige kart-/inventarkontroller, 35 importkontroller og uavhengig leveranseintegritet. Siste integrasjonskjøring er `integration-final/`; bundne fixturer ligger i `bound-runtime/` under hvert kandidatsett. Ni SHA-kontroller bekrefter gjenbygg etter aktivering, og seks negative gateprøver avviser utdaterte bilde-/kodebevis.
- `../hd-ui-followup-2026-10-11/verification/inventory-loading/`: 17 kontroller med blokkert bakgrunnsforespørsel. Begge originalsøylene beholdes under lasting; etterpå viser HD begge søylene. Ingen forsvinnende søyler ble reprodusert. Original og HD kommer tilbake pikselidentisk.
- `../hd-faithful-text-2026-10-11/verification/final-runtime/`: 33 font-runtimekontroller; `packing-report.json` har 24027 kilde-/formkontroller. Den tidligere `verification/runtime/` var en feilsøkingskjøring med et testinngrep som endret frontendlisten, og er ikke leveransebevis.
- Leveranseintegriteten bevarer alle 102 eldre rasterkontrakter med 118 PNG-er, 75 eldre bakgrunner, 20 eldre scenekontrakter og 52 beskyttede original-/kjernefiler mot04f0c8e.

Font og UI er originalformet kantutjevning. De telles ikke som fotografisk nytegning av figurer. Spillkjernen, originalarkivet, lagringsformatet og spillreglene er uendret. Lokal HTML er pakket med den uendrede main-CI-kjernen; ny full WASM-kompilering skjer i GitHub Actions. Ingen full gjennomspilling eller fysisk telefontest er utført.

## Gjenbygging og resten

`tools/hd_ui_bakgrunn_pakk.cjs` lager kandidater. `hd_ui_bakgrunn_aktiver.py` kontrollerer dem uten skriving som standard; `--activate` kopierer bare de fem gjennomgåtte rutene. Font og kontur-UI har egne bygge-/aktiveringsverktøy. Ikke kjør flere manifestaktiveringer samtidig.

Bestillingen i `docs/hd-bestilling-liste.csv` har 1796 rader etter deduplisering: 11 ikonmaterialer, fem bakgrunnsrevisjoner, logoen og resterende figurer/animasjoner. Ikoner tas først, bakgrunner etterpå og hver figurrute til slutt. Rulling og PIV-fliser er fortsatt egne oppgaver.
