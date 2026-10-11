/* Standardgrafikken lastes fra samme utgivelse. Råbilder endres ikke.
 * Bare kjent grafikk aktiveres; resten beholdes som kandidater i art/photoreal.
 * Bakgrunner hentes ved behov, med høyst fire standardbakgrunner på GPU-en. */
const StandardHd = (() => {
    'use strict';
    const manifest = %%HD_MANIFEST%%;
    const base = manifest.files.filter(f => f.kind === 'base');
    const bakgrunner = new Map(manifest.files.filter(f => f.kind === 'background')
        .map(f => [f.path.slice(3, -4), f]));
    const cache = new Map(), avvist = new Set(), oppdrag = new Set();
    let V = null, meld = () => {}, aktiv = false, klar = false, lasterBakgrunn = false;
    let kontroller = null, sistHash = null, feil = null;

    function spor(p) {
        oppdrag.add(p);
        p.finally(() => oppdrag.delete(p)).catch(() => {});
        return p;
    }

    function info() {
        return { aktiv, klar, laster: oppdrag.size, feil, bilder: V ? V.hdAntall() : 0,
            bakgrunner: [...cache.keys()], tilgjengelige: manifest.images };
    }

    function status() {
        if (!aktiv) return;
        meld(feil ? 'HD kunne ikke lastes. Originalgrafikken brukes der bilder mangler.'
            : klar ? 'Standard-HD: ' + V.hdAntall() + ' bilder lastet. Bakgrunner lastes ved behov.'
            : 'Laster standardgrafikken ...');
    }

    async function hent(f, signal) {
        const r = await fetch('hd/' + f.path + '?v=' + f.sha256.slice(0, 16), { signal });
        if (!r.ok) throw new Error('HTTP ' + r.status);
        const bytes = await r.arrayBuffer();
        if (bytes.byteLength !== f.bytes) throw new Error('Feil fillengde');
        const digest = [...new Uint8Array(await crypto.subtle.digest('SHA-256', bytes))]
            .map(b => b.toString(16).padStart(2, '0')).join('');
        if (digest !== f.sha256) throw new Error('Feil bilderevisjon');
        const file = new File([bytes], f.path.split('/').pop(),
            { type: f.path.endsWith('.png') ? 'image/png' : 'application/json' });
        Object.defineProperty(file, 'webkitRelativePath', { value: 'standard/' + f.path });
        return file;
    }

    function oppdater(hash) {
        if (hash !== undefined && hash !== null) sistHash = (hash >>> 0).toString(16).padStart(8, '0');
        if (!aktiv || !klar || !V.hdPaa() || !sistHash || !bakgrunner.has(sistHash)) return;
        const key = sistHash;
        if (cache.has(key)) {
            const value = cache.get(key); cache.delete(key); cache.set(key, value);
            return;
        }
        if (lasterBakgrunn || avvist.has(key)) return;
        lasterBakgrunn = true;
        const signal = kontroller.signal;
        spor((async () => {
            try {
                const file = await hent(bakgrunner.get(key), signal);
                if (!aktiv || signal.aborted) return;
                const n = await V.lastHdPakke([file], true);
                if (n !== 1) throw new Error('Bildet kunne ikke dekodes');
                cache.set(key, true);
                while (cache.size > manifest.background_cache_limit) {
                    const eldste = cache.keys().next().value;
                    V.fjernHdBilde('bg/' + eldste);
                    cache.delete(eldste);
                }
            } catch (e) {
                if (!signal.aborted) { avvist.add(key); feil = e.message; }
            } finally {
                lasterBakgrunn = false;
                status();
                if (aktiv && sistHash !== key) oppdater();
            }
        })());
    }

    function start(visning, melding) {
        if (aktiv) return;
        V = visning;
        if (melding) meld = melding;
        if (!/^https?:$/.test(location.protocol)) {
            meld('Originalgrafikk. Åpne nettversjonen for standard-HD, eller velg en lokal HD-mappe.');
            return;
        }
        if (!V.hdPaa()) return;
        aktiv = true; klar = false; feil = null;
        cache.clear(); avvist.clear();
        kontroller = new AbortController();
        const signal = kontroller.signal;
        V.settTvungetLag(true);
        status();
        spor((async () => {
            try {
                const files = new Array(base.length);
                let neste = 0;
                await Promise.all(Array.from({ length: Math.min(4, base.length) }, async () => {
                    while (neste < base.length) {
                        const i = neste++;
                        files[i] = await hent(base[i], signal);
                    }
                }));
                if (!aktiv || signal.aborted) return;
                const n = await V.lastHdPakke(files);
                const poser = V.hdPoseInfo();
                if (n !== base.filter(f => f.path.endsWith('.png')).length || poser.antall !== 5 || poser.ugyldig || poser.feil.length)
                    throw new Error('Ufullstendig standardpakke');
                klar = true;
                oppdater(V.lagNaa()?.hash);
            } catch (e) {
                if (!signal.aborted) { feil = e.message; kontroller.abort(); }
            } finally { status(); }
        })());
    }

    /* Vent på eventuell teksturoppretting før egne filer får overta pakken. */
    async function stopp() {
        aktiv = false; klar = false;
        if (kontroller) kontroller.abort();
        await Promise.allSettled([...oppdrag]);
        if (V) V.settTvungetLag(false);
        cache.clear(); avvist.clear();
    }

    return { start, stopp, oppdater, info, scener: () => manifest.scenes || [] };
})();
