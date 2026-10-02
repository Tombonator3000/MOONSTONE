/*
 * audio.js - lyd ut med WebAudio.
 *
 * Kjernen lager 48 kHz stereo for hvert bilde. Lyden gaar til en AudioWorklet
 * med en ringbuffer. Workleten justerer avspillingsfarten litt (opptil 2,5
 * prosent) etter hvor full bufferen er, slik at lyden holder takten selv om
 * nettleseren kjorer bildene litt ujevnt. Har lydkortet en annen samplerate
 * enn 48 kHz, regnes den om her ogsaa. (Hentet fra Moomesa-prosjektet.)
 */
'use strict';

const Lyd = (() => {
    const RATE = 48000;

    /* koden som kjorer i lydtraaden; ogsaa brukt som reserve uten AudioWorklet */
    const ringSrc = `
class Ring {
    constructor(outRate) {
        this.cap = 48000;
        this.buf = new Float32Array(this.cap * 2);
        this.r = 0;
        this.n = 0;
        this.pos = 0;
        this.step = 48000 / outRate;
        this.adj = 1;
        this.target = 0.07 * 48000;
    }
    push(s) {
        const frames = s.length >> 1;
        if (this.n + frames > this.cap) {
            const drop = this.n + frames - this.cap;
            this.r = (this.r + drop) % this.cap;
            this.n -= drop;
        }
        let w = (this.r + this.n) % this.cap;
        for (let i = 0; i < frames; i++) {
            this.buf[w * 2] = s[i * 2];
            this.buf[w * 2 + 1] = s[i * 2 + 1];
            if (++w === this.cap) w = 0;
        }
        this.n += frames;
    }
    clear() { this.n = 0; this.pos = 0; }
    render(L, R) {
        const err = (this.n - this.target) / this.target;
        const want = 1 + Math.max(-0.025, Math.min(0.025, err * 0.05));
        this.adj += (want - this.adj) * 0.02;
        const step = this.step * this.adj;
        for (let i = 0; i < L.length; i++) {
            if (this.n < 2) { L[i] = 0; R[i] = 0; continue; }
            const a = this.r, b = (this.r + 1) % this.cap, f = this.pos;
            L[i] = this.buf[a * 2] + (this.buf[b * 2] - this.buf[a * 2]) * f;
            R[i] = this.buf[a * 2 + 1] + (this.buf[b * 2 + 1] - this.buf[a * 2 + 1]) * f;
            this.pos += step;
            while (this.pos >= 1 && this.n > 1) {
                this.pos -= 1;
                this.r = (this.r + 1) % this.cap;
                this.n--;
            }
        }
    }
}`;

    const workletSrc = ringSrc + `
class MoonOut extends AudioWorkletProcessor {
    constructor() {
        super();
        this.ring = new Ring(sampleRate);
        this.ticks = 0;
        this.port.onmessage = (e) => {
            if (e.data === 'toem') this.ring.clear();
            else this.ring.push(e.data);
        };
    }
    process(inputs, outputs) {
        const out = outputs[0];
        this.ring.render(out[0], out[1] || out[0]);
        if (++this.ticks % 16 === 0) this.port.postMessage(this.ring.n);
        return true;
    }
}
registerProcessor('moon-out', MoonOut);`;

    let ctx = null, node = null, ring = null, ready = false, starting = null;
    let queued = 0;

    async function start() {
        if (ready) {
            if (ctx.state === 'suspended') await ctx.resume();
            return;
        }
        if (starting) return starting;
        starting = (async () => {
            try {
                ctx = new AudioContext({ sampleRate: RATE, latencyHint: 'interactive' });
            } catch (e) {
                ctx = new AudioContext();
            }
            try {
                const url = URL.createObjectURL(new Blob([workletSrc], { type: 'application/javascript' }));
                await ctx.audioWorklet.addModule(url);
                node = new AudioWorkletNode(ctx, 'moon-out', { numberOfInputs: 0, outputChannelCount: [2] });
                node.port.onmessage = (e) => { queued = e.data; };
            } catch (e) {
                // reserve: ScriptProcessor paa hovedtraaden
                console.log('AudioWorklet virker ikke her (' + e + '), bruker ScriptProcessor');
                const Ring = new Function(ringSrc + '; return Ring;')();
                ring = new Ring(ctx.sampleRate);
                node = ctx.createScriptProcessor(1024, 0, 2);
                node.onaudioprocess = (ev) => {
                    ring.render(ev.outputBuffer.getChannelData(0), ev.outputBuffer.getChannelData(1));
                    queued = ring.n;
                };
            }
            node.connect(ctx.destination);
            ready = true;
            if (ctx.state === 'suspended') await ctx.resume();
        })();
        return starting;
    }

    /* samples: Int16Array med frames*2 verdier (venstre, hoyre) */
    function push(samples) {
        if (!ready || ctx.state !== 'running' || !samples.length) return;
        const f = new Float32Array(samples.length);
        for (let i = 0; i < samples.length; i++) f[i] = samples[i] / 32768;
        if (ring) ring.push(f);
        else node.port.postMessage(f, [f.buffer]);
    }

    function clear() {
        if (ring) ring.clear();
        else if (node) node.port.postMessage('toem');
    }

    function running() { return ready && ctx.state === 'running'; }
    function bufferedMs() { return queued / RATE * 1000; }
    function outputRate() { return ctx ? ctx.sampleRate : 0; }

    return { start, push, clear, running, bufferedMs, outputRate };
})();
