# Analyse av de elleve monsterkonseptene

Konseptene er laget med innebygd image_gen og kontrollert visuelt mot originalrutene. Modellversjonen eksponeres ikke av verktøyet. Dette er forarbeid og foreslått detaljering, ikke en påstand om ferdige eller feilfrie spritesheets. Ingen av bildene er aktivert i spillet.

## Kilde og avgrensning

25 originale kampbanker gir 1302 ruter, inklusive Black Knight, separate våpen, skygger, blod og ridderofre. Dette er rå ruteantall, ikke 1302 nye HD-mastere. Hver rute har bredde, høyde, flagg, planmaske og SHA i [source/inventory.json](source/inventory.json). Kontaktarkene utvider sparsomme bitplan riktig. Palettkontraktene er hentet fra eksisterende original CPU-bevis eller konkret original palettkode 088a4e..088d14.

[Originalmanualen](https://www.freegameempire.com/games/Moonstone-A-Hard-Days-Knight/manual) støtter monstergruppene, tre Trogg-våpen, Mudmens planteidentitet og Guardians rolle. Form, klær, farger og ruteinndeling nedenfor er vurdert fra originale bilder og kode. Nye sømmer, hudporer, klør og materialdetaljer er kunstneriske tolkninger.

Den gamle beskrivelsen av dg1.cel som «grønt beist» er feil. Faktisk original sluttgren viser to ritualdansere. Kontrollen kjørte 6000 bilder med bare originalens sluttflagg 0x3e0 satt til 0x80 under oppstart, uten grafikk-/palettskriving. [Originalt bilde1750](source/ending-1750-original.png), kommando og filspor er bevart. Den er derfor utelatt fra monsterkonseptene. [Publiserte originalbilder av sluttsekvensen](https://moonstonetavern.co.uk/the-tales-conclusion/) bekrefter samme motiv. bg8-PIV-paletten alene er ikke en bekreftet full CPU-palett for danserne og skal ikke brukes til nytegning uten egen kontroll.

Klift1 er en ritualridder. Demon1..4 er én Guardian, ikke fire arter. Dragon5 er hovedsakelig brann/skade, ikke en ekstra drage. Trogg-øks og hammer deler kropp og banker, men har forskjellige våpenruter.

## Balok

[Konsept v2](concepts/balok-v2.png). Kilde: Balok1/2/3,156 ruter. Tydelige referanser er Balok1/027 helfigur,000/004/018 kjeve,041 åpen munn og043 sammenklemt kropp.

Bevar lav krøket kropp, enorm tannfylt kjeve, svart hår over hode/rygg, oransje/rustfarget kjøtt, kraftige bare armer og lange føtter. Fast monsterpalett9..14 er f96,c63,930,842,521,f63. Første kandidat fikk et ekstra lyst horn ved øret; dette er fjernet i v2. Bildet har nå riktig hovedidentitet, uten minotaurhorn eller rustning. Øreform og huddetaljer er tolkning.

Før spritesheets: skill hode/kjeve fra kropp der originalen gjør det. Åpning av munnen må ikke skalere skallen. Bind bitt, huking og strekk til de faktiske rutene og koblingene. Ridderrester i Balok2/3 beholder spillerens palett6..8 og må aldri farges som Balok-hud. Detaljert hår må følge originalens silhuett fremfor å utvide hver sprite.

## War Beast

[Konsept](concepts/war-beast.png). Kilde: be1.c/be2.c,134 ruter. be1/000,005,020 og029 viser helfigur/profil;009 viser front og054 sammensatt offerkontakt.

Bevar lav firbeint kropp, massiv svart manke, rustbrune lemmer, lys grå snute, små røde øyne og lange lyse fremspring ved munnen. Konseptet bevarer dette og gir ingen sal eller rytter. Det er en egen originalskapning, ikke en vanlig ulv. Hår, poter og snutedetaljer er realistisk tolkning.

Før spritesheets: avklar de lyse fremspringenes eksakte feste i flere sammensatte originalposer, før en fast modell eventuelt lages. Bevar originalens forhold mellom manke, kropp og korte bakparti. Separate hode-/haledeler og eventuelle spyttfelt får egne ruter; cyan effekt14 skal ikke bli permanent pelsfarge. Alle grep-/offerbilder må ha riktig kontakt og ridderfarge.

## Mudman

[Konsept v2](concepts/mudman-v2.png). Kilde: Mudmen1/2,129 ruter. Mudmen1/030,041 viser oppreist planteform;002 og016 fremkomst;037/038/044 rotgrep;053 og061 kontakt med ridder.

Bevar en koloni av bark, røtter, grønt plantemateriale og jord, med lyst avlangt dyreskallelignende hode og oker vekst på ryggen. Basen går over i bakken. Konseptet har ingen menneskeføtter eller rustning. V2 smalner og forlenger hodeformen, fordi første kandidat fikk et for rundt skallepreg. Den eksakte beinarten bak hodeformen er ikke dokumentert, så bildet gir den ikke et zoologisk navn.

Før spritesheets: fremkomst og nedsynking må bevare hver opprinnelig synlig høyde. Lange tynne gripe-røtter må forbli sammenhengende gjennom grep og tilbaketrekking. Ikke erstatt rotfragmenter med hele hender. Skill jord, blader og offerdeler; terrengavhengige plantefarger må kontrolleres i faktisk palett. Konseptets barktekstur er et materialforslag, ikke en endring av den opprinnelige bakkekontakten.

## Troll

[Konsept](concepts/troll.png). Kilde: TROLL1/2,64 ruter. TROLL1/013 helfigur,006 klar lav klubbestilling,016 stående grep,028 hode og032/037 hevet overkropp.

Bevar høy, langbeint og muskuløs hårløs kropp, blåfiolett hud, små røde øyne og grov treklubbe. Hud9..12 er55a,347,123,001. Konseptet følger dette, inklusive brune fotformer, og unngår brun/gullfarget kjempe, skjegg og metallhammer. Tær, hudfolder og trefliser er tolkning.

Før spritesheets: hold klubbe/hånd-festet stabilt når torso, bein og våpen tegnes separat. Skill den flate svarte originalskyggen fra kroppsdetaljer, uten å slette alt svart. Mål original høyde mot ridderen, ikke konseptbildets lerret. Kontroller alle klubbeposisjoner og treff, ikke bare hvilebildet.

## Ratman

[Konsept](concepts/ratman.png). Kilde: RATMEN1/2,128 ruter. Ratmen1/045 og043 viser lav helfigur,004..007 sammenrulling,024..028 hopp; Ratmen2/019 viser rulling med synlige føtter.

Bevar liten rund og krøket silhuett, stri rustbrun pels, lang lys snute, små bare hender/føtter og lang mørk hale. Konseptet har dette, uten menneskekropp, kappe eller våpen. Palett9..14 er653,942,720,500,a96,875. Pelsstrå, klør og fortenner er detaljtolkning.

Før spritesheets: gjenbruk samme hode/snute under hopp og rulling. Hold halefestet stabilt selv når kroppen ligger eller roterer. Bladverket i Ratmen1/063 er et eget skjulfelt, ikke pels eller en ny skapning. Riddergrep og spyd-/dødsfragmenter farges etter opprinnelig materiale. Bevar lav størrelse og lesbar silhuett når figuren skaleres til faktisk spillmål.

## Guardian

[Konsept](concepts/guardian.png). Kilde: Demon1..4,224 ruter. Demon1/027,035,041 viser ansikt/tendriler; Demon2/033,053 kropp; Demon3 piske-/grepformer; Demon4/003 og009 virvel. Eksisterende kontrollert originalkamp viser også ren virveltilstand.

Bevar cyan demonansikt, røde øyne, strømformede hodedeler, klør og blåhvit virvel. Konseptet viser en foreslått overgangstilstand med overkropp, energitendril og virvel, uten steinmateriale eller vanlig røyk. Det lysende energimaterialet er en visuell tolkning av originalens cyanformer. Originalen beviser ikke denne ene konseptkomposisjonen som en bestemt spillrute.

Før spritesheets: skill ren virvel, fremkomst, formet kropp, tendril, oppløsning og de opprinnelige segmenterte underkroppsdelene. Konseptets virvel må ikke fjerne kroppsdeler fra andre originalfaser. Energitendrilen er ikke en lærpisk. Ikke legg stor ukontrollert glød utenfor kildeformen. Alle Demon2-fragmenter med negative svartfelt må testes i samlet original sekvens, uten at kroppen skifter identitet når den løses opp.

## Dragon

[Konsept](concepts/dragon.png). Kilde: Dragon1/2/5,94 ruter, inklusive seks tomme startruter i Dragon1. Dragon1/006,009,012 viser hode/horn,013 åpen kjeve; Dragon2/000..007 vingedeler,008 torso og022/023 ild.

Bevar røde skjell, smal krokodillelignende snute, gult øye, svært lange bakoverrettede lyse hodehorn og matte brungrå vingemembraner. Konseptet følger disse kjennetegnene. Den komplette kroppen, halen, lemmene, ryggpiggene og vingefestene er delvis forslag, fordi de undersøkte originale bankene består av utsnitt. Dette bildet er derfor ikke nok til å låse en full dragemodell.

Før spritesheets: lag først en sammensatt originalreferanse for hver kameratilstand og kontroller vinger/torso/lemmer samlet. Ikke ta konseptets fire bein og ekstra små pigger som kildebevis. De lange hornene må beholde original retning og klipping. Bevar tomme ruter og egne munndeler. Brann29..31 og brennende offerbilder må holdes utenfor røde skjellmasker; ridder6..8 beholdes separat. Dragen er uttrykkelig ikke klar for mekanisk arkgenerering fra konseptet alene.

## Black Knight

[Konsept](concepts/black-knight.png). Kilde: HE1..3,148 ruter. HE1/000,010,017 og023 gir kropp/drakt; sverd og angrepsdeler ligger i videre HE-ruter.

Bevar lukket stålhjelm, smal mørk synsspalte, grå metallrustning, mørk lilla drakt, liten bakovervendt lilla hjelmduk og rett sverd. Konseptet viser samme menneskelige riddertype som originalen, uten demonansikt, horn, skjold eller bossproporsjoner. Slitasje, nagler og sømmer er tolkning.

Før spritesheets: HE og KN deler opprinnelige former med palettomlegging. Ikke lag en uavhengig annen kropp eller endre kamphøyden. Konseptets stoff er litt lysere i belyste partier enn de dypeste originalfargene; den levende palettbindingen må styre ferdige ruter. Hjelm, plume, hender og sverd skal følge de originale festene gjennom gange, treff og død.

## Trogg med øks

[Konsept](concepts/trogg-axe.png). Kilde: TroggAxe1/2,117 delte ruter med hammervarianten. TroggAxe1/025 og033 gir kropp,000/004 grepsoverdel. TroggAxe2/055..068 viser øksevåpenet.

Bevar oransjebrunt ansikt og bare underarmer, lang krokete nese, matt grå hjelm, langt mørkt hår, marineblå tunika/bukser og enkle støvler. Konseptet har en kompakt lys øks på mørkt skaft og riktig helfiguridentitet. Vi viser den originale terreng0c-varianten; originalen har flere terrengpaletter. Stoffslitasje og ansiktets fine detaljer er tolkning.

Før spritesheets: kroppen og våpenet forblir separate der originalen gjør det. Lås håndkontakt og riktig økserute per angrepsbilde, også etter speiling. Ikke behold samme diagonale konseptstilling i alle bilder. Tunikaens bredde og hårvolum må tilpasses egen originalrute, ikke uniform skalering av dette bildet.

## Trogg med hammer

[Konsept](concepts/trogg-hammer.png). Kilde er samme117 ruter som øksen. Hammeren finnes konkret i TroggAxe2/069 og073..079. Den er altså ikke en oppdiktet ny art eller en manglende egen CEL-bank.

Konseptet er en redigering av øksens samme figur, med bevart ansikt, hår, hjelm, drakt og kropp. Våpenet er byttet til en enkel lys rektangulær hammer på mørkt treskaft, uten økseblad, pigger eller strøm. Begge hender har tydelig kontakt med ett skaft.

Før spritesheets: bruk felles kroppsmastere med øksen når kildeindeksene er identiske. Hold hammerhode og skaftfeste samlet, men bind hvert våpenbilde til riktig originalrute. Kontroller om hovedet ses som blokk, tverrflate eller smalt snitt i hver vinkel. Ikke tegn en ny variant av klærne mellom våpenslag.

## Trogg med spyd

[Konsept](concepts/trogg-spear.png). Kilde: TroggSpear1/2,108 ruter. TroggSpear1/000 og008 viser samme kroppsidentitet; TroggSpear2/052,056,062,065 viser skaft og spiss. Maksimal original rutebredde i bank2 er126 piksler.

Konseptet beholder øksens samme figur og viser et langt mørkt skaft med liten lys spiss, holdt i begge hender. Hele spydet er synlig. Ingen øks, hammer eller ekstra skjold er igjen. Armstillingen er endret for våpenet, mens identiteten er bevart.

Før spritesheets: kontroller lange utstrekninger og spydspissens treffpunkt, særlig ved klipping og speiling. Ikke krymp spydet for å få en smalere celle. Delte kroppsruter gjenbrukes bare når faktiske originalindekser er like. De blå ridderfragmentene og spiddingssekvensene i bank1 er offerbilder, ikke Troggens antrekk.

## Bindende grunnlag for neste produksjonssteg

1. Lås riktig sourcebank/frame og original SHA før tegning. Les naboruter og faktisk sammensatt animasjon. Ingen standardoppskrift som «åtte gangbilder, åtte angrep» uten kildetabell.
2. Bruk hver originals bredde/høyde og godkjent4x-mål. Bevar tegnerekkefølge, xoff/anker, skjermpunkt, timing, speiling og original hitbox. Disse runtimefeltene er ikke fullkartlagt av en kontaktarkeksport.
3. Skriv en delkontrakt for hode/kropp, hånd/våpen, offer, jord, skygge, ild og energi. Et fragment får ikke erstattes av en helfigur. Konseptbildets positur er ikke rutekontrakt.
4. Skill faste materialer fra levende palettfelt. Riddere6..8, blod15, drageild29..31 og terrengavhengige farger skal testes i riktig tilstand. Ingen generell recoloring av hele bildet.
5. Lag en liten sammenhengende prøvesekvens per monster først. Kontroller original og HD ved samme originaltilstand, i faktisk kampmål og foran relevant bakgrunn. Deretter kan resterende kildebundne ruter produseres uten å endre identiteten.
6. Kontroller hele serien for størrelseshopp, endrede ansikter/klær, løse våpen, feil ledd, kantklipping, svart-/alfafeil, glød og ulovlige ekstra detaljer. Kontroller alle fire ridderfarger i kontaktbilder, ikke bare blå.
7. Aktivering krever både visuell kontroll av hele relevante animasjoner og tekniske mål-/kilde-/palett-/lagrings-/determinismekontroller. Ingen av disse konseptene eller preproduksjonskontrollene erstatter disse prøvene.

Første bilderevisjoner er bevart som avviste: Baloks ekstra ørehorn og Mudmans runde hode. De skal aldri brukes som positive identitetsreferanser. Dragens totale anatomi og Guardians tilstandsdeling må avklares før full serie. Vi kan redusere feil med disse kontraktene og prøvene; et løfte om null feil før spriteproduksjon ville vært udokumentert.
