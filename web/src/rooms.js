/*
 * rooms.js - liste over offentlige rom, via MQTT hos HiveMQ (valgfritt).
 *
 * Gratis PeerJS Cloud viser ikke hvem som er paa, saa offentlige rom legges ut
 * som en "retained" melding hos den gratis MQTT-megleren til HiveMQ, slik som i
 * Guild Life. Hvert rom har sitt eget emne. Meldingen gaar ut paa tid etter fem
 * minutter hvis verten forsvinner, og verten sletter den naar spillet slutter.
 * Invitasjonslenker virker uten dette.
 */
'use strict';

const Romliste = (() => {
    const MEGLER = 'wss://broker.hivemq.com:8884/mqtt';
    const TEMA = 'moonstone-ms/v1/rom/';
    const LEVETID = 300;
    let klient = null;

    function kobl() {
        if (klient) return klient;
        if (typeof mqtt === 'undefined') throw new Error('MQTT er ikke lastet');
        klient = mqtt.connect(MEGLER, {
            protocolVersion: 5, clean: true, connectTimeout: 10000, reconnectPeriod: 5000,
            clientId: 'moonstone_' + Math.random().toString(16).slice(2, 10),
        });
        return klient;
    }

    /* verten legger ut rommet og oppdaterer det hvert minutt; returnerer stopp() */
    function annonser(hentInfo) {
        let c;
        try { c = kobl(); } catch (e) { return () => {}; }
        const legg = () => {
            const info = hentInfo();
            info.tid = Date.now();
            c.publish(TEMA + info.kode, JSON.stringify(info), { retain: true, qos: 1, properties: { messageExpiryInterval: LEVETID } });
        };
        if (c.connected) legg(); else c.once('connect', legg);
        const t = setInterval(legg, 60000);
        return () => {
            clearInterval(t);
            const info = hentInfo();
            try { c.publish(TEMA + info.kode, '', { retain: true, qos: 1 }); } catch (e) { /* frakoblet */ }
        };
    }

    /* lytter paa alle rom; cb faar en liste sortert med nyeste forst */
    function lytt(cb) {
        let c;
        try { c = kobl(); } catch (e) { cb([], e.message); return () => {}; }
        const rom = new Map();
        const vis = () => {
            const grense = Date.now() - LEVETID * 1000;
            cb([...rom.values()].filter((r) => r.tid > grense).sort((a, b) => b.tid - a.tid));
        };
        const paaMelding = (tema, data) => {
            if (!tema.startsWith(TEMA)) return;
            const k = tema.slice(TEMA.length);
            const tekst = data.toString();
            if (!tekst) rom.delete(k);
            else {
                try {
                    const r = JSON.parse(tekst);
                    if (r && r.kode === k) rom.set(k, r);
                } catch (e) { /* ugyldig */ }
            }
            vis();
        };
        c.on('message', paaMelding);
        c.subscribe(TEMA + '+', { qos: 0 });
        const t = setInterval(vis, 15000);
        vis();
        return () => {
            clearInterval(t);
            c.removeListener('message', paaMelding);
            try { c.unsubscribe(TEMA + '+'); } catch (e) { /* frakoblet */ }
        };
    }

    return { annonser, lytt };
})();
