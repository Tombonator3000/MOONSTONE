# Kildebundne bakgrunnsrevisjoner og logo

Fem faste bakgrunner, to komplette rullestriper og logoen er nytegnet med den innebygde bildegeneratoren. Originalbildet bestemmer motiv, utsnitt og plassering. Råbilder og eksakte prompter ligger i `raw/` og `prompts/`; `generation-records.json` knytter hvert separat kall til riktig kilde.

| Rute | Kilde og kontrollert motiv |
| --- | --- |
| bg/94c7f163 | hen1.p/bg5.piv: åtte druider, fire på hver side, trappealter og steinporter |
| bg/c2501c17 | bg3.PIV: ti trilitter i ring og det lave midtalteret |
| bg/a45a2508 | bg2a.PIV: Stonehenge til venstre, samme ridder/rustning, røde klær og sverdretning til høyre |
| bg/46963198 | Mindscape: fotografisk gullmateriale i nøyaktige kildekonturer og original tekstform |
| bg/d0f67acb | bg8.PIV: voksen/barn, trær, ås og 401 kildebundne stjernepiksler |
| bg/6b258d27 | intro.stile + bg1a/bg1c/bg1b: full320x1200-skogskilde, 950 stjernepiksler |
| bg/0df34a83 | co.stile + bg7: full320x1200-sluttkilde,8966 stjernepiksler og flat vannvirvel nederst |
| bold.f/073 | Fotogull bundet til samtlige originale bokstaver, skygger, tre O-diamanthull og undertittel |

Faste bilder er1280x800, rullestriper1280x4800 og logo1220x216. Fri logo fra generatoren hadde feil bokstavhull og brukes bare som gullmateriale. Originalkonturer, hull og skygger kommer fra uendret bold.f. Ingen av de gamle avviste bakgrunnene er brukt som positiv referanse.

Bygg med `python3 tools/hd_completion_backgrounds_build.py`, deretter Node `tools/hd_completion_backgrounds_pack.cjs`. Logoen har egne `hd_completion_logo_build.py` og `hd_completion_logo_pack.cjs`. `tools/hd_completion_activate.py --activate` kontrollerer kilder, PNG-er, kontrakter og bundne ikonbevis før innkobling. Den tekniske rullestøtten dokumenteres i `../hd-program-support-2026-10-11/`.

Faktisk nybygd WASM/frontend består47 bakgrunnskontroller,35 logo/importkontroller og58 intro/sluttkontroller. Rapportene og original-/HD-bildene ligger i `verification/`. Alle fem faste HD-bilder og introens1800/2000 samt sluttens2900/3100/3300/4000 er visuelt kontrollert. Original-retur er eksakt og rendringen endrer ikke emulert spilltilstand. Sluttscenen bruker kontrollert originalt seiersflagg; dette er ikke full gjennomspilling. Den lokale leveransen har411 PNG-ruter,417 manifestfiler og81 bakgrunner. Figurruter er en separat pågående produksjon og er ikke ferdige fordi bakgrunnene er ferdige.
