# Hva mangler i Moonstone-porten (gjennomgang 2026-10-11)

Fem områder er gjennomgått. Funnene er kontrollert av en skeptiker, og like funn er slått sammen. Alle funnene under holdt. Ingenting i repoet er endret, og ingenting er committet.

**Kort sagt:** Det som hindrer spillerne mest nå, er at lagrede spill blir ubrukelige ved nye versjoner. Det største hullet mot målet er at ingen har spilt gjennom spillet. HD-grafikk finnes ikke for spilleren i dag, og nettspill finnes ikke på PC.

## 1) Hindrer spillere nå

1. **Lagrede spill slutter å virke når en ny versjon slippes.**
   - **Hvorfor:** Tilstanden er den eneste måten å lagre på, siden originalen ikke har egen lagring. Den avvises når STATE_VERSION, minneoppsettet eller spillfilens CRC er ulik. Versjonen har gått fra 1 til 13 på to dager.
   - **Også:**
     - Det finnes ingen overgang fra eldre versjoner.
     - Lagringer kan ikke eksporteres eller importeres.
     - En lagring fra PC (64 bit) kan ikke lastes på nettet (32 bit), og omvendt.
     - Meldingen sier ikke hvorfor lagringen ble avvist.
     - På PC havner lagringen i mappen programmet startes fra.
     - Står ikke i todo.md.
   - **Innsats:** middels.
   - **Bevis:**
     - port/src/state.c:21 `#define STATE_VERSION 13`, state.c:45-48 (sizeof(void *)), state.c:54 og 61-62.
     - web/src/app.js:1575 «Tilstanden passer ikke med denne versjonen».
     - log.md:105 «laget en ny kart.sav (den gamle hadde eldre tilstandsversjon)».
     - port/src/frontend.c:253.
     - `--load-state kamp6.sav` gir «Kunne ikke laste tilstanden».

2. **Ingen automatisk lagring, og nettsiden ber ikke om varig lagring.**
   - **Hvorfor:** På mobil kaster nettleseren ofte fanen når man bytter app eller låser telefonen. Da er alt siden siste lagring borte, og Safari kan i tillegg slette IndexedDB.
   - **Innsats:** liten.
   - **Bevis:**
     - app.js:1559: lagre() kalles bare fra knappen og PageUp (app.js:1721).
     - app.js:1735-1749: visibilitychange og pagehide lagrer ikke.
     - grep etter navigator.storage eller persist i web/src gir ingen treff.

3. **Trykk og klikk i inventaret, byen, butikkene og Select Knight gir fire der spillets skjulte peker står, ikke der man trykker.** Et trykk på kartet blir også til fire.
   - **Hvorfor:** Man kan bruke eller velge feil ting.
   - **Merk:** todo.md:27 har punktet, men ikke at alle disse skjermene deler samme peker og kan løses samlet.
   - **Innsats:** middels.
   - **Bevis:**
     - app.js:300-313: klikk() setter museFire og sjekker ikke pointerType.
     - Pekeren ligger på $098092/$098094 og feltlisten på $09A020 (disasm/mog.s 08c3ea, 08ab22).
     - grep etter 98092 og 8F51E i port/src gir ingen treff.

4. **Nettspill med ulike versjoner henger uten forklaring.**
   - **Hvorfor:** Nett.VERSJON har stått på 3 mens STATE_VERSION gikk fra 9 til 13.
     - En gjest med en gammel side i hurtigbufferen kommer gjennom «hei», men tilstanden avvises.
     - Gjesten blir stående i «venter», og ventekøen (rammer) vokser uten å tømmes.
     - Verten venter for alltid på turen hans, fordi pingen holder ham «i live».
     - Romlisten har heller ingen versjon.
   - **Innsats:** liten.
   - **Bevis:**
     - web/src/net.js:27 `const VERSJON = 3`, net.js:222 (g.sist settes ved alle meldinger), net.js:510-512.
     - app.js:913 «Kunne ikke laste spillet fra verten.» (modus endres ikke), app.js:1160.
     - git log -G'define STATE_VERSION': 4d01114, 074a75b, 3b6cf0f og 4672258 er alle etter ea5945b.

5. **I Separate er hverKart() sann hele spillet.**
   - **Hvorfor:**
     - En spiller i en by eller en monsterkamp blir aldri meldt «borte».
     - Han svarer automatisk ja på en utfordring.
     - Duellresultatet skrives inn midt i den andre kampen.
     - docs og README lover det motsatte.
   - **Innsats:** middels.
   - **Bevis:**
     - port/src/hver.c:297 (eneste `H.kart = 0`, i tittelmenyen) og hver.c:381 (`H.kart = 1` ved hver tur).
     - app.js:998 og 1143.
     - docs/flerspiller.md:116 og 175, README.md:85-86.

6. **PC-versjonen har ingen nedlastbar utgivelse.**
   - **Hvorfor:** README sender spillerne til Actions-artefakter. De krever GitHub-innlogging og slettes etter 90 dager. README sier heller ikke at spilleren trenger libSDL2 og glibc 2.34 på Linux.
   - **Innsats:** liten.
   - **Bevis:**
     - `gh api repos/Tombonator3000/MOONSTONE/releases` gir `[]`.
     - .github/workflows/bygg.yml har bare jobbene linux, windows, web og pages.
     - README.md:112.

7. **Nettsiden tror sluttscenen er introen.**
   - **Hvorfor:** Den som nettopp har vunnet, får teksten «hopper over introen». Fire, trykk og Enter blir gjort om til Esc, og musikken og HD-laget slås av.
   - **Merk:** Dette er funnet i koden, ikke vist i en nettleser.
   - **Innsats:** liten.
   - **Bevis:**
     - port/src/web.c:185 `return whd_mog_loaded ? 0 : 1`.
     - port/src/whdload.c:305.
     - app.js:226-241 og 253-258.

8. **Turns: en gjest med skjult fane regnes aldri som borte, og spillet venter på turen hans.**
   - **Hvorfor:** Pingen sendes fra setInterval, som går videre i en skjult fane. Dette gjelder mest PC, siden en låst mobil som regel fryser siden helt.
   - **Innsats:** liten.
   - **Bevis:**
     - net.js:467-474 og net.js:222.
     - log.md 12:48: testen stopper spillokka, ikke pingen.

9. **Turns: verten har den eneste kopien av spillet som kan lagres.**
   - **Hvorfor:** Gjesten kan ikke lagre. Mister gjesten verten, starter den fra introen igjen og kaster kopien.
   - **Innsats:** middels.
   - **Bevis:** app.js:1559 (lagre() avviser modus 'gjest'), app.js:910 og 157-180 (startPaaNytt).

10. **Tapt WebGL-kontekst gir svart skjerm uten reserve.**
    - **Hvorfor:** Det skjer ofte på mobil når appen går i bakgrunnen. Uten automatisk lagring er framgangen da borte.
    - **Innsats:** middels.
    - **Bevis:** grep etter contextlost i web/src gir ingen treff; render.js:232 lager WebGLRenderer uten reserve.

## 2) Mangler for målet

1. **Ingen har spilt gjennom spillet.**
   - **Hva som aldri er sjekket:**
     - butikkene og Merchant
     - tavernaen og terningene
     - Waterdeep og Math
     - dragen og vokteren
     - Stonehenge
     - Game Over for én spiller og i Turns
   - **Hvorfor:** Gjennomspilling på alle plattformer er selve målet. Highwood, healeren og sluttscenen er vist headless.
   - **Innsats:** stor.
   - **Bevis:**
     - disasm/functions.txt: 236 funksjoner med «kjort nei», blant dem 082844 kamp_mot_drage, 082960 kamp_mot_vokter og 08a802 stonehenge_druider.
     - log.md nevner Game Over bare i Separate og duell (log.md:82 og 94).
     - todo.md:22 står åpen.

2. **HD-grafikk finnes ikke for spilleren, bare verktøyene for å lage den.**
   - **Hvorfor:**
     - Bakgrunner leses bare som `bg/HASH.png`.
     - hd_skaler.py lager mapper som `HighWood.PIV/000.png`, som render.js aldri leser.
     - Fargene i de skalerte bildene kommer fra forhåndsvisningspaletten, ikke fra skjermen.
   - **Innsats:** stor.
   - **Bevis:**
     - git ls-files har ingen PNG utenom disasm.
     - web/src/render.js:493.
     - docs/hd-grafikk.md («Glatt (Scale4x)»).
     - todo-punktene «HD-pakke som eksempel» og «HD-bakgrunner etter filnavn» er ikke påbegynt.

3. **HD-pakken på nettet huskes ikke og er vanskelig å velge på mobil.**
   - **Hvorfor:**
     - Pakken må velges på nytt etter hver omlasting.
     - Den kan bare velges som en mappe, og zip støttes ikke.
     - Velges filene enkeltvis, blir alle hoppet over.
     - HD når dermed i praksis ikke mobil.
   - **Innsats:** middels.
   - **Bevis:** app.js:1702-1708 (ingen Lager.sett), web/src/index.html:101 (webkitdirectory), render.js:532-533.

4. **HD, effekter og Glatt-filteret mangler i PC-versjonen.**
   - **Hvorfor:**
     - PC kan ikke lese PNG.
     - Hele HD-logikken ligger i JavaScript og må skrives på nytt i C.
     - Det kan gjøres med SDL_Renderer, så OpenGL er ikke nødvendig.
   - **Innsats:** stor.
   - **Bevis:**
     - port/src/png.c:33 har bare png_write.
     - frontend.c:39 har bare tre filtre, og grep etter lag_ eller hd i frontend.c gir ingen treff.
     - lag_paa settes bare i main.c:223 og 226 (headless).

5. **PC-versjonen har ikke nettspill, og todo.md har verken punkt eller vedtak om det.**
   - **Hvorfor:** Målet er nettspill også på Linux og Windows.
   - **Innsats:** stor.
   - **Bevis:**
     - README.md:88.
     - Hovedløkka i frontend.c (ca. linje 365-368) leser ingen menyhendelser og kaller ikke hver_frame.

6. **Testene ligger ikke i repoet, og CI kjører nesten ingenting.**
   - **Hvorfor:**
     - Nettlesertestene (test26-36, Options, mus, mobil) finnes bare i scratchpad.
     - Det samme gjelder tilstandene de bruker, som kart.sav.
     - CI kjører bare introen og aldri check_hooks.py, selv om den tar 42 s og går grønt.
     - En gjennomspillingstest har ikke noe sted å bo.
   - **Innsats:** middels.
   - **Bevis:**
     - `git ls-files | grep -i test` gir ingenting.
     - bygg.yml:37-41.
     - memory.md:250, 258 og 321 viser til `$S/test26.js` og `$S/test35.js`.

7. **Hver for seg steg 4 er ikke begynt.**
   - **Hvorfor:**
     - To som utfordrer hverandre samtidig, kjemper begge mot en datamaskinstyrt kopi av den andre.
     - Ingen sier fra når motstanderen er «opptatt».
     - Årstidene går hver for seg.
   - **Innsats:** middels.
   - **Bevis:** app.js:1050-1077 og 1143, todo.md:10, docs/flerspiller.md:214.

8. **PC har ingen innstillingsmeny.**
   - **Hvorfor:**
     - Musikk og volum kan bare velges på kommandolinjen.
     - Alle beskjeder, også Pause, vises bare i vindustittelen og er usynlige i fullskjerm.
     - Spiller 2 på tastatur krever talltastatur.
     - `--online-meny` gir en Options-side som blir stående på «Creating Room...».
   - **Innsats:** middels.
   - **Bevis:** frontend.c:54 (show), frontend.c:237 og 359, frontend.c:117 (bare KP-taster), meny.c:476-489.

9. **Mobil mangler fullskjerm, hjemskjerm-app og Wake Lock.**
   - **Hvorfor:** Spillbildet blir lite, og skjermen kan slukke under lange turer.
   - **Innsats:** liten.
   - **Bevis:** grep etter fullscreen, wakeLock, manifest og serviceWorker i web/src gir ingen treff.

10. **Separate: et rom som forsvinner kan ikke samles igjen midt i spillet, og en død forbindelse blir stående som ridder på kartet.**
    - **Hvorfor:** Spillerne må tilbake til tittelmenyen for å lage et nytt rom.
    - **Innsats:** middels.
    - **Bevis:** net.js:190 (vakten er av i Separate), app.js:1009-1023.

11. **Et lagret Turns-spill fordeler ridderne etter rekkefølgen gjestene kommer inn i.**
    - **Hvorfor:** Verten må rette opp for hånd uten å få beskjed. Liten betydning.
    - **Bevis:** net.js:599 (husk tømmes), net.js:79 og 84 (sessionStorage), app.js:1568-1583.

12. **Native port: bare 2 av 412 funksjoner er i C.**
    - **Hvorfor:** C-utgaven av joydat_til_bits kjøres aldri og er dermed ikke sjekket. Det betyr lite for spilleren så lenge emulatoren kjører originalkoden.
    - **Innsats:** stor.
    - **Bevis:**
      - port/src/decomp/decomp.c:141-142.
      - `tools/check_hooks.py` gir «082008 joydat_til_bits kjort i C 0 ganger».
      - Testscriptet slutter i bilde 12000 (check_hooks.py:23-25).

13. **HD-bakgrunnen tones ikke inn første gang den vises.** Synes først når det finnes en HD-pakke.
    - **Innsats:** liten.
    - **Bevis:** render.js:495-497.

14. **CI bruker actions på Node 20, som er utfaset.**
    - **Hvorfor:** Publiseringen kan slutte å virke uten at koden er endret.
    - **Innsats:** liten.
    - **Bevis:** `gh run view 37130691317`; bygg.yml:29, 46, 86, 99 og 117.

## 3) Bare utestet

1. **Nettspill er aldri prøvd mot de offentlige serverne nettsiden bruker** (PeerJS Cloud, HiveMQ og TURN bak NAT). Alt er testet mot lokale servere. Dette er den største usikkerheten for nettspill.
   - **Bevis:** todo.md:23, README.md:240.
2. **Duellen er aldri målt over et ekte nett.**
   - **Hvorfor:** Angriperen har ingen forsinkelse, mens forsvarerens joystick kommer etter en tur over nettet. Etter 12 s stillhet tar datamaskinen over.
   - **Bevis:** app.js:1275-1277, 1389-1398 og 1038.
3. **Ingenting er prøvd på ekte iPhone eller Android:** iOS-lyd, zoom, mappevalg og nettspill fra mobil.
   - **Bevis:** todo-punktet står åpent; Playwright-testene var bare emulert mobil.
4. **Ekte Windows er ikke prøvd.** CI kjører aldri exe-filen, og den bygges med `-w`, som skjuler alle advarsler.
   - **Bevis:** bygg.yml (windows-jobben), port/Makefile:71.
5. **Sluttscenen virker i kjernen, men har ingen fast test.** Den ble vist headless ved å tvinge hoppet til $081846, med program, vmusic og tilbake til tittelmenyen. `--skriv` leser verdien med base 0, så heks uten 0x blir til 0 uten melding.
   - **Bevis:** port/src/main.c:282-283.

## 4) Feil i todo.md

1. **Punktet om å flette workflow-rettelsen (a998217) er allerede gjort.** Rettelsen er likevel aldri prøvd med en kjøring startet for hånd.
   - **Bevis:**
     - todo.md:15-16.
     - `git merge-base --is-ancestor a998217 origin/main` gir sant.
     - bygg.yml:100 og 106.
     - Siste kjøring startet for hånd var 2026-10-02 14:30, før rettelsen.
2. **Todo sier at «tekst i HD» og «fading på HD-bildene» gjenstår, men begge står under Ferdig.** docs/hd-grafikk.md:167-168 er halvt feil, siden menyrammer fortsatt gjenstår.
   - **Bevis:** todo.md:10 og 16 mot todo.md:41 og 44.
3. **«I dag bare tastene 1-9» er upresist.** LB, RB, X og Y på spillkontrolleren velger allerede 1-4. windows/LES_MEG.txt nevner ikke dette, og heller ikke musikken.
   - **Bevis:** todo.md:5, frontend.c:147-150.
4. **«HD på PC trenger OpenGL» undervurderer arbeidet.** Det som faktisk trengs, er en PNG-leser og HD-tegning i C (se punkt 2.4).
   - **Bevis:** todo.md:14-15, png.c:33.
5. **todo.md:21 («Flere funksjoner i C») sier det samme som steg 2 i todo.md:12.** De kan slås sammen.
6. **Kodedekningen er foreldet.** coverage.bin og functions.txt er fra 2 oktober, før kamp og rull ble testet. Todo bør si at dekningen må lages på nytt, helst fra en gjennomspilling.
   - **Bevis:** functions.txt:46-47 viser joystick_for_figur og vent_paa_fire som «kjort nei», selv om begge kjører i hver kamp.
7. **Dette mangler helt i todo.md:**
   - versjonering og overgang for lagringer, eksport og import
   - automatisk lagring
   - versjonssjekk ved oppkobling i nettspill
   - feilen med hverKart
   - utgivelser for PC
   - nettspill på PC (eller et vedtak om å la det være)
   - testene inn i repoet og CI
   - reserve for WebGL
   - fullskjerm på mobil
   - sluttscenen på nettsiden
   - innstillinger på PC
8. **Utdaterte dokumenter:** memory.md:246 sier «STATE_VERSION 8», og README.md:340 viser til mappen spill/, som ikke finnes.

## Ikke dekket

- **Gjennomspilling:** Ingen har spilt naturlig fram til butikkene, tavernaen, Waterdeep, lair-kampene, dragen, vokteren, Stonehenge eller Game Over. Det gjelder også sluttscenen og Game Over i Separate og Turns.
- **Sluttscenen i nettleser:** Om Esc og trykk faktisk kutter den, er ikke vist.
- **Ekte enheter:** ingen iPhone, Android eller Windows (heller ikke Wine), og PC-vinduet er ikke kjørt interaktivt. Spillkontroller er ikke prøvd i ekte SDL.
- **Nettspill:** Ingen kjøring med to nettlesere i denne runden. Funnene om nettspill bygger på koden.
- **HD på nettsiden:** Den ble ikke bygget, og HD-pakken og effektene er ikke prøvd i Chromium.
- **Kampbakgrunnene fra .t:** Det er ikke sjekket om de gir stabile hasher utenom Practice.