/*
 * render.js - bildet tegnes med three.js, i to trinn.
 *
 * 1. Sammensetting: lagene tegnes i et rendermaal med hoy opplosning
 *    (spillets 320 x 200 ganger en skala), i lowres-koordinater med y nedover:
 *      rammebufferet  hele Amiga-bildet (720 x 288), alltid underst
 *      bakgrunn       den rene bakgrunnen fra spillet (port/src/lag.c), eller et
 *                     HD-bilde for den (bg/HASH.png i HD-pakken)
 *      skygge         forgrunnen i svart, litt forskjovet (effekt)
 *      forgrunn       det skjermen viser der det er annerledes enn bakgrunnen
 *      HD-figurer     fra tegnelisten (kn1.ob/012.png osv.)
 *    Bakgrunn og forgrunn finnes bare naar kjernen har laget dem (Kjerne.lag).
 *    Uten HD-bilder og effekter er de sammen akkurat det samme som rammebufferet.
 * 2. Etterbehandling: rendermaalet tegnes paa lerretet med filteret:
 *      skarp   lowres-pikslene som flater, myke kanter ved skalering
 *      piksel  naermeste piksel
 *      myk     lineaer utjevning
 *      crt     skanlinjer, maske, litt glod og buet skjerm
 *    og effektene glod, sterkere farger og vignett.
 *
 * Spillets vindu (DIW, 320 x 200 lowres) vises med riktig sideforhold, eller hele
 * PAL-bildet med kanter (settHelt). Se docs/hd-grafikk.md.
 */
'use strict';

const Visning = (() => {
    let renderer, W = 720, H = 288;
    let filter = 'skarp', format = 'pal', helt = false;
    let maaTegnes = true;                   /* noe annet enn et nytt bilde krever ny tegning */
    let crop = [70, 19, 710, 219];          /* utsnittet av rammebufferet som vises (hires x, linjer) */
    let stabil = 0;
    let diwNaa = [70, 19, 710, 219];
    const effekter = { skygge: false, dybde: false, glod: false, farger: false, vignett: false };
    let tvungetLag = false;                 /* lagene alltid, ogsaa uten HD og effekter (testing) */

    /* trinn 1 */
    let scene1, kamera1, rt = null, skala = 4;
    let fbData, fbTex, fbMesh;
    let bakData, bakTex, bakMat, bakMesh;
    let forData, forTex, forMesh, skyggeMesh;
    let lagNaa = null;                      /* { hash, lys } for bildet som vises, eller null */
    const lysMaks = new Map();              /* bakgrunn -> lyseste paletten sett (fading av HD-bakgrunner) */

    /* trinn 2 */
    let scene2, kamera2, postMat;

    /* HD-lag: figurene fra tegnelisten tegnes med egne bilder over forgrunnen.
     * Spillet tegner figurene i en buffer utenfor skjermen, ofte fordelt paa to
     * bilder paa rad, og det ferdige bildet vises to bilder etter det siste. Vi
     * samler derfor tegninger fra bilder paa rad til en klynge og viser den naar
     * den er to bilder gammel. */
    let hdGruppe = null, hdPakke = new Map(), visRammer = false;
    let bildeNr = 0, sistTegnet = -99, klynger = [];
    let visteListe = [], visesFra = 0;
    const flater = [];
    let rammeMat = null;
    let antallBg = 0;                       /* HD-bakgrunner i pakken */

    const vertPost = `
        varying vec2 vUv;
        void main() { vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }`;
    const vertLag = `
        varying vec2 vUv;
        void main() { vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }`;

    /* bakgrunnen: Amiga-laget eller et HD-bilde, med fading og eventuelt uskarphet */
    const fragBak = `
        precision highp float;
        uniform sampler2D map;
        uniform vec2 texel;        // en lowres-piksel i teksturkoordinater
        uniform float uskarp;      // 0 = skarp
        uniform float lys;         // fading for HD-bakgrunner
        varying vec2 vUv;
        void main() {
            vec2 uv = vUv;
            vec3 c = texture2D(map, uv).rgb;
            if (uskarp > 0.0) {
                vec2 d = texel * uskarp;
                c = c * 0.2
                  + (texture2D(map, uv + vec2(d.x, 0.0)).rgb + texture2D(map, uv - vec2(d.x, 0.0)).rgb
                   + texture2D(map, uv + vec2(0.0, d.y)).rgb + texture2D(map, uv - vec2(0.0, d.y)).rgb) * 0.12
                  + (texture2D(map, uv + d).rgb + texture2D(map, uv - d).rgb
                   + texture2D(map, uv + vec2(d.x, -d.y)).rgb + texture2D(map, uv + vec2(-d.x, d.y)).rgb) * 0.08;
            }
            gl_FragColor = vec4(c * lys, 1.0);
        }`;

    /* skyggen: forgrunnen i svart */
    const fragSkygge = `
        precision highp float;
        uniform sampler2D map;
        varying vec2 vUv;
        void main() { gl_FragColor = vec4(0.0, 0.0, 0.0, texture2D(map, vUv).a * 0.55); }`;

    const fragPost = `
        precision highp float;
        uniform sampler2D tex;     // rendermaalet fra trinn 1
        uniform vec2 lores;        // utsnittet i lowres-piksler (bredde, linjer)
        uniform vec2 outSize;      // lerretet i piksler
        uniform int mode;          // 0 skarp, 1 piksel, 2 myk, 3 crt
        uniform float glod, farger, vignett;
        varying vec2 vUv;

        vec3 hent(vec2 uv) { return texture2D(tex, vec2(uv.x, 1.0 - uv.y)).rgb; }

        vec2 bueform(vec2 uv) {
            uv = uv * 2.0 - 1.0;
            vec2 off = abs(uv.yx) / vec2(7.0, 6.0);
            uv = uv + uv * off * off;
            return uv * 0.5 + 0.5;
        }

        void main() {
            vec2 uv = vec2(vUv.x, 1.0 - vUv.y);          // y nedover
            if (mode == 3) {
                uv = bueform(uv);
                if (uv.x < 0.0 || uv.x > 1.0 || uv.y < 0.0 || uv.y > 1.0) { gl_FragColor = vec4(0.0, 0.0, 0.0, 1.0); return; }
            }
            vec3 c = hent(uv);
            vec2 px = 1.0 / lores;                        // en lowres-piksel
            if (glod > 0.0) {
                // lyse omraader lyser utover: lyse naboer i to ringer, terskel paa lysstyrken
                vec3 sum = vec3(0.0);
                for (int i = 0; i < 12; i++) {
                    float a = float(i) * 0.5236;
                    vec2 r = vec2(cos(a), sin(a));
                    vec3 s1 = hent(uv + r * px * 2.0), s2 = hent(uv + r * px * 4.5);
                    sum += max(s1 - 0.55, 0.0) * 0.6 + max(s2 - 0.55, 0.0) * 0.4;
                }
                c += sum / 12.0 * 1.6 * glod;
            }
            if (mode == 3) {
                float line = fract(uv.y * lores.y);
                float scan = 0.62 + 0.38 * pow(sin(line * 3.14159), 1.6);
                vec3 nabo = (hent(uv + vec2(-2.0 * px.x, 0.0)) + hent(uv + vec2(2.0 * px.x, 0.0))
                           + hent(uv + vec2(0.0, -px.y)) + hent(uv + vec2(0.0, px.y))) * 0.25;
                c = c * scan + nabo * 0.18;
                float m = mod(gl_FragCoord.x, 3.0);
                vec3 mask = m < 1.0 ? vec3(1.08, 0.94, 0.94) : m < 2.0 ? vec3(0.94, 1.08, 0.94) : vec3(0.94, 0.94, 1.08);
                c *= mask;
                vec2 v = uv * (1.0 - uv);
                c *= pow(v.x * v.y * 15.0, 0.18);
            }
            if (farger > 0.0) {
                // litt mer kontrast og metning, og en varm tone
                float l = dot(c, vec3(0.299, 0.587, 0.114));
                c = mix(vec3(l), c, 1.0 + 0.25 * farger);
                c = (c - 0.5) * (1.0 + 0.12 * farger) + 0.5;
                c *= vec3(1.0 + 0.04 * farger, 1.0, 1.0 - 0.05 * farger);
            }
            if (vignett > 0.0) {
                vec2 d = uv - 0.5;
                c *= 1.0 - vignett * 0.55 * smoothstep(0.25, 0.75, length(d * vec2(1.0, 0.9)));
            }
            gl_FragColor = vec4(clamp(c, 0.0, 1.0), 1.0);
        }`;

    function dataTekstur(data, w, h) {
        const t = new THREE.DataTexture(data, w, h, THREE.RGBAFormat, THREE.UnsignedByteType);
        t.colorSpace = THREE.NoColorSpace;
        t.generateMipmaps = false;
        t.wrapS = t.wrapT = THREE.ClampToEdgeWrapping;
        t.magFilter = t.minFilter = THREE.NearestFilter;
        t.needsUpdate = true;
        return t;
    }

    function init(canvas, w, h) {
        W = w; H = h;
        renderer = new THREE.WebGLRenderer({ canvas, antialias: false, alpha: false, powerPreference: 'high-performance' });
        renderer.setPixelRatio(window.devicePixelRatio || 1);
        renderer.autoClear = true;

        /* trinn 1: lowres-koordinater, y nedover */
        scene1 = new THREE.Scene();
        kamera1 = new THREE.OrthographicCamera(0, 320, 0, 200, -1, 1);
        fbData = new Uint8Array(W * H * 4);
        fbTex = dataTekstur(fbData, W, H);
        fbMesh = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), new THREE.MeshBasicMaterial({ map: fbTex, side: THREE.DoubleSide, depthTest: false }));
        fbMesh.renderOrder = 0;
        scene1.add(fbMesh);

        bakData = new Uint8Array(320 * 200 * 4);
        bakTex = dataTekstur(bakData, 320, 200);
        bakMat = new THREE.ShaderMaterial({
            uniforms: { map: { value: bakTex }, texel: { value: new THREE.Vector2(1 / 320, 1 / 200) }, uskarp: { value: 0 }, lys: { value: 1 } },
            vertexShader: vertLag, fragmentShader: fragBak, side: THREE.DoubleSide, depthTest: false, depthWrite: false,
        });
        bakMesh = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), bakMat);
        bakMesh.renderOrder = 1;
        scene1.add(bakMesh);

        forData = new Uint8Array(320 * 200 * 4);
        forTex = dataTekstur(forData, 320, 200);
        skyggeMesh = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), new THREE.ShaderMaterial({
            uniforms: { map: { value: forTex } }, vertexShader: vertLag, fragmentShader: fragSkygge,
            side: THREE.DoubleSide, transparent: true, depthTest: false, depthWrite: false,
        }));
        skyggeMesh.renderOrder = 2;
        scene1.add(skyggeMesh);
        forMesh = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), new THREE.MeshBasicMaterial({ map: forTex, side: THREE.DoubleSide, transparent: true, depthTest: false }));
        forMesh.renderOrder = 3;
        scene1.add(forMesh);

        hdGruppe = new THREE.Group();
        scene1.add(hdGruppe);
        rammeMat = new THREE.MeshBasicMaterial({ color: 0xffd040, transparent: true, opacity: 0.28, depthTest: false, side: THREE.DoubleSide });

        /* trinn 2 */
        scene2 = new THREE.Scene();
        kamera2 = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
        postMat = new THREE.ShaderMaterial({
            uniforms: {
                tex: { value: null },
                lores: { value: new THREE.Vector2(320, 200) },
                outSize: { value: new THREE.Vector2(1, 1) },
                mode: { value: 0 },
                glod: { value: 0 }, farger: { value: 0 }, vignett: { value: 0 },
            },
            vertexShader: vertPost, fragmentShader: fragPost, depthTest: false, depthWrite: false,
        });
        scene2.add(new THREE.Mesh(new THREE.PlaneGeometry(2, 2), postMat));

        settFilter(filter);
        tilpass();
        window.addEventListener('resize', tilpass);
    }

    function sideforhold() {
        if (format === '43') return 4 / 3;
        const w = (crop[2] - crop[0]) / 2, h = crop[3] - crop[1];
        return w / h;
    }

    /* rendermaalet: utsnittet i lowres ganger en skala som passer lerretet (2-6) */
    function lagRendermaal(utH) {
        const lw = (crop[2] - crop[0]) / 2, lh = crop[3] - crop[1];
        const s = Math.max(2, Math.min(6, Math.ceil(utH / lh)));
        const w = Math.round(lw * s), h = Math.round(lh * s);
        if (rt && rt.width === w && rt.height === h) return;
        if (rt) rt.dispose();
        skala = s;
        rt = new THREE.WebGLRenderTarget(w, h, { depthBuffer: false });
        rt.texture.generateMipmaps = false;
        rt.texture.colorSpace = THREE.NoColorSpace;
        settRtFilter();
        postMat.uniforms.tex.value = rt.texture;
    }

    function settRtFilter() {
        if (!rt) return;
        rt.texture.magFilter = rt.texture.minFilter = filter === 'piksel' ? THREE.NearestFilter : THREE.LinearFilter;
        rt.texture.needsUpdate = true;
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
        postMat.uniforms.outSize.value.set(w * pr, h * pr);
        lagRendermaal(h * pr);
        maaTegnes = true;                   /* lerretet er toemt */
    }

    function settFilter(f) {
        filter = f;
        postMat.uniforms.mode.value = { skarp: 0, piksel: 1, myk: 2, crt: 3 }[f] ?? 0;
        const lin = f === 'myk';
        for (const t of [fbTex, bakTex, forTex]) {
            t.magFilter = t.minFilter = lin ? THREE.LinearFilter : THREE.NearestFilter;
            t.needsUpdate = true;
        }
        settRtFilter();
        maaTegnes = true;
    }

    function settFormat(f) { format = f; tilpass(); maaTegnes = true; }
    function settHelt(on) { helt = on; stabil = 99; maaTegnes = true; }

    function settEffekter(e) {
        Object.assign(effekter, e);
        postMat.uniforms.glod.value = effekter.glod ? 1 : 0;
        postMat.uniforms.farger.value = effekter.farger ? 1 : 0;
        postMat.uniforms.vignett.value = effekter.vignett ? 1 : 0;
        maaTegnes = true;
    }

    /* bytter utsnitt bare naar spillets vindu har vaert likt en stund */
    function oppdaterUtsnitt(diw) {
        const c = helt ? [0, 0, W, H] : [
            Math.max(0, diw[0]), Math.max(0, diw[1]), Math.min(W, diw[2]), Math.min(H, diw[3])
        ];
        if (!helt && (c[2] - c[0] < 320 || c[3] - c[1] < 100)) return;
        if (c.every((v, i) => v === crop[i])) { stabil = 0; return; }
        if (helt || ++stabil >= 25) {
            crop = c;
            stabil = 0;
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
            m.renderOrder = 4;
            hdGruppe.add(m);
            flater[i] = m;
        }
        return flater[i];
    }

    /* lowres-koordinater i trinn 1: (0, 0) er hjornet av utsnittet */
    const ux = () => crop[0] / 2, uy = () => crop[1];

    function plasser(m, x, y, w, h) {
        m.position.set(x + w / 2, y + h / 2, 0);
        m.scale.set(w, h, 1);
    }

    let hdLys = 1;                          /* fading for HD-bildene, fra paletten (lagene) */
    function tegnHd() {
        let n = 0;
        if (visRammer || hdPakke.size) {
            for (const d of visteListe) {
                const nokkel = d.fil.toLowerCase() + '/' + String(d.bilde).padStart(3, '0');
                const t = hdPakke.get(nokkel);
                if (!t && !visRammer) continue;
                const x = diwNaa[0] / 2 + d.x - d.xoff - ux(), y = diwNaa[1] + d.y - uy();
                const m = flate(n++);
                m.material = t ? t.mat : rammeMat;
                if (t) t.mat.color.setScalar(hdLys);
                plasser(m, x, y, d.w, d.h);
                if (d.speilet) m.scale.x = -d.w;           /* negativ bredde snur bildet */
                m.visible = true;
            }
        }
        for (let i = n; i < flater.length; i++) flater[i].visible = false;
    }

    /* Kalles bare naar kjernen har laget et nytt bilde, eller maaTegnes() er sann.
     * lag: { bak, for (Uint8Array, 320 x 200 RGBA), hash, lys } eller null. */
    function tegn(fb, diw, lag) {
        maaTegnes = false;
        if (diw) { oppdaterUtsnitt(diw); diwNaa = diw; }
        const lw = (crop[2] - crop[0]) / 2, lh = crop[3] - crop[1];
        kamera1.right = lw; kamera1.bottom = lh;
        kamera1.updateProjectionMatrix();
        postMat.uniforms.lores.value.set(lw, lh);

        fbData.set(fb);
        fbTex.needsUpdate = true;
        fbTex.offset.set(crop[0] / W, crop[1] / H);
        fbTex.repeat.set((crop[2] - crop[0]) / W, (crop[3] - crop[1]) / H);
        plasser(fbMesh, 0, 0, lw, lh);

        lagNaa = lag;
        const lx = diwNaa[0] / 2 - ux(), ly = diwNaa[1] - uy();
        if (lag) {
            const nokkel = 'bg/' + (lag.hash >>> 0).toString(16).padStart(8, '0');
            const hd = hdPakke.get(nokkel);
            const maks = Math.max(lysMaks.get(lag.hash) || 0, lag.lys);
            lysMaks.set(lag.hash, maks);
            hdLys = maks ? lag.lys / maks : 1;
            if (hd) {
                bakMat.uniforms.map.value = hd.tex;
                bakMat.uniforms.texel.value.set(1 / 320, 1 / 200);
                bakMat.uniforms.lys.value = hdLys;
            } else {
                bakData.set(lag.bak);
                bakTex.needsUpdate = true;
                bakMat.uniforms.map.value = bakTex;
                bakMat.uniforms.texel.value.set(1 / 320, 1 / 200);
                bakMat.uniforms.lys.value = 1;
            }
            bakMat.uniforms.uskarp.value = effekter.dybde ? 0.9 : 0;
            forData.set(lag.for);
            forTex.needsUpdate = true;
            plasser(bakMesh, lx, ly, 320, 200);
            plasser(forMesh, lx, ly, 320, 200);
            plasser(skyggeMesh, lx + 1.5, ly + 1.5, 320, 200);
        }
        if (!lag) hdLys = 1;
        bakMesh.visible = forMesh.visible = !!lag;
        skyggeMesh.visible = !!lag && effekter.skygge;
        tegnHd();
        renderer.setRenderTarget(rt);
        renderer.render(scene1, kamera1);
        renderer.setRenderTarget(null);
        renderer.render(scene2, kamera2);
    }

    /* HD-pakke: filer med stier som ".../kn1.ob/012.png" (som tools/gfx.py extract)
     * og ".../bg/1a2b3c4d.png" for bakgrunner (hash fra laget, se lagreBakgrunn) */
    async function lastHdPakke(filer) {
        let antall = 0;
        for (const f of filer) {
            const sti = (f.webkitRelativePath || f.name).split('/');
            if (sti.length < 2 || !/\.png$/i.test(sti[sti.length - 1])) continue;
            const nokkel = sti[sti.length - 2].toLowerCase() + '/' + sti[sti.length - 1].replace(/\.png$/i, '').toLowerCase();
            try {
                const bilde = await createImageBitmap(f);
                const lerret = document.createElement('canvas');
                lerret.width = bilde.width; lerret.height = bilde.height;
                lerret.getContext('2d').drawImage(bilde, 0, 0);
                bilde.close();
                const t = new THREE.Texture(lerret);
                t.colorSpace = THREE.NoColorSpace;
                t.flipY = false;                            /* trinn 1 har y nedover */
                t.generateMipmaps = false;
                t.minFilter = THREE.LinearFilter;
                t.needsUpdate = true;
                const old = hdPakke.get(nokkel);
                if (old) { old.tex.dispose(); old.mat.dispose(); }
                hdPakke.set(nokkel, { tex: t, mat: new THREE.MeshBasicMaterial({ map: t, transparent: true, depthTest: false, side: THREE.DoubleSide }) });
                antall++;
            } catch (e) { /* ikke et bilde */ }
        }
        antallBg = [...hdPakke.keys()].filter((k) => k.startsWith('bg/')).length;
        maaTegnes = true;
        return antall;
    }

    function tomHdPakke() {
        for (const v of hdPakke.values()) { v.tex.dispose(); v.mat.dispose(); }
        hdPakke.clear();
        antallBg = 0;
        maaTegnes = true;
    }

    function bildeTilPng() {
        return renderer.domElement.toDataURL('image/png');
    }

    return {
        init, tegn, nyttBilde, tilpass, settFilter, settFormat, settHelt, settEffekter, bildeTilPng, lastHdPakke, tomHdPakke,
        settRammer: (on) => { visRammer = on; maaTegnes = true; }, hdAntall: () => hdPakke.size, scene: () => scene1,
        hdBakgrunner: () => antallBg,
        maaTegnes: () => maaTegnes,
        utsnitt: () => crop.slice(),                /* delen av rammebufferet som vises (x0, y0, x1, y1) */
        brukerListe: () => hdPakke.size > 0 || visRammer,   /* trengs tegnelisten fra kjernen? */
        /* trengs lagene fra kjernen? (HD-bakgrunner eller effekter som skiller lagene) */
        trengerLag: () => hdPakke.size > 0 || effekter.skygge || effekter.dybde || tvungetLag,
        lagNaa: () => lagNaa,
        settTvungetLag: (on) => { tvungetLag = on; maaTegnes = true; },
    };
})();
