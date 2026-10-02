/*
 * audio.js - lyd ut med WebAudio.
 *
 * Kjernen lager 48 kHz stereo for hvert bilde. Lyden gaar til en AudioWorklet
 * med en ringbuffer. Workleten justerer avspillingsfarten litt (opptil 2,5
 * prosent) etter hvor full bufferen er, slik at lyden holder takten selv om
 * nettleseren kjorer bildene litt ujevnt. Har lydkortet en annen samplerate
 * enn 48 kHz, regnes den om her ogsaa. (Hentet fra Moomesa-prosjektet.)
 *
 * Gaar bufferen tom (siden hang, eller fanen var i bakgrunnen), tones lyden ut
 * i stedet for aa hakke, og den starter ikke igjen for bufferen er halvfull.
 * Hver gang det skjer, blir maalet for bufferen 20 ms stoerre, opp til 200 ms,
 * saa en treg maskin faar litt mer forsinkelse i stedet for knitring.
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
        this.target = 0.08 * 48000;
        this.tom = true;                    /* venter paa at bufferen fylles */
        this.hull = 0;                      /* antall ganger bufferen gikk tom */
        this.sisteL = 0;
        this.sisteR = 0;
        this.gain = 1;                      /* volum over 1 (kjernen gaar bare til 1) */
    }
    /* forsterk og begrens mykt over 0,9 i stedet for aa klippe (det skurrer) */
    myk(x) {
        x *= this.gain;
        const a = Math.abs(x);
        if (a <= 0.9) return x;
        return Math.sign(x) * (0.9 + 0.1 * Math.tanh((a - 0.9) / 0.1));
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
    clear() { this.n = 0; this.pos = 0; this.tom = true; }
    render(L, R) {
        if (this.tom && this.n >= this.target * 0.5) this.tom = false;
        const err = (this.n - this.target) / this.target;
        const want = 1 + Math.max(-0.025, Math.min(0.025, err * 0.05));
        this.adj += (want - this.adj) * 0.02;
        const step = this.step * this.adj;
        for (let i = 0; i < L.length; i++) {
            if (!this.tom && this.n < 2) {
                this.tom = true;
                this.hull++;
                this.target = Math.min(0.2 * 48000, this.target + 0.02 * 48000);
            }
            if (this.tom) {
                /* tone ut fra siste verdi, ikke hopp rett til 0 (det klikker) */
                this.sisteL *= 0.995; this.sisteR *= 0.995;
                L[i] = this.sisteL; R[i] = this.sisteR;
                continue;
            }
            const a = this.r, b = (this.r + 1) % this.cap, f = this.pos;
            L[i] = this.myk(this.buf[a * 2] + (this.buf[b * 2] - this.buf[a * 2]) * f);
            R[i] = this.myk(this.buf[a * 2 + 1] + (this.buf[b * 2 + 1] - this.buf[a * 2 + 1]) * f);
            this.sisteL = L[i]; this.sisteR = R[i];
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
            else if (typeof e.data === 'number') this.ring.gain = e.data;
            else this.ring.push(e.data);
        };
    }
    process(inputs, outputs) {
        const out = outputs[0];
        this.ring.render(out[0], out[1] || out[0]);
        if (++this.ticks % 16 === 0) this.port.postMessage([this.ring.n, this.ring.hull]);
        return true;
    }
}
registerProcessor('moon-out', MoonOut);`;

    let ctx = null, node = null, ring = null, ready = false, starting = null;
    let queued = 0, hull = 0;

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
                node.port.onmessage = (e) => { queued = e.data[0]; hull = e.data[1]; };
            } catch (e) {
                // reserve: ScriptProcessor paa hovedtraaden
                console.log('AudioWorklet virker ikke her (' + e + '), bruker ScriptProcessor');
                const Ring = new Function(ringSrc + '; return Ring;')();
                ring = new Ring(ctx.sampleRate);
                node = ctx.createScriptProcessor(1024, 0, 2);
                node.onaudioprocess = (ev) => {
                    ring.render(ev.outputBuffer.getChannelData(0), ev.outputBuffer.getChannelData(1));
                    queued = ring.n;
                    hull = ring.hull;
                };
            }
            node.connect(ctx.destination);
            ready = true;
            forsterk(gain);
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

    /* volum over 1: forsterkes her (kjernen stopper paa 1) */
    let gain = 1;
    function forsterk(g) {
        gain = g;
        if (ring) ring.gain = g;
        else if (node) node.port.postMessage(g);
    }

    function clear() {
        if (ring) ring.clear();
        else if (node) node.port.postMessage('toem');
    }

    function running() { return ready && ctx.state === 'running'; }
    function bufferedMs() { return queued / RATE * 1000; }
    function outputRate() { return ctx ? ctx.sampleRate : 0; }

    return { start, push, clear, forsterk, running, bufferedMs, outputRate, hull: () => hull };
})();
