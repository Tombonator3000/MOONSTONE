/*
 * grafikk.js - spillets egen grafikk paa nettsiden.
 *
 * Fonten fra tittelmenyen (bold.f), pilen (sel.cel), logoen (bold.f bilde 73)
 * og nattehimmelen med traerne (ch.piv) pakkes ut her fra spillfilen i kjernen,
 * saa sidemenyen, valgene paa kartet og knappene paa skjermen ser ut som resten
 * av spillet. Fargene er paletten til ch.piv, som er den tittelmenyen bruker.
 *
 * Formatene (se tools/moonfiles.py):
 *   LZ   en kontrollbyte med 8 flagg, hoyeste bit forst: 0 = en byte som den er,
 *        1 = to byte med 5 bit lengde (34 - n) og 11 bit avstand bakover
 *   PIV  ord plan, long pakket lengde, (1 << plan) palettord, LZ-data: plan for plan, 320 x 200
 *   CEL  ord antall, long pakket lengde, long minne, 10 byte per bilde (long offset,
 *        ord bredde, ord hoyde, byte flagg, byte planmaske), LZ-data. Hvert bilde
 *        plan for plan, bredden rundet opp til hele ord.
 *
 * Tekst tegnes ord for ord i smaa lerreter med spillets piksler (image-rendering:
 * pixelated), og nettleseren bryter linjene. Fonten har ikke ae, oe og aa, bindestrek,
 * kolon eller parenteser; de lages her av bokstavene som finnes, i samme stil.
 * Uten spillfilen (eller om noe feiler) blir teksten vanlig tekst.
 */
const Spillgrafikk = (() => {
    'use strict';
    let klar = false;
    let palett = null;                      /* 16 farger [r, g, b]; 0 er gjennomsiktig */
    const glyfer = [];                      /* bildene i bold.f: { w, h, px } */
    const laget = new Map();                /* tegn som er satt sammen (ae, oe, aa, -, :, ...) */
    let pilB = null, logoB = null, nattB = null;
    let enhet = 1;                          /* CSS-piksler per spillpiksel */
    const lerreter = new Set();             /* alle tekstlerreter, for ny storrelse */

    /* ---------------------------------------------------------------- formatene */
    const u16 = (d, i) => d[i] << 8 | d[i + 1];
    const u32 = (d, i) => (d[i] << 24 | d[i + 1] << 16 | d[i + 2] << 8 | d[i + 3]) >>> 0;

    function lz(d, s, slutt, maks) {
        const ut = new Uint8Array(maks);
        let n = 0;
        while (s < slutt && n < maks) {
            let ctl = d[s++];
            for (let i = 0; i < 8 && s < slutt && n < maks; i++, ctl <<= 1) {
                if (ctl & 0x80) {
                    const w = (d[s] << 8 | (d[s + 1] || 0));
                    s += 2;
                    const avstand = w & 0x7ff, lengde = 34 - (w >> 11);
                    for (let j = 0; j < lengde && n < maks; j++, n++) ut[n] = avstand > 0 && avstand <= n ? ut[n - avstand] : 0;
                } else ut[n++] = d[s++];
            }
        }
        return ut;
    }

    function amigaFarge(c) {
        c &= 0xfff;
        return [((c >> 8) & 15) * 17, ((c >> 4) & 15) * 17, (c & 15) * 17];
    }

    function piv(d) {
        const plan = u16(d, 0), plen = u32(d, 2), nc = 1 << plan;
        const pal = [];
        for (let i = 0; i < nc; i++) pal.push(amigaFarge(u16(d, 6 + i * 2)));
        const start = 6 + nc * 2;
        const bp = lz(d, start, start + plen, plan * 8000);
        const px = new Uint8Array(320 * 200);
        for (let p = 0; p < plan; p++) {
            const bit = 1 << p, base = p * 8000;
            for (let i = 0; i < 8000; i++) {
                const b = bp[base + i];
                if (!b) continue;
                const o = ((i / 40) | 0) * 320 + (i % 40) * 8;
                for (let k = 0; k < 8; k++) if (b & (0x80 >> k)) px[o + k] |= bit;
            }
        }
        return { pal, px };
    }

    function cel(d) {
        const n = u16(d, 0), plen = u32(d, 2);
        const tab = [];
        let total = 0;
        for (let i = 0; i < n; i++) {
            const e = 10 + i * 10, m = d[e + 9];
            let plan = 0;
            for (let b = m; b; b >>= 1) plan += b & 1;
            const t = { off: u32(d, e), w: u16(d, e + 4), h: u16(d, e + 6), plan };
            total = Math.max(total, t.off + ((t.w + 15) >> 4) * 2 * t.h * plan);
            tab.push(t);
        }
        const start = 10 + n * 10;
        const raw = lz(d, start, start + plen, total);
        return tab.map((t) => {
            const bpr = ((t.w + 15) >> 4) * 2, ps = bpr * t.h, px = new Uint8Array(t.w * t.h);
            for (let p = 0; p < t.plan; p++) {
                const bit = 1 << p;
                for (let y = 0; y < t.h; y++) {
                    const r = t.off + p * ps + y * bpr;
                    for (let x = 0; x < t.w; x++) if (raw[r + (x >> 3)] & (0x80 >> (x & 7))) px[y * t.w + x] |= bit;
                }
            }
            return { w: t.w, h: t.h, px };
        });
    }

    /* ---------------------------------------------------------------- tegn som mangler
     * Bokstavene er 19 punkter hoye: store fra rad 2, smaa fra rad 5, grunnlinjen
     * rundt rad 12. W = lys (9), g, G, b = gull og brunt (10-12), # = svart kant (5). */
    const KODER = { '.': 0, '#': 5, W: 9, g: 10, G: 11, b: 12, L: 1 };

    function fraTegning(linjer, y0, w) {
        const h = 19, px = new Uint8Array(w * h);
        linjer.forEach((l, i) => {
            for (let x = 0; x < l.length && x < w; x++) px[(y0 + i) * w + x] = KODER[l[x]] || 0;
        });
        return { w, h, px, adv: w - 1 };
    }

    /* b oppaa a, forskjovet dx (bare pikslene som ikke er tomme) */
    function legg(a, b, dx, dy, w) {
        const bredde = w || Math.max(a.w, dx + b.w);
        const g = { w: bredde, h: 19, px: new Uint8Array(bredde * 19), adv: Math.max(a.adv, dx + b.adv) };
        for (const [kilde, ox, oy] of [[a, 0, 0], [b, dx, dy || 0]]) {
            for (let y = 0; y < kilde.h; y++) {
                for (let x = 0; x < kilde.w; x++) {
                    const v = kilde.px[y * kilde.w + x], nx = x + ox, ny = y + oy;
                    if (v && nx >= 0 && nx < g.w && ny >= 0 && ny < 19) g.px[ny * g.w + nx] = v;
                }
            }
        }
        return g;
    }

    function lagTegn() {
        const G = (i) => glyfer[i];
        const ring = fraTegning(['.###.', '#WgW#', '#g#g#', '#WgW#', '.###.'], 0, 5);
        const ringLiten = fraTegning(['.###.', '#W#g#', '.###.'], 0, 5);
        const strek = (w, x0, y0, x1, y1) => {
            const t = { w, h: 19, px: new Uint8Array(w * 19), adv: w - 1 };
            const n = Math.max(Math.abs(x1 - x0), Math.abs(y1 - y0));
            for (let i = 0; i <= n; i++) {
                const x = Math.round(x0 + (x1 - x0) * i / n), y = Math.round(y0 + (y1 - y0) * i / n);
                t.px[y * w + x] = 9;
                if (x + 1 < w) t.px[y * w + x + 1] = t.px[y * w + x + 1] || 5;
            }
            return t;
        };
        laget.set('å', legg(G(26), ring, 3, 0));
        laget.set('Å', legg(G(0), ringLiten, 7, 0));
        laget.set('ø', legg(G(40), strek(12, 2, 13, 9, 4), 0, 0));
        laget.set('Ø', legg(G(14), strek(14, 2, 13, 11, 2), 0, 0));
        laget.set('æ', legg(G(26), G(30), 9, 0));
        laget.set('Æ', legg(G(0), G(4), 13, 0));
        laget.set('-', fraTegning(['.####..', '#WggG#.', '.#####.'], 8, 7));
        laget.set(':', legg(G(64), G(64), 0, -6));
        laget.set(';', legg(G(65), G(64), 0, -7));
        laget.set('(', fraTegning(['...##', '..#W#', '.#W#.', '#Wg#.', '#Wg#.', '#Wg#.', '#Wg#.', '#Wg#.', '.#G#.', '..#b#', '...##'], 3, 5));
        laget.set(')', fraTegning(['##...', '#W#..', '.#g#.', '.#gG#', '.#gG#', '.#gG#', '.#gG#', '.#gG#', '.#G#.', '#b#..', '##...'], 3, 5));
        laget.set('/', strek(9, 1, 14, 7, 2));
        laget.set('+', fraTegning(['..##...', '.#W#...', '##g###.', '#WggGb#', '.#G###.', '.#b#...', '..#....'], 5, 7));
        laget.set('"', legg(G(70), G(70), 5, 0));
        laget.set('«', laget.get('"'));
        laget.set('»', laget.get('"'));
        laget.set('…', legg(legg(G(64), G(64), 5, 0), G(64), 10, 0));
    }

    /* tegnet c som bilde; ukjente tegn blir tomme */
    const MELLOM = { w: 9, h: 19, px: new Uint8Array(9 * 19), adv: 9 };
    function glyf(c) {
        if (laget.has(c)) return laget.get(c);
        const k = c.charCodeAt(0);
        if (k >= 65 && k <= 90) return glyfer[k - 65];
        if (k >= 97 && k <= 122) return glyfer[k - 97 + 26];
        if (k >= 48 && k <= 57) return glyfer[k - 48 + 52];
        const andre = { '!': 62, '?': 63, '.': 64, ',': 65, '#': 66, '$': 67, '%': 68, "'": 70, '’': 70, '_': 71 };
        if (c in andre) return glyfer[andre[c]];
        const enkel = c.normalize('NFD').replace(/[̀-ͯ]/g, '');
        if (enkel !== c && enkel.length === 1) return glyf(enkel);
        return MELLOM;
    }

    /* ---------------------------------------------------------------- tegning */
    function tilLerret(bilde, pal) {
        const c = document.createElement('canvas');
        c.width = bilde.w;
        c.height = bilde.h;
        const ctx = c.getContext('2d');
        const id = ctx.createImageData(bilde.w, bilde.h);
        for (let i = 0; i < bilde.px.length; i++) {
            const v = bilde.px[i];
            if (!v) continue;
            const f = (pal || palett)[v] || [255, 0, 255];
            id.data.set([f[0], f[1], f[2], 255], i * 4);
        }
        ctx.putImageData(id, 0, 0);
        return c;
    }

    /* Spillet flytter seg bredden minus 3 for hver bokstav i bold.f ($089166), saa
     * skyggen til hoyre ligger under neste bokstav. Det samme her. */
    function ordBilde(ord) {
        const g = [...ord].map(glyf);
        let w = 1, x = 0;
        for (const t of g) { w = Math.max(w, x + t.w); x += t.adv; }
        const bilde = { w, h: 19, px: new Uint8Array(w * 19) };
        x = 0;
        for (const t of g) {
            for (let y = 0; y < 19 && y < t.h; y++) {
                for (let i = 0; i < t.w; i++) {
                    const v = t.px[y * t.w + i];
                    if (v) bilde.px[y * w + x + i] = v;
                }
            }
            x += t.adv;
        }
        return bilde;
    }

    function storrelse(c) {
        const s = (+c.dataset.skala || 1) * enhet;
        c.style.width = (c.width * s) + 'px';
        c.style.height = (c.height * s) + 'px';
        if (c.dataset.mellom) c.style.marginRight = (9 * s) + 'px';     /* mellomrommet etter ordet (spillet: 15 - 3) */
    }

    /* teksten i el med spillets font; skala 1 eller 2 */
    function sett(el, tekst, skala) {
        tekst = String(tekst == null ? '' : tekst);
        const noekkel = tekst + '|' + (skala || 1) + '|' + klar;
        if (el.dataset.ptNoekkel === noekkel) return;
        el.dataset.ptNoekkel = noekkel;
        el.dataset.ptTekst = tekst;
        for (const c of el.querySelectorAll('canvas')) lerreter.delete(c);
        if (!klar) { el.textContent = tekst; return; }
        el.textContent = '';
        el.classList.add('pt-klar');
        const ord = tekst.split(/\s+/).filter(Boolean);
        ord.forEach((o, i) => {
            const c = tilLerret(ordBilde(o));
            c.dataset.skala = String(skala || 1);
            if (i < ord.length - 1) c.dataset.mellom = '1';
            c.setAttribute('aria-hidden', 'true');
            storrelse(c);
            lerreter.add(c);
            el.appendChild(c);
            if (i < ord.length - 1) el.appendChild(document.createTextNode(' '));     /* her kan linjen brytes */
        });
        /* skjermlesere leser teksten, ikke bildene */
        const s = document.createElement('span');
        s.className = 'pt-tekst';
        s.textContent = tekst;
        el.appendChild(s);
    }

    /* alle elementer med klassen pt (eller pt2 for dobbel storrelse) under rot */
    function stil(rot) {
        for (const el of (rot || document).querySelectorAll('.pt, .pt2')) {
            const t = el.dataset.ptTekst != null ? el.dataset.ptTekst : el.textContent.trim();
            sett(el, t, el.classList.contains('pt2') ? 2 : 1);
        }
    }

    function oppdaterEnhet() {
        const dpr = window.devicePixelRatio || 1;
        const ny = Math.max(1, Math.round(dpr)) / dpr;
        const rot = document.documentElement.style;
        rot.setProperty('--pe', ny + 'px');
        /* nattehimmelen bak menyen: hele ganger, minst to, saa traerne gaar ut over kanten */
        const k = Math.max(2, Math.ceil(window.innerWidth / (320 * ny)));
        rot.setProperty('--natt-b', (320 * k * ny) + 'px');
        if (ny === enhet) return;
        enhet = ny;
        for (const c of lerreter) if (c.isConnected) storrelse(c); else lerreter.delete(c);
    }

    /* ---------------------------------------------------------------- oppstart */
    function last(hentFil) {
        try {
            const ch = hentFil('data/ch.piv'), bold = hentFil('data/bold.f'), sel = hentFil('data/sel.cel');
            if (!ch || !bold || !sel) return false;
            const natt = piv(ch);
            palett = natt.pal;
            const b = cel(bold);
            if (b.length < 74) return false;
            glyfer.length = 0;
            for (const g of b) glyfer.push(Object.assign(g, { adv: Math.max(1, g.w - 3) }));
            lagTegn();
            pilB = tilLerret(cel(sel)[0]);
            logoB = tilLerret(glyfer[73]);
            nattB = tilLerret({ w: 320, h: 200, px: natt.px }, natt.pal.map((f, i) => (i === 0 ? [0, 0, 34] : f)));
            klar = true;
        } catch (e) {
            console.warn('spillets grafikk kunne ikke brukes paa siden:', e);
            klar = false;
            return false;
        }
        oppdaterEnhet();
        window.addEventListener('resize', oppdaterEnhet);
        const rot = document.documentElement.style;
        rot.setProperty('--pil', 'url(' + pilB.toDataURL() + ')');
        rot.setProperty('--natt-bilde', 'url(' + nattB.toDataURL() + ')');
        document.documentElement.classList.add('spillgrafikk');
        return true;
    }

    /* et nytt lerret med pilen eller logoen, i spillets piksler */
    function kopi(kilde, skala) {
        const c = document.createElement('canvas');
        c.width = kilde.width;
        c.height = kilde.height;
        c.getContext('2d').drawImage(kilde, 0, 0);
        c.dataset.skala = String(skala || 1);
        c.setAttribute('aria-hidden', 'true');
        storrelse(c);
        lerreter.add(c);
        return c;
    }

    return {
        last, sett, stil,
        klar: () => klar,
        pil: (skala) => (pilB ? kopi(pilB, skala) : null),
        logo: (skala) => (logoB ? kopi(logoB, skala) : null),
        enhet: () => enhet,
        /* til tester og verktøy */
        _lz: lz, _piv: piv, _cel: cel,
    };
})();
