# Trogg: avslutt bakehistorikken ved kampbytte og lasting

Oppfølging av PR50 sitt P2-reviewfunn. Bakgrunnskomposisjon og bakeopplysninger kunne leve videre når en ny kamp brukte samme rene arenahash, eller en senere lagring ble lastet. Dette kunne fjerne originalvernet på en ny blodpiksel som tilfeldigvis samsvarte med den gamle Trogg-komposisjonen.

scenes.js nullstiller Trogg-komposisjon ved overgangen til en ny ren kampkopi og ved en kjent scene utenfor kampen. Sammenhengende rene bilder sletter ikke nye bakekall. core.js har en frontendteller som bare økes ved vellykket lasting; scenes.js bruker den også når det lastede bildenummeret er større enn det forrige. render.js fjerner bare Troggens gamle plasseringer, køelementer og baketillatelser. UI og andre figurer beholdes. Original CPU, C-kode og lagringsformat er urørt.

reset.cjs kjører original økskamp fram til bilde2062 og prøver deretter separate frontendfixturer.92kontroller består, inklusive ny kamp med identisk ren hash, nytt blod på en tidligere eid15-piksel, reell vellykket lasting med stigende frontend-bildenummer, mislykket lasting uten revisjonsendring, kilde-/pikselavvisning og nullstilling. Full save er byteidentisk før lasting og etter de rene frontendprøvene. Vellykket original lasting beholder kjernens sjekksum. Den uendrede native lastingen normaliserer én GAME-byte (offset31 i CEL-navnet,15 til0) via game_state i port/src/game.c. Første test antok feilaktig at også denne normaliseringen skulle være byteidentisk; det er avklart i saveChanges. Mislykket lasting og etterfølgende cacheprøver beholder hele den lastede tilstanden byteidentisk.

Grafikken er nøyaktig samme225 PNG-ruter/151masker som i PR50. Den offentlige PR50-pakken består1054 kontroller, alle376 filer er byteidentiske og alle72 lagrede kampbilder har HD-bakgrunn. Oppfølgingens egne tre originalkamper, brukerflyt, CI og offentlig kontroll arkiveres i verification/.

Sluttregresjon:224/224 i tre originale kamper, alle72 kampfangster har HD-bakgrunn og samme kjernesjekksum som PR50. Brukerflyt53/53 består. PNG-er, masker og manifest er uendret.
