/*
 * input.js - tastatur, spillkontrollere og berøringsknapper.
 *
 * Tastaturet sendes til Amigaen som det er (koder etter KeyboardEvent.code, saa
 * det virker likt paa alle tastaturoppsett), unntatt tastene som er joystick.
 * Som standard:
 *
 *   joystick A: piltastene og Ctrl (fire)          (spiller 1, port 2 naar du spiller alene)
 *   joystick B: talltastaturet 8 2 4 6 og 0 (fire)  (spiller 2, port 1 naar du spiller alene)
 *
 * Spillkontrollere: den forste er joystick A, den andre joystick B. Knappene er
 * som CD32-padden i cd32load-oppsettet paa ISO-en: A = fire, B = mellomrom
 * (inventar), Start = E (avslutt turen), X/Y = 3/4, LB/RB = 1/2, Back = Esc.
 *
 * Oppsettet kan endres (Options i spillets tittelmeny, se app.js): fire-tasten
 * og bevegelsen for hver joystick, og hvilke knapper paa spillkontrolleren som er
 * fire, inventar, avslutt turen og Esc. fang() venter paa neste tast eller knapp.
 *
 * Bitene er de samme som i kjernen: 1 opp, 2 ned, 4 venstre, 8 hoyre, 16 fire.
 */
'use strict';

const Inndata = (() => {
    const OPP = 1, NED = 2, VENSTRE = 4, HOYRE = 8, FIRE = 16;

    const amiga = {
        Backquote: 0x00, Digit1: 0x01, Digit2: 0x02, Digit3: 0x03, Digit4: 0x04, Digit5: 0x05,
        Digit6: 0x06, Digit7: 0x07, Digit8: 0x08, Digit9: 0x09, Digit0: 0x0a, Minus: 0x0b,
        Equal: 0x0c, Backslash: 0x0d, KeyQ: 0x10, KeyW: 0x11, KeyE: 0x12, KeyR: 0x13, KeyT: 0x14,
        KeyY: 0x15, KeyU: 0x16, KeyI: 0x17, KeyO: 0x18, KeyP: 0x19, BracketLeft: 0x1a,
        BracketRight: 0x1b, KeyA: 0x20, KeyS: 0x21, KeyD: 0x22, KeyF: 0x23, KeyG: 0x24, KeyH: 0x25,
        KeyJ: 0x26, KeyK: 0x27, KeyL: 0x28, Semicolon: 0x29, Quote: 0x2a, IntlBackslash: 0x30,
        KeyZ: 0x31, KeyX: 0x32, KeyC: 0x33, KeyV: 0x34, KeyB: 0x35, KeyN: 0x36, KeyM: 0x37,
        Comma: 0x38, Period: 0x39, Slash: 0x3a, Space: 0x40, Backspace: 0x41, Tab: 0x42,
        NumpadEnter: 0x43, Enter: 0x44, Escape: 0x45, Delete: 0x46, NumpadSubtract: 0x4a,
        NumpadDecimal: 0x3c, NumpadDivide: 0x5c, NumpadMultiply: 0x5d, NumpadAdd: 0x5e,
        F1: 0x50, F2: 0x51, F3: 0x52, F4: 0x53, F5: 0x54, F6: 0x55, F7: 0x56, F8: 0x57, F9: 0x58, F10: 0x59,
        ShiftLeft: 0x60, ShiftRight: 0x61, CapsLock: 0x62, AltLeft: 0x64, AltRight: 0x65,
        MetaLeft: 0x66, MetaRight: 0x67, Insert: 0x5f,
    };

    /* bevegelsen kan vaere et av disse oppsettene */
    const FLYTT = {
        piler: { ArrowUp: OPP, ArrowDown: NED, ArrowLeft: VENSTRE, ArrowRight: HOYRE },
        wasd: { KeyW: OPP, KeyS: NED, KeyA: VENSTRE, KeyD: HOYRE },
        ijkl: { KeyI: OPP, KeyK: NED, KeyJ: VENSTRE, KeyL: HOYRE },
        numpad: {
            Numpad8: OPP, Numpad2: NED, Numpad4: VENSTRE, Numpad6: HOYRE,
            Numpad7: OPP | VENSTRE, Numpad9: OPP | HOYRE, Numpad1: NED | VENSTRE, Numpad3: NED | HOYRE,
        },
    };
    const FLYTT_NAVN = { piler: 'Arrows', wasd: 'WASD', ijkl: 'IJKL', numpad: 'Keypad' };
    /* knappene paa spillkontrolleren: fire, inventar (mellomrom), avslutt turen (E), Esc */
    const PAD_TASTER = [null, 0x40, 0x12, 0x45];
    const PAD_NAVN = ['A', 'B', 'X', 'Y', 'LB', 'RB', 'LT', 'RT', 'Back', 'Start', 'L3', 'R3', 'Up', 'Down', 'Left', 'Right', 'Home'];
    /* tastene siden selv bruker, og Esc (avbryter), kan ikke bli joystick */
    const RESERVERT = new Set(['Home', 'PageUp', 'PageDown', 'End', 'Pause', 'Escape', 'F11', 'F12']);

    const forvalg = () => ({
        fire1: ['ControlLeft', 'ControlRight'], flytt1: 'piler',
        fire2: ['Numpad0', 'Numpad5'], flytt2: 'numpad',
        pad: [0, 1, 9, 8],
    });
    let oppsett = forvalg();
    let joyA = {}, joyB = {}, padTaster = {};

    /* bygger tabellene fra oppsettet; joystick A vinner om en tast er i begge */
    function settOppsett(o) {
        const f = forvalg();
        o = o || {};
        oppsett = {
            fire1: Array.isArray(o.fire1) && o.fire1.length ? o.fire1.slice(0, 2) : f.fire1,
            flytt1: FLYTT[o.flytt1] ? o.flytt1 : f.flytt1,
            fire2: Array.isArray(o.fire2) && o.fire2.length ? o.fire2.slice(0, 2) : f.fire2,
            flytt2: FLYTT[o.flytt2] ? o.flytt2 : f.flytt2,
            pad: Array.isArray(o.pad) && o.pad.length === 4 && o.pad.every((k) => Number.isInteger(k) && k >= 0 && k < 32) ? o.pad.slice() : f.pad,
        };
        joyA = Object.assign({}, FLYTT[oppsett.flytt1]);
        for (const c of oppsett.fire1) joyA[c] = FIRE;
        joyB = {};
        for (const [c, b] of Object.entries(FLYTT[oppsett.flytt2])) if (!(c in joyA)) joyB[c] = b;
        for (const c of oppsett.fire2) if (!(c in joyA)) joyB[c] = FIRE;
        /* tallene 1-4 ligger paa LB, RB, X og Y, om ikke knappen er tatt til noe annet */
        padTaster = {};
        for (const [k, t] of [[4, 0x01], [5, 0x02], [2, 0x03], [3, 0x04]]) if (!oppsett.pad.includes(k)) padTaster[k] = t;
        for (let i = 1; i < 4; i++) padTaster[oppsett.pad[i]] = PAD_TASTER[i];
        /* nede toemmes ikke: en tast som holdes, skal fortsatt slippes til Amigaen */
        kort.clear();
        return oppsett;
    }

    function tastNavn(c) {
        const navn = {
            ControlLeft: 'Ctrl', ControlRight: 'Ctrl', ShiftLeft: 'Shift', ShiftRight: 'Shift', AltLeft: 'Alt', AltRight: 'Alt Gr',
            MetaLeft: 'Meta', MetaRight: 'Meta', Space: 'Space', Enter: 'Return', NumpadEnter: 'Enter', Backspace: 'Backspace',
            Tab: 'Tab', CapsLock: 'Caps Lock', ArrowUp: 'Up', ArrowDown: 'Down', ArrowLeft: 'Left', ArrowRight: 'Right',
            Delete: 'Del', Insert: 'Ins', Comma: ',', Period: '.', Slash: '/', Semicolon: ';', Quote: "'", Minus: '-', Equal: '=',
            BracketLeft: '[', BracketRight: ']', Backslash: '\\', IntlBackslash: '<', Backquote: 'Tilde',
            NumpadAdd: 'Num +', NumpadSubtract: 'Num -', NumpadMultiply: 'Num *', NumpadDivide: 'Num /', NumpadDecimal: 'Num .',
        };
        if (navn[c]) return navn[c];
        let m = /^Key([A-Z])$/.exec(c);
        if (m) return m[1];
        if ((m = /^Digit(\d)$/.exec(c))) return m[1];
        if ((m = /^Numpad(\d)$/.exec(c))) return 'Num ' + m[1];
        return String(c).replace(/(Left|Right)$/, '');
    }
    const padNavn = (k) => PAD_NAVN[k] || 'Button ' + k;

    /* navnene til menyen: fire og bevegelse for joystick A og B, saa knappene */
    function oppsettNavn() {
        return [tastNavn(oppsett.fire1[0]), FLYTT_NAVN[oppsett.flytt1], tastNavn(oppsett.fire2[0]), FLYTT_NAVN[oppsett.flytt2]]
            .concat(oppsett.pad.map(padNavn));
    }

    /* naar en tast eller knapp skal velges: neste trykk gaar til cb (null = avbrutt) */
    let fanger = null;
    let stille = false;                     /* etter et valg: ingenting til alt er sluppet */
    function fang(type, cb) {
        fanger = { type, cb: (k) => { stille = true; cb(k); }, holdt: new Set(padKnapper()) };
    }
    function avbrytFang() { if (fanger) stille = true; fanger = null; }

    /* knappene som er nede paa den forste spillkontrolleren */
    function padKnapper() {
        const pads = navigator.getGamepads ? navigator.getGamepads() : [];
        for (const g of pads) {
            if (!g || !g.connected) continue;
            const ut = [];
            g.buttons.forEach((b, i) => { if (b && b.pressed) ut.push(i); });
            return ut;
        }
        return [];
    }

    /* kalles hvert skjermbilde mens en knapp skal velges: ny knapp ned = valgt */
    function sjekkFang() {
        const f = fanger;
        if (!f || f.type !== 'pad') return;
        const trykket = padKnapper();
        for (const k of [...f.holdt]) if (!trykket.includes(k)) f.holdt.delete(k);     /* sluppet: kan velges igjen */
        const ny = trykket.find((k) => !f.holdt.has(k));
        if (ny === undefined) return;
        fanger = null;
        f.cb(ny);
    }

    const nede = new Set();
    const kort = new Set();                 /* joysticktaster trykket siden sist, ogsaa om de er sluppet */
    const tasteKo = [];                     /* [kode, ned] siden sist */
    let touchA = 0;
    let aktiv = false;                      /* bare naar spillet vises */
    let hurtig = null;                      /* taster siden selv bruker (meny osv.) */
    const padForrige = [{}, {}];

    function paa(on) {
        aktiv = on;
        if (!on) { nede.clear(); kort.clear(); tasteKo.length = 0; }
    }

    function tastNed(e) {
        if (!aktiv) return;
        if (fanger) {
            /* en tast skal velges: den gaar ikke til spillet */
            e.preventDefault();
            if (e.repeat) return;
            const f = fanger;
            if (e.code === 'Escape') { fanger = null; f.cb(null); return; }
            if (f.type !== 'tast' || RESERVERT.has(e.code)) return;
            fanger = null;
            f.cb(e.code);
            return;
        }
        if (hurtig && hurtig(e)) { e.preventDefault(); return; }
        if (e.repeat) { e.preventDefault(); return; }
        const c = e.code;
        if (c in joyA || c in joyB) { nede.add(c); kort.add(c); e.preventDefault(); return; }
        if (c in amiga) {
            nede.add(c);
            tasteKo.push([amiga[c], true]);
            e.preventDefault();
        }
    }

    function tastOpp(e) {
        if (!aktiv) return;
        const c = e.code;
        if (!nede.has(c)) return;
        nede.delete(c);
        if (c in amiga) tasteKo.push([amiga[c], false]);
        e.preventDefault();
    }

    function sluppAlt() {
        for (const c of nede) if (c in amiga) tasteKo.push([amiga[c], false]);
        nede.clear();
    }

    window.addEventListener('keydown', tastNed);
    window.addEventListener('keyup', tastOpp);
    window.addEventListener('blur', sluppAlt);

    function pad(i) {
        const pads = navigator.getGamepads ? navigator.getGamepads() : [];
        let n = 0;
        for (const g of pads) {
            if (!g || !g.connected) continue;
            if (n++ !== i) continue;
            let b = 0;
            const ax = g.axes[0] || 0, ay = g.axes[1] || 0;
            const k = (j) => g.buttons[j] && g.buttons[j].pressed;
            if (ay < -0.4 || k(12)) b |= OPP;
            if (ay > 0.4 || k(13)) b |= NED;
            if (ax < -0.4 || k(14)) b |= VENSTRE;
            if (ax > 0.4 || k(15)) b |= HOYRE;
            if (k(oppsett.pad[0])) b |= FIRE;
            /* de andre knappene er taster, som CD32-padden */
            const forr = padForrige[i];
            for (const j in padTaster) {
                const p = !!k(+j);
                if (p !== !!forr[j]) tasteKo.push([padTaster[j], p]);
                forr[j] = p;
            }
            return b;
        }
        return 0;
    }

    /* joystick A og B akkurat naa; et trykk som er sluppet foer bildet, teller ett bilde */
    function les() {
        if (stille) {
            /* knappen eller tasten som ble valgt, er kanskje fortsatt nede: den skal
             * ikke bli et fire eller et valg i menyen foer den er sluppet */
            const trykket = padKnapper();
            const forr = padForrige[0];
            for (const k in forr) forr[k] = trykket.includes(+k);
            for (const k of trykket) forr[k] = true;
            kort.clear();
            let joy = false;
            for (const c of nede) if (c in joyA || c in joyB) joy = true;
            if (trykket.length || joy) return { a: 0, b: 0 };
            stille = false;
        }
        let a = touchA, b = 0;
        for (const c of nede) kort.add(c);
        for (const c of kort) {
            if (c in joyA) a |= joyA[c];
            if (c in joyB) b |= joyB[c];
        }
        kort.clear();
        a |= pad(0);
        b |= pad(1);
        return { a, b };
    }

    function hentTaster() {
        return tasteKo.splice(0, tasteKo.length);
    }

    /* berøringsknapper: et styrekors og noen knapper */
    function lagTouch(rot) {
        const kors = rot.querySelector('.kors');
        const sett = (bit, on) => { touchA = on ? (touchA | bit) : (touchA & ~bit); };
        const retning = (ev) => {
            const r = kors.getBoundingClientRect();
            const x = (ev.clientX - r.left) / r.width - 0.5, y = (ev.clientY - r.top) / r.height - 0.5;
            let b = 0;
            if (Math.hypot(x, y) > 0.12) {
                const v = Math.atan2(y, x);
                const s = Math.PI / 8;
                if (v > -7 * s && v < -s) b |= OPP;
                if (v > s && v < 7 * s) b |= NED;
                if (v > 5 * s || v < -5 * s) b |= VENSTRE;
                if (v > -3 * s && v < 3 * s) b |= HOYRE;
            }
            touchA = (touchA & FIRE) | b;
        };
        kors.addEventListener('pointerdown', (e) => { kors.setPointerCapture(e.pointerId); retning(e); e.preventDefault(); });
        kors.addEventListener('pointermove', (e) => { if (e.buttons || e.pointerType === 'touch') retning(e); });
        const slipp = () => { touchA &= FIRE; };
        kors.addEventListener('pointerup', slipp);
        kors.addEventListener('pointercancel', slipp);
        for (const knapp of rot.querySelectorAll('[data-knapp]')) {
            const hva = knapp.dataset.knapp;
            let trykket = false;
            const ned = (e) => {
                e.preventDefault();
                trykket = true;
                if (hva === 'fire') sett(FIRE, true);
                else tasteKo.push([parseInt(hva, 16), true]);
            };
            const opp = (e) => {
                e.preventDefault();
                if (!trykket) return;
                trykket = false;
                if (hva === 'fire') sett(FIRE, false);
                else tasteKo.push([parseInt(hva, 16), false]);
            };
            knapp.addEventListener('pointerdown', ned);
            knapp.addEventListener('pointerup', opp);
            knapp.addEventListener('pointercancel', opp);
            knapp.addEventListener('pointerleave', opp);
        }
    }

    function settHurtigtaster(fn) { hurtig = fn; }
    const holdt = (kode) => nede.has(kode);

    settOppsett(null);

    return {
        les, hentTaster, paa, lagTouch, settHurtigtaster, holdt, OPP, NED, VENSTRE, HOYRE, FIRE,
        settOppsett, oppsett: () => JSON.parse(JSON.stringify(oppsett)), forvalg, oppsettNavn, tastNavn, padNavn,
        fang, avbrytFang, sjekkFang, fanger: () => !!fanger, flyttValg: Object.keys(FLYTT),
    };
})();
