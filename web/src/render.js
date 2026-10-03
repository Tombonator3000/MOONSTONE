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
    let fbData, fbTex, fbMat, fbMesh;
    let bakData, bakTex, bakMat, bakAmigaMat, bakMesh;
    let forData, forTex, forMat, skyggeMat, forMesh, skyggeMesh;
    let lagNaa = null;                      /* { hash, lys } for bildet som vises, eller null */
    const lysMaks = new Map();              /* bakgrunn -> lyseste paletten sett (fading av HD-bakgrunner) */

    /* trinn 2 */
    let scene2, kamera2, postMat;

    /* HD-lag: figurene fra tegnelisten (ogsaa bokstavene, som er figurer i bold.f og
     * Small.font) tegnes med egne bilder over forgrunnen. Spillet tegner figurene i
     * en buffer utenfor skjermen, ofte fordelt paa to bilder paa rad, og det ferdige
     * bildet vises to bilder etter det siste. Vi samler derfor tegninger fra bilder
     * paa rad til en klynge og viser den naar den er to bilder gammel.
     * Med lagene blir en figur staaende saa lenge forgrunnen der den ligger er
     * uendret (tekst tegnes bare en gang); uten lag vises klyngen til det har gaatt
     * 50 bilder uten nye tegninger. */
    let hdGruppe = null, hdPakke = new Map(), visRammer = false;
    let hdPaa = true;                       /* false: original grafikk, selv om en HD-pakke er lastet */
    let bildeNr = 0, sistTegnet = -99, klynger = [];
    let visteListe = [], visesFra = 0;
    let plasserte = new Map(), sisteBakHash = -1;    /* "x,y,b,h" -> { d, x, y, w, h, hash } */
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

    /* Amiga-lagene (rammebufferet, bakgrunnen, forgrunnen og skyggen). modus 0 er hele
     * lowres-piksler, 1 lineaer utjevning, 2 Scale4x: Scale2x (EPX) to ganger, regnet ut
     * for hver piksel i utgangen fra 5 x 5 lowres-piksler rundt. Scale2x runder av
     * trappetrinn paa skraa kanter uten aa lage nye farger, saa paletten og fadingen er
     * spillets egen. Alfa er med, saa kantene paa figurene i forgrunnen rundes ogsaa. */
    const fragAmiga = `
        precision highp float;
        uniform sampler2D map;
        uniform vec2 texSize;      // teksturen i texler
        uniform vec2 celle;        // texler per lowres-piksel (rammebufferet: 2 x 1)
        uniform vec4 region;       // det flaten viser, i lowres-piksler: x, y, bredde, hoyde
        uniform int modus;         // 0 piksler, 1 lineaer, 2 Scale4x
        uniform float skygge;      // 1 = bare svart med alfa (skyggen)
        uniform float uskarp;      // 0 = skarp
        varying vec2 vUv;

        vec4 px(vec2 c) { return texture2D(map, (c * celle + 0.5) / texSize); }
        bool lik(vec4 a, vec4 b) { vec4 d = abs(a - b); return max(max(d.x, d.y), max(d.z, d.w)) < 0.002; }
        // Scale2x: E i midten, A over, B til hoyre, C til venstre, D under; f er hjornet (0/1)
        vec4 epx(vec4 E, vec4 A, vec4 B, vec4 C, vec4 D, vec2 f) {
            if (f.y < 0.5) {
                if (f.x < 0.5) { if (lik(C, A) && !lik(C, D) && !lik(A, B)) return A; }
                else           { if (lik(A, B) && !lik(A, C) && !lik(B, D)) return B; }
            } else {
                if (f.x < 0.5) { if (lik(D, C) && !lik(D, B) && !lik(C, A)) return C; }
                else           { if (lik(B, D) && !lik(B, A) && !lik(D, C)) return D; }
            }
            return E;
        }
        vec4 s2(vec2 q) {          // Scale2x-bildet i heltallskoordinat q
            vec2 c = floor(q * 0.5);
            return epx(px(c), px(c + vec2(0.0, -1.0)), px(c + vec2(1.0, 0.0)), px(c + vec2(-1.0, 0.0)), px(c + vec2(0.0, 1.0)), q - c * 2.0);
        }
        vec4 s4(vec2 p) {          // Scale4x i lowres-posisjon p
            vec2 r = floor(p * 4.0), q = floor(r * 0.5);
            return epx(s2(q), s2(q + vec2(0.0, -1.0)), s2(q + vec2(1.0, 0.0)), s2(q + vec2(-1.0, 0.0)), s2(q + vec2(0.0, 1.0)), r - q * 2.0);
        }
        void main() {
            vec2 p = region.xy + vUv * region.zw;
            vec4 c;
            if (uskarp > 0.0) {
                vec2 t = p * celle / texSize, d = celle * uskarp / texSize;
                c = texture2D(map, t) * 0.2
                  + (texture2D(map, t + vec2(d.x, 0.0)) + texture2D(map, t - vec2(d.x, 0.0))
                   + texture2D(map, t + vec2(0.0, d.y)) + texture2D(map, t - vec2(0.0, d.y))) * 0.12
                  + (texture2D(map, t + d) + texture2D(map, t - d)
                   + texture2D(map, t + vec2(d.x, -d.y)) + texture2D(map, t + vec2(-d.x, d.y))) * 0.08;
            } else if (modus == 2) c = s4(p);
            else if (modus == 1) c = texture2D(map, p * celle / texSize);
            else c = texture2D(map, (floor(p * celle) + 0.5) / texSize);   // hel texel (ogsaa hires)
            gl_FragColor = skygge > 0.5 ? vec4(0.0, 0.0, 0.0, c.a * 0.55) : c;
        }`;

    function amigaMat(tex, texW, texH, celleX, gjennomsiktig, skygge) {
        return new THREE.ShaderMaterial({
            uniforms: {
                map: { value: tex }, texSize: { value: new THREE.Vector2(texW, texH) }, celle: { value: new THREE.Vector2(celleX, 1) },
                region: { value: new THREE.Vector4(0, 0, 320, 200) }, modus: { value: 0 }, skygge: { value: skygge ? 1 : 0 }, uskarp: { value: 0 },
            },
            vertexShader: vertLag, fragmentShader: fragAmiga, side: THREE.DoubleSide,
            transparent: !!gjennomsiktig, depthTest: false, depthWrite: false,
        });
    }

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
        fbMat = amigaMat(fbTex, W, H, 2, false, false);
        fbMesh = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), fbMat);
        fbMesh.renderOrder = 0;
        scene1.add(fbMesh);

        bakData = new Uint8Array(320 * 200 * 4);
        bakTex = dataTekstur(bakData, 320, 200);
        bakAmigaMat = amigaMat(bakTex, 320, 200, 1, false, false);
        bakMat = new THREE.ShaderMaterial({         /* HD-bakgrunnen */
            uniforms: { map: { value: bakTex }, texel: { value: new THREE.Vector2(1 / 320, 1 / 200) }, uskarp: { value: 0 }, lys: { value: 1 } },
            vertexShader: vertLag, fragmentShader: fragBak, side: THREE.DoubleSide, depthTest: false, depthWrite: false,
        });
        bakMesh = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), bakAmigaMat);
        bakMesh.renderOrder = 1;
        scene1.add(bakMesh);

        forData = new Uint8Array(320 * 200 * 4);
        forTex = dataTekstur(forData, 320, 200);
        skyggeMat = amigaMat(forTex, 320, 200, 1, true, true);
        skyggeMesh = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), skyggeMat);
        skyggeMesh.renderOrder = 2;
        scene1.add(skyggeMesh);
        forMat = amigaMat(forTex, 320, 200, 1, true, false);
        forMesh = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), forMat);
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
        /* Scale4x trenger fire ganger; mer gir bare mer arbeid for skjermkortet */
        const s = filter === 'glatt' ? 4 : Math.max(2, Math.min(4, Math.ceil(utH / lh)));
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
        const f = filter === 'piksel' ? THREE.NearestFilter : THREE.LinearFilter;
        if (rt.texture.magFilter === f) return;
        rt.texture.magFilter = rt.texture.minFilter = f;
        /* three.js laster ikke teksturen til et rendermaal opp paa nytt (needsUpdate
         * virker ikke); dispose gjoer at maalet settes opp igjen med filteret */
        rt.dispose();
    }

    function tilpass() {
        if (!renderer) return;
        const holder = renderer.domElement.parentElement;
        const bw = holder.clientWidth, bh = holder.clientHeight;
        const a = sideforhold();
        let w = bw, h = Math.round(bw / a);
        if (h > bh) { h = bh; w = Math.round(bh * a); }
        const dpr = window.devicePixelRatio || 1;   /* endres ved zoom og ved bytte av skjerm */
        if (renderer.getPixelRatio() !== dpr) renderer.setPixelRatio(dpr);
        renderer.setSize(w, h, true);
        const pr = renderer.getPixelRatio();
        postMat.uniforms.outSize.value.set(w * pr, h * pr);
        lagRendermaal(h * pr);
        maaTegnes = true;                   /* lerretet er toemt */
    }

    function settFilter(f) {
        filter = f;
        if (!postMat) return;               /* visningen er ikke laget ennaa; init bruker filteret */
        postMat.uniforms.mode.value = { skarp: 0, piksel: 1, myk: 2, crt: 3, glatt: 0 }[f] ?? 0;
        const modus = f === 'glatt' ? 2 : f === 'myk' ? 1 : 0;
        for (const m of [fbMat, bakAmigaMat, forMat, skyggeMat]) m.uniforms.modus.value = m === skyggeMat ? Math.min(modus, 1) : modus;
        /* lineaer: px() henter midt i texlene, saa det gir hele piksler ogsaa */
        for (const t of [fbTex, bakTex, forTex]) {
            t.magFilter = t.minFilter = THREE.LinearFilter;
            t.needsUpdate = true;
        }
        lagRendermaal(renderer ? renderer.getSize(new THREE.Vector2()).y * renderer.getPixelRatio() : 800);
        settRtFilter();
        maaTegnes = true;
    }

    function settFormat(f) { format = f; tilpass(); maaTegnes = true; }
    function settHelt(on) { helt = on; stabil = 99; maaTegnes = true; }

    function settEffekter(e) {
        Object.assign(effekter, e);
        if (!postMat) return;
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
            /* tegninger i bilder paa rad hoerer sammen, men en klynge varer hoeyst fire
             * bilder: tegner spillet i hvert bilde (inventaret), ville den ellers aldri
             * blitt vist og vokst uten grense */
            const k = klynger[klynger.length - 1];
            if (sistTegnet === bildeNr - 1 && k && bildeNr - k.start < 4 && k.liste.length < 2000) k.liste.push(...liste);
            else klynger.push({ liste: liste.slice(), start: bildeNr });
            klynger[klynger.length - 1].vis = bildeNr + 2;
            sistTegnet = bildeNr;
        }
    }

    /* forgrunnen innenfor et rektangel (lowres i spillets vindu), som en hash av
     * fargeindeksene: de endres ikke naar spillet toner inn eller ut med paletten */
    function rektHash(u, x0, y0, w, h) {
        const xa = Math.max(0, x0), ya = Math.max(0, y0), xb = Math.min(320, x0 + w), yb = Math.min(200, y0 + h);
        let s = 2166136261;
        for (let y = ya; y < yb; y++) {
            const o = y * 320;
            for (let x = xa; x < xb; x++) { s ^= u[o + x]; s = Math.imul(s, 16777619); }
        }
        return s >>> 0;
    }

    /* hvilke figurer som vises naa (se over) */
    function oppdaterViste(lag) {
        if (!lag) {
            plasserte.clear();
            while (klynger.length && klynger[0].vis <= bildeNr) {
                visteListe = klynger.shift().liste;
                visesFra = bildeNr;
            }
            /* spillet tegner figurene paa nytt flere ganger i sekundet; har det ikke
             * tegnet paa en stund er vi paa en skjerm uten figurer */
            if (visteListe.length && bildeNr - visesFra > 50) visteListe = [];
            return;
        }
        if (lag.hash !== sisteBakHash) { plasserte.clear(); sisteBakHash = lag.hash; }
        while (klynger.length && klynger[0].vis <= bildeNr) {
            for (const d of klynger.shift().liste) {
                const x = d.x - d.xoff, y = d.y, k = x + ',' + y + ',' + d.w + ',' + d.h;
                plasserte.delete(k);
                plasserte.set(k, { d, x, y, w: d.w, h: d.h, hash: rektHash(lag.forIdx, x, y, d.w, d.h) });
            }
        }
        for (const [k, p] of plasserte) if (rektHash(lag.forIdx, p.x, p.y, p.w, p.h) !== p.hash) plasserte.delete(k);
        if (plasserte.size > 2000) plasserte.clear();
        visteListe = [...plasserte.values()].map((p) => p.d);
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
        if (hdPaa && (visRammer || hdPakke.size)) {        /* «Original»: ingen HD-bilder og ingen gule felt */
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

        /* rammebufferet: lowres-piksel (x, y) er texelen (2x, y); utsnittet starter i crop */
        fbData.set(fb);
        fbTex.needsUpdate = true;
        fbMat.uniforms.region.value.set(crop[0] / 2, crop[1], lw, lh);
        plasser(fbMesh, 0, 0, lw, lh);
        fbMesh.visible = !lag || helt;          /* ellers dekker bakgrunnslaget alt */

        lagNaa = lag;
        const lx = diwNaa[0] / 2 - ux(), ly = diwNaa[1] - uy();
        if (lag) {
            const nokkel = 'bg/' + (lag.hash >>> 0).toString(16).padStart(8, '0');
            const hd = hdPaa ? hdPakke.get(nokkel) : null;
            const maks = Math.max(lysMaks.get(lag.hash) || 0, lag.lys);
            lysMaks.set(lag.hash, maks);
            hdLys = maks ? lag.lys / maks : 1;
            if (hd) {
                bakMesh.material = bakMat;
                bakMat.uniforms.map.value = hd.tex;
                bakMat.uniforms.texel.value.set(1 / 320, 1 / 200);
                bakMat.uniforms.lys.value = hdLys;
                bakMat.uniforms.uskarp.value = effekter.dybde ? 0.9 : 0;
            } else {
                bakMesh.material = bakAmigaMat;
                bakData.set(lag.bak);
                bakTex.needsUpdate = true;
                bakAmigaMat.uniforms.uskarp.value = effekter.dybde ? 0.9 : 0;
            }
            forData.set(lag.for);
            forTex.needsUpdate = true;
            plasser(bakMesh, lx, ly, 320, 200);
            plasser(forMesh, lx, ly, 320, 200);
            plasser(skyggeMesh, lx + 1.5, ly + 1.5, 320, 200);
        }
        if (!lag) hdLys = 1;
        oppdaterViste(lag);
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
        viste: () => visteListe.length,             /* figurer som vises med HD-bilde eller gult felt */
        maaTegnes: () => maaTegnes,
        utsnitt: () => crop.slice(),                /* delen av rammebufferet som vises (x0, y0, x1, y1) */
        brukerListe: () => hdPaa && (hdPakke.size > 0 || visRammer),   /* trengs tegnelisten fra kjernen? */
        /* trengs lagene fra kjernen? (HD-bakgrunner eller effekter som skiller lagene) */
        trengerLag: () => (hdPaa && hdPakke.size > 0) || effekter.skygge || effekter.dybde || tvungetLag,
        /* HD-grafikk eller originalen (bryteren i menyen) */
        settHd: (on) => { hdPaa = !!on; maaTegnes = true; },
        hdPaa: () => hdPaa,
        lagNaa: () => lagNaa,
        settTvungetLag: (on) => { tvungetLag = on; maaTegnes = true; },
    };
})();
