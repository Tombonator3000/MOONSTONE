/*
 * store.js - lagring i nettleseren.
 *
 * IndexedDB (database "moonstone", tabell "filer") har spillfilen (zip eller
 * ISO) og lagrede tilstander, plass 1-9. Innstillingene ligger i localStorage.
 * I nettspill er det verten som lagrer; gjestene lagrer ingenting.
 */
'use strict';

const Lager = (() => {
    let db = null;

    function aapne() {
        if (db) return Promise.resolve(db);
        return new Promise((ok, feil) => {
            let r;
            try { r = indexedDB.open('moonstone', 1); } catch (e) { feil(e); return; }
            r.onupgradeneeded = () => r.result.createObjectStore('filer');
            r.onsuccess = () => { db = r.result; ok(db); };
            r.onerror = () => feil(r.error);
        });
    }

    async function hent(nokkel) {
        try {
            const d = await aapne();
            return await new Promise((ok, feil) => {
                const r = d.transaction('filer').objectStore('filer').get(nokkel);
                r.onsuccess = () => ok(r.result);
                r.onerror = () => feil(r.error);
            });
        } catch (e) { return undefined; }
    }

    async function sett(nokkel, verdi) {
        try {
            const d = await aapne();
            await new Promise((ok, feil) => {
                const t = d.transaction('filer', 'readwrite');
                t.objectStore('filer').put(verdi, nokkel);
                t.oncomplete = ok;
                t.onerror = () => feil(t.error);
            });
            return true;
        } catch (e) { return false; }
    }

    async function slett(nokkel) {
        try {
            const d = await aapne();
            await new Promise((ok) => {
                const t = d.transaction('filer', 'readwrite');
                t.objectStore('filer').delete(nokkel);
                t.oncomplete = ok;
                t.onerror = ok;
            });
        } catch (e) { /* ingen lagring */ }
    }

    function innstillinger() {
        try { return JSON.parse(localStorage.getItem('moonstone.innstillinger') || '{}'); }
        catch (e) { return {}; }
    }

    function lagreInnstillinger(v) {
        try { localStorage.setItem('moonstone.innstillinger', JSON.stringify(v)); } catch (e) { /* privat vindu */ }
    }

    return { hent, sett, slett, innstillinger, lagreInnstillinger };
})();
