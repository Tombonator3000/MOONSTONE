# Månen i originalkoden

Undersøkt 12. oktober 2026 i Amiga CD32-utgaven vi kjører (punkt 2 i planen i
[kuttet-innhold-og-feil.md](../kuttet-innhold-og-feil.md)). Hver påstand er merket:

- **målt**: kjørt med `tools/maane.py`, `tools/maane_kamp.py` eller headless med `--vakt`
- **kode**: lest i `disasm/mog.s`, ikke kjørt
- **manual**: står i manualen [S3]

Utgaven (fra `tools/maane.py`):

| Fil | SHA-256 |
|---|---|
| Moonstonecd32-AMIGA.zip | 35b7d4c67b9fae6019e257780050d0f421d6ec4c250cdde48a8f296086d67a02 |
| Moonstone.Slave (v1.4) | cfd615e6ec063a7f111604eaf8ab804cb6b35a050513bb5622fc7d5989240fb8 |
| data/mog | d8cc4ec9f848ee30032f1e0c0db4e37c2484114910d314760956da9fee96da81 |
| data/program | b0a84503c0664515ef8b31072098acd62dbf50de3a36fe4ffe9492b094f593a6 |

## Hvor månen ligger

| Adresse | Hva | Belegg |
|---|---|---|
| `sub_08064a` | Kjøres hver ny dag. Teller dagen og skifter fase. | kode, målt |
| `$08CEA8` (`$08CE94+$14`) | Dagtelleren, 1-4. På 4 nullstilles den og fasen går ett steg. | kode, målt |
| `$08F152` | Faseindeksen 0-7 (`andi #7`). Leses bare av `sub_08064a`. | kode |
| `$08F147` | Tabellen fra fase til bilde: 45 46 47 48 49 48 47 46. | kode |
| `$08CEA6` (`$08CE94+$12`) | Månebildet (ki.cel 45-49). Det er dette resten av spillet leser. | kode, målt |
| `$08F150` | Antall faseskifter i spillet. | kode |

## Sammenligning

| Punkt | Manualen | Originalen (denne utgaven) | Belegg |
|---|---|---|---|
| Hvor ofte månen skifter | hvert tredje døgn | hvert fjerde døgn | målt over 6 skifter: dag 4, 8, 12, 16 ... |
| Fasene | ny, voksende, full, avtagende | 8 trinn med fem bilder: 45 46 47 48 49 48 47 46 | kode, målt |
| Moonstone | dobbel hit points med riktig stein | **dobbel skade** fra ridderen når han bærer steinen som passer til bildet (`sub_085ae0`, `$085b2a`-`$085b74`). Ingen endring av hit points funnet. | kode, målt: slaget mot en rotte går fra 3 til 6 bare når steinen passer til bildet |
| Hvilke steiner | fire Moonstones | fire stein-biter (`$16` i inventaret, bit 0-3) mot tre bilder: bit 1 = 45, bit 0 og bit 3 = 47, bit 2 = 49. Bilde 46 og 48 gir ingen effekt. | kode, målt for alle fire biter mot 45, 47 og 49 |
| Stonehenge | lever steinen i riktig fase | druidene (`$08170a`) tar bare imot en stein som passer til månebildet nå | kode |
| Ratmen sterkere med månen | ja | **nei.** Månebildet leses bare tre steder: skadeberegningen over, Stonehenge og tegningen (`$082b6e`). Ingen monsterkode leser fasen eller bildet. | kode, målt: rottebittet tar 3 ved nymåne, halvmåne og fullmåne |
| Svart ridder | jakter deltakerne | blir aktiv først når `$08F150` >= 2, altså etter to faseskifter (dag 8) (`sub_0ab03e`) | kode |

## Feil funnet i originalen

**M1. Nytt spill nullstiller ikke faseindeksen** (målt). Nytt spill (`$084c72`) setter
månebildet til 45 (nymåne), dagtelleren og `$08F150` til 0, men ikke `$08F152`. Første
faseskifte etter et game over hopper derfor til fasen forrige spill var kommet til.
Målt: etter fullmåne (49) og nytt spill gikk bildet fra 45 rett til 48. De fire første
dagene viser altså nymåne mens steinene og druidene følger en annen fase enn den neste
som kommer, og skiftet hopper over trinn. Gjelder bare et nytt spill uten at programmet
startes på nytt (game over eller nytt spill fra menyen).

## Sykdom

| Punkt | Originalen | Belegg |
|---|---|---|
| Hvem smitter | Ratmen. Slaghandleren deres (`dat_0855ce`, valgt fra tabellen `$08D8DE` med `+$4D = $24`) har to angrep: type 4 er et bitt som trekker skade og setter `$82 = 1` på ridderen (`$0855ec`), type 8 trekker bare skade | kode, målt: tre av fire forsøk med ulik ventetid ga smitte |
| Hva den gjør | **ved hvert faseskifte**, ikke hver dag, trekkes 1 fra livsnivået `$49` (0-5) for en syk ridder. Trekket ligger i `sub_080704`, som bare kalles når månen skifter (`$08068c`). | kode, målt: livsnivået falt på dag 4, 8 og 12 |
| Hvor fort | fra fullt (5) til 0 tar fem faseskifter, altså 20 døgn uten andre tap. Et tapt slag i kamp (livet `$50` til 0, `$080446`) koster også ett livsnivå, så i praksis går det fortere. | målt |
| Hva som kurerer | helbrederen for minst 10 gull (`$089db2`), druidene ved Stonehenge (`$0817b2`), og drikken i inventaret (`sub_08bd44`) | kode |

Manualen sier at sykdommen tærer på ridderen over tid. At den følger månen og ikke
dagene, står ikke der. Med månereglene på skifter fasen hvert tredje døgn, og da
går sykdommen tilsvarende fortere.

## Valget: månereglene fra manualen

Av som standard. På nettsiden heter det «Moon rules from the manual» under
innstillingene, på PC `--maaneregler`. Valget lagres i spillet (delen `MAAN` i
lagringen), så en lagring beholder reglene den ble startet med, og en gjest i
nettspill får vertens regler. Lappene ligger i `port/src/game.c`:

| Endring | Hvordan | Målt |
|---|---|---|
| Fasen skifter hvert tredje døgn | `$080664`: når dagtelleren er 3, settes den til 4 før sammenligningen | `tools/maane.py --maaneregler`: skifte på dag 3, 6, 9 ... |
| Ratmen sterkere med månen | `$0855de`, `$085608` og `$085b76`: skaden fra en angriper med `+$4D = $24` ganges med (4 + trinn) / 4, der trinn er 0 ved nymåne og 4 ved fullmåne. Altså x1, x1,25, x1,5, x1,75 og x2. | `tools/maane_kamp.py`: bittet tar 3, 4 og 6 ved nymåne, halvmåne og fullmåne |
| M1 rettet | `$084c7e`: nytt spill nullstiller også `$08F152` | etter game over går bildet 45, 46, 47 som i et nytt spill |

## Neste målinger

1. Hva som skjer når en syk ridder står på livsnivå 0 og månen skifter igjen
   (`subi.b` fra 0 gir 255, men spillet kan fange det før).
2. Om datamaskinens riddere blir smittet og helbredet på samme måte.
