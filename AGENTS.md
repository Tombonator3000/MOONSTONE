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
- JavaScript: vanlige skript uten byggesteg (web/pakk.py setter dem sammen). three.js,
  PeerJS og MQTT.js ligger i web/vendor og bygges inn i siden.

## Regler
- Spillfilene (`Moonstonecd32-AMIGA.zip`) ligger i repoet fordi eieren la dem der.
  Eieren regner Moonstone som abandonware og vil ha det enkelt: Pages-utgaven og
  Windows/Linux-pakkene fra Actions har spillfilen med (`MED_SPILLET` i
  `.github/workflows/bygg.yml`). Utpakket grafikk og lyd (`assets/`) og disassemblyen
  (`disasm/*.s`) lages lokalt med verktøyene og sjekkes ikke inn, fordi de kan lages
  på nytt når som helst.
- Porten kjører originalkoden. En C-erstatning for en 68000-funksjon
  (`port/src/decomp/`) skal gi samme resultat som originalen. Sjekk med
  `tools/check_hooks.py`, som kjører med og uten `--nohooks` og sammenligner.
- Nettspill bygger på at kjernen er deterministisk: samme tilstand og samme
  inndata gir samme resultat på alle maskiner. Ikke bruk klokke, tilfeldige tall
  eller flyttall i emuleringen (lyd ut og bilde ut er unntatt).
- `tools/gfx.py extract` etterfulgt av `build` uten endringer skal gi identiske filer.
- Lapper som bevisst endrer spillet (`port/src/patch.c`, `port/src/meny.c`: tekster.txt
  og «Online Game») skal ikke gjøre noe når de ikke er i bruk, så originalspillet er
  urørt. De registreres alltid og styres av verdier i den lagrede tilstanden, slik at
  alle maskinene i et nettspill gjør det samme også etter at en tilstand er lastet.
  Det som endrer spillets minne utenfra, går som menykommandoer ved starten av et bilde.
- Tekstene fra spillet (`tools/tekst.py extract`) sjekkes ikke inn, som grafikken.
