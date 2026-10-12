/* Standardgrafikken lastes fra samme utgivelse. Råbilder endres ikke.
 * Bare kjent grafikk aktiveres; resten beholdes som kandidater i art/photoreal.
 * Bakgrunner hentes ved behov, med høyst fire standardbakgrunner på GPU-en. */
const StandardHd = (() => {
    'use strict';
    const manifest = %%HD_MANIFEST%%;
    const base = manifest.files.filter(f => f.kind === 'base');
    /* 045a1ac5 er hashen av en helt tom bakgrunnskopi (40000 nullbyte). Den staar
     * paa alle tomme skjermer og i alle overganger, saa et bilde der ville dekke
     * meldinger, lasteskjermen og toningene. Den faar aldri HD, heller ikke om
     * noen legger den i manifestet. pakk.py nekter den ogsaa. */
    const TOM_BAKGRUNN = '045a1ac5';
    const bakgrunner = new Map(manifest.files.filter(f => f.kind === 'background')
        .map(f => [f.path.slice(3, -4), f]).filter(([hash]) => hash !== TOM_BAKGRUNN));
    const scener = (manifest.scenes || []).filter(s => s.hash !== TOM_BAKGRUNN);
    const cache = new Map(), avvist = new Set(), oppdrag = new Set(), bakgrunnForsok = new Map();
    let V = null, meld = () => {}, aktiv = false, klar = false, lasterBakgrunn = false;
    let kontroller = null, baseKontroller = null, sistHash = null, baseFeil = null, bakgrunnFeil = null;
    let importKo = Promise.resolve(), provIgjen = null, provHash = null;

    function spor(p) {
        oppdrag.add(p);
        p.finally(() => oppdrag.delete(p)).catch(() => {});
        return p;
    }

    function info() {
        return { aktiv, klar, laster: oppdrag.size, feil: baseFeil || bakgrunnFeil, bilder: V ? V.hdAntall() : 0,
            bakgrunner: [...cache.keys()], tilgjengelige: manifest.images };
    }

    /* Er HD slaatt av, viser siden at HD er av, selv om lastingen fortsetter */
    function status() {
        if (!aktiv || !V.hdPaa()) return;
        /* meld faar norsk kildetekst og verdier; siden oversetter (sprak.js) */
        meld(baseFeil || bakgrunnFeil ? 'HD kunne ikke lastes. Originalgrafikken brukes der bilder mangler.'
            : klar ? 'Standard-HD: {0} bilder lastet. Bakgrunner lastes ved behov.'
            : 'Laster standardgrafikken ...', V.hdAntall());
    }

    async function hent(f, signal) {
        const r = await fetch('hd/' + f.path + '?v=' + f.sha256.slice(0, 16), { signal });
        if (!r.ok) {
            const e = new Error('HTTP ' + r.status);
            e.midlertidig = r.status === 408 || r.status === 429 || r.status >= 500;
            throw e;
        }
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

    const midlertidig = e => e.midlertidig || e instanceof TypeError;

    // De mange figurfilene skal ogsaa taale en kort nettfeil. SHA og lengde
    // kontrolleres paa hvert forsoek; en feil utgivelse blir aldri godkjent.
    async function hentBase(f, signal) {
        for (let forsok = 1; ; forsok++) {
            try { return await hent(f, signal); }
            catch (e) {
                if (signal.aborted || !midlertidig(e) || forsok >= 3) throw e;
                await new Promise((resolve, reject) => {
                    const ferdig = () => { signal.removeEventListener('abort', avbrutt); resolve(); };
                    const timer = setTimeout(ferdig, 500 * forsok);
                    const avbrutt = () => { clearTimeout(timer); reject(new DOMException('Avbrutt', 'AbortError')); };
                    signal.addEventListener('abort', avbrutt, { once: true });
                    if (signal.aborted) avbrutt();
                });
            }
        }
    }

    // Bakgrunnen kan bli klar mens figurpakken fremdeles hentes. Selve importen
    // er sekvensiell, saa metadata og teksturer ikke endres av to pakker samtidig.
    function importer(files, signal) {
        const p = importKo.then(() => aktiv && !signal.aborted ? V.lastHdPakke(files) : 0);
        importKo = p.catch(() => {});
        return p;
    }

    function oppdater(hash) {
        if (hash !== undefined && hash !== null) sistHash = (hash >>> 0).toString(16).padStart(8, '0');
        if (!aktiv || !V.hdPaa() || !sistHash || !bakgrunner.has(sistHash)) return;
        const key = sistHash;
        if (provIgjen && provHash !== key) { clearTimeout(provIgjen); provIgjen = null; provHash = null; }
        if (cache.has(key)) {
            const value = cache.get(key); cache.delete(key); cache.set(key, value);
            return;
        }
        if (lasterBakgrunn || avvist.has(key) || provIgjen) return;
        lasterBakgrunn = true;
        const signal = kontroller.signal;
        bakgrunnForsok.set(key, (bakgrunnForsok.get(key) || 0) + 1);
        spor((async () => {
            try {
                const file = await hent(bakgrunner.get(key), signal);
                if (!aktiv || signal.aborted) return;
                const n = await importer([file], signal);
                if (n !== 1) throw new Error('Bildet kunne ikke dekodes');
                cache.set(key, true);
                bakgrunnForsok.delete(key);
                bakgrunnFeil = null;
                while (cache.size > manifest.background_cache_limit) {
                    const eldste = cache.keys().next().value;
                    V.fjernHdBilde('bg/' + eldste);
                    cache.delete(eldste);
                }
            } catch (e) {
                if (!signal.aborted) {
                    bakgrunnFeil = e.message;
                    // En kort nettfeil skal ikke fjerne HD resten av oekten.
                    // Feil bytes eller SHA avvises fortsatt uten nytt forsoek.
                    if (midlertidig(e) && bakgrunnForsok.get(key) < 3) {
                        provHash = key;
                        provIgjen = setTimeout(() => { provIgjen = null; provHash = null; oppdater(); }, 500 * bakgrunnForsok.get(key));
                    } else avvist.add(key);
                }
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
        aktiv = true; klar = false; baseFeil = null; bakgrunnFeil = null;
        cache.clear(); avvist.clear(); bakgrunnForsok.clear();
        kontroller = new AbortController();
        baseKontroller = new AbortController();
        const signal = baseKontroller.signal;
        V.settTvungetLag(true);
        oppdater(V.lagNaa()?.hash);
        status();
        spor((async () => {
            try {
                const files = new Array(base.length);
                // Menytekst/pil og riddervalg trengs foer monsterbankene. Hver
                // gruppe importeres komplett, med uendret kilde-/SHA-kontroll.
                const gruppe = f => /^(text\.json$|bold\.f\/|small\.font\/|sel\.cel\/00[01]\.png$)/i.test(f.path) ? 0
                    : /^sel\.cel\//i.test(f.path) ? 1 : 2;
                let n = 0;
                for (let g = 0; g < 3; g++) {
                    const indekser = base.map((f, i) => gruppe(f) === g ? i : -1).filter(i => i >= 0);
                    let neste = 0;
                    await Promise.all(Array.from({ length: Math.min(4, indekser.length) }, async () => {
                        while (neste < indekser.length) {
                            const i = indekser[neste++];
                            files[i] = await hentBase(base[i], signal);
                        }
                    }));
                    if (!aktiv || signal.aborted) return;
                    if (indekser.length) n += await importer(indekser.map(i => files[i]), signal);
                }
                const poser = V.hdPoseInfo(), poseFil = base.findIndex(f => f.path === 'poses.json');
                const poseListe = poseFil < 0 ? [] : JSON.parse(await files[poseFil].text()).poses;
                if (!Array.isArray(poseListe)) throw new Error('Ugyldig posemanifest');
                if (n !== base.filter(f => f.path.endsWith('.png')).length || poser.antall !== poseListe.length || poser.ugyldig || poser.feil.length)
                    throw new Error('Ufullstendig standardpakke');
                klar = true;
                oppdater(V.lagNaa()?.hash);
            } catch (e) {
                // En ugyldig figurpakke avbryter bare sine egne arbeidere.
                // Nye, kildeverifiserte bakgrunner kan fremdeles lastes.
                if (!signal.aborted) { baseFeil = e.message; baseKontroller.abort(); }
            } finally { status(); }
        })());
    }

    /* Vent på eventuell teksturoppretting før egne filer får overta pakken. */
    async function stopp() {
        aktiv = false; klar = false;
        if (kontroller) kontroller.abort();
        if (baseKontroller) baseKontroller.abort();
        if (provIgjen) clearTimeout(provIgjen);
        provIgjen = null; provHash = null;
        await Promise.allSettled([...oppdrag]);
        if (V) V.settTvungetLag(false);
        cache.clear(); avvist.clear(); bakgrunnForsok.clear();
    }

    /* Bakgrunner som bare dekker en del av skjermen: scenene med et mindre rektangel
     * (byene og kroen), eller "partial": true i filoppfoeringen. De vises bare med
     * rektangelet fra et scenetreff (render.js). */
    function utsnitt() {
        const liste = new Set();
        for (const s of scener) {
            const r = s.rect || [0, 0, 320, 200];
            if (r[0] > 0 || r[1] > 0 || r[2] < 320 || r[3] < 200) liste.add(parseInt(s.hash, 16));
        }
        for (const f of bakgrunner.values()) if (f.partial) liste.add(parseInt(f.path.slice(3, -4), 16));
        return [...liste];
    }

    return { start, stopp, oppdater, info, status, utsnitt, scener: () => scener };
})();
