/*
 * net.js - nettspill med PeerJS (WebRTC).
 *
 * Oppskriften er den samme som i Guild Life: en spillers nettleser er vert og
 * kjorer spillet, og opptil tre gjester kobler seg til. PeerJS Cloud hjelper
 * nettleserne aa finne hverandre, deretter gaar dataene direkte mellom dem.
 *
 * Verten styrer alt. For hvert bilde samler verten inndata fra alle (hver
 * spiller er koblet til en joystickport), kjorer bildet og sender inndataene
 * til gjestene. Gjestene kjorer de samme bildene med de samme inndataene paa sin
 * egen kopi av maskinen, saa alle ser det samme spillet. Spillkoden og reglene
 * er helt uendret; det er bare joystickene som kommer over nettet.
 *
 * Naar en gjest kobler seg til (eller kommer ut av takt), sender verten hele
 * tilstanden til maskinen, pakket med gzip. Filer spillet laster senere (nye
 * kart, monstre, lyder) sendes sammen med bildet der de brukes, saa gjestene
 * trenger ikke spillfilene selv. Hvert 120. bilde sender verten en sjekksum, og
 * gjesten ber om ny tilstand hvis den ikke stemmer.
 *
 * Rommet har en kode paa seks tegn. Peer-ID-en til verten er "moonstone-ms-" + kode.
 * Invitasjonslenken er siden med ?rom=KODE.
 */
'use strict';

const Nett = (() => {
    const PREFIKS = 'moonstone-ms-';
    const VERSJON = 2;                          /* 2: Mode Separate (ridder-meldinger, spill i lobbyen) */
    const MAKS_GJESTER = 3;
    const DEL = 48 * 1024;
    const PORTER = ['p2', 'p1', 'p2'];        /* standard for gjest 1, 2, 3 */

    let peer = null, rolle = null, kode = '', mittNavn = 'Spiller';
    let h = {};                               /* hendelser til app.js */

    /* ---------------------------------------------------------------- felles */
    function nyKode() {
        const a = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
        let s = '';
        const r = crypto.getRandomValues(new Uint8Array(6));
        for (let i = 0; i < 6; i++) s += a[r[i] % a.length];
        return s;
    }

    function tilBytes(d) {
        if (d instanceof Uint8Array) return d;
        if (d instanceof ArrayBuffer) return new Uint8Array(d);
        if (ArrayBuffer.isView(d)) return new Uint8Array(d.buffer, d.byteOffset, d.byteLength);
        return new Uint8Array(0);
    }

    function tilBuffer(u8) {
        return u8.buffer.slice(u8.byteOffset, u8.byteOffset + u8.byteLength);
    }

    async function pakk(bytes) {
        if (!window.CompressionStream) return { z: false, data: bytes };
        const s = new Blob([bytes]).stream().pipeThrough(new CompressionStream('gzip'));
        return { z: true, data: new Uint8Array(await new Response(s).arrayBuffer()) };
    }

    async function pakkUt(bytes, z) {
        if (!z) return bytes;
        const s = new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip'));
        return new Uint8Array(await new Response(s).arrayBuffer());
    }

    /* Egen PeerJS-server i stedet for PeerJS Cloud: ?peer=vert:port[/sti] i adressen. */
    let server = {};
    (() => {
        const p = new URLSearchParams(location.search).get('peer');
        if (!p) return;
        const m = /^(?:(wss?|https?):\/\/)?([^:/]+)(?::(\d+))?(\/.*)?$/.exec(p);
        if (!m) return;
        const sikker = m[1] ? /s$/.test(m[1]) : !/^(localhost|127\.|192\.168\.|10\.)/.test(m[2]);
        server = { host: m[2], port: m[3] ? +m[3] : (sikker ? 443 : 80), path: m[4] || '/', secure: sikker };
    })();

    function lagPeer(id) {
        const o = Object.assign({ debug: 1 }, server);
        return id ? new Peer(id, o) : new Peer(o);
    }

    /* lenken beholder en egen PeerJS-server og MQTT-megler, saa gjesten bruker de samme */
    function invitasjon(k) {
        const u = new URL(location.href);
        const behold = ['peer', 'mqtt', 'mqttv'].map((n) => [n, u.searchParams.get(n)]);
        u.search = '';
        u.hash = '';
        u.searchParams.set('rom', k || kode);
        for (const [n, v] of behold) if (v) u.searchParams.set(n, v);
        return u.toString();
    }

    /* ---------------------------------------------------------------- vert */
    const gjester = new Map();                /* peer-id -> gjest */
    let vertPort = 'p2', vertSpiller = 0;
    let portModus = 'auto';                   /* 'auto' = joysticken folger turen, 'fast' = faste porter */

    function ledigSpiller() {
        const brukt = new Set([vertSpiller]);
        for (const g of gjester.values()) brukt.add(g.spiller);
        for (let i = 0; i < 4; i++) if (!brukt.has(i)) return i;
        return -1;
    }
    const gjesteTaster = [];
    /* 'sammen': verten kjorer spillet for alle (tur for tur, som originalen).
     * 'hver': alle spiller sitt eget spill, og ridderne sendes til hverandre
     * (docs/flerspiller.md); da faar gjestene ingen tilstand eller bilder. */
    let romSpill = 'sammen';

    function lagRom(navn, hendelser, spill) {
        h = hendelser;
        mittNavn = navn || 'Vert';
        rolle = 'vert';
        romSpill = spill === 'hver' ? 'hver' : 'sammen';
        return new Promise((ok, feil) => {
            let forsok = 0, aapen = false;
            const tidsfrist = setTimeout(() => {
                if (aapen) return;
                if (peer) peer.destroy();
                feil(new Error('Fikk ikke kontakt med PeerJS-serveren. Sjekk nettforbindelsen og prov igjen.'));
            }, 20000);
            const prov = () => {
                kode = nyKode();
                peer = lagPeer(PREFIKS + kode.toLowerCase());
                peer.on('open', () => { aapen = true; clearTimeout(tidsfrist); oppdaterLobby(); ok(kode); });
                peer.on('connection', nyGjest);
                peer.on('disconnected', () => { if (aapen && peer && !peer.destroyed) peer.reconnect(); });
                peer.on('error', (e) => {
                    if (e.type === 'unavailable-id' && ++forsok < 5) { peer.destroy(); prov(); return; }
                    if (!aapen) return;           /* tidsfristen gir feilmeldingen */
                    h.status && h.status('Nettverksfeil: ' + (e.message || e.type));
                });
            };
            prov();
        });
    }

    function nyGjest(conn) {
        conn.on('data', (d) => fraGjest(conn, d));
        conn.on('close', () => {
            const g = gjester.get(conn.peer);
            if (g) {
                gjester.delete(conn.peer);
                h.chat && h.chat('', g.navn + ' koblet fra');
                oppdaterLobby();
            }
        });
        conn.on('error', () => { /* close kommer etterpaa */ });
    }

    function fraGjest(conn, d) {
        if (!d || typeof d !== 'object') return;
        let g = gjester.get(conn.peer);
        switch (d.t) {
        case 'hei': {
            if (g) return;
            if (d.v !== VERSJON) {
                conn.send({ t: 'feil', tekst: 'Verten har en annen versjon av siden. Last siden paa nytt.' });
                setTimeout(() => conn.close(), 500);
                return;
            }
            if (gjester.size >= MAKS_GJESTER) {
                conn.send({ t: 'feil', tekst: 'Rommet er fullt (fire spillere).' });
                setTimeout(() => conn.close(), 500);
                return;
            }
            g = {
                conn, id: conn.peer, navn: String(d.navn || 'Gjest').slice(0, 20),
                port: PORTER[gjester.size] || 'ingen', spiller: ledigSpiller(),
                inn: 0, klar: false, venter: true, ko: [], filer: new Set(),
            };
            gjester.set(conn.peer, g);
            h.chat && h.chat('', g.navn + ' koblet seg til');
            if (romSpill === 'hver') {          /* gjesten spiller sitt eget spill */
                g.klar = true;
                g.venter = false;
                oppdaterLobby();
            } else {
                oppdaterLobby();
                h.trengerTilstand && h.trengerTilstand(g.id);
            }
            break;
        }
        case 'inn': if (g) g.inn = d.j & 31; break;
        case 'tast': if (g && g.klar) gjesteTaster.push([d.k & 0x7f, !!d.ned, g.spiller]); break;
        case 'velg': if (g && g.klar) h.velg && h.velg(d.rad | 0); break;     /* gjesten klikket paa en rad i menyen */
        case 'ridder':                          /* hver for seg: ridderen til en gjest, videre til de andre */
            if (g && romSpill === 'hver') {
                const m = d.borte ? { t: 'ridder', fra: g.id, borte: true }
                    : { t: 'ridder', fra: g.id, x: d.x | 0, y: d.y | 0, liv: d.liv | 0, figur: d.figur | 0, navn: String(d.navn || '').slice(0, 20) };
                for (const a of gjester.values()) if (a !== g && a.conn.open) a.conn.send(m);
                h.ridder && h.ridder(g.id, m);
            }
            break;
        case 'chat':
            if (g) {
                const tekst = String(d.tekst || '').slice(0, 300);
                sendAlle({ t: 'chat', fra: g.navn, tekst });
                h.chat && h.chat(g.navn, tekst);
            }
            break;
        case 'synk':
            if (g) { h.status && h.status(g.navn + ' kom ut av takt, sender tilstanden paa nytt'); h.trengerTilstand && h.trengerTilstand(g.id); }
            break;
        case 'ping': conn.send({ t: 'pong', tid: d.tid }); break;
        }
    }

    function sendAlle(msg) {
        for (const g of gjester.values()) if (g.conn.open) g.conn.send(msg);
    }

    function spillere() {
        const l = [{ id: 'vert', navn: mittNavn, port: vertPort, spiller: vertSpiller, vert: true }];
        for (const g of gjester.values()) l.push({ id: g.id, navn: g.navn, port: g.port, spiller: g.spiller, klar: g.klar });
        return l;
    }

    function oppdaterLobby() {
        const l = spillere();
        sendAlle({ t: 'lobby', spillere: l, kode, modus: portModus, spill: romSpill });
        h.lobby && h.lobby(l, kode, portModus, romSpill);
        h.antall && h.antall(l.length);
    }

    function settPort(id, port) {
        if (id === 'vert') vertPort = port;
        else if (gjester.has(id)) gjester.get(id).port = port;
        oppdaterLobby();
    }

    function settSpiller(id, n) {
        if (id === 'vert') vertSpiller = n;
        else if (gjester.has(id)) gjester.get(id).spiller = n;
        oppdaterLobby();
    }

    function settModus(m) { portModus = m; oppdaterLobby(); }

    /* Tilstanden sendes i deler. Bildene som kjores mens den pakkes, legges i
     * koen til gjesten og sendes etterpaa, i riktig rekkefolge. */
    async function sendTilstand(id, bytes, bildeNr) {
        const g = gjester.get(id);
        if (!g) return;
        g.klar = false;
        g.venter = true;
        g.ko = [];
        g.filer.clear();
        const p = await pakk(bytes);
        if (!gjester.has(id)) return;
        const n = Math.ceil(p.data.length / DEL);
        const tid = Date.now();
        for (let i = 0; i < n; i++) {
            g.conn.send({ t: 'tilstand', id: tid, i, n, f: bildeNr, z: p.z, data: tilBuffer(p.data.subarray(i * DEL, (i + 1) * DEL)) });
        }
        for (const m of g.ko) g.conn.send(m);
        g.ko = [];
        g.venter = false;
        g.klar = true;
        oppdaterLobby();
    }

    /* Inndata for de to portene. Med 'auto' folger joysticken turen i spillet:
     * eiere[1] er spilleren (0-3) som styrer port 2 naa, eiere[0] port 1 (se
     * port/src/game.c). Er det ukjent (menyer, intro), styrer alle spillerne
     * port 2. Med 'fast' er hver deltaker koblet til en bestemt port. */
    function porter(lokal, eiere) {
        const deltakere = [{ spiller: vertSpiller, port: vertPort, inn: lokal }];
        for (const g of gjester.values()) if (g.klar) deltakere.push({ spiller: g.spiller, port: g.port, inn: g.inn });
        const j = [0, 0];
        if (portModus === 'auto') {
            const har = (n) => n >= 0 && deltakere.some((d) => d.spiller === n);
            const fra = (n) => { let b = 0; for (const d of deltakere) if (d.spiller === n) b |= d.inn; return b; };
            const e2 = eiere ? eiere[1] : -1, e1 = eiere ? eiere[0] : -1;
            if (har(e2)) j[1] = fra(e2);
            else if (e2 < 0) { for (const d of deltakere) if (d.spiller >= 0) j[1] |= d.inn; }
            else j[1] = lokal;                    /* ingen er den spilleren: verten styrer */
            if (har(e1)) j[0] = fra(e1);
            else if (e1 >= 0) j[0] = lokal;
            return j;
        }
        const legg = (port, b) => {
            if (port === 'p1' || port === 'begge') j[0] |= b;
            if (port === 'p2' || port === 'begge') j[1] |= b;
        };
        for (const d of deltakere) legg(d.port, d.inn);
        return j;
    }

    function hentGjesteTaster() { return gjesteTaster.splice(0, gjesteTaster.length); }

    /* Med joystick etter tur gjelder det ogsaa tastene (mellomrom, E osv.):
     * bare den som har turen kan trykke ned en tast. Slipp gaar alltid gjennom. */
    function tastTillatt(spiller, ned, eiere) {
        if (!ned || portModus !== 'auto' || !eiere) return true;
        const e2 = eiere[1];
        if (e2 < 0) return true;
        let finnes = vertSpiller === e2;
        for (const g of gjester.values()) if (g.klar && g.spiller === e2) finnes = true;
        return !finnes || spiller === e2;
    }

    function vertensSpiller() { return vertSpiller; }

    /* etter hvert bilde: send inndataene og filene som ble brukt */
    /* kommandoer: menykommandoer (meny.c) som verten brukte foer dette bildet */
    function sendBilde(f, j, taster, filer, hentFil, sjekksum, kommandoer) {
        if (!gjester.size) return;
        for (const g of gjester.values()) {
            const m = { t: 'f', f, j };
            if (taster.length) m.k = taster;
            if (kommandoer && kommandoer.length) m.c = kommandoer;
            if (sjekksum !== undefined) m.h = sjekksum;
            const nye = filer.filter((p) => !g.filer.has(p));
            if (nye.length) {
                m.fil = [];
                for (const p of nye) {
                    const d = hentFil(p);
                    if (d) m.fil.push({ n: p, d: tilBuffer(d) });
                    g.filer.add(p);
                }
            }
            if (g.venter) g.ko.push(m);
            else if (g.conn.open) g.conn.send(m);
        }
    }

    function harGjester() { return gjester.size > 0; }

    /* ---------------------------------------------------------------- gjest */
    let vert = null;
    const rammer = [];
    let deler = null, sistInn = -1, sistSendt = 0;
    let ping = 0, pingTimer = null, sistFraVert = 0;
    const STILLE = 20000;                     /* ms uten svar fra verten for gjesten gir opp */

    function bliMed(romkode, navn, hendelser) {
        h = hendelser;
        mittNavn = navn || 'Gjest';
        rolle = 'gjest';
        kode = romkode.toUpperCase();
        return new Promise((ok, feil) => {
            peer = lagPeer(null);
            let aapnet = false;
            peer.on('open', () => {
                vert = peer.connect(PREFIKS + kode.toLowerCase(), { reliable: true });
                vert.on('open', () => {
                    aapnet = true;
                    sistFraVert = performance.now();
                    vert.send({ t: 'hei', navn: mittNavn, v: VERSJON });
                    /* WebRTC merker ikke alltid at verten er borte (lukket fane, tapt nett),
                     * saa gjesten gir opp naar verten ikke har svart paa en stund */
                    pingTimer = setInterval(() => {
                        if (performance.now() - sistFraVert > STILLE) {
                            clearInterval(pingTimer);
                            h.frakoblet && h.frakoblet('Verten svarer ikke lenger.');
                        } else if (vert && vert.open) vert.send({ t: 'ping', tid: performance.now() });
                    }, 2000);
                    ok();
                });
                vert.on('data', (d) => { sistFraVert = performance.now(); fraVert(d); });
                vert.on('close', () => { clearInterval(pingTimer); h.frakoblet && h.frakoblet('Forbindelsen til verten ble brutt.'); });
                vert.on('error', () => {});
            });
            peer.on('error', (e) => {
                if (e.type === 'peer-unavailable') feil(new Error('Fant ikke rommet ' + kode + '. Sjekk koden, eller om verten fortsatt er der.'));
                else if (!aapnet) feil(new Error(e.message || e.type));
                else h.status && h.status('Nettverksfeil: ' + (e.message || e.type));
            });
            setTimeout(() => { if (!aapnet) feil(new Error('Fikk ikke kontakt med verten.')); }, 20000);
        });
    }

    async function fraVert(d) {
        if (!d || typeof d !== 'object') return;
        switch (d.t) {
        case 'lobby': romSpill = d.spill || 'sammen'; h.lobby && h.lobby(d.spillere, d.kode, d.modus, romSpill); break;
        case 'ridder': h.ridder && h.ridder(d.fra, d); break;
        case 'tilstand': {
            if (!deler || deler.id !== d.id) deler = { id: d.id, n: d.n, f: d.f, z: d.z, biter: new Array(d.n), fatt: 0 };
            if (!deler.biter[d.i]) { deler.biter[d.i] = tilBytes(d.data); deler.fatt++; }
            h.status && h.status('Henter spillet fra verten ... ' + Math.round(deler.fatt / deler.n * 100) + ' %');
            if (deler.fatt === deler.n) {
                const total = deler.biter.reduce((s, b) => s + b.length, 0);
                const alt = new Uint8Array(total);
                let o = 0;
                for (const b of deler.biter) { alt.set(b, o); o += b.length; }
                const f = deler.f, z = deler.z;
                deler = null;
                rammer.length = 0;
                const bytes = await pakkUt(alt, z);
                h.tilstand && h.tilstand(bytes, f);
            }
            break;
        }
        case 'f':
            if (d.fil) for (const fil of d.fil) fil.d = tilBytes(fil.d);
            rammer.push(d);
            break;
        case 'chat': h.chat && h.chat(d.fra, d.tekst); break;
        case 'pong': ping = Math.round(performance.now() - d.tid); h.ping && h.ping(ping); break;
        case 'feil': h.feil && h.feil(d.tekst); break;
        case 'slutt': h.frakoblet && h.frakoblet('Verten avsluttet spillet.'); break;
        }
    }

    function sendInn(bits) {
        if (!vert || !vert.open) return;
        const naa = performance.now();
        if (bits !== sistInn || naa - sistSendt > 500) {
            vert.send({ t: 'inn', j: bits });
            sistInn = bits;
            sistSendt = naa;
        }
    }

    function sendTast(k, ned) { if (vert && vert.open) vert.send({ t: 'tast', k, ned }); }

    /* hver for seg: min ridder til de andre (verten sender til alle, en gjest til verten) */
    function sendRidder(r) {
        const m = Object.assign({ t: 'ridder' }, r);
        if (rolle === 'vert') sendAlle(Object.assign(m, { fra: 'vert' }));
        else if (vert && vert.open) vert.send(m);
    }
    function sendVelg(rad) { if (vert && vert.open) vert.send({ t: 'velg', rad }); }
    function beOmSynk() { if (vert && vert.open) vert.send({ t: 'synk' }); }

    /* ---------------------------------------------------------------- begge */
    function chat(tekst) {
        tekst = String(tekst).slice(0, 300);
        if (rolle === 'vert') { sendAlle({ t: 'chat', fra: mittNavn, tekst }); h.chat && h.chat(mittNavn, tekst); }
        else if (vert && vert.open) vert.send({ t: 'chat', tekst });
    }

    /* app.js faar ingen hendelser fra forbindelser som lukkes her */
    function avslutt() {
        h = {};
        if (rolle === 'vert') { sendAlle({ t: 'slutt' }); for (const g of gjester.values()) g.conn.close(); gjester.clear(); }
        if (vert) { vert.close(); vert = null; }
        clearInterval(pingTimer);
        if (peer) { peer.destroy(); peer = null; }
        rolle = null;
        romSpill = 'sammen';
        rammer.length = 0;
    }

    return {
        lagRom, bliMed, avslutt, chat, invitasjon, settPort, settSpiller, settModus, sendTilstand, porter, sendBilde,
        hentGjesteTaster, tastTillatt, vertensSpiller, harGjester, sendInn, sendTast, sendVelg, sendRidder, beOmSynk, spillere,
        romSpill: () => romSpill, minId: () => (rolle === 'vert' ? 'vert' : peer ? peer.id : null),
        rammer, rolle: () => rolle, kode: () => kode, ping: () => ping,
    };
})();
