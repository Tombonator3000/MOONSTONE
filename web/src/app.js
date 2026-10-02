/*
 * app.js - oppstarten, spillokka og menyen.
 *
 * Siden har ingen egen startside. Spillet starter med en gang, med introen.
 * Introen hoppes over med Esc, og mens den gaar ogsaa med fire, Enter,
 * mellomrom og et trykk paa skjermen (introTaster). Nettspill velges i
 * spillets tittelmeny under «Online Game» (port/src/meny.c), og en
 * invitasjonslenke aapner «Join Game» der med rommet valgt. Innstillinger,
 * lagring og egne filer ligger i sidemenyen (Home eller knappen oppe til hoyre).
 *
 * Maater aa spille paa:
 *   alene  kjernen kjorer her, joystick A paa port 2 og B paa port 1
 *   vert   som alene, men gjestene kobler seg til og faar hvert sitt joystick
 *          (tur for tur, som originalen: verten kjorer spillet for alle)
 *   gjest  kjernen kjorer de samme bildene som verten, med inndataene fra verten
 *   hver   hver for seg (docs/flerspiller.md): alle i rommet spiller sitt eget
 *          spill, som alene, og ridderne sendes mellom maskinene, saa de andre
 *          staar paa kartet ditt (port/src/hver.c)
 */
'use strict';

(() => {
    const $ = (id) => document.getElementById(id);
    const inn = Lager.innstillinger();
    const innst = Object.assign({ filter: 'skarp', format: 'pal', helt: false, volum: 1, knappevent: false, navn: '', offentlig: false, knapper: false,
        effekter: { skygge: false, dybde: false, glod: false, farger: false, vignett: false }, spill: 'hver' }, inn);
    const lagreInnst = () => Lager.lagreInnstillinger(innst);

    const INNEBYGD = 'innebygd';
    let spillfil = null;                    /* INNEBYGD, eller en annen spillfil (Uint8Array) */
    let modFiler = {};                      /* navn -> Uint8Array, legges over data/ */
    let modus = null;                       /* 'alene' | 'vert' | 'venter' | 'gjest' | 'hver' */
    let pause = false, menyApen = false, dialogApen = false, venterSynk = false, kjorer = false;
    let periode = 1 / 49.92;
    let akk = 0, sist = 0, plass = 1;
    let stoppAnnonse = null;
    let statusTimer = null;
    let invitasjon = null;                  /* romkoden i en invitasjonslenke, til tittelmenyen er naadd */
    const statistikk = { sjekket: 0, avvik: 0 };

    /* ---------------------------------------------------------------- meldinger */
    function status(tekst) {
        const s = $('status');
        s.textContent = tekst;
        s.classList.add('vis');
        clearTimeout(statusTimer);
        statusTimer = setTimeout(() => s.classList.remove('vis'), 3500);
    }

    /* teppet over spillet mens det lastes, kobler til eller ikke kan starte */
    function lasting(tekst) {
        $('lasting').hidden = !tekst;
        $('lasting-tekst').textContent = tekst || '';
    }

    function chatLinje(fra, tekst) {
        const linje = document.createElement('div');
        linje.textContent = fra ? fra + ': ' + tekst : tekst;
        const logg = $('chatlogg');
        logg.appendChild(linje.cloneNode(true));
        logg.scrollTop = logg.scrollHeight;
        const ut = $('chatlinjer');
        ut.appendChild(linje);
        while (ut.children.length > 5) ut.removeChild(ut.firstChild);
        setTimeout(() => { linje.style.opacity = '0'; setTimeout(() => linje.remove(), 1200); }, 8000);
    }

    /* ---------------------------------------------------------------- spillfilen */
    /* Spillfilen er bygget inn i kjernen (MED_SPILLET i bygget). Bare et bygg uten
     * den trenger en valgt fil, eller at filen ligger ved siden av siden. */
    async function finnSpillfil() {
        await Kjerne.last();
        if (Kjerne.harInnebygd()) { spillfil = INNEBYGD; return true; }
        $('spillfil-hjelp').textContent = 'Velg spillfilen (Moonstonecd32-AMIGA.zip eller «Moonstone CD32.iso»). Den lagres bare i denne nettleseren. Gjester i nettspill trenger den ikke.';
        const lagret = await Lager.hent('spillfil');
        if (lagret) { spillfil = new Uint8Array(lagret); return true; }
        for (const sti of ['spill/Moonstonecd32-AMIGA.zip', 'spill/moonstone.zip', 'Moonstonecd32-AMIGA.zip']) {
            try {
                const r = await fetch(sti);
                if (!r.ok) continue;
                const b = new Uint8Array(await r.arrayBuffer());
                if (b.length > 100000) { spillfil = b; return true; }
            } catch (e) { /* fra disk eller uten nett */ }
        }
        return false;
    }

    $('velg-fil').addEventListener('change', async (e) => {
        const f = e.target.files[0];
        if (!f) return;
        const b = new Uint8Array(await f.arrayBuffer());
        const innebygd = spillfil === INNEBYGD;
        spillfil = b;
        if (!innebygd) await Lager.sett('spillfil', b);
        startPaaNytt(innebygd ? 'Bruker den valgte spillfilen til siden lastes på nytt' : 'Spillfilen er lagret i nettleseren');
    });

    function visMod() {
        const navn = Object.keys(modFiler);
        $('mod-liste').textContent = navn.length ? 'Brukes: ' + navn.join(', ') : 'Ingen egne filer.';
    }

    $('velg-mod').addEventListener('change', async (e) => {
        for (const f of e.target.files) modFiler[f.name] = new Uint8Array(await f.arrayBuffer());
        await Lager.sett('mod', modFiler);
        visMod();
        status('Brukes når spillet startes på nytt');
    });
    $('fjern-mod').addEventListener('click', async () => { modFiler = {}; await Lager.slett('mod'); visMod(); status('Brukes ikke etter neste omstart'); });

    /* ---------------------------------------------------------------- oppstart */
    async function startKjerne(somGjest) {
        await Kjerne.last();
        Kjerne.menyPaa(true);               /* "Online Game" i spillets tittelmeny */
        if (somGjest) {
            Kjerne.startSomGjest();
        } else {
            if (!spillfil) throw new Error('Spillfilen mangler.');
            if (spillfil === INNEBYGD) Kjerne.aapneInnebygd();
            else Kjerne.aapne(spillfil.slice());
            for (const [n, d] of Object.entries(modFiler)) Kjerne.leggInnFil('data/' + n, d);
            Kjerne.start(innst.knappevent);
        }
        periode = 1 / Kjerne.hz();
        settVolum(innst.volum);
    }

    /* spillet starter rett paa introen; ingenting aa velge foer det */
    async function startSpillet() {
        lasting('Laster Moonstone ...');
        try {
            if (!spillfil && !(await finnSpillfil())) {
                visSpill();
                lasting('Spillfilen mangler. Velg den under «Spillfil og egne filer» i menyen.');
                visMeny(true);
                return;
            }
            await startKjerne(false);
            modus = 'alene';
            akk = 0;
            menyKmd(KMD.MITTNAVN, 0, rensNavn(innst.navn, 10));
            menyKmd(KMD.SPILL, innst.spill === 'sammen' ? 1 : 0);
            visSpill();
            lasting(null);
        } catch (e) {
            lasting('Kunne ikke starte spillet: ' + e.message);
        }
    }

    /* ut av et nettspill, eller ny spillfil: spillet startes paa nytt fra introen */
    function startPaaNytt(tekst) {
        if (stoppAnnonse) { stoppAnnonse(); stoppAnnonse = null; }
        stoppMenyRom();
        menyInvitert = null;
        menyKo.length = 0;
        if (D) { const d = D; D = null; clearTimeout(d.tidsfrist); try { if (d.conn) d.conn.close(); } catch (e) { /* lukket */ } }
        Nett.avslutt();
        Nett.rammer.length = 0;
        fjerne.clear();
        rekkefolge = [];
        sistSendt = '';
        modus = null;
        venterSynk = false;
        pause = false;
        visDialog('kode-dialog', false);
        visDialog('navn-dialog', false);
        visMeny(false);
        Lyd.clear();
        hopper = false;
        escOpp = 0;
        if (tekst) status(tekst);
        startSpillet();
    }

    function visSpill() {
        if (!Visning.klar) {
            Visning.init($('lerret'), Kjerne.bredde(), Kjerne.hoyde());
            Visning.klar = true;
        }
        Visning.settFilter(innst.filter);
        Visning.settFormat(innst.format);
        Visning.settHelt(innst.helt);
        Visning.settEffekter(innst.effekter);
        Visning.tilpass();
        Inndata.paa(!menyApen && !dialogApen);
        visKnapper();
        if (!kjorer) { kjorer = true; requestAnimationFrame(lokke); }
    }

    function navn() { return innst.navn || 'Player'; }

    /* styrekors og knapper paa skjermen: alltid ved beroering, ellers hvis valgt i menyen */
    const beroering = () => matchMedia('(pointer: coarse)').matches;
    function visKnapper() { $('touch').hidden = !(beroering() || innst.knapper); }

    /* ---------------------------------------------------------------- lyd og introen
     * Nettleseren slipper ikke lyden ut foer noen har trykket paa noe. Det forste
     * trykket starter lyden (og hopper ikke over introen), saa introen kan hores.
     * Esc teller ikke som et trykk for nettleseren, saa vi prover igjen ved neste. */
    let lydForsokt = false, forsteTrykk = 0, skjermTrykk = false;

    function lydPaa() {
        if (Lyd.running()) return;
        if (!lydForsokt) { lydForsokt = true; forsteTrykk = performance.now(); }
        Lyd.start().catch(() => {});
    }
    for (const t of ['pointerdown', 'keydown', 'touchend']) window.addEventListener(t, lydPaa, { capture: true });

    $('skjerm').addEventListener('pointerdown', () => { skjermTrykk = true; });

    /* Introen hoppes over med Esc. Mens den gaar, gjor fire, Enter, mellomrom og
     * et trykk paa skjermen det samme, saa det gaar ogsaa paa mobil og med
     * spillkontroller. Trykket som starter lyden, regnes ikke med, unntatt naar
     * siden er aapnet med en invitasjon: da vil man rett til rommet. */
    let introFire = false, escOpp = 0, hopper = false;
    function introTaster(j0, j1, taster) {
        if (escOpp && --escOpp === 0) taster.push([0x45, false]);
        if (!Kjerne.iIntro()) { introFire = false; skjermTrykk = false; hopper = false; return taster; }
        const fire = ((j0 | j1) & Inndata.FIRE) !== 0;
        const nyFire = fire && !introFire;
        introFire = fire;
        const tast = taster.some(([k, d]) => d && (k === 0x44 || k === 0x40));     /* Return, mellomrom */
        /* Introen ser bare paa den siste tasten (uten slipp-biten), saa Return eller
         * mellomrom etter Esc ville skjult den. De gjor ingenting i introen uansett. */
        taster = taster.filter(([k]) => k !== 0x44 && k !== 0x40);
        if (taster.some(([k, d]) => d && k === 0x45)) hopper = true;
        const trykk = skjermTrykk;
        skjermTrykk = false;
        const lov = invitasjon || !lydForsokt || performance.now() - forsteTrykk > 300;
        if ((nyFire || tast || trykk) && lov && !escOpp) {
            taster.push([0x45, true]);
            escOpp = 4;
            hopper = true;
        }
        return taster;
    }

    let sisteHint = null;
    function visHint() {
        let t = '', topp = false;
        if ((modus === 'alene' || modus === 'vert' || modus === 'hver') && !menyBrukt && !Kjerne.iIntro() && Kjerne.iMeny()) {
            /* spillets meny kan ikke klikkes i originalen; si at det gaar her */
            t = beroering() ? 'Trykk på et valg i menyen' : 'Klikk på et valg, eller bruk piltastene og Enter';
            topp = true;
        } else if (modus === 'alene' && Kjerne.iIntro()) {
            /* introen gjor ferdig det den holder paa med, det kan ta et par sekunder */
            if (hopper) t = 'Hopper over introen ...';
            else if (invitasjon) t = 'Du er invitert til rom ' + invitasjon + '. Trykk på skjermen, fire eller Esc for å hoppe over introen.';
            else if (lydForsokt) t = 'Esc, fire eller et trykk på skjermen hopper over introen';
            else t = 'Trykk på skjermen eller en tast for lyd';
        }
        if (!topp && $('status').classList.contains('vis')) t = '';     /* meldingen staar paa samme sted */
        if (t + topp === sisteHint) return;
        sisteHint = t + topp;
        $('hint').hidden = !t;
        $('hint').textContent = t;
        $('hint').classList.toggle('topp', topp);
    }

    /* ---------------------------------------------------------------- mus, trykk og Enter
     * Spillet selv bruker bare joystick: det leser musen i avbruddet, men ingenting
     * bruker det den finner. Her er musen koblet inn slik det er naturlig:
     *  - klikk eller trykk paa en rad i tittelmenyen (eller en nettspillside): pilen
     *    dit og fire (kommando VELG; port/src/meny.c gir spillet fire naar menyen er
     *    tegnet, likt paa alle maskiner i nettspill). Enter og mellomrom er fire der.
     *  - ellers er venstre knapp fire saa lenge den holdes, og drar du mens den
     *    holdes, blir det ogsaa en retning: fire og retning er angrepene i kamp.
     *    Hoyre knapp og dra er bare retning (gaa). Et klikk er et kort fire.
     * Introen har sin egen behandling (introTaster). */
    const FIRE = Inndata.FIRE;
    const MENYTASTER = [0x44, 0x43, 0x40];          /* Return, Enter paa talltastaturet, mellomrom */
    let museFire = false, museRetning = 0, museStart = null, klikkHold = 0, klikkTil = 0, menyBrukt = false;

    /* linjen i spillets bilde (0 = overst i spillets vindu) der det ble klikket */
    function spillY(e) {
        const r = $('lerret').getBoundingClientRect();
        const fy = (e.clientY - r.top) / r.height;
        if (!(fy >= 0 && fy <= 1)) return -1000;
        const c = Visning.utsnitt();
        return Math.floor(c[1] + fy * (c[3] - c[1]) - Kjerne.vindu()[1]);
    }

    /* rad (eller -1 = raden pilen staar paa) er valgt her eller av en gjest */
    function velgRad(rad) {
        if (modus === 'gjest') { Nett.sendVelg(rad); return; }
        menyKmd(KMD.VELG, rad);
        menyBrukt = true;
    }

    const spillAktivt = () => (modus === 'alene' || modus === 'vert' || modus === 'gjest' || modus === 'hver') && !menyApen && !dialogApen;

    function klikk(e) {
        if ((e.button !== 0 && e.button !== 2) || !spillAktivt() || Kjerne.iIntro()) return;
        const rad = Kjerne.menyRad(spillY(e));
        if (e.button === 0 && rad >= 0) { velgRad(rad); return; }
        if (rad !== -1) return;                      /* i menyen, men ikke paa en rad */
        museStart = { x: e.clientX, y: e.clientY };
        museRetning = 0;
        try { $('skjerm').setPointerCapture(e.pointerId); } catch (err) { /* ikke viktig */ }
        if (e.button === 0) {
            museFire = true;
            klikkHold = 3;                           /* et kort klikk varer minst tre bilder */
            klikkTil = performance.now() + 80;       /* det samme for en gjest */
        }
    }
    function slippMus() { museFire = false; museRetning = 0; museStart = null; }
    $('skjerm').addEventListener('pointerdown', klikk);
    $('skjerm').addEventListener('contextmenu', (e) => e.preventDefault());
    for (const t of ['pointerup', 'pointercancel', 'blur']) window.addEventListener(t, slippMus);

    /* retning fra der knappen ble trykket ned, i aatte retninger som styrekorset */
    function dragRetning(e) {
        const dx = e.clientX - museStart.x, dy = e.clientY - museStart.y;
        if (Math.hypot(dx, dy) < 14) return 0;
        const v = Math.atan2(dy, dx), s = Math.PI / 8;
        let b = 0;
        if (v > -7 * s && v < -s) b |= Inndata.OPP;
        if (v > s && v < 7 * s) b |= Inndata.NED;
        if (v > 5 * s || v < -5 * s) b |= Inndata.VENSTRE;
        if (v > -3 * s && v < 3 * s) b |= Inndata.HOYRE;
        return b;
    }

    /* dra for retning, og haanden over rader som kan velges, saa man ser at de kan klikkes */
    $('skjerm').addEventListener('pointermove', (e) => {
        if (museStart) { museRetning = dragRetning(e); return; }
        const over = spillAktivt() && !Kjerne.iIntro() && Kjerne.menyRad(spillY(e)) >= 0;
        $('skjerm').style.cursor = over ? 'pointer' : '';
    });

    /* fire og retning fra musen; regnes per bilde, saa et kort klikk ogsaa kommer med */
    function museBits() {
        let b = museRetning;
        if (klikkHold > 0) { klikkHold--; b |= FIRE; }
        if (museFire) b |= FIRE;
        return b;
    }

    /* i menyen er Enter og mellomrom fire (paa raden pilen staar paa) og gaar ikke til spillet */
    function menyTaster(taster) {
        if (!Kjerne.iMeny()) return taster;
        if (taster.some(([k, d]) => d && MENYTASTER.includes(k))) velgRad(-1);
        return taster.filter(([k]) => !MENYTASTER.includes(k));
    }

    /* ---------------------------------------------------------------- nettspill i tittelmenyen
     * Spillets tittelmeny har «Online Game» (port/src/meny.c). Menyen sender
     * hendelser hit, og vi svarer med kommandoer. Kommandoene brukes ved starten
     * av neste bilde, og verten sender dem med bildet til gjestene, saa alle
     * maskinene viser det samme. */
    const MENY = { VERT: 1, JOIN_SIDE: 2, JOIN_ROM: 3, KODE: 4, KOPIER: 5, OFFENTLIG: 6, FORLAT_JOIN: 7, TILBAKE: 8, NAVN: 9, SPILL: 10 };
    const KMD = { VERT: 1, SPILLERE: 2, OFFENTLIG: 3, ROM: 4, MELDING: 5, SLUTT: 6, NAVN: 7, MITTNAVN: 8, SIDE: 9, VELG: 10, SPILL: 11 };
    const SIDE_JOIN = 3;
    const menyKo = [];
    let menyRom = [], sisteRomTekst = null, stoppMenyListe = null, sistAntall = 0, sisteNavn = null;
    let menyInvitert = null;                /* rommet i invitasjonen, foerst i Join Game */

    /* spillets font har bare engelske bokstaver, tall og noen tegn */
    function rensNavn(t, maks) {
        return String(t || '')
            .replace(/[æÆ]/g, (c) => (c === 'æ' ? 'ae' : 'Ae')).replace(/[øØ]/g, (c) => (c === 'ø' ? 'o' : 'O'))
            .normalize('NFD').replace(/[\u0300-\u036f]/g, '')
            .replace(/[^A-Za-z0-9 .,!']/g, '').replace(/\s+/g, ' ').trim().slice(0, maks);
    }

    /* navnene i rommet til spillets meny: "1 Tom", i spillerrekkefolge */
    function sendNavn(liste) {
        const l = liste.slice().sort((a, b) => (a.spiller < 0) - (b.spiller < 0) || a.spiller - b.spiller);
        const tekst = l.map((x) => (x.spiller >= 0 ? (x.spiller + 1) + ' ' : '') + (rensNavn(x.navn, 10) || 'Player')).join('\n');
        if (tekst === sisteNavn) return;
        sisteNavn = tekst;
        menyKmd(KMD.NAVN, 0, tekst);
    }

    function menyKmd(k, arg, tekst) { menyKo.push([k, arg | 0, tekst || '']); }

    function vertHendelser() {
        sistAntall = 0;
        sisteNavn = null;
        return {
            lobby: (liste, kode, portModus) => { visSpillere(liste, kode, portModus); sendNavn(liste); if (modus === 'hver') oppdaterFjerne(liste); },
            ridder: (id, d) => mottaRidder(id, d),
            duell: (conn) => duellInn(conn),
            chat: chatLinje,
            status,
            velg: (rad) => { if (Kjerne.iMeny()) velgRad(rad); },   /* en gjest klikket i menyen */
            trengerTilstand: (id) => {
                const s = Kjerne.lagreTilstand();
                if (s) Nett.sendTilstand(id, s, Kjerne.bildeNr());
            },
            antall: (n) => {
                if (n === sistAntall) return;
                sistAntall = n;
                menyKmd(KMD.SPILLERE, n);
                if (stoppAnnonse) stoppAnnonse.oppdater();      /* riktig antall i den offentlige listen */
            },
        };
    }

    const erVert = () => modus === 'vert' || (modus === 'hver' && Nett.rolle() === 'vert');

    function settOffentlig(on) {
        innst.offentlig = on;
        lagreInnst();
        if (!erVert()) return;
        if (on && !stoppAnnonse) {
            stoppAnnonse = Romliste.annonser(() => ({
                kode: Nett.kode(), vert: innst.navn || 'Vert', spillere: Nett.spillere().length, maks: 4, spill: Nett.romSpill(),
            }));
        }
        if (!on && stoppAnnonse) { stoppAnnonse(); stoppAnnonse = null; }
        menyKmd(KMD.OFFENTLIG, on ? 1 : 0);
    }

    async function vertFraMeny(spill) {
        if (erVert()) { menyKmd(KMD.VERT, 0, Nett.kode()); return; }
        if (modus === 'hver') { menyKmd(KMD.MELDING, 0, 'Already In Room\n' + Nett.kode()); return; }
        if (modus !== 'alene') return;
        try {
            status('Lager rom ...');
            const kode = await Nett.lagRom(navn(), vertHendelser(), spill);
            if (modus !== 'alene') { Nett.avslutt(); return; }
            modus = spill === 'hver' ? 'hver' : 'vert';
            menyKmd(KMD.VERT, 0, kode);
            settOffentlig(innst.offentlig);
            oppdaterMeny();
            status('Rommet ' + kode + ' er klart. Velg «Copy Link» og send lenken.'
                + (spill === 'hver' ? ' Alle spiller sitt eget spill og ser hverandre på kartet.' : ''));
        } catch (e) {
            Nett.avslutt();
            menyKmd(KMD.MELDING, 0, 'No Connection\nTry Again Later');
            status('Kunne ikke lage rom: ' + e.message);
        }
    }

    /* "navn<tab>1 of 4"; spillet kutter navnet saa linjen faar plass.
     * Invitasjonen er "Room ABC123" uten antall. */
    function romLinje(r) {
        if (r.invitert) return 'Room ' + r.kode;
        return (rensNavn(r.vert, 10) || 'Host') + '\t' + (r.spillere || 1) + ' of ' + (r.maks || 4);
    }

    function oppdaterRomliste(rom, feil) {
        const liste = menyInvitert ? [{ kode: menyInvitert, invitert: true }] : [];
        for (const r of rom || []) if ((r.spillere || 1) < (r.maks || 4) && r.kode !== menyInvitert) liste.push(r);
        menyRom = liste.slice(0, 3);
        let n = menyRom.length, tekst = menyRom.map(romLinje).join('\n');
        if (!n && feil) { n = -1; tekst = 'No Room List'; }
        if (n + tekst === sisteRomTekst) return;
        sisteRomTekst = n + tekst;
        menyKmd(KMD.ROM, n, tekst);
    }

    function lyttMenyRom() {
        stoppMenyRom();
        if (menyInvitert) oppdaterRomliste([], null);
        stoppMenyListe = Romliste.lytt(oppdaterRomliste);
    }

    function stoppMenyRom() {
        if (stoppMenyListe) { stoppMenyListe(); stoppMenyListe = null; }
        sisteRomTekst = null;
    }

    /* invitasjonslenke: naar tittelmenyen er kommet, aapnes Join Game med rommet valgt */
    function aapneInvitasjon() {
        menyInvitert = invitasjon;
        invitasjon = null;
        const u = new URL(location.href);
        u.searchParams.delete('rom');
        history.replaceState(null, '', u);
        menyKmd(KMD.SIDE, SIDE_JOIN);
        lyttMenyRom();
        status('Du er invitert til rom ' + menyInvitert + '. Trykk fire for å bli med.');
    }

    async function kopierLenke() {
        if (!erVert()) return;
        try { await navigator.clipboard.writeText(Nett.invitasjon()); status('Invitasjonslenken er kopiert'); }
        catch (e) { visMeny(true); status('Kopier lenken her i menyen'); }
    }

    /* ---------------------------------------------------------------- dialoger (navn og romkode) */
    function visDialog(id, on) {
        $(id).hidden = !on;
        dialogApen = !$('kode-dialog').hidden || !$('navn-dialog').hidden;
        Inndata.paa(!menyApen && !dialogApen && !!modus);
    }

    function kodeFraTekst(t) {
        const m = String(t).match(/[?&]rom=([A-Za-z0-9]{6})/) || String(t).match(/^\s*([A-Za-z0-9]{6})\s*$/);
        return m ? m[1].toUpperCase() : null;
    }

    let etterNavn = null, avbruttNavn = null;
    function spoerNavn(etter, avbrutt) {
        etterNavn = etter || null;
        avbruttNavn = avbrutt || null;
        $('navn-felt').value = innst.navn;
        visDialog('navn-dialog', true);
        $('navn-felt').focus();
        $('navn-felt').select();
    }

    function navnOk() {
        const n = $('navn-felt').value.trim().slice(0, 20);
        if (!n) { status('Skriv navnet ditt'); return; }
        innst.navn = n;
        lagreInnst();
        menyKmd(KMD.MITTNAVN, 0, rensNavn(n, 10));
        visDialog('navn-dialog', false);
        const f = etterNavn;
        etterNavn = avbruttNavn = null;
        if (f) f();
    }

    function navnAvbryt() {
        visDialog('navn-dialog', false);
        const f = avbruttNavn;
        etterNavn = avbruttNavn = null;
        if (f) f();
    }

    /* noe som trenger navnet: spoer forst hvis det mangler */
    function medNavn(f, avbrutt) { if (innst.navn) f(); else spoerNavn(f, avbrutt); }

    function menyHendelse(h, arg) {
        switch (h) {
        case MENY.VERT:
            medNavn(() => vertFraMeny(arg ? 'sammen' : 'hver'), () => menyKmd(KMD.MELDING, 0, 'No Room Created'));
            break;
        case MENY.SPILL:
            innst.spill = arg ? 'sammen' : 'hver';
            lagreInnst();
            status(arg ? 'Tur for tur: verten kjører spillet for alle, én ridder om gangen'
                : 'Hver for seg: alle spiller sitt eget spill og ser hverandre på kartet');
            break;
        case MENY.JOIN_SIDE: if (modus === 'alene') lyttMenyRom(); break;
        case MENY.FORLAT_JOIN: stoppMenyRom(); menyInvitert = null; break;
        case MENY.JOIN_ROM: {
            const r = menyRom[arg];
            if (r && modus === 'alene') medNavn(() => bliMed(r.kode));
            break;
        }
        case MENY.KODE: if (modus === 'alene') { $('kode-felt').value = ''; visDialog('kode-dialog', true); $('kode-felt').focus(); } break;
        case MENY.KOPIER: kopierLenke(); break;
        case MENY.OFFENTLIG: settOffentlig(!!arg); break;
        case MENY.NAVN: spoerNavn(null); break;
        }
    }

    /* etter hvert bilde: verten og den som spiller alene handler, gjestene ser bare */
    function menyHendelser() {
        for (let e; (e = Kjerne.menyHendelse()); ) {
            if (modus === 'alene' || modus === 'vert' || modus === 'hver') menyHendelse(e & 0xff, e >> 8);
        }
        if (invitasjon && modus === 'alene' && Kjerne.menyKlar()) aapneInvitasjon();
    }

    /* ---------------------------------------------------------------- bli med som gjest */
    async function bliMed(kode) {
        kode = String(kode || '').trim().toUpperCase();
        if (!/^[A-Z0-9]{6}$/.test(kode)) { status('Romkoden har seks tegn.'); return; }
        stoppMenyRom();
        menyInvitert = null;
        modus = 'venter';
        venterSynk = false;
        lasting('Kobler til rom ' + kode + ' ...');
        /* Spillet her staar mens vi kobler til. Rommet sier om det er hver for seg
         * (da fortsetter spillet her) eller tur for tur (da blir kjernen en gjest
         * og faar tilstanden fra verten, som kommer rett etter forste lobby). */
        let forste = true, gjestKjerne = false;
        try {
            await Nett.bliMed(kode, navn(), {
                lobby: (liste, k, portModus, spill) => {
                    if (forste) {
                        forste = false;
                        if (spill === 'hver') {
                            modus = 'hver';
                            lasting(null);
                            oppdaterMeny();
                            menyKmd(KMD.MELDING, 1, 'In Room ' + k + '\nSeparate Games');
                            status('Du er med i rom ' + k + '. Alle spiller sitt eget spill og ser hverandre på kartet.');
                        } else {
                            Kjerne.startSomGjest();
                            gjestKjerne = true;
                        }
                    }
                    visSpillere(liste, k, portModus);
                    if (modus === 'hver') oppdaterFjerne(liste);
                },
                ridder: (id, d) => mottaRidder(id, d),
                duell: (conn) => duellInn(conn),
                chat: chatLinje,
                status,
                ping: () => {},
                feil: (t) => status(t),
                frakoblet: (t) => { if (modus === 'hver') forlatHver(t); else startPaaNytt(t); },
                tilstand: (bytes) => {
                    if (!Kjerne.lastTilstand(bytes)) { status('Kunne ikke laste spillet fra verten.'); return; }
                    venterSynk = false;
                    akk = 0;
                    if (modus !== 'gjest') {
                        modus = 'gjest';
                        oppdaterMeny();
                        lasting(null);
                        visSpill();
                    }
                    status('Du er med i spillet.');
                },
            });
        } catch (e) {
            if (gjestKjerne) { startPaaNytt('Kunne ikke koble til: ' + e.message); return; }
            Nett.avslutt();
            modus = 'alene';                    /* spillet her er urort */
            lasting(null);
            status('Kunne ikke koble til: ' + e.message);
        }
    }

    /* ---------------------------------------------------------------- hver for seg
     * Ridderne til de andre i rommet faar plass 2-4 hos oss (de datamaskinen ellers
     * styrer), i rekkefolgen i rommet. Hver maskin sender sin ridder noen ganger i
     * sekundet mens den er paa kartet. Se docs/flerspiller.md og port/src/hver.c. */
    const HVER = { FJERN: 1, RIDDER: 2, BLOB: 3, MEG: 4, DUELL: 5, AI: 6 };
    const fjerne = new Map();               /* id -> { x, y, liv, figur, navn } eller { borte: true } */
    let rekkefolge = [];                    /* de andre i rommet, i rekkefolgen i rommet */
    let sistSendt = '', sistSendtTid = 0;

    function mottaRidder(id, d) {
        const foer = fjerne.get(id);
        const varPaa = !!(foer && !foer.borte);
        fjerne.set(id, d.borte ? { borte: true } : { x: d.x | 0, y: d.y | 0, liv: d.liv | 0, figur: d.figur & 3, navn: String(d.navn || ''),
            b: typeof d.b === 'string' && /^[0-9a-f]{312}$/.test(d.b) ? d.b : null });
        oppdaterFjerne();
        if (menyApen && varPaa === !!d.borte) visSpillere(null);     /* kom paa eller gikk av kartet */
    }

    function oppdaterFjerne(liste) {
        if (liste) rekkefolge = liste.map((s) => s.id).filter((id) => id !== Nett.minId());
        for (const id of [...fjerne.keys()]) if (!rekkefolge.includes(id)) fjerne.delete(id);
        /* under en duell kjorer kjernen et spill begge maskinene har: ingen endringer utenfra */
        if (D) { fjerneVenter = true; return; }
        fjerneVenter = false;
        let maske = 0, duell = 0;
        const kmd = [];
        /* har to valgt samme ridder, faar den andre en ledig farge, saa de ikke ser like ut */
        const brukt = new Set();
        const min = Kjerne.hverKart() ? Kjerne.hverRidder(0)[3] : -1;
        if (min >= 0 && min < 4) brukt.add(min);
        rekkefolge.slice(0, 3).forEach((id, i) => {
            const r = fjerne.get(id);
            if (!r || r.borte) return;
            const plass = i + 1;
            maske |= 1 << plass;
            if (r.vent) return;                 /* etter en duell: vent paa ridderen slik den er naa */
            duell |= 1 << plass;
            let figur = r.figur;
            if (brukt.has(figur)) figur = [0, 1, 2, 3].find((f) => !brukt.has(f));
            brukt.add(figur);
            const n = (r.navn || 'KNIGHT').toUpperCase().replace(/[^A-Z0-9 ]/g, '').trim().replace(/ +/g, '_').slice(0, 15) || 'KNIGHT';
            if (r.b) kmd.push([HVER.BLOB, plass, r.b]);
            kmd.push([HVER.RIDDER, 0, plass + ' ' + r.x + ' ' + r.y + ' ' + r.liv + ' ' + figur + ' ' + n]);
        });
        Kjerne.hverKmd(HVER.FJERN, maske);
        Kjerne.hverKmd(HVER.DUELL, duell);
        for (const [k, a, t] of kmd) Kjerne.hverKmd(k, a, t);
    }

    /* min ridder til de andre: naar den endrer seg (hoyst sju ganger i sekundet,
     * ridderen flytter seg en piksel per bilde), og ellers hvert andre sekund */
    function sendMinRidder() {
        if (D && D.rolle === 'b') return;        /* kjernen kjorer kampen til den andre naa */
        const naa = performance.now();
        let m;
        if (Kjerne.hverKart()) {
            const [x, y, liv, figur] = Kjerne.hverRidder(0);
            m = { x, y, liv, figur, navn: Kjerne.hverNavn(0), b: Kjerne.hverBlob(0) };
        } else m = { borte: true };
        const s = JSON.stringify(m);
        if (naa - sistSendtTid < (s === sistSendt ? 2000 : 150)) return;
        Nett.sendRidder(m);
        sistSendt = s;
        sistSendtTid = naa;
    }

    /* ut av et rom med hver for seg: spillet her fortsetter, de andre forsvinner */
    function forlatHver(tekst) {
        avbrytDuell('');
        if (stoppAnnonse) { stoppAnnonse(); stoppAnnonse = null; }
        Nett.avslutt();
        fjerne.clear();
        rekkefolge = [];
        sistSendt = '';
        Kjerne.hverKmd(HVER.FJERN, 0);
        menyKmd(KMD.SLUTT);
        modus = 'alene';
        oppdaterMeny();
        if (tekst) status(tekst);
    }

    /* ---------------------------------------------------------------- dueller
     * Angriper du en annen spiller (port/src/hver.c: HVER_EV_DUELL), stopper
     * spillet ditt etter bildet, og den andre faar hele maskinen over en direkte
     * forbindelse (Nett.duellKoble). Den andre lagrer sitt eget spill, kjorer
     * kampen sammen med deg (du er vert for kampen, den andre styrer port 1) og
     * tar med seg ridderen sin tilbake naar kampen er over (HVER_EV_DUELL_SLUTT,
     * HVER_MEG). Svarer ikke den andre, styrer datamaskinen ridderen (HVER_AI). */
    const HEV = { DUELL: 1, SLUTT: 2 };
    let D = null;                            /* duellen: { rolle 'a' (angriper) | 'b', conn, plass, status, ... } */
    let fjerneVenter = false;

    const navnTil = (id) => { const s = sisteSpillere.find((x) => x.id === id); return s ? s.navn : 'den andre'; };

    function hverHendelser() {
        for (let e; (e = Kjerne.hverHendelse()); ) {
            if ((e & 0xff) === HEV.DUELL && (!D || D.rolle !== 'b')) startDuell(e >> 8);
            else if ((e & 0xff) === HEV.SLUTT) { if (D && D.rolle === 'b') sluttDuellB(); else if (D) sluttDuellA(); }
        }
    }

    /* A: du angrep ridderen paa plass k */
    function startDuell(k) {
        const id = rekkefolge[k - 1];
        if (!id || D || modus !== 'hver') { Kjerne.hverKmd(HVER.AI, k); return; }
        const d = D = { rolle: 'a', plass: k, id, status: 'venter', inn: 0, navn: navnTil(id), conn: null };
        status('Utfordrer ' + d.navn + ' ...');
        d.tidsfrist = setTimeout(() => utenDuell(d, d.navn + ' svarte ikke.'), 15000);
        Nett.duellKoble(id).then((conn) => {
            if (D !== d) { conn.close(); return; }
            d.conn = conn;
            conn.on('data', (m) => fraB(d, m));
            conn.on('close', () => { if (D === d) utenDuell(d, 'Forbindelsen til ' + d.navn + ' ble brutt.'); });
            conn.send({ t: 'utfordring', navn: innst.navn || 'Player', plass: k });
        }).catch(() => utenDuell(d, 'Fikk ikke kontakt med ' + d.navn + '.'));
    }

    /* A: ingen duell likevel; datamaskinen styrer den andre ridderen i kampen */
    function utenDuell(d, tekst) {
        if (D !== d) return;
        clearTimeout(d.tidsfrist);
        Kjerne.hverKmd(HVER.AI, d.plass);
        D = null;
        if (d.conn) { const c = d.conn; d.conn = null; setTimeout(() => c.close(), 300); }
        if (fjerneVenter) oppdaterFjerne();
        akk = 0;
        status(tekst + ' Datamaskinen styrer ridderen i kampen.');
    }

    function fraB(d, m) {
        if (D !== d || !m) return;
        switch (m.t) {
        case 'ja':
        case 'synk': {
            d.status = 'sender';
            const t = Kjerne.lagreTilstand();
            if (t) Nett.sendTilstandTil(d.conn, t, Kjerne.bildeNr());
            if (m.t === 'ja') status(d.navn + ' tar imot. Sender spillet ...');
            break;
        }
        case 'klar':
            clearTimeout(d.tidsfrist);
            d.status = 'aktiv';
            akk = 0;
            status('Kamp mot ' + d.navn + '!');
            break;
        case 'nei': utenDuell(d, d.navn + ' kan ikke kjempe nå.'); break;
        case 'inn': d.inn = m.j & 31; break;
        }
    }

    /* A: kampen er over; den andre har kjort de samme bildene og tar ridderen sin */
    function sluttDuellA() {
        const d = D;
        clearTimeout(d.tidsfrist);
        D = null;
        const r = fjerne.get(d.id);
        if (r) r.vent = true;                    /* til den andre sender ridderen slik den er etter kampen */
        oppdaterFjerne();
        if (d.conn) { const c = d.conn; setTimeout(() => c.close(), 3000); }
        status('Kampen mot ' + d.navn + ' er over.');
    }

    /* B: noen vil kjempe mot deg */
    function duellInn(conn) {
        conn.on('data', (m) => fraA(conn, m));
        conn.on('close', () => { if (D && D.rolle === 'b' && D.conn === conn) avbrytDuell('Forbindelsen ble brutt. Tilbake i ditt eget spill.'); });
    }

    async function fraA(conn, m) {
        if (!m) return;
        if (m.t === 'utfordring') {
            const egen = !D && modus === 'hver' && !menyApen && Kjerne.hverKart() ? Kjerne.lagreTilstand() : null;
            if (!egen) { conn.send({ t: 'nei' }); setTimeout(() => conn.close(), 500); return; }
            D = { rolle: 'b', conn, plass: m.plass | 0, status: 'venter', egen, rammer: [], navn: String(m.navn || 'Player').slice(0, 20),
                motta: Nett.tilstandsMottaker(), sistInn: -1, sistInnTid: 0, akk: 0 };
            Lyd.clear();
            status(D.navn + ' utfordrer deg til kamp!');
            conn.send({ t: 'ja' });
            return;
        }
        const d = D;
        if (!d || d.rolle !== 'b' || d.conn !== conn) return;
        if (m.t === 'f') { d.rammer.push(m); return; }
        if (m.t === 'tilstand') {
            const t = await d.motta(m);
            if (!t || D !== d) return;
            if (!Kjerne.lastTilstand(t.bytes)) { avbrytDuell('Kunne ikke laste kampen.'); return; }
            d.rammer = d.rammer.filter((r) => r.f >= t.f);
            d.status = 'aktiv';
            d.akk = 0;
            Lyd.clear();
            conn.send({ t: 'klar' });
            status('Kamp mot ' + d.navn + '! Du styrer ridderen din.');
        }
    }

    /* B: et bilde av kampen, med inndataene fra den andre */
    function kjorDuellbilde(d, m) {
        if (m.f !== Kjerne.bildeNr()) { d.status = 'venter'; d.rammer.length = 0; d.conn.send({ t: 'synk' }); return false; }
        if (m.c) for (const [k, a, t] of m.c) Kjerne.menyKommando(k, a, t);
        Kjerne.inndata(m.j[0], m.j[1]);
        if (m.k) for (const [k, ned] of m.k) Kjerne.tast(k, ned);
        Kjerne.bilde();
        nyttBilde = true;
        Visning.nyttBilde(Visning.brukerListe() ? Kjerne.tegneliste() : INGEN);
        Lyd.push(Kjerne.lyd());
        Kjerne.brukteFiler();
        while (Kjerne.menyHendelse()) { /* menyen er den andres */ }
        if (m.h !== undefined) {
            if (Kjerne.sjekksum() === m.h) statistikk.duellSjekket = (statistikk.duellSjekket || 0) + 1;
            else statistikk.duellAvvik = (statistikk.duellAvvik || 0) + 1;
        }
        if (m.h !== undefined && Kjerne.sjekksum() !== m.h && D === d) {
            d.status = 'venter';
            d.rammer.length = 0;
            d.conn.send({ t: 'synk' });
            status('Ute av takt, henter kampen på nytt ...');
        }
        hverHendelser();
        return D === d && d.status === 'aktiv';
    }

    /* B: kampen er over: ridderen ut av kampen og inn i ditt eget spill */
    function sluttDuellB() {
        const d = D;
        const ridder = Kjerne.hverBlob(d.plass);
        D = null;
        if (!Kjerne.lastTilstand(d.egen)) { status('Kunne ikke hente ditt eget spill tilbake.'); return; }
        Kjerne.hverKmd(HVER.MEG, 0, ridder);
        oppdaterFjerne();
        sistSendt = '';
        sistSendtTid = 0;
        akk = 0;
        Lyd.clear();
        const c = d.conn;
        setTimeout(() => c.close(), 1000);
        status('Kampen er over. Tilbake i ditt eget spill.');
    }

    /* duellen avbrytes (forbindelsen brutt, du forlater rommet) */
    function avbrytDuell(tekst) {
        const d = D;
        if (!d) return;
        if (d.rolle === 'a') { utenDuell(d, tekst || ''); return; }
        D = null;
        if (d.egen) Kjerne.lastTilstand(d.egen);
        try { d.conn.close(); } catch (e) { /* lukket */ }
        oppdaterFjerne();
        akk = 0;
        Lyd.clear();
        if (tekst) status(tekst);
    }

    /* B: joysticken din til den andre (port 1 i kampen) */
    function sendDuellInn(d) {
        const l = Inndata.les();
        const j = l.a | l.b | museRetning | (museFire || performance.now() < klikkTil ? FIRE : 0);
        const naa = performance.now();
        if (j === d.sistInn && naa - d.sistInnTid < 500) return;
        if (d.conn.open) d.conn.send({ t: 'inn', j });
        d.sistInn = j;
        d.sistInnTid = naa;
    }

    /* ---------------------------------------------------------------- spillokka */
    const INGEN = [];
    let nyttBilde = false;                  /* kjernen har laget et bilde siden sist det ble tegnet */
    function kjorEttBilde() {
        const lokalt = Inndata.les();
        lokalt.a |= museBits();
        if ((lokalt.a | lokalt.b) && Kjerne.iMeny()) menyBrukt = true;
        let taster = menyTaster(Inndata.hentTaster());
        let j0, j1;
        if (modus === 'vert') {
            const eiere = Kjerne.portSpillere();
            [j0, j1] = Nett.porter(lokalt.a | lokalt.b, eiere);
            if (!Nett.harGjester()) { j0 = lokalt.b; j1 = lokalt.a; }
            else {
                const alle = taster.map(([k, d]) => [k, d, Nett.vertensSpiller()]).concat(Nett.hentGjesteTaster());
                taster = alle.filter(([, d, sp]) => Nett.tastTillatt(sp, d, eiere)).map(([k, d]) => [k, d]);
            }
        } else if (D && D.rolle === 'a' && D.status === 'aktiv') {
            j0 = D.inn;                          /* port 1: den andre i duellen */
            j1 = lokalt.a | lokalt.b;
        } else {
            j0 = lokalt.b;
            j1 = lokalt.a;
        }
        taster = introTaster(j0, j1, taster);
        const f = Kjerne.bildeNr();
        const kommandoer = menyKo.splice(0);
        for (const [k, a, t] of kommandoer) Kjerne.menyKommando(k, a, t);
        Kjerne.inndata(j0, j1);
        for (const [k, d] of taster) Kjerne.tast(k, d);
        Kjerne.bilde();
        nyttBilde = true;
        Visning.nyttBilde(Visning.brukerListe() ? Kjerne.tegneliste() : INGEN);
        Lyd.push(Kjerne.lyd());
        const filer = Kjerne.brukteFiler();
        if (modus === 'vert' && Nett.harGjester()) {
            Nett.sendBilde(f, [j0, j1], taster, filer, Kjerne.hentFil, f % 120 === 0 ? Kjerne.sjekksum() : undefined, kommandoer);
        }
        if (D && D.rolle === 'a' && D.status === 'aktiv' && D.conn && D.conn.open) {
            const m = { t: 'f', f, j: [j0, j1] };
            if (taster.length) m.k = taster;
            if (kommandoer.length) m.c = kommandoer;
            if (f % 120 === 0) m.h = Kjerne.sjekksum();
            D.conn.send(m);
        }
        menyHendelser();
        if (modus === 'hver') hverHendelser();
    }

    function kjorGjestebilde(m) {
        if (m.f !== Kjerne.bildeNr()) {
            if (!venterSynk) { venterSynk = true; Nett.beOmSynk(); status('Ute av takt, henter spillet på nytt ...'); }
            Nett.rammer.length = 0;
            return false;
        }
        if (m.fil) for (const fil of m.fil) Kjerne.leggInnFil(fil.n, fil.d);
        if (m.c) for (const [k, a, t] of m.c) Kjerne.menyKommando(k, a, t);
        Kjerne.inndata(m.j[0], m.j[1]);
        if (m.k) for (const [k, d] of m.k) Kjerne.tast(k, d);
        Kjerne.bilde();
        nyttBilde = true;
        Visning.nyttBilde(Visning.brukerListe() ? Kjerne.tegneliste() : INGEN);
        Lyd.push(Kjerne.lyd());
        Kjerne.brukteFiler();
        menyHendelser();
        if (m.h !== undefined) {
            if (Kjerne.sjekksum() === m.h) statistikk.sjekket++;
            else if (!venterSynk) {
                statistikk.avvik++;
                venterSynk = true;
                Nett.beOmSynk();
                status('Ute av takt, henter spillet på nytt ...');
            }
        }
        return true;
    }

    function lokke(t) {
        requestAnimationFrame(lokke);
        const dt = Math.min(0.25, Math.max(0, (t - sist) / 1000));
        sist = t;
        if (modus === 'gjest') {
            /* send egne knapper til verten */
            const l = Inndata.les();
            Nett.sendInn(l.a | l.b | museRetning | (museFire || performance.now() < klikkTil ? FIRE : 0));
            for (const [k, d] of menyTaster(Inndata.hentTaster())) Nett.sendTast(k, d);
            const ko = Nett.rammer;
            while (ko.length && ko[0].f < Kjerne.bildeNr()) ko.shift();
            if (!venterSynk) {
                /* hold 2-4 bilder i koen: litt fortere naar den vokser */
                const maal = 3;
                akk += dt * (1 + Math.max(-0.5, Math.min(1, (ko.length - maal) * 0.08)));
                let n = 0;
                while (akk >= periode && ko.length && n < 6) { if (!kjorGjestebilde(ko.shift())) break; akk -= periode; n++; }
                if (!ko.length) akk = Math.min(akk, periode);
                if (ko.length > 40) while (ko.length > maal) { if (!kjorGjestebilde(ko.shift())) break; }
            }
        } else if (D && D.rolle === 'b') {
            /* kampen til den andre: de samme bildene, som en gjest */
            const d = D;
            sendDuellInn(d);
            if (d.status === 'aktiv') {
                const ko = d.rammer;
                d.akk += dt * (1 + Math.max(-0.5, Math.min(1, (ko.length - 3) * 0.08)));
                let n = 0;
                while (d.akk >= periode && ko.length && n < 6 && D === d) { if (!kjorDuellbilde(d, ko.shift())) break; d.akk -= periode; n++; }
                if (!ko.length) d.akk = Math.min(d.akk, periode);
                while (ko.length > 40 && D === d) { if (!kjorDuellbilde(d, ko.shift())) break; }
            }
        } else if (D && D.rolle === 'a' && D.status !== 'aktiv') {
            akk = 0;                                 /* venter paa den andre */
        } else if ((modus === 'alene' || modus === 'vert' || modus === 'hver') && !pause && !(menyApen && modus !== 'vert' && !D)) {
            akk += dt;
            let n = 0;
            /* stopper med en gang en duell begynner (spillet venter paa den andre) */
            while (akk >= periode && n < 4 && !(D && D.status !== 'aktiv')) { kjorEttBilde(); akk -= periode; n++; }
            if (akk > periode * 4) akk = 0;
            if (Kjerne.stoppet()) {
                startPaaNytt(Kjerne.stoppMelding());
                return;
            }
        }
        if (modus === 'hver') sendMinRidder();     /* ogsaa naar spillet staar, saa de andre vet at vi er her */
        if (modus === 'alene' || modus === 'vert' || modus === 'gjest' || modus === 'hver') {
            if (sisteModus === 'auto') visTur();
            visHint();
            /* bare naar det er noe nytt aa vise (se Visning.tegn); lagene bare naar de trengs */
            if (nyttBilde || Visning.maaTegnes()) Visning.tegn(Kjerne.rammebuffer(), Kjerne.vindu(), Visning.trengerLag() ? Kjerne.lag() : null);
            nyttBilde = false;
            Kjerne.lagPaa(Visning.trengerLag());
        }
    }

    /* ---------------------------------------------------------------- sidemenyen */
    function visMeny(on) {
        if (on !== menyApen && (modus === 'alene' || modus === 'hver')) Lyd.clear();     /* spillet staar mens menyen er aapen */
        menyApen = on;
        $('meny').hidden = !on;
        $('meny-knapp').hidden = on;        /* ellers ligger den over «Tilbake til spillet» */
        /* knappen som lukket menyen skal ikke ha fokus, ellers trykker Enter og mellomrom paa den */
        if (!on && document.activeElement && document.activeElement !== document.body) document.activeElement.blur();
        Inndata.paa(!on && !dialogApen && !!modus);
        if (on) oppdaterMeny();
    }

    function oppdaterMeny() {
        const nett = modus === 'vert' || modus === 'gjest' || modus === 'hver';
        $('nettspill').hidden = !nett;
        $('lagring').hidden = modus === 'gjest';
        $('omstart').textContent = modus === 'hver' ? 'Forlat rommet' : nett ? 'Forlat nettspillet og start på nytt' : 'Start spillet på nytt';
        $('lagring-hjelp').textContent = 'Tilstanden lagres i denne nettleseren.';
        if (modus === 'hver') {
            $('rominfo').textContent = (erVert() ? 'Du er vert for rom ' + Nett.kode() + '. Send lenken til opptil tre andre.' : 'Du er med i rom ' + Nett.kode() + '.')
                + ' Alle spiller sitt eget spill og ser de andre ridderne på kartet.';
            $('lenke').value = erVert() ? Nett.invitasjon() : '';
            $('lenkerad').hidden = !erVert();
            $('lagring-hjelp').textContent = 'Tilstanden lagres i denne nettleseren og gjelder bare ditt eget spill.';
        } else if (modus === 'vert') {
            $('rominfo').textContent = 'Du er vert for rom ' + Nett.kode() + '. Send lenken til opptil tre gjester.';
            $('lenke').value = Nett.invitasjon();
            $('lenkerad').hidden = false;
            $('lagring-hjelp').textContent = 'Tilstanden lagres i din nettleser. Laster du en tilstand, får gjestene den også.';
        } else if (modus === 'gjest') {
            $('rominfo').textContent = 'Du er med i rom ' + Nett.kode() + '. Verten kjører spillet og lagrer.';
            $('lenkerad').hidden = true;
        }
        visSpillere(null);
    }

    let sisteSpillere = [], sisteModus = 'auto';
    function visSpillere(liste, kode, portModus) {
        if (liste) sisteSpillere = liste;
        else if (erVert()) sisteSpillere = Nett.spillere();
        if (portModus) sisteModus = portModus;
        const tab = $('spillerliste');
        tab.innerHTML = '';
        if (modus === 'hver') {
            for (const s of sisteSpillere) {
                const tr = document.createElement('tr');
                const td1 = document.createElement('td');
                td1.textContent = s.navn + (s.vert ? ' (vert)' : '') + (s.id === Nett.minId() ? ' (deg)' : '');
                const td2 = document.createElement('td');
                const r = fjerne.get(s.id);
                td2.textContent = s.id === Nett.minId() ? '' : r && !r.borte ? 'På kartet' : 'Ikke på kartet';
                tr.append(td1, td2);
                tab.appendChild(tr);
            }
            $('port-hjelp').textContent = 'Hver for seg: alle styrer sin egen ridder i sitt eget spill. De andre ridderne står på kartet ditt '
                + 'der de er i sine spill, i stedet for datamaskinens riddere.';
            return;
        }
        const vert = modus === 'vert';
        /* hvordan joystickene fordeles */
        const topp = document.createElement('tr');
        const t1 = document.createElement('td');
        t1.textContent = 'Joystick';
        const t2 = document.createElement('td');
        if (vert) {
            const sel = document.createElement('select');
            for (const [v, t] of [['auto', 'Følger turen i spillet'], ['fast', 'Faste porter']]) {
                const o = document.createElement('option');
                o.value = v; o.textContent = t; o.selected = v === sisteModus;
                sel.appendChild(o);
            }
            sel.addEventListener('change', () => Nett.settModus(sel.value));
            t2.appendChild(sel);
        } else t2.textContent = sisteModus === 'auto' ? 'Følger turen i spillet' : 'Faste porter';
        topp.append(t1, t2);
        tab.appendChild(topp);
        const portNavn = { p2: 'Joystick 1 (port 2)', p1: 'Joystick 2 (port 1)', begge: 'Begge', ingen: 'Ser på' };
        const spillerNavn = { '-1': 'Ser på', 0: 'Spiller 1', 1: 'Spiller 2', 2: 'Spiller 3', 3: 'Spiller 4' };
        for (const s of sisteSpillere) {
            const tr = document.createElement('tr');
            const td1 = document.createElement('td');
            td1.textContent = s.navn + (s.vert ? ' (vert)' : '') + (s.klar === false ? ' (kobler til ...)' : '');
            const td2 = document.createElement('td');
            const valg = sisteModus === 'auto' ? spillerNavn : portNavn;
            const verdi = sisteModus === 'auto' ? String(s.spiller) : s.port;
            if (vert) {
                const sel = document.createElement('select');
                for (const [v, t] of Object.entries(valg)) {
                    const o = document.createElement('option');
                    o.value = v; o.textContent = t; o.selected = v === verdi;
                    sel.appendChild(o);
                }
                sel.addEventListener('change', () => {
                    if (sisteModus === 'auto') Nett.settSpiller(s.id, +sel.value);
                    else Nett.settPort(s.id, sel.value);
                });
                td2.appendChild(sel);
            } else {
                td2.textContent = valg[verdi] || verdi;
            }
            tr.append(td1, td2);
            tab.appendChild(tr);
        }
        $('port-hjelp').textContent = sisteModus === 'auto'
            ? 'Spiller 1 er den som velger ridder først i spillet, spiller 2 den neste osv. Joysticken går automatisk til den som har turen på kartet, og i kamp mellom to riddere får begge sin joystick. I menyene kan alle styre.'
            : 'Moonstone har to joystickporter. Joystick 1 (port 2) brukes på kartet og i menyene, i kamp mellom to riddere brukes begge.';
    }

    /* vis hvem som har turen naar det endrer seg */
    let sistEier = -2;
    function visTur() {
        if (modus !== 'vert' && modus !== 'gjest') return;
        const e = Kjerne.portSpillere()[1];
        if (e === sistEier) return;
        sistEier = e;
        if (e < 0) return;
        const s = sisteSpillere.find((x) => x.spiller === e);
        if (s) status(s.navn + ' har turen');
    }

    function fyllPlasser() {
        const sel = $('plass');
        for (let i = 1; i <= 9; i++) {
            const o = document.createElement('option');
            o.value = i; o.textContent = 'Plass ' + i;
            sel.appendChild(o);
        }
        sel.addEventListener('change', () => { plass = +sel.value; });
    }

    async function lagre() {
        if (modus !== 'alene' && modus !== 'vert' && modus !== 'hver') return;
        const s = Kjerne.lagreTilstand();
        if (!s) { status('Kunne ikke lagre.'); return; }
        const ok = await Lager.sett('tilstand' + plass, { data: s, tid: Date.now() });
        status(ok ? 'Lagret på plass ' + plass : 'Nettleseren tillater ikke lagring');
    }

    async function last() {
        if (modus !== 'alene' && modus !== 'vert' && modus !== 'hver') return;
        const v = await Lager.hent('tilstand' + plass);
        if (!v) { status('Ingenting lagret på plass ' + plass); return; }
        if (!Kjerne.lastTilstand(new Uint8Array(v.data))) { status('Tilstanden passer ikke med denne versjonen'); return; }
        /* de fjerne ridderne i tilstanden er fra da den ble lagret: bruk de som er i rommet naa */
        if (modus === 'hver') oppdaterFjerne();
        else Kjerne.hverKmd(HVER.FJERN, 0);
        Lyd.clear();
        status('Lastet plass ' + plass);
        if (modus === 'vert') for (const s of Nett.spillere()) if (!s.vert) Nett.sendTilstand(s.id, Kjerne.lagreTilstand(), Kjerne.bildeNr());
    }

    /* ---------------------------------------------------------------- knapper og taster */
    $('meny-knapp').addEventListener('click', () => visMeny(!menyApen));
    $('lukk-meny').addEventListener('click', () => visMeny(false));
    $('omstart').addEventListener('click', () => {
        if (modus === 'hver') { forlatHver('Du har forlatt rommet'); visMeny(false); return; }
        startPaaNytt(modus === 'vert' || modus === 'gjest' ? 'Du har forlatt nettspillet' : '');
    });
    $('lagre').addEventListener('click', lagre);
    $('last').addEventListener('click', last);
    $('kopier').addEventListener('click', async () => {
        try { await navigator.clipboard.writeText($('lenke').value); status('Lenken er kopiert'); }
        catch (e) { $('lenke').select(); document.execCommand('copy'); status('Lenken er kopiert'); }
    });
    $('chatfelt').addEventListener('keydown', (e) => {
        if (e.key !== 'Enter') return;
        const t = e.target.value.trim();
        if (t) Nett.chat(t);
        e.target.value = '';
    });
    $('filter').addEventListener('change', (e) => { innst.filter = e.target.value; Visning.settFilter(innst.filter); lagreInnst(); });
    $('format').addEventListener('change', (e) => { innst.format = e.target.value; Visning.settFormat(innst.format); lagreInnst(); });
    $('helt').addEventListener('change', (e) => { innst.helt = e.target.checked; Visning.settHelt(innst.helt); lagreInnst(); });
    /* kjernen tar volumet opp til 1; resten forsterkes i lydtraaden med myk begrensning */
    function settVolum(v) {
        Kjerne.volum(Math.min(1, v));
        Lyd.forsterk(Math.max(1, v));
    }
    $('volum').addEventListener('input', (e) => { innst.volum = +e.target.value; if (modus) settVolum(innst.volum); lagreInnst(); });
    $('knappevent').addEventListener('change', (e) => { innst.knappevent = e.target.checked; lagreInnst(); status('Gjelder fra neste start'); });
    $('skjermknapper').addEventListener('change', (e) => { innst.knapper = e.target.checked; lagreInnst(); visKnapper(); });

    const kodeOk = () => {
        const k = kodeFraTekst($('kode-felt').value);
        if (!k) { status('Skriv romkoden (seks tegn) eller lim inn lenken'); return; }
        visDialog('kode-dialog', false);
        medNavn(() => bliMed(k));
    };
    $('kode-ok').addEventListener('click', kodeOk);
    $('kode-felt').addEventListener('keydown', (e) => {
        if (e.key === 'Enter') kodeOk();
        if (e.key === 'Escape') visDialog('kode-dialog', false);
        e.stopPropagation();
    });
    $('kode-avbryt').addEventListener('click', () => visDialog('kode-dialog', false));
    $('navn-ok').addEventListener('click', navnOk);
    $('navn-felt').addEventListener('keydown', (e) => {
        if (e.key === 'Enter') navnOk();
        if (e.key === 'Escape') navnAvbryt();
        e.stopPropagation();
    });
    $('navn-avbryt').addEventListener('click', navnAvbryt);

    $('rammer').addEventListener('change', (e) => { Visning.settRammer(e.target.checked); });

    /* effekter: avkrysningsboksene heter effekt-NAVN */
    for (const navn of Object.keys(innst.effekter)) {
        const boks = $('effekt-' + navn);
        if (!boks) continue;
        boks.checked = !!innst.effekter[navn];
        boks.addEventListener('change', () => {
            innst.effekter[navn] = boks.checked;
            Visning.settEffekter(innst.effekter);
            lagreInnst();
        });
    }

    /* bakgrunnen som vises, som PNG med navnet HD-pakken bruker (bg/HASH.png) */
    $('lagre-bg').addEventListener('click', () => {
        if (!modus || modus === 'venter') return;
        /* lagene lages fra siste bilde, ogsaa naar spillet staar mens menyen er aapen */
        Kjerne.lagPaa(true);
        Kjerne.lagBygg();
        const lag = Kjerne.lag();
        Kjerne.lagPaa(Visning.trengerLag());
        {
            if (!lag) { status('Denne skjermen har ingen bakgrunn spillet holder for seg selv'); return; }
            const lerret = document.createElement('canvas');
            lerret.width = 320; lerret.height = 200;
            const ctx = lerret.getContext('2d');
            const bilde = ctx.createImageData(320, 200);
            bilde.data.set(lag.bak);
            ctx.putImageData(bilde, 0, 0);
            const navn = lag.hash.toString(16).padStart(8, '0') + '.png';
            lerret.toBlob((b) => {
                const a = document.createElement('a');
                a.href = URL.createObjectURL(b);
                a.download = navn;
                a.click();
                setTimeout(() => URL.revokeObjectURL(a.href), 5000);
                status('Lagret ' + navn + '. Legg den i mappen bg i HD-pakken.');
            });
        }
    });
    $('velg-hd').addEventListener('change', async (e) => {
        const n = await Visning.lastHdPakke(e.target.files);
        const bg = Visning.hdBakgrunner();
        $('hd-status').textContent = Visning.hdAntall() + ' bilder i HD-pakken' + (bg ? ', av dem ' + bg + ' bakgrunner.' : '.');
        status(n + ' HD-bilder lastet');
    });
    $('tom-hd').addEventListener('click', () => { Visning.tomHdPakke(); $('hd-status').textContent = 'Ingen HD-pakke.'; });

    Inndata.settHurtigtaster((e) => {
        if (e.code === 'Home') { visMeny(!menyApen); return true; }
        if (e.repeat) return false;
        if (e.code === 'PageUp') { lagre(); return true; }
        if (e.code === 'PageDown') { last(); return true; }
        if (e.code === 'End') { plass = plass % 9 + 1; $('plass').value = plass; status('Plass ' + plass); return true; }
        if (e.code === 'Pause' && (modus === 'alene' || modus === 'hver')) { pause = !pause; Lyd.clear(); status(pause ? 'Pause' : 'Fortsetter'); return true; }
        return false;
    });
    /* Home lukker menyen ogsaa naar spillet ikke tar tastene; har hurtigtasten
     * nettopp aapnet den (samme trykk, defaultPrevented), skal den staa aapen */
    window.addEventListener('keydown', (e) => {
        if (e.code === 'Home' && menyApen && !e.defaultPrevented) { visMeny(false); e.preventDefault(); }
    });
    /* fanen skjules: nettleseren stopper spillokka, saa lyden toemmes i stedet for aa hakke */
    document.addEventListener('visibilitychange', () => { if (document.hidden) Lyd.clear(); });

    /* fanen lukkes: si fra til gjestene og fjern rommet fra listen */
    window.addEventListener('pagehide', () => {
        if (modus !== 'vert' && modus !== 'hver') return;
        if (stoppAnnonse) { stoppAnnonse(); stoppAnnonse = null; }
        Nett.avslutt();
    });

    /* ---------------------------------------------------------------- start */
    $('filter').value = innst.filter;
    $('format').value = innst.format;
    $('helt').checked = innst.helt;
    $('volum').value = innst.volum;
    $('knappevent').checked = innst.knappevent;
    $('skjermknapper').checked = innst.knapper;
    fyllPlasser();
    Inndata.lagTouch($('touch'));
    const rom = new URLSearchParams(location.search).get('rom');
    if (rom && /^[A-Za-z0-9]{6}$/.test(rom)) invitasjon = rom.toUpperCase();
    Lager.hent('mod').then((m) => { if (m) { modFiler = m; visMod(); } }).finally(startSpillet);
    window.moonDebug = { Kjerne, Nett, Visning, innst, statistikk, modus: () => modus, lyd: () => ({ ms: Lyd.bufferedMs(), hull: Lyd.hull() }),
        duell: () => (D ? { rolle: D.rolle, status: D.status, plass: D.plass, inn: D.inn, sistInn: D.sistInn } : null) };
})();
