# AGENTS.md

Instrukser for AI-agenter og andre som jobber i dette repoet.

## Før du starter
- Les `memory.md` (fakta om spillet, maskinvaren og koden) og `todo.md` (hva som gjenstår).
- Les de siste linjene i `log.md`.

## Mens du jobber
- Logg alt du gjør i `log.md` med tidsstempel i UTC, nyeste nederst. Format:
  `- YYYY-MM-DD HH:MM UTC: hva som ble gjort, og resultatet`
- Oppdater `todo.md` når noe blir ferdig eller nye oppgaver dukker opp.
- Nye varige fakta om spillet, maskinvaren eller koden skrives i `memory.md`.

## Stil
- Dokumentasjon og kommentarer på norsk. Ingen emoji og ingen tankestrek (em dash).
- Skriv enkelt og menneskelig, uten floskler.
- C-kode: C99 (gnu99), 4 mellomrom innrykk, ingen nye avhengigheter uten god grunn.
  Kommentarer i C-filene skrives uten æ, ø og å (aa, oe), som i Moomesa-prosjektet.
- JavaScript: vanlige ES-moduler uten byggesteg. Three.js og PeerJS hentes fra CDN.

## Regler
- Spillfilene (`Moonstonecd32-AMIGA.zip`) ligger i repoet fordi eieren la dem der.
  Utpakket grafikk, lyd, disassembly (`disasm/*.s`) og bygg med spillet inni skal
  ikke sjekkes inn, og ingenting av spillets data skal på GitHub Pages (Pages er
  offentlig selv når repoet er privat). Nettsiden ber brukeren velge sin egen fil.
- Porten kjører originalkoden. En C-erstatning for en 68000-funksjon
  (`port/src/decomp/`) skal gi samme resultat som originalen. Sjekk med
  `tools/check_hooks.py`, som kjører med og uten `--nohooks` og sammenligner.
- Nettspill bygger på at kjernen er deterministisk: samme tilstand og samme
  inndata gir samme resultat på alle maskiner. Ikke bruk klokke, tilfeldige tall
  eller flyttall i emuleringen (lyd ut og bilde ut er unntatt).
- `tools/gfx.py extract` etterfulgt av `build` uten endringer skal gi identiske filer.
