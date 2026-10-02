# Plan for HD-grafikk

Målet er å kunne bytte ut grafikken med versjoner i høy oppløsning, uten å endre
spillkoden eller reglene. Porten kjører originalkoden, så Amigaen tegner fortsatt
320 x 200 i 32 farger. Det er to veier, og de kan brukes sammen.

## 1. Endre filene (virker i dag)

`tools/gfx.py extract` gir alle bakgrunner og figurer som PNG. Rediger dem og kjør
`tools/gfx.py build`, så lages nye datafiler som porten bruker med `--mod MAPPE` (eller
«Egne filer» på nettsiden). Grensene er Amigaens: samme størrelse, samme antall farger,
og fargene til figurene kommer fra paletten til skjermen de vises på. Det er bra for
oppussing og egne varianter, men ikke for ekte HD.

## 2. HD-lag i three.js (neste steg)

Nettsiden tegner Amiga-bildet som en tekstur på en flate i en three.js-scene
(`web/src/render.js`). HD-grafikk legges som egne lag i samme scene, i høyere
oppløsning, oppå eller i stedet for Amiga-pikslene. Det er samme teknikk som
"HD packs" i emulatorer.

Det som trengs:

1. **Vite hva som tegnes hvor.** Figurene tegnes med Blitteren av IMAGEXCEL-modulen.
   Finn tegnerutinen i `disasm/mog.s` (den bruker CEL-dataene som kilde), og sett en
   hook på den i `port/src/decomp/` som logger hvert kall: hvilken fil, hvilket bilde,
   x, y og speiling. Bakgrunnen er kjent fra hvilken PIV som sist ble lastet
   (`last_piv` på $9CCAE). Kjernen gir listen ut med en ny funksjon i `web.c`
   (f.eks. `ms_draws()`), én liste per bilde.
2. **En HD-pakke.** En mappe med PNG-er navngitt etter fil og bildenummer, f.eks.
   `hd/kn1.ob/012.png` i fire ganger størrelse, og `hd/HighWood.PIV/0.png` i 1280 x 800.
   `tools/gfx.py extract` gir allerede riktige navn og størrelser å tegne over.
3. **Tegning.** For hver figur i listen legges en `THREE.Mesh` med HD-teksturen på
   samme sted (skalert), og for bakgrunnen en flate med HD-bildet. Der det ikke finnes
   HD-grafikk, vises Amiga-pikslene som før. Effekter som fading og fargeskift kan tas
   fra paletten i kjernen.
4. **Nettspill.** Listen over hva som tegnes lages lokalt hos hver spiller (alle kjører
   samme maskin), så HD-pakken kan være forskjellig fra spiller til spiller.

Rekkefølgen jeg foreslår: først logging av tegnekall og en testvisning som tegner
rammer rundt figurene, så bakgrunnene i HD (enklest), så figurene.
