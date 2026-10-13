# Trogg: avslutt bakehistorikken ved kampbytte og lasting

Oppfølging av PR50 sitt P2-reviewfunn. Bakgrunnskomposisjon og bakeopplysninger kunne leve videre når en ny kamp brukte samme rene arenahash, eller en senere lagring ble lastet. Dette kunne fjerne originalvernet på en ny blodpiksel som tilfeldigvis samsvarte med den gamle Trogg-komposisjonen.

scenes.js nullstiller Trogg-komposisjon ved overgangen til en ny ren kampkopi og ved en kjent scene utenfor kampen. Sammenhengende rene bilder sletter ikke nye bakekall. core.js har en frontendteller som bare økes ved vellykket lasting; scenes.js bruker den også når det lastede bildenummeret er større enn det forrige. render.js fjerner bare Troggens gamle plasseringer, køelementer og baketillatelser. UI og andre figurer beholdes. Original CPU, C-kode og lagringsformat er urørt.

reset.cjs kjører original økskamp fram til bilde2062 og prøver deretter separate frontendfixturer.92kontroller består, inklusive ny kamp med identisk ren hash, nytt blod på en tidligere eid15-piksel, reell vellykket lasting med stigende frontend-bildenummer, mislykket lasting uten revisjonsendring, kilde-/pikselavvisning og nullstilling. Full save er byteidentisk før lasting og etter de rene frontendprøvene. Vellykket original lasting beholder kjernens sjekksum. Den uendrede native lastingen normaliserer én GAME-byte (offset31 i CEL-navnet,15 til0) via game_state i port/src/game.c. Første test antok feilaktig at også denne normaliseringen skulle være byteidentisk; det er avklart i saveChanges. Mislykket lasting og etterfølgende cacheprøver beholder hele den lastede tilstanden byteidentisk.

Grafikken er nøyaktig samme225 PNG-ruter/151masker som i PR50. Den offentlige PR50-pakken består1054 kontroller, alle376 filer er byteidentiske og alle72 lagrede kampbilder har HD-bakgrunn. Oppfølgingens egne tre originalkamper, brukerflyt, CI og offentlig kontroll arkiveres i verification/.

Sluttregresjon:224/224 i tre originale kamper, alle72 kampfangster har HD-bakgrunn og samme kjernesjekksum som PR50. Brukerflyt53/53 består. PNG-er, masker og manifest er uendret.

## Synkron lasting og flere native bilder per tegning

PR51 sitt P2-funn er rettet: core.js varsler scenes.js synkront etter vellykket lasting, før nye spillbilder kan kjøre. Den gamle native tegnelisten er ikke en del av lagringsformatet og skjules til første nye native bilde. Mislykket lasting endrer ingen revisjon eller cache.

render.js samler alle087b34-bakekall i en avgrenset kø mellom skjermtegningene. scenes.js bruker denne køen, ikke bare tegnelisten fra siste native bilde. SHA-kontroll som fortsatt venter kan prøves igjen. Når en ny ren arena oppdages, fjernes gamle plasseringer og komposisjon mens nye, ennå ikke konsumerte bakekall bevares. Kildenes SHA, geometri og pikselvern er fortsatt påkrevd.

Ny målrettet prøve i verification/synchronous-reset består102 kontroller: gammel native tegneliste skjules, reset skjer før første post-load-bake, første-av-fire-bake og tillatelse bevares, og ny ren arena beholder ferske bakekall. Tidligere92/95-resultater er historiske bevis fra eldre kode. verification/local-final.json beskriver den tidligere revisjonen, ikke denne siste rettelsen.

Fire native bilder per tegning:221/221 kontroller i tre kamper,57 øks-/58 hammer-/64 spydruter observert. Alle71 fangster har HD-bakgrunn. Færre observerte ruter enn enkeltrammeprøven skyldes at skjermen nå bare fanges hver fjerde ramme; alle225 konkrete filer er fortsatt i pakken. verification/synchronous-final.json binder den siste koden til disse bevisene.
