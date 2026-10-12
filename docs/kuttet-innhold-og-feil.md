# Moonstone: kuttet innhold, feil og utviklingsideer

Samlet 12. oktober 2026 fra tidligere undersøkelser og kontrollert mot kildene
under. Kodegrunnlaget er `Tombonator3000/MOONSTONE`, main `f77a2d25` etter PR #44.
Dette er et funnregister. Oppføringer her betyr ikke at innhold er implementert,
at en feil er gjenskapt lokalt eller at en foreslått regelendring er bestilt.

**Status:** Bekreftet betyr direkte utviklerutsagn eller konkret kildekode.
Rapportert betyr en navngitt spillers observasjon. Uavklart betyr at påstanden
fortsatt mangler tilstrekkelig belegg. Forslag betyr en ny utviklingsidé.
Bekreftet historikk er ikke det samme som gjenfunnet kode eller ferdige assets.

## Bekreftede utelatelser og planer

| ID | Funn | Grunnlag og begrensning |
| --- | --- | --- |
| C01 | Synlige endringer når ridderen får bedre rustning eller sverd. | Rob Anderson ønsket dette. Minne og lastetid var viktige hindringer. [S1] |
| C02 | Riddertyper med forskjellig høyde, kroppsbygning, kampstil og angrep. | Rob beskriver ønsket variasjon, og at Moonstone 2-designet skulle ta den videre. Ingen komplett animasjonsbank er gjenfunnet. [S1] |
| C03 | Større Guardian- og Dragon-kamper. | Rob sier at tid og minne begrenset omfanget. Intervjuet gir ingen komplett spesifikasjon for nye faser eller arenaer. [S2] |
| C04 | Flere fiender som aldri ble ferdigutviklet. | Rob sier at de ga for liten ekstra spillverdi i forhold til utviklingstiden. Antall, navn og brukbare spritebanker er ikke fastslått. [S2] |
| C05 | Flere RPG-elementer, mer monsterinnhold og bedre drageoppførsel på kartet. | Todd Prescotts etterfølgende ønsker, ikke en dokumentert liste over ferdiglagde kutt. [S1] |
| C06 | Moonstone 2 kom til design og konseptkunst. | Rob beskriver omtrent en måneds arbeid. Oppfølgeren ble ikke realisert etter svakt salg; nordamerikansk uteblivelse inngår i hans forklaring. [S1] |
| C07 | Lagring manglet i originalen. | Rob og Todd mener i ettertid at lagring ville hjulpet spillere og testing. Dette bekrefter en mangel, men ikke at en ferdig save-/passordfunksjon ble kuttet av RAM-hensyn. [S1], [S2] |

Rob kommenterer også at omslagets hobbitlignende figur ikke finnes i spillet.
Omslagskunst alene beviser derfor ingen kuttet spillfigur. [S2]

## Spillbeskrivelser som må undersøkes i originalkoden

Manualen beskriver måneskifte hvert tredje spilldøgn, styrkepåvirkning på enkelte
skapninger, Ratmen som blir sterkere mens månen vokser, og doble gjeldende
hit points med passende Moonstone. Black Knights skal jakte deltakere og øke
ferdighet og styrke under kamp. Dette er testkrav fra manualen, ikke bevis for
at funksjonene mangler. Byene har allerede handel, helbredelse, Dragon Dice,
High Temple og Mythral. [S3]

Vår kildekartlegging skiller `svart_ridder` ved `$8D7C4` fra de fire vanlige
ridderstrukturene. Svart ridder bruker `He1.ob` til `He3.ob`.
[Symboloversikten](../disasm/symbols.txt) gir utgangspunktet for kodearbeidet.
«Black Knight» skal derfor ikke brukes som et upresist navn på all rival-AI.

Fem visuelle månefaser er allerede observert i originalkjøring. Den tidligere
KI-kildeprøven fant fasetabellen `45,46,47,48,49,48,47,46` ved `$08F147`, med
`ki.cel/045..049` tegnet via `$082B8C`. Bevismappen er
`art/photoreal/review/ki-moon-source/` i den lokale produksjonscheckouten.
Visuelle faser beviser ikke riktig skade, monsterstyrke eller magi.
Senere månevisningsrettinger står i [prosjektminnet](../memory.md).

## Rapporterte feil i originalutgaver

| ID | Funn og status | Hva som gjenstår |
| --- | --- | --- |
| B01 | **Rapportert trollkrasj:** Matt Taylors veiledning beskriver to troll som vender mot hverandre og gjør slag over hodet samtidig. [S4] | Gjenskap med identifisert Amiga-utgave, lagring og eksakte inndata. Samtidig spising og stack overflow er ikke dokumentert årsak. |
| B02 | **Rapportert DOS-tekstfeil:** en halvmånestein kalles nymåne. Spilleren anbefaler å følge bildet. [S5] | Kontroller DOS-tekst, ikon og leveringslogikk. Ikke overfør DOS-feilen til vår Amiga-utgave uten belegg. |
| B03 | **Rapportert DOS-fasegrafikk:** samme guide beskriver halvmånebildet som større enn trekvartmånen. [S5] | Sammenlign alle DOS- og Amiga-faser med kildeidentitet. Grafikkavvik og beregningsfeil må skilles. |
| B04 | **Uavklart Black Knight-sporing:** den innlimte oversikten påsto fastkjøring og løkker. | Ingen repeterbar lokal tilstand eller kodeårsak ble funnet i undersøkelsen. Først dokumenteres målvalg, posisjoner og turer. |
| B05 | **Uavklart måneberegning:** den innlimte oversikten påsto manglende matematiske variabler. | Finn lesere og skrivere av fasetilstanden og sammenlign faktisk oppførsel med manualen. Nye multiplikatorer er ikke en dokumentert restaurering. |
| B06 | **Uavklart antall steintyper:** manualens innledning omtaler fire Moonstones, mens speedrun-guiden oppgir tre typer. Lokal KI-kartlegging identifiserer KI000..002 som steinbilder. [S3], [S5] | Kontroller gjenstandstabell og seiersbetingelser i hver utgave. Forskjellen beviser ikke en kuttet fjerde stein. |

Sykdom må ikke automatisk tolkes som en krasjfeil. Manualen omtaler Ratmen-smitte.
Undines portforfatter beskriver at sykdom ble fjernet med hensikt, fordi den
opplevdes uklar. Det er en regelendring i det prosjektet, ikke dokumentasjon på
kuttet originalinnhold. Den konkrete periodiske virkningen må fortsatt måles
i vår kildeutgave. [S3], [S8]

## Hva WHDLoad faktisk dokumenterer

[Wepls endringslogg][S6] oppgir rettinger av synkronisering, minnetilgang,
tastatur, lyd og avbrudd, samt introhopp. Den oppgir også endret gullgrense
fra 150 til 999. I v1.5 endres tilfeldig initialisering for mer variert
gjenstandsfordeling; v1.6 retter støtte for tre spillutgaver etter en regresjon.
Dette er dels feilrettinger, dels bevisste endringer.

Endringsloggen navngir verken save/restore, Black Knight-stifinning eller
B01s nøyaktige trollscenario. «Diverse feil rettet» er ikke tilstrekkelig til
å markere disse tre som løst. Emulatorens tilstandslagring er en egen funksjon.

Vår innebygde `Moonstone.Slave` er **v1.4 fra 22.08.2002**, ifølge den lokale
fil- og slaveanalysen i [memory.md](../memory.md). Nettsidens **v1.6 fra
11.05.2011** er en annen versjon. Senere WHDLoad-rettinger skal ikke regnes som
inkludert uten sammenligning av slave og patchliste. Vår kilde støtter allerede
999-grensen; se `$8C0C6`, `$8C2E8` og `$8C2F0` i
[disasm/symbols.txt](../disasm/symbols.txt).

## Fanprosjekter og tekniske referanser

Status kontrollert på nytt mot GitHub README og API 12. oktober 2026.
Ingen ekstern kode er kopiert, bygget eller kjørt i denne innsamlingen.

| Prosjekt | Faktisk grunnlag | Bruk og begrensning |
| --- | --- | --- |
| [OpenMoonstone][S7] | Rust/Python, DOS-data, AGPL-3.0. HEAD `60b253ec76c6b85924de6c9d08d42e9e42913760`, 15.05.2023. README viser øvingskamp og kampanjekart under utvikling. | Mulig format-/kampreferanse. Ikke dokumentert som en komplett eller aktiv C++-port i 2026. README omtaler SDL2, mens Cargo-koden bruker ggez; kontroller kode fremfor å anta én stack. |
| [moonstone-ace][S9] | C++-rekonstruksjon fra Amiga 68k på ACE. Amiga 1200/WinUAE, 68020, AGA, Kickstart 3.x og originale disker. HEAD `2bc43a2e673819cc9c71a50a800e5676edcacfb3`, 10.10.2026. | Rutine-/modulkart er relevant. Ikke dokumentert som native PC-port. GitHub oppgir ingen identifisert lisens; tidligere filgjennomgang fant ingen lisensfil. Paritet og gjenbruksrett må avklares før kodeimport. |
| [Undines Moonstone 2026][S8] | Windows x64, Amiga-basert, hovedsakelig C, runtime GPL-3.0. HEAD `74f7fde041501d2619b273233135629d857ffdd7`, 08.10.2026. Innebygd emuleringskjerne, lagring og lokal flerspiller. | Referanse for konkrete rettinger og versjonsforskjeller. Forfatterens påstand om omfattende krasjrettinger er ikke selvstendig testet her. Sykdom er bevisst fjernet; porten er derfor ikke uendret fasit. |

Den tidligere [tekniske vurderingen](tekniske-referanser-2026-10-12.md) beholdes
som bakgrunn. Datoer og SHA-er over er øyeblikksbilder, ikke løfter om videre status.

## Korrigering av den opprinnelige innlimte oversikten

| Påstand | Konklusjon |
| --- | --- |
| Utforskbare Waterdeep/Highwood, NPC-sideoppdrag og flere krospill ble kuttet av RAM-hensyn. | **Uavklart.** Ingen tilsvarende utviklerbekreftelse funnet. Eksisterende bytjenester skal ikke fremstilles som fraværende. |
| Lagring og passord ble kuttet fordi grafikken tok all RAM. | **Uavklart årsak.** Manglende lagring er bekreftet; RAM-forklaringen er ikke det. |
| Ridderkopier ble laget for å oppfylle et markedsføringsløfte om tusenvis av bilder. | **Uavklart forklaring.** C01/C02 dokumenterer ønsket variasjon og hindringer; markedsføringsmotivet mangler belegg. |
| WHDLoad løser AI-sporing, trollkrasjet og lagring. | **Ikke dokumentert i undersøkt endringslogg.** Kontroller versjon og konkret patch før en slik påstand. |
| OpenMoonstone er en komplett, moderne C++-motor med bevist mindre inputlag og riktige spriteprioriteter. | **Feil språk-/fullføringsbeskrivelse; ytelsespåstandene er uavklarte.** |
| moonstone-ace er en moderne native PC-port. | **Feil målplattformbeskrivelse.** Se Amiga-kravene over. |
| DOS-feilen skyldes en forhastet lokalisering, og trollkrasjet skyldes stack overflow. | **Uavklarte årsaksforklaringer.** B01/B02 er rapporterte symptomer. |
| Alle månemultiplikatorer mangler og må gjeninnføres. | **Uavklart.** Fasevisning finnes; spillvirkning må undersøkes separat. |

## Feil og mangler i vår port, holdt atskilt fra historiske kutt

[Gjennomgangen fra 11. oktober](hva-mangler.md) er historikk og har delvis
utdaterte konklusjoner. Den skal leses sammen med dagens kode, `todo.md` og
[HD-statusen](hd-status-2026-10-12.md), ikke som en ny liste over aktive feil.

| Funn fra våre samtaler og revisjoner | Status i grunnlaget f77a2d25 | Videre kontroll |
| --- | --- | --- |
| Lagringer ble ugyldige ved oppdatering; ingen eksport, import eller autosave. | `MOONSAV2` med versjonerte deler, overgang fra gammel v13 og lagring på PC/nett er implementert. [state.c](../port/src/state.c), README og todo. | Bevar migrasjonsprøvene. Originalen fikk ikke dermed en historisk save-funksjon. |
| Ulike nettversjoner hang uten forklaring; skjulte Turns-faner kunne blokkere turen. | Formatutveksling og håndtering av skjult gjest er registrert ferdig i todo. | Ekte nett, NAT og forsinkelse er fortsatt utestet der. |
| Klikk traff skjult peker; riddervalg og introhopp var vanskelige. | Pekerkommando, portrettvalg og introhopp er rettet i PR #40/#42. | Bevar spillerautoritet, navneflyt og eldre PEKR-lagringer. |
| HD manglet ved tidlig oppstart, falt ut ved lasting eller ga blå månefirkant. | Standardoppstart, tidlig tegneliste, prioritert lasting, retry og kildeavgrenset månefelt er rettet i PR #40/#41/#42. | Ukjent kilde/palett skal fortsatt gi Original. |
| Lange tekster kunne skrive forbi 45-plassers gjenopprettingslister. | `widen_restore_lists` flytter listene og utvider dem ved tekst-/menylapp. [patch.c](../port/src/patch.c). | Dette er ikke dokumentert retting av B01. |
| Tapt WebGL-kontekst, sluttscene tolket som intro og ingen PC-utgivelse. | Reserve/lagring, sluttscenegjenkjenning og nedlastbare utgivelser er registrert ferdig. | Full naturlig kampanje og fysisk Windows-/mobiltest er fortsatt ikke dokumentert. |
| HD-ikonspor forsvant ved nye tall eller pekeroverlapping; ulikt grønne/blå hjelmer. | Retensjon rettet i PR #43. Bilder som allerede finnes skal ikke telles som manglende mastere. | Flere naturlige inventar-/utbyttesekvenser. |
| Mosaikkpreget Ratmen-lauv og feil grønn variant i andre terrengpaletter. | Foto og Wa2-port rettet i PR #43. Andre paletter beholder konservativ Original063. | Ikke kall alle terrengvarianter ferdige. |
| 23 kartporter i eksporten, men 24 lairs i originalen. | `map-icons/026` fullfører portkontraktene i PR #43. Loot og seierlogikk bevares. | Test faktisk tur/loot; HD-skjuling av vunnet port er en bestilt visningsendring. |
| Separate kan godta duell mens spilleren er i by eller kamp; brutt forbindelse og romgjenoppretting. | Åpne funn i todo og den eldre gjennomgangen. Ikke rettet av denne dokumentleveransen. | Repeterbar toklienttest før kodeendring. |
| Turns-gjesten mister lagringskopien når verten forsvinner; ridderfordeling etter ankomstrekkefølge. | Åpne punkter i todo. | Test vertstap, lagring og ny oppkobling. |
| PC mangler nettspill, HD-rendering, enkelte kontroller og Options-integrasjon. | Fortsatt planlagte portoppgaver, ikke historisk kuttet 1991-innhold. | Egen leveranse med PC-kjøring. |
| Uferdige figurer og lokale 009-kandidater. | Main-registeret har 749 manglende mastere / 812 ruter / 59 mastermasker etter PR #44. | Bruk kilde-/manifestregisteret; galleri og lokale kandidater teller ikke som publisert. |

Tabellen bygger på allerede lagrede kode-/testrapporter og lesende kontroll.
Spilltestene er ikke kjørt på nytt i dette dokumentoppdraget. Full naturlig
gjennomspilling, offentlig nettspill mellom to fysiske enheter og fysisk mobiltest
er ikke etablert av denne innsamlingen.

## Plan for undersøkelser og eventuelt nytt innhold

Dette er foreslått rekkefølge, ikke en implementert eller godkjent utvidelse.

1. **Gjenskap B01 først:** lagre før trollkampen, registrer utgave, CRC/SHA,
   inndata, CPU/stack og siste bilde. Sammenlign identisk scenario med/uten
   C-hooks. Skill symptomet fra årsaken og fra WHDLoad-versjonsforskjeller.
2. **Mål månelogikken:** følg hele faseomløpet, koble KI-bildet til dagtelleren,
   og mål Ratmen og steineffekt med identiske øvrige vilkår. Skill manualtekst,
   faktisk originaloppførsel og ønsket endring. Mål også sykdom separat.
3. **Kartlegg svart ridder:** spor struktur, målvalg, bevegelse, hindringer og
   kampverdier. En ny A*-jeger endrer oppførsel og skal ikke innføres som en
   feilretting uten et avgrenset, påvist avvik.
4. **Undersøk versjoner:** sammenlign vår mog/program/slave med en identifisert
   retail-utgave og aktuelle patcher. DOS-feil får egne prøver og egne data.
5. **Fortsett originaltro HD og C-dekompilering:** bevar C99/SDL2, Amiga-kjerne,
   WebAssembly/Three.js, originalkonstanter og determinisme. De to registrerte
   C-erstatningene er joystickrutiner, ikke omskrevet kart-/kampmotor.
   Bruk `tools/check_hooks.py` ved nye erstatninger.
6. **Beskriv utvidet modus separat:** synlig utstyrsprogresjon, ulike
   ridderkropper/kampstiler, større bosskamper og nye fiender har historisk
   inspirasjon i C01-C04. Egne byoppdrag, A*, generelle månemultiplikatorer,
   nye idle-animasjoner og omskrevet kollisjon er moderne forslag. De trenger
   egne spillregler, balanse, assets, lagringsversjon og nettprøver.

ESRGAN var foreslått i den innlimte teksten, men er ikke valgt produksjonsmetode.
Prosjektets eksisterende bestilling krever separat fotorealistisk nytegning med
originalens form, ankre, palettmasker og animasjonskontinuitet. En filtertest må
ikke erstatte den bestillingen eller telle som ferdige figurer.

## Kilder og sporbarhet

Historikken ble hentet fra «Kartlegg kuttet Moonstone-innhold»
(`01a12eae-228e-7f03-8a0d-24eb83a4528e`), dens lagrede kildevurderinger og
«Moonstone HD grafikk konvertering» (`01a10201-d4e6-7b43-9cf5-c75c123ccd87`).
Den innlimte engelske oversikten er behandlet som påstander som må kontrolleres.
Private samtalelogger og vedlegg er ikke kopiert inn i repoet.
[Gjenopptaksnotatet](samtale-gjenopptak-2026-10-12.md) beskriver siste arbeidsstatus.

- **S1:** [Utviklerkorrespondanse hos Moonstone Tavern][S1], særlig Todd om ønsker
  og testing, og Robs svar 16.02.2005 om riddervariasjon og oppfølgeren.
- **S2:** [Rob Anderson-intervju, Spillhistorie 11.12.2024][S2], spørsmålene om
  sluttkamper, uutviklede fiender, lagring og omslagskunst.
- **S3:** [Originalmanual i transkripsjon][S3], delene om månen, byer,
  Ratmen, Black Knights og Moonstones. Transkripsjonen inneholder skrivefeil.
- **S4:** [Matt Taylors spillerveiledning][S4], Trolls. Rapport, ikke lokal reproduksjon.
- **S5:** [Speedrun-veiledning][S5], Moonstone, moon-phases & end.
- **S6:** [Wepls WHDLoad-dokumentasjon og versjonslogg][S6].
- **S7:** [OpenMoonstone][S7], README, språk, lisens og commit ved oppgitt SHA.
- **S8:** [Undines Moonstone 2026][S8], README, spillrevisjoner, sykdom og lisens.
- **S9:** [moonstone-ace][S9], README, BUILD.md, ROADMAP.md og modulreferanser.

[S1]: https://moonstonetavern.co.uk/meet-the-makers/
[S2]: https://spillhistorie.no/2024/12/11/interview-with-the-creator-of-moonstone/
[S3]: https://www.freegameempire.com/games/Moonstone-A-Hard-Days-Knight/manual
[S4]: https://moonstonetavern.co.uk/killing-with-style/
[S5]: https://www.speedrun.com/moonstone_a_hard_days_knight/guides/s65c4
[S6]: https://www.whdload.de/games/Moonstone.html
[S7]: https://github.com/joetsoi/OpenMoonstone
[S8]: https://github.com/Undine1/Moonstone-A-Hard-Days-Knight-2026
[S9]: https://github.com/Jarskih/moonstone-ace-public
