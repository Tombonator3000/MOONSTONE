/*
 * render.js - bildet tegnes med three.js.
 *
 * Rammebufferet fra kjernen (720 x 288, hires-piksler over hele PAL-omraadet)
 * legges i en DataTexture paa en flate som fyller lerretet. Vi viser bare
 * spillets vindu (DIW, i Moonstone 320 x 200 lowres-piksler) med riktig
 * sideforhold. Filtrene er shadere:
 *
 *   skarp   heltallsskalering med myke kanter (som "sharp bilinear")
 *   piksel  naermeste piksel
 *   myk     lineaer utjevning
 *   crt     skanlinjer, maske, litt glod og buet skjerm
 *
 * Scenen er vanlig three.js, saa senere kan grafikk i hoy opplosning tegnes
 * som egne lag over eller i stedet for Amiga-bildet (se docs/hd-grafikk.md).
 */
'use strict';

const Visning = (() => {
    let renderer, scene, camera, mesh, tex, mat, data;
    let W = 720, H = 288;
    let filter = 'skarp', format = 'pal', helt = false;
    let maaTegnes = true;                   /* noe annet enn et nytt bilde krever ny tegning */
    let crop = [70, 19, 710, 219];
    let stabil = 0, nyCrop = null;
    let diwNaa = [70, 19, 710, 219];

    /* HD-lag (eksperimentelt): figurene fra tegnelisten tegnes med egne bilder
     * oppaa Amiga-bildet. Spillet tegner figurene i en buffer utenfor skjermen,
     * ofte fordelt paa to bilder paa rad (i kamp den ene ridderen i ett bilde og
     * resten i det neste), og det ferdige bildet vises to bilder etter det siste.
     * Vi samler derfor tegninger fra bilder paa rad til en klynge og viser den
     * naar den er to bilder gammel. */
    let hdGruppe = null, hdPakke = new Map(), visRammer = false;
    let bildeNr = 0, sistTegnet = -99, klynger = [];
    let visteListe = [], visesFra = 0;
    const flater = [];
    let rammeMat = null;

    const vert = `
        varying vec2 vUv;
        void main() { vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }`;

    const frag = `
        precision highp float;
        uniform sampler2D tex;
        uniform vec2 srcSize;      // rammebufferet i piksler
        uniform vec4 crop;         // x0, y0, x1, y1 i piksler
        uniform vec2 outSize;      // utgangen i piksler
        uniform int mode;          // 0 skarp, 1 piksel, 2 myk, 3 crt
        varying vec2 vUv;

        vec3 hent(vec2 p) {        // p i rammebuffer-piksler (y nedover)
            return texture2D(tex, vec2(p.x / srcSize.x, p.y / srcSize.y)).rgb;
        }

        vec2 bueform(vec2 uv) {
            uv = uv * 2.0 - 1.0;
            vec2 off = abs(uv.yx) / vec2(7.0, 6.0);
            uv = uv + uv * off * off;
            return uv * 0.5 + 0.5;
        }

        void main() {
            vec2 uv = vec2(vUv.x, 1.0 - vUv.y);
            if (mode == 3) {
                uv = bueform(uv);
                if (uv.x < 0.0 || uv.x > 1.0 || uv.y < 0.0 || uv.y > 1.0) { gl_FragColor = vec4(0.0, 0.0, 0.0, 1.0); return; }
            }
            vec2 size = crop.zw - crop.xy;
            vec2 p = crop.xy + uv * size;
            vec3 c;
            if (mode == 1) {
                c = hent(floor(p) + 0.5);
            } else if (mode == 2) {
                c = hent(p);
            } else {
                // skarp: hver kildepiksel er en flate, bare kantene utjevnes
                vec2 scale = max(outSize / size, vec2(1.0));
                vec2 t = p - 0.5;
                vec2 fl = floor(t);
                vec2 s = fract(t);
                vec2 region = 0.5 - 0.5 / scale;
                vec2 cd = s - 0.5;
                vec2 f = (cd - clamp(cd, -region, region)) * scale + 0.5;
                c = hent(fl + f + 0.5);
                if (mode == 3) {
                    // skanlinjer etter Amiga-linjene, aperturmaske og litt glod
                    float line = fract(p.y);
                    float scan = 0.62 + 0.38 * pow(sin(line * 3.14159), 1.6);
                    vec3 glow = (hent(p + vec2(-2.0, 0.0)) + hent(p + vec2(2.0, 0.0)) + hent(p + vec2(0.0, -1.0)) + hent(p + vec2(0.0, 1.0))) * 0.25;
                    c = c * scan + glow * 0.18;
                    float m = mod(gl_FragCoord.x, 3.0);
                    vec3 mask = m < 1.0 ? vec3(1.08, 0.94, 0.94) : m < 2.0 ? vec3(0.94, 1.08, 0.94) : vec3(0.94, 0.94, 1.08);
                    c *= mask;
                    vec2 v = uv * (1.0 - uv);
                    c *= pow(v.x * v.y * 15.0, 0.18);
                }
            }
            gl_FragColor = vec4(c, 1.0);
        }`;

    function init(canvas, w, h) {
        W = w; H = h;
        renderer = new THREE.WebGLRenderer({ canvas, antialias: false, alpha: false, powerPreference: 'high-performance' });
        renderer.setPixelRatio(window.devicePixelRatio || 1);
        scene = new THREE.Scene();
        camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
        data = new Uint8Array(W * H * 4);
        tex = new THREE.DataTexture(data, W, H, THREE.RGBAFormat, THREE.UnsignedByteType);
        tex.colorSpace = THREE.NoColorSpace;
        tex.generateMipmaps = false;
        tex.wrapS = tex.wrapT = THREE.ClampToEdgeWrapping;
        tex.magFilter = THREE.LinearFilter;
        tex.minFilter = THREE.LinearFilter;
        tex.needsUpdate = true;
        mat = new THREE.ShaderMaterial({
            uniforms: {
                tex: { value: tex },
                srcSize: { value: new THREE.Vector2(W, H) },
                crop: { value: new THREE.Vector4(crop[0], crop[1], crop[2], crop[3]) },
                outSize: { value: new THREE.Vector2(1, 1) },
                mode: { value: 0 },
            },
            vertexShader: vert,
            fragmentShader: frag,
            depthTest: false,
            depthWrite: false,
        });
        mesh = new THREE.Mesh(new THREE.PlaneGeometry(2, 2), mat);
        scene.add(mesh);
        hdGruppe = new THREE.Group();
        scene.add(hdGruppe);
        rammeMat = new THREE.MeshBasicMaterial({ color: 0xffd040, transparent: true, opacity: 0.28, depthTest: false });
        tilpass();
        window.addEventListener('resize', tilpass);
    }

    function sideforhold() {
        if (format === '43') return 4 / 3;
        const w = (crop[2] - crop[0]) / 2, h = crop[3] - crop[1];
        return w / h;
    }

    function tilpass() {
        if (!renderer) return;
        const holder = renderer.domElement.parentElement;
        const bw = holder.clientWidth, bh = holder.clientHeight;
        const a = sideforhold();
        let w = bw, h = Math.round(bw / a);
        if (h > bh) { h = bh; w = Math.round(bh * a); }
        renderer.setSize(w, h, true);
        const pr = renderer.getPixelRatio();
        mat.uniforms.outSize.value.set(w * pr, h * pr);
        maaTegnes = true;                   /* lerretet er toemt */
    }

    function settFilter(f) {
        filter = f;
        mat.uniforms.mode.value = { skarp: 0, piksel: 1, myk: 2, crt: 3 }[f] ?? 0;
        const lin = f !== 'piksel';
        tex.magFilter = tex.minFilter = lin ? THREE.LinearFilter : THREE.NearestFilter;
        tex.needsUpdate = true;
        maaTegnes = true;
    }

    function settFormat(f) { format = f; tilpass(); maaTegnes = true; }
    function settHelt(on) { helt = on; nyCrop = null; stabil = 99; maaTegnes = true; }

    /* bytter utsnitt bare naar spillets vindu har vaert likt en stund */
    function oppdaterUtsnitt(diw) {
        let c = helt ? [0, 0, W, H] : [
            Math.max(0, diw[0]), Math.max(0, diw[1]), Math.min(W, diw[2]), Math.min(H, diw[3])
        ];
        if (!helt && (c[2] - c[0] < 320 || c[3] - c[1] < 100)) return;
        if (c.every((v, i) => v === crop[i])) { stabil = 0; return; }
        if (helt || ++stabil >= 25) {
            crop = c;
            stabil = 0;
            mat.uniforms.crop.value.set(c[0], c[1], c[2], c[3]);
            tilpass();
        }
    }

    /* kalles etter hvert bilde emulatoren kjorer, med tegnelisten for bildet */
    function nyttBilde(liste) {
        bildeNr++;
        if (liste.length) {
            if (sistTegnet === bildeNr - 1 && klynger.length) klynger[klynger.length - 1].liste.push(...liste);
            else klynger.push({ liste: liste.slice() });
            klynger[klynger.length - 1].vis = bildeNr + 2;
            sistTegnet = bildeNr;
        }
        while (klynger.length && klynger[0].vis <= bildeNr) {
            visteListe = klynger.shift().liste;
            visesFra = bildeNr;
        }
        /* spillet tegner figurene paa nytt flere ganger i sekundet; har det ikke
         * tegnet paa en stund er vi paa en skjerm uten figurer */
        if (visteListe.length && bildeNr - visesFra > 50) visteListe = [];
    }

    function flate(i) {
        if (!flater[i]) {
            const m = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), rammeMat);
            m.renderOrder = 2;
            hdGruppe.add(m);
            flater[i] = m;
        }
        return flater[i];
    }

    function tegnHd() {
        let n = 0;
        if (visRammer || hdPakke.size) {
            const cw = crop[2] - crop[0], ch = crop[3] - crop[1];
            for (const d of visteListe) {
                const nokkel = d.fil.toLowerCase() + '/' + String(d.bilde).padStart(3, '0');
                const t = hdPakke.get(nokkel);
                if (!t && !visRammer) continue;
                const fx = diwNaa[0] + (d.x - d.xoff) * 2, fy = diwNaa[1] + d.y;
                const u = (fx - crop[0]) / cw, v = (fy - crop[1]) / ch;
                const bw = d.w * 2 / cw, bh = d.h / ch;
                const m = flate(n++);
                m.material = t ? t.mat : rammeMat;
                m.scale.set(d.speilet ? -bw * 2 : bw * 2, bh * 2, 1);   /* negativ bredde snur bildet */
                m.position.set(-1 + (u + bw / 2) * 2, 1 - (v + bh / 2) * 2, 0);
                m.visible = true;
            }
        }
        for (let i = n; i < flater.length; i++) flater[i].visible = false;
    }

    /* Kalles bare naar kjernen har laget et nytt bilde, eller maaTegnes() er sann
     * (storrelse eller innstillinger endret). Ellers blir skjermen staaende, saa en
     * skjerm med 120 eller 144 Hz ikke laster opp og tegner det samme bildet flere ganger. */
    function tegn(fb, diw) {
        maaTegnes = false;
        data.set(fb);
        tex.needsUpdate = true;
        if (diw) { oppdaterUtsnitt(diw); diwNaa = diw; }
        tegnHd();
        renderer.render(scene, camera);
    }

    /* HD-pakke: filer med stier som ".../kn1.ob/012.png" (samme navn som tools/gfx.py extract) */
    async function lastHdPakke(filer) {
        let antall = 0;
        for (const f of filer) {
            const sti = (f.webkitRelativePath || f.name).split('/');
            if (sti.length < 2 || !/\.png$/i.test(sti[sti.length - 1])) continue;
            const nokkel = sti[sti.length - 2].toLowerCase() + '/' + sti[sti.length - 1].replace(/\.png$/i, '');
            try {
                /* ImageBitmap snus ikke av WebGL (flipY virker ikke), et lerret gjor */
                const bilde = await createImageBitmap(f);
                const lerret = document.createElement('canvas');
                lerret.width = bilde.width; lerret.height = bilde.height;
                lerret.getContext('2d').drawImage(bilde, 0, 0);
                bilde.close();
                const t = new THREE.Texture(lerret);
                t.colorSpace = THREE.SRGBColorSpace;
                t.needsUpdate = true;
                const old = hdPakke.get(nokkel);
                if (old) { old.tex.dispose(); old.mat.dispose(); }
                hdPakke.set(nokkel, { tex: t, mat: new THREE.MeshBasicMaterial({ map: t, transparent: true, depthTest: false }) });
                antall++;
            } catch (e) { /* ikke et bilde */ }
        }
        return antall;
    }

    function tomHdPakke() {
        for (const v of hdPakke.values()) { v.tex.dispose(); v.mat.dispose(); }
        hdPakke.clear();
        maaTegnes = true;
    }

    function bildeTilPng() {
        return renderer.domElement.toDataURL('image/png');
    }

    return {
        init, tegn, nyttBilde, tilpass, settFilter, settFormat, settHelt, bildeTilPng, lastHdPakke, tomHdPakke,
        settRammer: (on) => { visRammer = on; maaTegnes = true; }, hdAntall: () => hdPakke.size, scene: () => scene,
        maaTegnes: () => maaTegnes,
        utsnitt: () => crop.slice(),                /* delen av rammebufferet som vises (x0, y0, x1, y1) */
        brukerListe: () => hdPakke.size > 0 || visRammer,   /* trengs tegnelisten fra kjernen? */
    };
})();
