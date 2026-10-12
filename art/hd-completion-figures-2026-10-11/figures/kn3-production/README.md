# KN3, separat kandidatleveranse

Frosset kandidatleveranse for sekvensiell integrasjon. Ingen aktiv manifestfil, frontend eller spillkjerne er endret av denne leveransen.

- 60 masterruter har nye synlige fotomaterialer fra hvert sitt innebygde bildegenkall.
- 036,039,041,044 er fire rene svarte originalskygger. De er bevart og telles ikke som synlig nytegnet foto.
- 64 HE3-kopier bruker identisk RGB-PNG, men egne masker med originalens indeksflytting6..8 til9..11. RATMEN2.CEL/058 er ett kildebekreftet eksakt kopialias.
- 129 bilder og90 levende palettmasker gir219 PNG-filer. Originalens tegnerektangler, speiling, transparente hull og svarte fragmenter bevares.

`delivery.json` inneholder originalbank, rutenummer, original-PNG-hash, dimensjoner, råmaster, prompt, ferdig PNG, masker og bevis. `generation-records.json` bevarer alle separate kall og tre forkastede varianter. Feilvariantene brukes ikke som positive referanser.

`activation-set-kn3-001.json` følger det generiske aktivatorskjemaet. Kontroller uten aktivering med:

```sh
python3 tools/hd_figurer_aktiver.py art/hd-completion-figures-2026-10-11/figures/kn3-production/activation-set-kn3-001.json
```

`verification/packing-test.json` består954890 kontroller. `verification/all-routes/test.json` består1897 kontroller for alle129ruter normal/speilet, fem originale ridderpaletter, masker, ankre og eksakte Original/HD-returer uten endret emulert tilstand. Kildebaserte scanout-fixturer er ikke naturlig gameplay for alle rutene. De åtte KN3/HE3-skyggevisningene er identiske med originalen og krever derfor ingen pikselforskjell.

To originale CPU-kampposer er kontrollert med faktisk tegneliste og original palett. Scenefiksturen bruker tre dokumenterte minneskrivinger for å velge TROLL-kampen, uten palettskriving. Bilde1407 viser000/001+KN4/000 og består14kontroller. Bilde1412 viser002/003/004+KN4/001 og består17kontroller. Original- og HD-bilder finnes i `verification/composed/` og `verification/composed-wound/`. Begge sammenstillinger er visuelt sammenlignet med originalen; kropp, føtter, sverd og blod beholder originalplassering.

Samlet runtime:1928 beståtte kontroller. Rapporter og PNG-er er bundet til sourcekontrakt, faktisk HTML, produksjons-JavaScript og WASM med SHA256. Den frosne HTML-kopien ligger i den felles `verification/runtime-baseline/` og matcher testens faktisk serverte byte.

Tidlige feilforsøk er bevart som egne rapporter: manglende ekstern server, uventet lukket nettleser og testens tidligere uriktige krav om endrede svarte skyggepiksler. Siste samlede kjøring bruker en egen HTTP-server i samme Node-prosess. Ingen prosesser fra andre oppgaver stoppes.

Den aktive standardpakkens fem eldre KN1-helposeprøver har fortsatt opprinnelig prioritet. Pensjonering av disse og standardaktivering tilhører integrasjonseieren.
