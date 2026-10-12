# Kuttet og skjult innhold i filene

Funnet 12. oktober 2026 ved å lese slaven, `data/mog` og arkivet
(Moonstonecd32-AMIGA.zip, SHA-256 35b7d4c6...). Supplerer funnregisteret i
[kuttet-innhold-og-feil.md](../kuttet-innhold-og-feil.md), som handler om innhold
fra utviklingen som ikke kom med. Dette er det som faktisk ligger i filene vi kjører.

Merking: **kode** = lest, ikke kjørt. **målt** = kjørt i emulatoren.

## Tatt inn

| Hva | Hvor | Hva vi gjorde |
|---|---|---|
| Spørsmålstegnet i bold.f vises ikke | tegntabellen `$96210`, plass 31 (`$9622F`) peker på den tomme glyfen 69. Glyf 63 i fila er et spørsmålstegn og brukes ellers ikke. | Rettet når mog lastes (`port/src/patch.c`). Målt: tabellen har 63 etter oppstart. Gjelder bl.a. «What are the creatures of the North?». |
| Månereglene fra manualen | se [maane.md](maane.md) | Valg, av som standard. |

## Funnet, ikke tatt inn

| Hva | Hvor | Status |
|---|---|---|
| Juksekode W E P L i slaven: ridder 1 får 5 i alle egenskaper og 500 gull | Moonstone.Slave | kode. Virker allerede i porten fordi slaven kjører som den er. |
| Skjult tast Q: game over | `$0AAD8C` på kartet | kode. Virker allerede. |
| Skjult tast V: en feilsøkingskonsoll fra v1.4 | `$0AAD98` | kode. Virker allerede. Ikke nevnt i hjelpen, siden den kan ødelegge et spill. |
| Monstertest-meny som aldri kalles | tekst `$82D82`, rutine `$82CE8`, tabell `$95F74` | kode. Kan bli et valg på PC (`--monstertest`) når vi har sett at den virker. |
| Manual-, joystick- og månefasebilder (IFF) som spillet ikke bruker | arkivet | Kan vises i hjelpen på nettsiden. |
| Lyden Wn.a (vind) spilles aldri | data | Ikke vurdert hvor den hørte hjemme. |
| Rester av kopibeskyttelsen (spørsmål om manualen) | mog | Brukes ikke. |
| Meldingene «has attacked » og «The dragon is attacking», og «Take Padded armour» | mog | Ingen kode leser dem. |
| Feilsøkingstekstene DEMON HIT, DIDIT og STUU | mog | Ingen kode leser dem. |
| Filnavnet bg8.piv uten noen referanse | mog | Alle de 150 datafilene i arkivet er ellers i bruk. |

## Ikke funnet i filene

Kuttede monstre, flere steder eller en fjerde Moonstone-type. Funnregisterets C01 til
C07 er rapporter om utviklingen, ikke data vi kan ta inn.
