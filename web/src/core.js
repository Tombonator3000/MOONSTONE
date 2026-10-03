/*
 * core.js - innpakning rundt emulatorkjernen (WebAssembly, port/src/web.c).
 *
 * Kjernen kjorer originalkoden til Moonstone paa en emulert Amiga 500. Her er
 * bare smaa hjelpere for aa sende data inn og ut av minnet til WebAssembly.
 */
'use strict';

const Kjerne = (() => {
    let M = null;
    let fbW = 720, fbH = 288;

    /* lastes bare en gang, ogsaa om flere spor ber om den samtidig */
    let laster = null;
    function last() {
        if (!laster) {
            laster = MoonCore().then((m) => {
                M = m;
                fbW = M._ms_fb_w();
                fbH = M._ms_fb_h();
                return M;
            });
            laster.catch(() => { laster = null; });
        }
        return laster;
    }

    function kopierInn(bytes) {
        const p = M._malloc(bytes.length || 1);
        M.HEAPU8.set(bytes, p);
        return p;
    }

    function streng(s) {
        const n = M.lengthBytesUTF8(s) + 1;
        const p = M._malloc(n);
        M.stringToUTF8(s, p, n);
        return p;
    }

    /* spillfila som er bygget inn i kjernen (port/bin2c.py) */
    function harInnebygd() { return !!M._ms_has_embedded(); }
    function aapneInnebygd() {
        if (!M._ms_open_embedded()) throw new Error(M.UTF8ToString(M._ms_error()) || 'Den innebygde spillfilen kan ikke leses.');
    }

    /* andre spillfiler (zip eller ISO); kjernen tar over bufferet */
    function aapne(bytes) {
        const p = kopierInn(bytes);
        if (!M._ms_open_mem(p, bytes.length)) throw new Error(M.UTF8ToString(M._ms_error()));
    }

    function start(knappevent) {
        if (!M._ms_start(knappevent ? 1 : 0)) throw new Error(M.UTF8ToString(M._ms_error()) || 'Oppstart feilet');
    }

    function startSomGjest() {
        M._ms_guest();
        M._ms_start_empty();
    }

    function inndata(j0, j1) { M._ms_input(j0 | 0, j1 | 0); }
    function tast(kode, ned) { M._ms_key(kode | 0, ned ? 1 : 0); }
    function bilde() { M._ms_frame(); }

    function rammebuffer() {
        return new Uint8Array(M.HEAPU8.buffer, M._ms_fb(), fbW * fbH * 4);
    }

    function vindu() {
        const p = M._ms_diw() >> 2;
        return [M.HEAP32[p], M.HEAP32[p + 1], M.HEAP32[p + 2], M.HEAP32[p + 3]];
    }

    function lyd() {
        const n = M._ms_audio_frames();
        return new Int16Array(M.HEAP16.buffer, M._ms_audio(), n * 2);
    }

    function lagreTilstand() {
        const n = M._ms_state_save();
        if (!n) return null;
        return new Uint8Array(M.HEAPU8.buffer, M._ms_state_buf(), n).slice();
    }

    function lastTilstand(bytes) {
        const p = kopierInn(bytes);
        const ok = M._ms_state_load(p, bytes.length);
        M._free(p);
        return !!ok;
    }

    /* nettspill: filer spillet har brukt i dette bildet */
    function brukteFiler() {
        const n = M._ms_accessed_count();
        const ut = [];
        for (let i = 0; i < n; i++) ut.push(M.UTF8ToString(M._ms_accessed_name(i)));
        M._ms_accessed_clear();
        return ut;
    }

    function hentFil(sti) {
        const s = streng(sti);
        const p = M._ms_file_peek(s);
        M._free(s);
        if (!p) return null;
        return new Uint8Array(M.HEAPU8.buffer, p, M._ms_file_size()).slice();
    }

    function leggInnFil(sti, bytes) {
        const s = streng(sti);
        const p = kopierInn(bytes);
        M._ms_file_inject(s, p, bytes.length);
        M._free(p);
        M._free(s);
    }

    function fjernFil(sti) {
        const s = streng(sti);
        M._ms_file_remove(s);
        M._free(s);
    }

    /* figurene spillet tegnet i siste bilde: fil, bildenummer, x, y, bredde, hoyde, speilet */
    function tegneliste() {
        const n = M._ms_draw_count();
        if (!n) return [];
        const p = M._ms_draws(), st = M._ms_draw_size();
        const h = new Int16Array(M.HEAPU8.buffer, p, (n * st) >> 1);
        const ut = [];
        for (let i = 0; i < n; i++) {
            const o = (i * st) >> 1;
            ut.push({ fil: M.UTF8ToString(M._ms_cel_name(h[o])), bilde: h[o + 1], x: h[o + 2], y: h[o + 3], w: h[o + 4], h: h[o + 5], xoff: h[o + 6], speilet: h[o + 7] !== 0 });
        }
        return ut;
    }

    /* nettspill i tittelmenyen (port/src/meny.c) */
    function menyKommando(k, arg, tekst) {
        const t = tekst || '';
        const n = M.lengthBytesUTF8(t) + 1;
        const p = M._malloc(n);
        M.stringToUTF8(t, p, n);
        M._ms_menu_cmd(k, arg | 0, p);
        M._free(p);
    }

    return {
        menyPaa: (on) => M._ms_menu_enable(on ? 1 : 0),
        menyHendelse: () => M._ms_menu_event(),
        menyKlar: () => !!(M && M._ms_menu_ready()),     /* tittelmenyen er naadd (false mens kjernen lastes) */
        iIntro: () => !!(M && M._ms_in_intro()),
        iMeny: () => !!(M && M._ms_in_menu()),      /* tittelmenyen eller en nettspillside er framme */
        menyRad: (y) => M._ms_menu_row(y | 0),      /* raden paa linje y, -1 ikke i menyen, -2 ingen rad */
        menyKommando,
        /* hver for seg (port/src/hver.c) */
        hverKmd: (k, arg, tekst) => {
            const t = tekst || '', n = M.lengthBytesUTF8(t) + 1, p = M._malloc(n);
            M.stringToUTF8(t, p, n);
            M._ms_hver_cmd(k, arg | 0, p);
            M._free(p);
        },
        hverKart: () => !!(M && M._ms_hver_kart()),
        hverRidder: (k) => { const p = M._ms_hver_ridder(k) >> 2; return [M.HEAP32[p], M.HEAP32[p + 1], M.HEAP32[p + 2], M.HEAP32[p + 3]]; },
        hverNavn: (k) => M.UTF8ToString(M._ms_hver_navn(k)),
        hverHendelse: () => M._ms_hver_hendelse(),   /* kode | plass << 8, 0 = ingen */
        hverBlob: (k) => M.UTF8ToString(M._ms_hver_blob(k)),
        /* lagene (port/src/lag.c): bakgrunn og forgrunn, 320 x 200 RGBA, eller null */
        lagPaa: (on) => M._ms_lag_paa(on ? 1 : 0),
        lagBygg: () => M._ms_lag_bygg(),
        lag: () => {
            if (!M._ms_lag_gyldig()) return null;
            const n = 320 * 200 * 4;
            return {
                bak: new Uint8Array(M.HEAPU8.buffer, M._ms_lag_bak(), n),
                for: new Uint8Array(M.HEAPU8.buffer, M._ms_lag_for(), n),
                forIdx: new Uint8Array(M.HEAPU8.buffer, M._ms_lag_for_idx(), 320 * 200),
                hash: M._ms_lag_hash() >>> 0,
                lys: M._ms_lag_lys() >>> 0,
            };
        },
        last, aapne, harInnebygd, aapneInnebygd, start, startSomGjest, inndata, tast, bilde, rammebuffer, vindu, lyd,
        lagreTilstand, lastTilstand, brukteFiler, hentFil, leggInnFil, fjernFil,
        bredde: () => fbW, hoyde: () => fbH,
        bildeNr: () => M._ms_frame_no() >>> 0,
        hz: () => M._ms_hz(),
        sjekksum: () => M._ms_hash() >>> 0,
        stoppet: () => !!M._ms_aborted(),
        stoppMelding: () => M.UTF8ToString(M._ms_abort_msg()),
        volum: (v) => M._ms_volume(v),
        portSpillere: () => [M._ms_port_player(0), M._ms_port_player(1)],
        tegneliste,
        ridderNavn: (k) => M.UTF8ToString(M._ms_knight_name(k)),
        /* valgene paa kartet (tastene 1-9) og navnet som skrives etter Select a Knight (port/src/game.c) */
        kartValg: () => {
            const n = M._ms_valg_antall();
            if (!n) return null;
            const valg = [];
            for (let i = 0; i < n; i++) valg.push(M.UTF8ToString(M._ms_valg_tekst(i)));
            return { tittel: M.UTF8ToString(M._ms_valg_tittel()), valg };
        },
        navnAktiv: () => !!(M && M._ms_navn_aktiv()),
        navnKlar: () => !!(M && M._ms_navn_klar()),     /* lokka leser tastene akkurat naa */
        navn: () => M.UTF8ToString(M._ms_navn()),
        les8: (a) => M._ms_peek8(a),
        les16: (a) => M._ms_peek16(a),
    };
})();
