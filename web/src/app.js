/*
 * app.js - startsiden, spillokka og menyen.
 *
 * Tre maater aa spille paa:
 *   alene  kjernen kjorer her, joystick A paa port 2 og B paa port 1
 *   vert   som alene, men gjestene kobler seg til og faar hvert sitt joystick
 *   gjest  kjernen kjorer de samme bildene som verten, med inndataene fra verten
 *
 * Spillfilen hentes fra IndexedDB, eller fra spill/Moonstonecd32-AMIGA.zip ved
 * siden av siden hvis den ligger der (GitHub Pages-utgaven kan ha den med).
 */
'use strict';

(() => {
    const $ = (id) => document.getElementById(id);
    const inn = Lager.innstillinger();
    const innst = Object.assign({ filter: 'skarp', format: 'pal', helt: false, volum: 1, knappevent: false, navn: '', offentlig: false }, inn);
    const lagreInnst = () => Lager.lagreInnstillinger(innst);

    let spillfil = null;                    /* Uint8Array */
    let modFiler = {};                      /* navn -> Uint8Array, legges over data/ */
    let modus = null;                       /* 'alene' | 'vert' | 'gjest' */
    let pause = false, menyApen = false, venterSynk = false, kjorer = false;
    let periode = 1 / 49.92;
    let akk = 0, sist = 0, plass = 1;
    let stoppAnnonse = null, stoppListe = null;
    let statusTimer = null;
    const statistikk = { sjekket: 0, avvik: 0 };

    /* ---------------------------------------------------------------- meldinger */
    function melding(tekst, feil) {
        const m = $('melding');
        m.textContent = tekst || '';
        m.classList.toggle('feil', !!feil);
    }

    function status(tekst) {
        const s = $('status');
        s.textContent = tekst;
        s.classList.add('vis');
        clearTimeout(statusTimer);
        statusTimer = setTimeout(() => s.classList.remove('vis'), 3000);
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
    async function finnSpillfil() {
        const lagret = await Lager.hent('spillfil');
        if (lagret) { spillfil = new Uint8Array(lagret); visSpillfil('Spillfilen er klar (lagret i nettleseren).'); return; }
        for (const sti of ['spill/Moonstonecd32-AMIGA.zip', 'spill/moonstone.zip', 'Moonstonecd32-AMIGA.zip']) {
            try {
                const r = await fetch(sti);
                if (!r.ok) continue;
                const b = new Uint8Array(await r.arrayBuffer());
                if (b.length > 100000) { spillfil = b; visSpillfil('Spillfilen er klar (fulgte med siden).'); return; }
            } catch (e) { /* fra disk eller uten nett */ }
        }
        visSpillfil('Velg spillfilen for å spille alene eller være vert. Som gjest trenger du den ikke.');
    }

    function visSpillfil(tekst) { $('spillfil-status').textContent = tekst; }

    $('velg-fil').addEventListener('change', async (e) => {
        const f = e.target.files[0];
        if (!f) return;
        const b = new Uint8Array(await f.arrayBuffer());
        spillfil = b;
        const ok = await Lager.sett('spillfil', b);
        visSpillfil(ok ? 'Spillfilen er lagret i nettleseren.' : 'Spillfilen er valgt (kunne ikke lagres i nettleseren).');
        melding('');
    });

    function visMod() {
        const navn = Object.keys(modFiler);
        $('mod-liste').textContent = navn.length ? 'Brukes: ' + navn.join(', ') : 'Ingen egne filer.';
    }

    $('velg-mod').addEventListener('change', async (e) => {
        for (const f of e.target.files) modFiler[f.name] = new Uint8Array(await f.arrayBuffer());
        await Lager.sett('mod', modFiler);
        visMod();
    });
    $('fjern-mod').addEventListener('click', async () => { modFiler = {}; await Lager.slett('mod'); visMod(); });

    /* ---------------------------------------------------------------- oppstart */
    async function startKjerne(somGjest) {
        await Kjerne.last();
        if (somGjest) {
            Kjerne.startSomGjest();
        } else {
            if (!spillfil) throw new Error('Velg spillfilen først.');
            Kjerne.aapne(spillfil.slice());
            for (const [n, d] of Object.entries(modFiler)) Kjerne.leggInnFil('data/' + n, d);
            Kjerne.start(innst.knappevent);
        }
        periode = 1 / Kjerne.hz();
        Kjerne.volum(innst.volum);
    }

    function visSpill() {
        $('start').hidden = true;
        $('spill').hidden = false;
        if (!Visning.klar) {
            Visning.init($('lerret'), Kjerne.bredde(), Kjerne.hoyde());
            Visning.klar = true;
        }
        Visning.settFilter(innst.filter);
        Visning.settFormat(innst.format);
        Visning.settHelt(innst.helt);
        Visning.tilpass();
        Inndata.paa(true);
        const touch = matchMedia('(pointer: coarse)').matches;
        $('touch').hidden = !touch;
        if (!kjorer) { kjorer = true; requestAnimationFrame(lokke); }
    }

    function navn() {
        const n = $('navn').value.trim().slice(0, 20);
        innst.navn = n;
        lagreInnst();
        return n || 'Spiller';
    }

    async function spillAlene() {
        try {
            melding('Starter ...');
            await Lyd.start();
            await startKjerne(false);
            modus = 'alene';
            oppdaterMeny();
            visSpill();
            melding('');
        } catch (e) { melding(e.message, true); }
    }

    async function lagRom() {
        try {
            if (!spillfil) throw new Error('Velg spillfilen først. Gjestene trenger den ikke, men verten gjør det.');
            melding('Lager rom ...');
            await Lyd.start();
            await startKjerne(false);
            const kode = await Nett.lagRom(navn(), {
                lobby: visSpillere,
                chat: chatLinje,
                status,
                trengerTilstand: (id) => {
                    const s = Kjerne.lagreTilstand();
                    if (s) Nett.sendTilstand(id, s, Kjerne.bildeNr());
                },
                antall: () => {},
            });
            modus = 'vert';
            if ($('offentlig').checked) {
                stoppAnnonse = Romliste.annonser(() => ({
                    kode, vert: innst.navn || 'Vert', spillere: Nett.spillere().length, maks: 4,
                }));
            }
            oppdaterMeny();
            visSpill();
            melding('');
            status('Rommet ' + kode + ' er klart. Del lenken i menyen (Home).');
            visMeny(true);
        } catch (e) { melding('Kunne ikke lage rom: ' + e.message, true); Nett.avslutt(); modus = null; }
    }

    async function bliMed(kode) {
        kode = (kode || $('romkode').value).trim().toUpperCase();
        if (!/^[A-Z0-9]{6}$/.test(kode)) { melding('Romkoden har seks tegn.', true); return; }
        try {
            melding('Kobler til rom ' + kode + ' ...');
            await Lyd.start();
            await startKjerne(true);
            await Nett.bliMed(kode, navn(), {
                lobby: visSpillere,
                chat: chatLinje,
                status: (t) => { status(t); melding(t); },
                ping: () => {},
                feil: (t) => { melding(t, true); status(t); },
                frakoblet: (t) => { avslutt(); melding(t, true); },
                tilstand: (bytes) => {
                    if (!Kjerne.lastTilstand(bytes)) { melding('Kunne ikke laste spillet fra verten.', true); return; }
                    venterSynk = false;
                    akk = 0;
                    if (modus !== 'gjest') {
                        modus = 'gjest';
                        oppdaterMeny();
                        visSpill();
                        melding('');
                    }
                    status('Du er med i spillet.');
                },
            });
            modus = modus || 'venter';
        } catch (e) { melding(e.message, true); Nett.avslutt(); modus = null; }
    }

    /* ---------------------------------------------------------------- spillokka */
    function kjorEttBilde() {
        const lokalt = Inndata.les();
        let taster = Inndata.hentTaster();
        let j0, j1;
        if (modus === 'vert') {
            const eiere = Kjerne.portSpillere();
            [j0, j1] = Nett.porter(lokalt.a | lokalt.b, eiere);
            if (!Nett.harGjester()) { j0 = lokalt.b; j1 = lokalt.a; }
            else {
                const alle = taster.map(([k, d]) => [k, d, Nett.vertensSpiller()]).concat(Nett.hentGjesteTaster());
                taster = alle.filter(([, d, sp]) => Nett.tastTillatt(sp, d, eiere)).map(([k, d]) => [k, d]);
            }
        } else {
            j0 = lokalt.b;
            j1 = lokalt.a;
        }
        const f = Kjerne.bildeNr();
        Kjerne.inndata(j0, j1);
        for (const [k, d] of taster) Kjerne.tast(k, d);
        Kjerne.bilde();
        Visning.nyttBilde(Kjerne.tegneliste());
        Lyd.push(Kjerne.lyd());
        const filer = Kjerne.brukteFiler();
        if (modus === 'vert' && Nett.harGjester()) {
            Nett.sendBilde(f, [j0, j1], taster, filer, Kjerne.hentFil, f % 120 === 0 ? Kjerne.sjekksum() : undefined);
        }
    }

    function kjorGjestebilde(m) {
        if (m.f !== Kjerne.bildeNr()) {
            if (!venterSynk) { venterSynk = true; Nett.beOmSynk(); status('Ute av takt, henter spillet på nytt ...'); }
            Nett.rammer.length = 0;
            return false;
        }
        if (m.fil) for (const fil of m.fil) Kjerne.leggInnFil(fil.n, fil.d);
        Kjerne.inndata(m.j[0], m.j[1]);
        if (m.k) for (const [k, d] of m.k) Kjerne.tast(k, d);
        Kjerne.bilde();
        Visning.nyttBilde(Kjerne.tegneliste());
        Lyd.push(Kjerne.lyd());
        Kjerne.brukteFiler();
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
            Nett.sendInn(l.a | l.b);
            for (const [k, d] of Inndata.hentTaster()) Nett.sendTast(k, d);
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
        } else if ((modus === 'alene' || modus === 'vert') && !pause && !(menyApen && modus === 'alene')) {
            akk += dt;
            let n = 0;
            while (akk >= periode && n < 4) { kjorEttBilde(); akk -= periode; n++; }
            if (akk > periode * 4) akk = 0;
            if (Kjerne.stoppet()) {
                const msg = Kjerne.stoppMelding();
                avslutt();
                melding(msg);
                return;
            }
        }
        if (modus) {
            if (sisteModus === 'auto') visTur();
            Visning.tegn(Kjerne.rammebuffer(), Kjerne.vindu());
        }
    }

    /* ---------------------------------------------------------------- meny */
    function visMeny(on) {
        menyApen = on;
        $('meny').hidden = !on;
        Inndata.paa(!on);
        if (on) oppdaterMeny();
    }

    function oppdaterMeny() {
        const nett = modus === 'vert' || modus === 'gjest';
        $('nettspill').hidden = !nett;
        $('lagring').hidden = modus === 'gjest';
        if (modus === 'vert') {
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
        else if (modus === 'vert') sisteSpillere = Nett.spillere();
        if (portModus) sisteModus = portModus;
        const tab = $('spillerliste');
        tab.innerHTML = '';
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
        if (modus !== 'alene' && modus !== 'vert') return;
        const s = Kjerne.lagreTilstand();
        if (!s) { status('Kunne ikke lagre.'); return; }
        const ok = await Lager.sett('tilstand' + plass, { data: s, tid: Date.now() });
        status(ok ? 'Lagret på plass ' + plass : 'Nettleseren tillater ikke lagring');
    }

    async function last() {
        if (modus !== 'alene' && modus !== 'vert') return;
        const v = await Lager.hent('tilstand' + plass);
        if (!v) { status('Ingenting lagret på plass ' + plass); return; }
        if (!Kjerne.lastTilstand(new Uint8Array(v.data))) { status('Tilstanden passer ikke med denne versjonen'); return; }
        Lyd.clear();
        status('Lastet plass ' + plass);
        if (modus === 'vert') for (const s of Nett.spillere()) if (!s.vert) Nett.sendTilstand(s.id, Kjerne.lagreTilstand(), Kjerne.bildeNr());
    }

    function avslutt() {
        if (stoppAnnonse) { stoppAnnonse(); stoppAnnonse = null; }
        Nett.avslutt();
        modus = null;
        venterSynk = false;
        Inndata.paa(false);
        visMeny(false);
        Lyd.clear();
        $('spill').hidden = true;
        $('start').hidden = false;
        Nett.rammer.length = 0;
        history.replaceState(null, '', location.pathname);
    }

    /* ---------------------------------------------------------------- knapper og taster */
    $('spill-alene').addEventListener('click', spillAlene);
    $('lag-rom').addEventListener('click', lagRom);
    $('bli-med').addEventListener('click', () => bliMed());
    $('romkode').addEventListener('keydown', (e) => { if (e.key === 'Enter') bliMed(); });
    $('meny-knapp').addEventListener('click', () => visMeny(!menyApen));
    $('lukk-meny').addEventListener('click', () => visMeny(false));
    $('avslutt').addEventListener('click', avslutt);
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
    $('volum').addEventListener('input', (e) => { innst.volum = +e.target.value; if (modus) Kjerne.volum(innst.volum); lagreInnst(); });
    $('knappevent').addEventListener('change', (e) => { innst.knappevent = e.target.checked; lagreInnst(); status('Gjelder fra neste start'); });
    $('offentlig').addEventListener('change', (e) => { innst.offentlig = e.target.checked; lagreInnst(); });
    $('rammer').addEventListener('change', (e) => { Visning.settRammer(e.target.checked); });
    $('velg-hd').addEventListener('change', async (e) => {
        const n = await Visning.lastHdPakke(e.target.files);
        $('hd-status').textContent = Visning.hdAntall() + ' bilder i HD-pakken.';
        status(n + ' HD-bilder lastet');
    });
    $('tom-hd').addEventListener('click', () => { Visning.tomHdPakke(); $('hd-status').textContent = 'Ingen HD-pakke.'; });

    Inndata.settHurtigtaster((e) => {
        if (e.code === 'Home') { visMeny(!menyApen); return true; }
        if (e.repeat) return false;
        if (e.code === 'PageUp') { lagre(); return true; }
        if (e.code === 'PageDown') { last(); return true; }
        if (e.code === 'End') { plass = plass % 9 + 1; $('plass').value = plass; status('Plass ' + plass); return true; }
        if (e.code === 'Pause' && modus === 'alene') { pause = !pause; status(pause ? 'Pause' : 'Fortsetter'); return true; }
        return false;
    });
    window.addEventListener('keydown', (e) => {
        if (e.code === 'Home' && menyApen && modus) { visMeny(false); e.preventDefault(); }
    });

    /* offentlige rom: listen fylles naar boksen aapnes */
    $('offentlige').addEventListener('toggle', () => {
        if ($('offentlige').open && !stoppListe) {
            stoppListe = Romliste.lytt((rom, feil) => {
                const ul = $('romliste');
                ul.innerHTML = '';
                if (feil) { ul.innerHTML = '<li class="hjelp"></li>'; ul.firstChild.textContent = 'Listen er ikke tilgjengelig: ' + feil; return; }
                if (!rom.length) { ul.innerHTML = '<li class="hjelp">Ingen offentlige rom akkurat nå.</li>'; return; }
                for (const r of rom) {
                    const li = document.createElement('li');
                    const tekst = document.createElement('span');
                    tekst.textContent = (r.vert || 'Vert') + ' (' + r.kode + '), ' + (r.spillere || 1) + ' av ' + (r.maks || 4) + ' spillere';
                    const b = document.createElement('button');
                    b.className = 'knapp liten';
                    b.textContent = 'Bli med';
                    b.disabled = (r.spillere || 1) >= (r.maks || 4);
                    b.addEventListener('click', () => bliMed(r.kode));
                    li.append(tekst, b);
                    ul.appendChild(li);
                }
            });
        }
    });

    /* ---------------------------------------------------------------- start */
    $('navn').value = innst.navn;
    $('filter').value = innst.filter;
    $('format').value = innst.format;
    $('helt').checked = innst.helt;
    $('volum').value = innst.volum;
    $('knappevent').checked = innst.knappevent;
    $('offentlig').checked = innst.offentlig;
    fyllPlasser();
    Inndata.lagTouch($('touch'));
    finnSpillfil();
    Lager.hent('mod').then((m) => { if (m) { modFiler = m; visMod(); } });
    const rom = new URLSearchParams(location.search).get('rom');
    if (rom) {
        $('romkode').value = rom.toUpperCase();
        melding('Du er invitert til rom ' + rom.toUpperCase() + '. Skriv navnet ditt og trykk «Bli med».');
        $('bli-med').focus();
    }
    window.moonDebug = { Kjerne, Nett, Visning, innst, statistikk, modus: () => modus };
})();
