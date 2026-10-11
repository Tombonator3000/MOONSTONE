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
    let vernData, vernTex;                  /* senere originalfragmenter som skal dekke HD */
    let sceneVernData, sceneVernTex;
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
    let hdPaa = false;                      /* false: original grafikk, selv om en HD-pakke er lastet (standard) */
    let bildeNr = 0, sistTegnet = -99, klynger = [];
    let visteListe = [], visesFra = 0;
    let plasserte = new Map(), sisteBakHash = -1;    /* "x,y,b,h" -> { d, x, y, w, h, hash } */
    let nyesteMenypil = 0, menypilBakFra = 0;
    const flater = [];
    const sceneFlater = [];
    let rammeMat = null;
    let antallBg = 0;                       /* HD-bakgrunner i pakken */
    const originalCeler = new Map();        /* originale indekser, aldri preview-paletten */
    const hdTekstBanker = new Map();
    const hdIkoner = new Map();
    let hdIkonFeil = [];
    let hdMarkor = null;
    let hdTekstGlyfer = new Set();
    let hdTekstMeta = new Map();
    let hdTegnbare = new Set();
    let hdFigurLys = new Map();             /* ruter med verifisert egen fading */
    const hdPoser = new Map(), hdPoseKontrakter = new Map(), indeksHasher = new WeakMap(), bankHasher = new WeakMap();
    let hdPoseViste = [], hdPoseFeil = [];
    let hdPoseLaster = false, hdPoseUgyldig = false;
    let hdKontroll = { godkjent: 0, utenLag: 0, kilde: 0, overlapp: 0, piksler: 0 };

    const vertPost = `
        varying vec2 vUv;
        void main() { vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }`;
    const vertLag = `
        varying vec2 vUv;
        void main() { vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }`;

    const vertHd = `
        varying vec2 vUv, vPos;
        void main() {
            vUv = uv; vPos = (modelMatrix * vec4(position, 1.0)).xy;
            gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
        }`;
    const fragHd = `
        precision highp float;
        uniform sampler2D map, vern;
        uniform vec2 lagPos;
        uniform float lys;
        uniform vec4 imageRegion;
        uniform float alphaCutoff;
        varying vec2 vUv, vPos;
        void main() {
            vec2 p = vPos - lagPos;
            if (p.x >= 0.0 && p.y >= 0.0 && p.x < 320.0 && p.y < 200.0 &&
                texture2D(vern, (floor(p) + 0.5) / vec2(320.0, 200.0)).a > 0.5) discard;
            vec2 uv = imageRegion.xy + vUv * imageRegion.zw;
            if (uv.x < 0.0 || uv.y < 0.0 || uv.x > 1.0 || uv.y > 1.0) discard;
            vec4 c = texture2D(map, uv);
            if (c.a < alphaCutoff) discard;
            gl_FragColor = vec4(c.rgb * lys, c.a);
        }`;

    /* bakgrunnen: Amiga-laget eller et HD-bilde, med fading og eventuelt uskarphet */
    const fragBak = `
        precision highp float;
        uniform sampler2D map;
        uniform vec2 texel;        // en lowres-piksel i teksturkoordinater
        uniform float uskarp;      // 0 = skarp
        uniform float lys;         // fading for HD-bakgrunner
        uniform vec4 region;
        varying vec2 vUv;
        void main() {
            vec2 uv = (vUv - region.xy) / region.zw;
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

    let tapt = false, vedTapt = null, vedTilbake = null;

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
        /* Mobil kaster ofte grafikken naar appen gaar i bakgrunnen. three.js bygger den
         * opp igjen naar nettleseren gir den tilbake (teksturene lastes paa nytt); app.js
         * lagrer spillet med en gang og laster siden paa nytt hvis den ikke kommer. */
        canvas.addEventListener('webglcontextlost', (e) => { e.preventDefault(); tapt = true; if (vedTapt) vedTapt(); });
        canvas.addEventListener('webglcontextrestored', () => { tapt = false; maaTegnes = true; if (vedTilbake) vedTilbake(); });
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
            uniforms: { map: { value: bakTex }, texel: { value: new THREE.Vector2(1 / 320, 1 / 200) }, uskarp: { value: 0 }, lys: { value: 1 }, region: { value: new THREE.Vector4(0, 0, 1, 1) } },
            vertexShader: vertLag, fragmentShader: fragBak, side: THREE.DoubleSide, depthTest: false, depthWrite: false,
        });
        bakMesh = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), bakAmigaMat);
        bakMesh.renderOrder = 1;
        scene1.add(bakMesh);

        forData = new Uint8Array(320 * 200 * 4);
        forTex = dataTekstur(forData, 320, 200);
        vernData = new Uint8Array(320 * 200 * 4);
        vernTex = dataTekstur(vernData, 320, 200);
        sceneVernData = new Uint8Array(320*200*4);
        sceneVernTex = dataTekstur(sceneVernData,320,200);
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

    /* Bare den maalte pilen i originalens og nettutgavens tittelposisjoner. */
    function erTittelmenypil(d) {
        return d.fil.toLowerCase() === 'sel.cel' && d.bilde === 0 && d.w === 38 && d.h === 19 &&
            !d.speilet && d.xoff === 0 && d.x === 50 && [85, 110, 134, 148, 154, 168, 176].includes(d.y);
    }

    /* kalles etter hvert bilde emulatoren kjorer, med tegnelisten for bildet */
    function nyttBilde(liste) {
        bildeNr++;
        if (liste.length) {
            // Egen kopi: en nyere pil maa ogsaa kunne avlyse en eldre pil i koeen.
            liste = liste.map((d) => erTittelmenypil(d) ? { ...d, menypilNr: ++nyesteMenypil, menypilBilde: bildeNr } : d);
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
        if (lag.hash !== sisteBakHash) { plasserte.clear(); menypilBakFra = bildeNr; sisteBakHash = lag.hash; }
        while (klynger.length && klynger[0].vis <= bildeNr) {
            for (const d of klynger.shift().liste) {
                const ventMenypil = lag.hash === 0x55bb9767 && erTittelmenypil(d);
                if (ventMenypil && (d.menypilNr !== nyesteMenypil || d.menypilBilde < menypilBakFra)) continue;
                if (ventMenypil) for (const [gammel, p] of plasserte) if (erTittelmenypil(p.d)) plasserte.delete(gammel);
                // P/G stikker inn i pilens transparente hoeyrekant. Bare den
                // maalte originalglyfen som foelger pilen faar samme ventetid.
                const menybokstav = d.fil.toLowerCase() === 'bold.f' && !d.speilet && d.xoff === 0 && d.x === 86 && d.h === 19 &&
                    ((d.bilde === 15 && d.y === 83 && d.w === 17) || (d.bilde === 6 && d.y === 108 && d.w === 14));
                const bokstavPil = menybokstav ? [...plasserte.values()].find((p) => p.menypilKlar !== null && erTittelmenypil(p.d) &&
                    p.x < d.x + d.w && p.x + p.w > d.x && p.y < d.y + d.h && p.y + p.h > d.y) : null;
                const x = d.x - d.xoff, y = d.y, k = x + ',' + y + ',' + d.w + ',' + d.h;
                const hash = rektHash(lag.forIdx, x, y, d.w, d.h), forrige = plasserte.get(k);
                const erValgbilde = (v, min, maks) => v && v.fil.toLowerCase() === 'sel.cel' &&
                    v.w === 64 && v.h === 76 && !v.speilet && v.bilde >= min && v.bilde <= maks;
                // Bare den kjente cyan valgrammen kan beholde sitt portrett.
                // Begge originalkildene kontrolleres fortsatt pikselvis nedenfor.
                let underlag = null;
                if (erValgbilde(d, 1, 1)) {
                    if (erValgbilde(forrige?.d, 2, 5)) underlag = forrige.d;
                    else if (erValgbilde(forrige?.d, 1, 1) && forrige.hash === hash) underlag = forrige.underlag;
                }
                if (/^(bold\.f|small\.font)$/i.test(d.fil)) for (const [gammel,p] of plasserte) {
                    if (p.x===x && p.y===y && p.d.fil.toLowerCase()===d.fil.toLowerCase()) plasserte.delete(gammel);
                }
                plasserte.delete(k);
                plasserte.set(k, { d, x, y, w: d.w, h: d.h, hash, underlag,
                    menypilKlar: ventMenypil ? bildeNr + 2 : (bokstavPil?.menypilKlar ?? null),
                    ventPilNr: ventMenypil ? d.menypilNr : bokstavPil?.ventPilNr });
            }
        }
        for (const [k, p] of plasserte) {
            if (p.menypilKlar !== null) {
                if (p.ventPilNr !== nyesteMenypil) { plasserte.delete(k); continue; }
                if (bildeNr < p.menypilKlar) continue;
                // Menyen bygger skjermen over flere bilder. Ikke vis pilen foer
                // siste skjermbytte; deretter gjelder vanlig pikselvalidering.
                p.hash = rektHash(lag.forIdx, p.x, p.y, p.w, p.h);
                p.menypilKlar = null;
            }
            // Tekst bygges over flere bilder med overlappende skygger. Valider
            // hele raden nedenfor; et endret nabotegn maa ikke slette bokstaven.
            const tekst = /^(bold\.f|small\.font)$/i.test(p.d.fil);
            if (!tekst && rektHash(lag.forIdx, p.x, p.y, p.w, p.h) !== p.hash) plasserte.delete(k);
        }
        if (plasserte.size > 2000) plasserte.clear();
        visteListe = [...plasserte.values()].filter((p) => p.menypilKlar === null).flatMap((p) => p.underlag ? [p.underlag, p.d] : [p.d]);
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

    /* Les gjeldende spillfil, ogsaa etter at egne filer eller en nettvert bytter den.
     * Byte-sammenligningen hindrer at en gammel maske brukes til en ny CEL-fil. */
    function originalCel(fil, lest) {
        const navn = fil.toLowerCase();
        if (lest.has(navn)) return lest.get(navn);
        let bilder = null;
        try {
            if (typeof Kjerne !== 'undefined' && typeof Spillgrafikk !== 'undefined') {
                const data = Kjerne.hentFil('data/' + fil);
                if (data && data.length >= 20) {
                    const gammel = originalCeler.get(navn);
                    if (gammel && data.length === gammel.data.length && data.every((v, i) => v === gammel.data[i])) bilder = gammel.bilder;
                    else {
                        const n = data[0] * 256 + data[1];
                        const long = (p) => ((data[p] << 24) | (data[p + 1] << 16) | (data[p + 2] << 8) | data[p + 3]) >>> 0;
                        let gyldig = n > 0 && n <= 2000 && 10 + n * 10 + long(2) <= data.length;
                        for (let i = 0; gyldig && i < n; i++) {
                            const e = 10 + i * 10, w = data[e + 4] * 256 + data[e + 5], h = data[e + 6] * 256 + data[e + 7];
                            if (w > 320 || h > 200 || long(e) + ((w + 15) >> 4) * 2 * h * 8 > 4 * 1024 * 1024) gyldig = false;
                        }
                        if (gyldig) {
                            bilder = Spillgrafikk._cel(data).map((g, i) => {
                                const maske = data[19 + i * 10];
                                g.planmaske = maske;
                                if (maske > 31) return null;
                                // CEL lagrer bare planene som er satt i masken.
                                // F.eks. $17 betyr bit 0,1,2,4, ikke bit 0..3.
                                if (maske & (maske + 1)) {
                                    const bits = [1,2,4,8,16].filter(b => maske & b);
                                    g.px = g.px.map(v => bits.reduce((n,b,i) => n | ((v & (1 << i)) ? b : 0), 0));
                                }
                                return g;
                            });
                            originalCeler.set(navn, { data, bilder });
                            forvarmPoseIndekser(navn, bilder);
                            for (const m of hdIkoner.values()) if (m.source.file === navn && bilder[m.source.frame]) indeksHash(bilder[m.source.frame]);
                        }
                    }
                }
            }
        } catch (e) { /* ingen paalitelig kilde: behold originalen */ }
        lest.set(navn, bilder);
        return bilder;
    }

    async function sha256(data) {
        if (!globalThis.crypto?.subtle) throw new Error('SHA256 er ikke tilgjengelig');
        const hash = new Uint8Array(await crypto.subtle.digest('SHA-256', data));
        return Array.from(hash, (b) => b.toString(16).padStart(2, '0')).join('');
    }

    function bankHash(bank) {
        if (!bankHasher.has(bank)) {
            const verdi = { hash: null, venter: null };
            verdi.venter = sha256(bank.data).then((hash) => { verdi.hash = hash; maaTegnes = true; }).catch(() => {});
            bankHasher.set(bank, verdi);
        }
        return bankHasher.get(bank);
    }

    /* Hash beregnes bare for en ny, dekodet kilde. En endret CEL faar nye objekter.
     * Foer hashen er klar, vises originalen. Ingen venting i spillokka. */
    function indeksHash(g) {
        if (!indeksHasher.has(g)) {
            indeksHasher.set(g, null);
            sha256(g.px).then((hash) => { indeksHasher.set(g, hash); maaTegnes = true; }).catch(() => {});
        }
        return indeksHasher.get(g);
    }

    /* Naar en bank allerede er dekodet, start ogsaa hashene til de andre
     * manifestmedlemmene i den banken. De forberedes asynkront foer neste pose
     * blir synlig. Byte-invalidering lager fortsatt nye objekter, og hver pose
     * maa fortsatt bestaa de samme kilde-, palett- og pikselkontrollene. */
    function forvarmPoseIndekser(navn, bilder) {
        for (const pose of hdPoseKontrakter.values()) for (const m of pose.members) {
            if (m.file !== navn) continue;
            const g = bilder[m.frame];
            if (g && g.w === m.width && g.h === m.height && g.planmaske === m.plane_mask) indeksHash(g);
        }
    }

    function overlapper(x, y, w, h, d) {
        const dx = d.x - d.xoff;
        return x < dx + d.w && x + w > dx && y < d.y + d.h && y + h > d.y;
    }

    /* Nabobokstaven overskriver skyggen til forrige bokstav. Valider derfor
     * hele originalraden i tegnerekkefolge foer HD-glyfene erstatter den.
     * Dette virker ogsaa for endrede tall/ord; ingen menytitler hardkodes. */
    function forberedTekst(lag, lest) {
        const reservert = new Set(), grupper = new Map();
        if (!lag?.forIdx) return reservert;
        // Engangstegningen kan ha skjedd mens pakken lastet. Gjenfinn bare
        // den originale pilens ikke-overlappende kropp i kjente menyposisjoner.
        if (lag.hash === 0x55bb9767 && !visteListe.some(erTittelmenypil)) {
            const g = originalCel('sel.cel', lest)?.[0];
            if (g?.w === 38 && g.h === 19) {
                const funnet = [];
                for (const y of [85,110,134,148,154,168,176]) {
                    let gyldig = true, n = 0;
                    for (let j=0;j<19 && gyldig;j++) for (let i=0;i<36;i++) {
                        const c=g.px[j*38+i]; if (!c) continue;
                        const p=(y+j)*320+50+i, actual=lag.forIdx[p];
                        if (actual===c || (actual===255 && lag.bakIdx?.[p]===c)) n++;
                        else { gyldig=false; break; }
                    }
                    if (gyldig && n>100) funnet.push({fil:'sel.cel',bilde:0,x:50,y,w:38,h:19,xoff:0,speilet:false});
                }
                if (funnet.length===1) visteListe.push(funnet[0]);
            }
        }
        for (const d of visteListe) {
            const navn = d.fil.toLowerCase(), key = navn + '/' + String(d.bilde).padStart(3, '0');
            if (!hdTekstGlyfer.has(key) || !hdPakke.has(key)) continue;
            reservert.add(d);
            const g = originalCel(navn, lest)?.[d.bilde], bank = originalCeler.get(navn);
            if (!g || !bank || bankHash(bank).hash !== hdTekstBanker.get(navn) || d.speilet ||
                g.w !== d.w || g.h !== d.h || !Number.isInteger(d.x - d.xoff) || !Number.isInteger(d.y)) continue;
            const rad = navn + ':' + d.y + ':' + d.h;
            if (!grupper.has(rad)) grupper.set(rad, []);
            grupper.get(rad).push({ d, g, x: d.x - d.xoff });
        }
        const felt = [];
        for (const rad of grupper.values()) {
            let gruppe=[], slutt=-999;
            for (const p of rad.slice().sort((a,b)=>a.x-b.x)) {
                if (gruppe.length && p.x > slutt + Math.max(8,p.d.w)) { felt.push(gruppe); gruppe=[]; }
                gruppe.push(p); slutt=Math.max(slutt,p.x+p.d.w);
            }
            if (gruppe.length) felt.push(gruppe);
        }
        const scan = typeof Kjerne !== 'undefined' ? Kjerne.skanout() : null;
        for (const gruppe of felt) {
            const x = Math.max(0, Math.min(...gruppe.map(p => p.x))), y = gruppe[0].d.y;
            const w = Math.min(320, Math.max(...gruppe.map(p => p.x + p.d.w))) - x, h = gruppe[0].d.h;
            if (y < 0 || y + h > 200 || w <= 0) continue;
            const maske = new Uint8Array(w * h), medlemmer = new Set(gruppe.map(p => p.d));
            for (const p of gruppe) for (let j = 0; j < h; j++) for (let i = 0; i < p.d.w; i++) {
                const v = p.g.px[j * p.d.w + i], dx = p.x + i - x;
                if (v && dx >= 0 && dx < w) maske[j * w + dx] = v;
            }
            const over = visteListe.filter(d => !medlemmer.has(d) && overlapper(x, y, w, h, d))
                .map(d => ({d, g: originalCel(d.fil, lest)?.[d.bilde], x: d.x - d.xoff}));
            const fjern = [], vern = [];
            let gyldig = true;
            for (let j = 0; gyldig && j < h; j++) for (let i = 0; i < w; i++) {
                let c = maske[j * w + i];
                const p = (y + j) * 320 + x + i;
                let faktisk = lag.forIdx[p];
                // $FE betyr en palettendring, mens den faktiske indeksen
                // fremdeles kan kontrolleres mot den originale glyfen.
                if (faktisk===254 && scan?.gyldig) faktisk=scan.idx[(diwNaa[1]+y+j)*720+diwNaa[0]+(x+i)*2];
                if (c && faktisk === c) { fjern.push(p); continue; }
                if (faktisk === 255 && (!c || lag.bakIdx?.[p] === c)) continue;
                const dekket = over.some(o => {
                    const ox = x + i - o.x, oy = y + j - o.d.y;
                    return o.g && ox >= 0 && ox < o.g.w && oy >= 0 && oy < o.g.h &&
                        o.g.px[oy * o.g.w + (o.d.speilet ? o.g.w - 1 - ox : ox)] === faktisk;
                });
                if (dekket) vern.push(p);
                else { hdKontroll.tekstFeil.push({ x: x+i, y: y+j, wanted: c, actual: faktisk,
                    frames: gruppe.map(p => p.d.bilde) }); gyldig = false; break; }
            }
            if (!gyldig || !fjern.length) { hdKontroll.tekstAvvist++; continue; }
            for (const p of fjern) forData[p * 4 + 3] = 0;
            for (const p of vern) vernData[p * 4 + 3] = 255;
            for (const p of gruppe) hdTegnbare.add(p.d);
            hdKontroll.tekstGodkjent += gruppe.length;
        }
        return reservert;
    }

    /* I tittelbildet er fontens svarte indeks 5 ogsaa brukt i bakgrunnen.
     * Laget utelater derfor enkelte ekte tekstpiksler. Bare de kildeverifiserte
     * tittelfeltene nedenfor kan faa tilbake denne alfaen over en HD-bakgrunn.
     * Ingen nye tegn beholdes, og endret tekst/palett/kilde gir originalfallback. */
    function bevarTitteltekst(lag, lest) {
        if (!lag || lag.hash !== 0x55bb9767 || !hdPakke.has('bg/55bb9767') ||
            !lag.forIdx || lag.forIdx.length !== 64000 || !lag.for || !lag.bak) return;
        const bilder = originalCel('bold.f', lest), bank = originalCeler.get('bold.f');
        if (!bilder || !bank) return;
        if (bankHash(bank).hash !== '2aec40683ea11d9eed6000e1a32731d65ff1682b89298e5469adeb136fa996f8') return;
        // Logo, Players, Gore og de maalte verdiene 1 / On. Andre verdier
        // eller en oversatt/endret meny maa verifiseres separat.
        const felt = [
            [10, [[73, 5]]],
            [83, [[15, 86], [37, 100], [26, 105], [50, 115], [30, 124], [43, 132], [44, 141]]],
            [108, [[6, 86], [40, 97], [43, 106], [30, 115]]],
            [83, [[53, 214], [69, 218], [69, 230]]],
            [108, [[14, 214], [39, 225]]],
        ];
        const kjent = (d) => d.fil.toLowerCase() === 'bold.f' && !d.speilet && d.xoff === 0 &&
            felt.some(([y, ruter]) => d.y === y && ruter.some(([n, x]) => n === d.bilde && x === d.x &&
                bilder[n]?.w === d.w && bilder[n]?.h === d.h));
        const pil = visteListe.find(erTittelmenypil), pilKilde = pil ? originalCel(pil.fil, lest)?.[0] : null;
        const svart = (data, p) => data[p * 4] === 0 && data[p * 4 + 1] === 0 && data[p * 4 + 2] === 0 && data[p * 4 + 3] === 255;
        let verifiserte = 0;
        for (const [y, ruter] of felt) {
            if (ruter.some(([n]) => !bilder[n] || hdPakke.has('bold.f/' + String(n).padStart(3, '0')))) continue;
            const x = Math.min(...ruter.map(([, x]) => x)), h = bilder[ruter[0][0]].h;
            const w = Math.max(...ruter.map(([n, x]) => x + bilder[n].w)) - x;
            if (ruter.some(([n]) => bilder[n].h !== h) ||
                visteListe.some((d) => overlapper(x, y, w, h, d) && !kjent(d) && d !== pil)) continue;
            // Nabobokstavene overskriver svarte skygger. Bruk original rekkefolge
            // til en samlet maske foer noen piksel valideres eller endres.
            const maske = new Uint8Array(w * h);
            for (const [n, gx] of ruter) {
                const g = bilder[n];
                for (let j = 0; j < h; j++) for (let i = 0; i < g.w; i++) {
                    const c = g.px[j * g.w + i];
                    if (c) maske[j * w + gx - x + i] = c;
                }
            }
            let gyldig = true, synlig = 0;
            const gjenopprett = [];
            for (let j = 0; gyldig && j < h; j++) for (let i = 0; i < w; i++) {
                const c = maske[j * w + i], p = (y + j) * 320 + x + i, faktisk = lag.forIdx[p];
                if (!c) {
                    if (faktisk === 255) continue;
                    const px = x + i - (pil?.x ?? -999), py = y + j - (pil?.y ?? -999);
                    if (pilKilde && pilKilde.w === 38 && pilKilde.h === 19 && px >= 0 && px < 38 && py >= 0 && py < 19 &&
                        pilKilde.px[py * 38 + px] === faktisk) continue;
                    gyldig = false; break;
                }
                if (faktisk === c && (c !== 5 || svart(lag.for, p))) { synlig++; continue; }
                if (c === 5 && faktisk === 255 && svart(lag.bak, p)) { gjenopprett.push(p); continue; }
                gyldig = false; break;
            }
            if (!gyldig || !synlig) continue;
            verifiserte++;
            for (const p of gjenopprett) {
                forData.set(lag.bak.subarray(p * 4, p * 4 + 4), p * 4);
                vernData[p * 4 + 3] = 255;
            }
        }
        return verifiserte === felt.length;
    }

    /* Et posemanifest eier sine medlemruter mens det er lastet. Hvis gruppen ikke
     * er komplett, brukes originalen for disse rutene, ikke loese HD-fragmenter.
     * Andre enkeltfragmenter beholder den eksisterende behandlingen. */
    function forberedPoser(lag, lest) {
        const reservert = new Set(), kandidater = [];
        if (hdPoseLaster || hdPoseUgyldig) return new Set(visteListe);
        for (const pose of hdPoseKontrakter.values()) for (const d of visteListe) {
            if (pose.members.some((m) => m.file === d.fil.toLowerCase() && m.frame === d.bilde)) reservert.add(d);
        }
        for (const pose of hdPoser.values()) {
            const forste = pose.members[0];
            for (const anker of visteListe) {
                if (anker.fil.toLowerCase() !== forste.file || anker.bilde !== forste.frame) continue;
                const speilet = !!anker.speilet;
                if (pose.mirror !== 'both' && (pose.mirror === 'mirrored') !== speilet) { hdKontroll.poseGruppe++; continue; }
                const x = anker.x - anker.xoff - (speilet ? pose.width - forste.x - forste.width : forste.x);
                const y = anker.y - forste.y;
                const gruppe = [], masker = [];
                let gyldig = Number.isInteger(x) && Number.isInteger(y) && x >= 0 && y >= 0 && x + pose.width <= 320 && y + pose.height <= 200;
                let forrige = -1;
                for (const m of pose.members) {
                    const mx = x + (speilet ? pose.width - m.x - m.width : m.x), my = y + m.y;
                    const funnet = visteListe.filter((d) => d.fil.toLowerCase() === m.file && d.bilde === m.frame &&
                        d.x - d.xoff === mx && d.y === my && d.w === m.width && d.h === m.height && !!d.speilet === speilet);
                    if (funnet.length !== 1 || visteListe.indexOf(funnet[0]) <= forrige) { gyldig = false; break; }
                    forrige = visteListe.indexOf(funnet[0]); gruppe.push(funnet[0]);
                }
                if (!gyldig) { hdKontroll.poseGruppe++; continue; }
                if (!lag || !lag.forIdx || lag.forIdx.length !== 64000 || !lag.for || !lag.bak) { hdKontroll.utenLag++; continue; }
                // Alle fremmede rektangler avvises, ogsaa senere og delvis transparente.
                if (visteListe.some((d) => !gruppe.includes(d) && overlapper(x, y, pose.width, pose.height, d))) { hdKontroll.poseOverlapp++; continue; }
                for (const m of pose.members) {
                    const g = originalCel(m.file, lest)?.[m.frame];
                    if (!g || g.w !== m.width || g.h !== m.height || g.planmaske !== m.plane_mask || indeksHash(g) !== m.indices_sha256) { gyldig = false; break; }
                    masker.push(g);
                }
                if (!gyldig) { hdKontroll.poseKilde++; continue; }
                const indeks = new Uint8Array(pose.width * pose.height);
                for (let k = 0; k < pose.members.length; k++) {
                    const m = pose.members[k], g = masker[k];
                    for (let j = 0; j < m.height; j++) for (let i = 0; i < m.width; i++) {
                        const c = g.px[j * m.width + i];
                        if (c) indeks[(m.y + j) * pose.width + m.x + i] = c;
                    }
                }
                const fjern = [], sett = new Set();
                let palettFeil = false;
                for (let j = 0; gyldig && j < pose.height; j++) for (let i = 0; i < pose.width; i++) {
                    const c = indeks[j * pose.width + (speilet ? pose.width - 1 - i : i)];
                    const p = (y + j) * 320 + x + i, faktisk = lag.forIdx[p];
                    if (!c) { if (faktisk !== 255) { gyldig = false; break; } continue; }
                    if (faktisk !== 255 && faktisk !== c) { gyldig = false; break; }
                    const rgba = faktisk === 255 ? lag.bak : lag.for, forventet = pose.palette[c];
                    if (!forventet || forventet.some((v, n) => rgba[p * 4 + n] !== v)) { gyldig = false; palettFeil = true; break; }
                    if (faktisk !== 255) { fjern.push(p); sett.add(c); }
                }
                if (gyldig && pose.identity_indices.some((c) => !sett.has(c))) { gyldig = false; palettFeil = true; }
                if (!gyldig || !fjern.length) { hdKontroll[palettFeil ? 'posePalett' : 'posePiksler']++; continue; }
                // Samme indeks fra en ukjent tegner er fortsatt uten eget pikseleierskap.
                // Ingen rektangler slettes: bare de kildepikslene som ble kontrollert over.
                kandidater.push({ pose, x, y, speilet, fjern });
            }
        }
        for (const p of kandidater) {
            if (kandidater.some((o) => o !== p && p.x < o.x + o.pose.width && p.x + p.pose.width > o.x &&
                p.y < o.y + o.pose.height && p.y + p.pose.height > o.y)) { hdKontroll.poseOverlapp++; continue; }
            for (const i of p.fjern) forData[i * 4 + 3] = 0;
            hdPoseViste.push(p);
            hdKontroll.poseGodkjent++; hdKontroll.godkjent++;
        }
        return reservert;
    }

    /* Next Day fyller himmelen i forgrunnen; baklaget kan fortsatt inneholde
     * titteltegningen. Det er derfor ikke trygt aa slette maanens alfamaske.
     * Originale 045–049, hele rektangelet og alle 16 innfadepaletter er maalt
     * i review/ki-moon-source. Ingen andre KI-ruter arver denne kontrakten. */
    function forberedMaane(d, g, lag, foran) {
        const bank = originalCeler.get('ki.cel');
        if (!bank || bankHash(bank).hash !== '02287e8990919c21e62cf94142d60d9a5fbd0573df5be283eb6e31d367071104' ||
            d.x !== 119 || d.y !== 12 || d.xoff !== 0 || d.speilet || d.w !== 57 || d.h !== 44 ||
            !lag.for || lag.for.length !== 256000 || !lag.bak || lag.bak.length !== 256000) {
            hdKontroll.kilde++; return;
        }
        if (foran.length) { hdKontroll.overlapp++; return; }
        const palett = [0x000, 0xdef, 0xabc, 0x789, 0x567, 0x000, 0x123, 0x321,
            0x210, 0xfed, 0xdc9, 0xc95, 0x842, 0x066, 0x034, 0x002];
        // Indeks 1 finnes i alle fem ruter og har maksimal blaakomponent.
        const s = g.px.indexOf(1), anker = (12 + Math.floor(s / 57)) * 320 + 119 + s % 57;
        if (s < 0) { hdKontroll.kilde++; return; }
        const ankerLag = lag.forIdx[anker] === 255 ? lag.bak : lag.for;
        const nivaa = ankerLag[anker * 4 + 2] / 17;
        if (!Number.isInteger(nivaa) || nivaa < 0 || nivaa > 15) { hdKontroll.piksler++; return; }
        // Maalt fading klipper hver 4-bits fargekomponent til nivaa 0–15.
        // Kontroller ogsaa $FF-piksler mot baklaget. De er ikke tomme bevis.
        for (let j = 0; j < 44; j++) for (let i = 0; i < 57; i++) {
            const p = (12 + j) * 320 + 119 + i, c = g.px[j * 57 + i] || 15;
            const indeks = lag.forIdx[p], rgba = indeks === 255 ? lag.bak : lag.for;
            const farge = palett[c];
            if ((indeks !== 255 && indeks !== c) || rgba[p * 4 + 3] !== 255 ||
                rgba[p * 4] !== Math.min(farge >> 8 & 15, nivaa) * 17 ||
                rgba[p * 4 + 1] !== Math.min(farge >> 4 & 15, nivaa) * 17 ||
                rgba[p * 4 + 2] !== Math.min(farge & 15, nivaa) * 17) {
                hdKontroll.piksler++; return;
            }
        }
        // Foerst etter full kontroll: behold riktig himmel under fotoets alfa.
        const himmel = [0, 0, Math.min(2, nivaa) * 17, 255];
        for (let j = 0; j < 44; j++) for (let i = 0; i < 57; i++)
            forData.set(himmel, ((12 + j) * 320 + 119 + i) * 4);
        hdFigurLys.set(d, nivaa / 15);
        hdTegnbare.add(d);
        hdKontroll.godkjent++;
    }

    /* Gjenkjente figurer kan erstattes, med senere originalfragmenter foran seg.
     * Listen har ikke pikseleierskap for andre tegnerutiner. Ved tvetydig overlapp,
     * ukjente forgrunnspiksler eller feil maske beholder vi hele originalfiguren.
     * $FF betyr at pikselen allerede er lik bakgrunnen; den slettes aldri her.
     * Vi rydder bare kildepiksler som har samme indeks i den viste forgrunnen,
     * ikke rektangelet og ikke pikslene fra en eksportert preview-palett. */
    function forberedHd(lag) {
        hdTegnbare = new Set();
        hdFigurLys = new Map();
        hdPoseViste = [];
        hdKontroll = { godkjent: 0, utenLag: 0, kilde: 0, overlapp: 0, piksler: 0,
            poseGodkjent: 0, poseGruppe: 0, poseKilde: 0, posePalett: 0, poseOverlapp: 0, posePiksler: 0,
            tekstGodkjent: 0, tekstAvvist: 0, tekstFeil: [] };
        hdKontroll.ikonGodkjent = 0; hdKontroll.ikonAvvist = 0;
        hdMarkor=null;
        vernData.fill(0);
        vernTex.needsUpdate = true;
        if (!hdPaa || (!hdPakke.size && !hdPoser.size)) return;
        const lest = new Map();
        const reservert = forberedPoser(lag, lest);
        for (const d of forberedTekst(lag, lest)) reservert.add(d);
        forberedMarkor(lag,lest);
        for (let nr = 0; nr < visteListe.length; nr++) {
            const d = visteListe[nr];
            if (reservert.has(d)) continue;
            if (!hdPakke.has(d.fil.toLowerCase() + '/' + String(d.bilde).padStart(3, '0'))) continue;
            if (!lag || !lag.forIdx || lag.forIdx.length !== 320 * 200) { hdKontroll.utenLag++; continue; }
            const g = originalCel(d.fil, lest)?.[d.bilde], x = d.x - d.xoff, y = d.y;
            if (!g || g.w !== d.w || g.h !== d.h || !Number.isInteger(x) || !Number.isInteger(y)) { hdKontroll.kilde++; continue; }
            const ikey = d.fil.toLowerCase() + '/' + String(d.bilde).padStart(3, '0'), ikon = hdIkoner.get(ikey);
            if (ikon && (bankHash(originalCeler.get(d.fil.toLowerCase())).hash !== ikon.source.bank_sha256 ||
                indeksHash(g) !== ikon.indices_sha256 || g.planmaske !== ikon.plane_mask ||
                !fargeleggIkon(ikon, hdPakke.get(ikey), y))) { hdKontroll.ikonAvvist++; continue; }
            const foran = [];
            let tvetydig = false;
            for (let k = 0; k < visteListe.length; k++) {
                const o = visteListe[k], ox = o.x - o.xoff;
                if (o === d || x >= ox + o.w || x + d.w <= ox || y >= o.y + o.h || y + d.h <= o.y) continue;
                const og = originalCel(o.fil, lest)?.[o.bilde];
                if (hdTegnbare.has(o) && hdTekstGlyfer.has(o.fil.toLowerCase() + '/' + String(o.bilde).padStart(3, '0')) && og) {
                    foran.push({ d: o, g: og, x: ox, hdTekst: true }); continue;
                }
                if (k < nr || hdPakke.has(o.fil.toLowerCase() + '/' + String(o.bilde).padStart(3, '0')) || !og || og.w !== o.w || og.h !== o.h) { tvetydig = true; break; }
                foran.push({ d: o, g: og, x: ox });
            }
            if (tvetydig) { hdKontroll.overlapp++; continue; }
            if (d.fil.toLowerCase() === 'ki.cel' && d.bilde >= 45 && d.bilde <= 49) {
                forberedMaane(d, g, lag, foran);
                continue;
            }
            const fjern = [], beskytt = [];
            let gyldig = true;
            for (let j = 0; gyldig && j < d.h; j++) {
                if (y + j < 0 || y + j >= 200) continue;
                for (let i = 0; i < d.w; i++) {
                    if (x + i < 0 || x + i >= 320) continue;
                    const p = (y + j) * 320 + x + i, indeks = lag.forIdx[p];
                    if (hdMarkor?.visible.has(p)) continue;
                    let over = 0, hdOver = false;
                    for (const o of foran) {
                        const oi = x + i - o.x, oj = y + j - o.d.y;
                        if (oi >= 0 && oj >= 0 && oi < o.d.w && oj < o.d.h) {
                            const c = o.g.px[oj * o.d.w + (o.d.speilet ? o.d.w - 1 - oi : oi)];
                            if (c) { over = c; hdOver = !!o.hdTekst; }
                        }
                    }
                    if (over) {
                        if (indeks !== 255 && indeks !== over) { gyldig = false; break; }
                        if (!hdOver) beskytt.push(p);
                        continue;
                    }
                    if (indeks === 255) continue;
                    const c = g.px[j * d.w + (d.speilet ? d.w - 1 - i : i)];
                    if (!c || c !== indeks) { gyldig = false; break; }
                    fjern.push(p);
                }
            }
            if (!gyldig || !fjern.length) { hdKontroll.piksler++; continue; }
            for (const p of fjern) forData[p * 4 + 3] = 0;
            for (const p of beskytt) vernData[p * 4 + 3] = 255;
            hdTegnbare.add(d);
            if (ikon) { hdFigurLys.set(d, 1); hdKontroll.ikonGodkjent++; }
            hdKontroll.godkjent++;
        }
        if (hdMarkor) for (const p of hdMarkor.visible) vernData[p*4+3]=0;
        return (lag?.hash === 0x55bb9767 && visteListe.some(d => d.fil.toLowerCase() === 'bold.f' &&
            d.bilde === 73 && hdTegnbare.has(d))) || bevarTitteltekst(lag, lest);
    }

    let hdLys = 1;                          /* fading for HD-bildene, fra paletten (lagene) */
    function tegnHd() {
        let n = 0;
        for (const m of sceneFlater) m.visible = false;
        // Faste landemerker ligger over terrenget og under originale markorer.
        if (hdPaa && lagNaa?.overlays && hdPakke.has('bg/' + (lagNaa.hash >>> 0).toString(16).padStart(8,'0'))) {
            let i = 0;
            for (const o of lagNaa.overlays) {
                const t = hdPakke.get(o.key); if (!t) continue;
                const ikon = hdIkoner.get(o.key);
                if (ikon && !fargeleggIkon(ikon,t,o.rect[1])) continue;
                if (!sceneFlater[i]) {
                    const m = new THREE.Mesh(new THREE.PlaneGeometry(1,1),t.mat);
                    hdGruppe.add(m); sceneFlater[i] = m;
                }
                const m=sceneFlater[i++], [x0,y0,x1,y1]=o.rect;
                m.renderOrder=o.foreground ? 4 : 2.5;
                m.material=t.mat; t.mat.uniforms.imageRegion.value.set(...o.uv_rect);
                t.mat.uniforms.vern.value=o.foreground ? sceneVernTex : vernTex;
                t.mat.uniforms.alphaCutoff.value=o.alpha_cutoff || 0;
                t.mat.uniforms.lys.value=ikon ? 1 : hdLys;
                t.mat.uniforms.lagPos.value.set(diwNaa[0]/2-ux(),diwNaa[1]-uy());
                plasser(m,diwNaa[0]/2+x0-ux(),diwNaa[1]+y0-uy(),x1-x0,y1-y0);m.visible=true;
            }
        }
        if (hdPaa && (visRammer || hdPakke.size || hdPoser.size)) {        /* «Original»: ingen HD-bilder og ingen gule felt */
            for (const d of visteListe) {
                const nokkel = d.fil.toLowerCase() + '/' + String(d.bilde).padStart(3, '0');
                const t = hdTegnbare.has(d) ? hdPakke.get(nokkel) : null;
                if (!t && !visRammer) continue;
                const x = diwNaa[0] / 2 + d.x - d.xoff - ux(), y = diwNaa[1] + d.y - uy();
                const m = flate(n++);
                m.material = t ? t.mat : rammeMat;
                if (t) {
                    t.mat.uniforms.lys.value = hdFigurLys.get(d) ?? hdLys;
                    t.mat.uniforms.lagPos.value.set(diwNaa[0] / 2 - ux(), diwNaa[1] - uy());
                }
                plasser(m, x, y, d.w, d.h);
                if (d.speilet) m.scale.x = -d.w;           /* negativ bredde snur bildet */
                m.visible = true;
            }
            for (const p of hdPoseViste) {
                const m = flate(n++), t = p.pose.texture;
                m.material = t.mat;
                // Varianten krever eksakt originalpalett. Den tones ikke en gang til.
                t.mat.uniforms.lys.value = 1;
                t.mat.uniforms.lagPos.value.set(diwNaa[0] / 2 - ux(), diwNaa[1] - uy());
                plasser(m, diwNaa[0] / 2 + p.x - ux(), diwNaa[1] + p.y - uy(), p.pose.width, p.pose.height);
                if (p.speilet) m.scale.x = -p.pose.width;
                m.visible = true;
            }
            if (hdMarkor) {
                const {x,y,meta,t}=hdMarkor,m=flate(n++);
                m.material=t.mat;t.mat.uniforms.lys.value=1;
                t.mat.uniforms.lagPos.value.set(diwNaa[0]/2-ux(),diwNaa[1]-uy());
                plasser(m,diwNaa[0]/2+x-ux(),diwNaa[1]+y-uy(),meta.width,meta.height);m.visible=true;
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
        sceneVernData.fill(0);
        if (lag?.sceneVern) for (let p=0;p<64000;p++) if (lag.sceneVern[p]) sceneVernData[p*4+3]=255;
        sceneVernTex.needsUpdate=true;
        const lx = diwNaa[0] / 2 - ux(), ly = diwNaa[1] - uy();
        if (lag) {
            const nokkel = 'bg/' + (lag.hash >>> 0).toString(16).padStart(8, '0');
            const hd = hdPaa ? hdPakke.get(nokkel) : null;
            const maks = Math.max(lysMaks.get(lag.hash) || 0, lag.lys);
            lysMaks.set(lag.hash, maks);
            hdLys = maks ? lag.lys / maks : 0;
            if (hd) {
                bakMesh.material = bakMat;
                bakMat.uniforms.map.value = hd.tex;
                bakMat.uniforms.texel.value.set(1 / 320, 1 / 200);
                bakMat.uniforms.lys.value = hdLys;
                const r = lag.hdRect || [0,0,320,200];
                bakMat.uniforms.region.value.set(r[0]/320,r[1]/200,(r[2]-r[0])/320,(r[3]-r[1])/200);
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
        const titteltekstKlar = forberedHd(lag);
        // Ved sen pakkeinnlasting kan den opprinnelige engangstegningen av
        // pilen mangle i tegnelisten. Behold original bakgrunn til hele den
        // kjente tekstkontrakten passer, fremfor aa vise hull i svarte tegn.
        if (hdPaa && lag?.hash === 0x55bb9767 && hdPakke.has('bg/55bb9767') && !titteltekstKlar) {
            bakMesh.material = bakAmigaMat;
            bakData.set(lag.bak);
            bakTex.needsUpdate = true;
            bakAmigaMat.uniforms.uskarp.value = effekter.dybde ? 0.9 : 0;
        }
        bakMesh.visible = forMesh.visible = !!lag;
        skyggeMesh.visible = !!lag && effekter.skygge;
        tegnHd();
        renderer.setRenderTarget(rt);
        renderer.render(scene1, kamera1);
        renderer.setRenderTarget(null);
        renderer.render(scene2, kamera2);
    }

    async function hdTekstur(f, region) {
        const bilde = await createImageBitmap(f);
        const lerret = document.createElement('canvas');
        lerret.width = bilde.width; lerret.height = bilde.height;
        lerret.getContext('2d').drawImage(bilde, 0, 0);
        bilde.close();
        const t = new THREE.Texture(lerret);
        t.colorSpace = THREE.NoColorSpace;
        t.flipY = false;
        t.generateMipmaps = false;
        t.minFilter = THREE.LinearFilter;
        t.needsUpdate = true;
        return { tex: t, canvas: lerret, width: lerret.width, height: lerret.height, mat: new THREE.ShaderMaterial({
            uniforms: { map: { value: t }, vern: { value: vernTex }, lagPos: { value: new THREE.Vector2() }, lys: { value: 1 },
                imageRegion: { value: region || new THREE.Vector4(0, 0, 1, 1) }, alphaCutoff: { value: 0 } },
            vertexShader: vertHd, fragmentShader: fragHd, transparent: true, depthTest: false, depthWrite: false, side: THREE.DoubleSide,
        }) };
    }

    /* Konturikonene bruker skjermens virkelige palett, ogsaa ved fading og
     * fargebytte. Vi lager ikke nye farger, teksturer, lys eller dekorasjoner. */
    function ikonPalett(m,y,diw=diwNaa) {
        if (!Kjerne.skanout().gyldig) return null;
        const pal = Kjerne.skanout().pal, top = diw[1] + y;
        if (top < 0 || top + m.height > 288) return null;
        const colors = [...new Set([m.base_index,...m.paths.map(p=>p.index)])];
        const offset=m.palette_offset||0;
        const rgb = colors.map(c=>Array.from(pal.subarray((top*32+c+offset)*4,(top*32+c+offset)*4+3)));
        for (let j=1;j<m.height;j++) for (let k=0;k<colors.length;k++) for (let b=0;b<3;b++) {
            if (pal[((top+j)*32+colors[k]+offset)*4+b]!==rgb[k][b]) return null;
        }
        return {colors,rgb};
    }

    function fargeleggIkon(m, t, y) {
        if (!t) return false;
        const palette=ikonPalett(m,y);if(!palette)return false;
        const {colors,rgb}=palette;
        const key=rgb.flat().join(',');
        if (t.ikonPalett === key) return true;
        const ctx=t.canvas.getContext('2d'), s=m.scale;
        ctx.resetTransform();ctx.clearRect(0,0,t.canvas.width,t.canvas.height);ctx.scale(s,s);
        ctx.save();ctx.clip(m.clipPath,'evenodd');
        const fill=(c,p)=>{ctx.fillStyle='rgb('+rgb[colors.indexOf(c)].join(',')+')';ctx.fill(p,'evenodd');};
        fill(m.base_index,m.clipPath);
        for (const p of m.paths) fill(p.index,p.path);
        ctx.restore();t.ikonPalett=key;t.tex.needsUpdate=true;
        return true;
    }

    /* po.cel blir brukt som hardware-sprite, med fargene 17..19. Det er
     * derfor ingen tegn_figur-post for den. Identifiser bare den eksakte
     * originalmasken; bit 7 i skanout skiller sprite fra vanlig grafikk. */
    function forberedMarkor(lag,lest) {
        const meta=hdIkoner.get('po.cel/000'),t=hdPakke.get('po.cel/000');
        if (!meta?.hardware_sprite || !t || !lag) return;
        const g=originalCel('po.cel',lest)?.[0],bank=originalCeler.get('po.cel'),scan=Kjerne.skanout();
        if (!g || !scan.gyldig || bankHash(bank).hash!==meta.source.bank_sha256 || indeksHash(g)!==meta.indices_sha256) return;
        const used=[];for(let j=0;j<g.h;j++)for(let i=0;i<g.w;i++)if(g.px[j*g.w+i])used.push([i,j,g.px[j*g.w+i]]);
        const anchor=used[Math.floor(used.length/2)],originX=diwNaa[0],originY=diwNaa[1];
        for(let sy=0;sy<200;sy++)for(let sx=0;sx<320;sx++) {
            if(scan.idx[(originY+sy)*720+originX+sx*2]!==128+16+anchor[2])continue;
            const x=sx-anchor[0],y=sy-anchor[1];if(x<0||y<0||x+g.w>320||y+g.h>200)continue;
            const visible=new Set(),hidden=[];let bad=false;
            for(let j=0;j<g.h&&!bad;j++)for(let i=0;i<g.w;i++) {
                const v=g.px[j*g.w+i],actual=scan.idx[(originY+y+j)*720+originX+(x+i)*2];
                if(actual&128) {if(!v||actual!==144+v){bad=true;break;}visible.add((y+j)*320+x+i);}
                else if(v)hidden.push([i,j]);
            }
            if(bad||visible.size<used.length*.9)continue;
            const mask=hidden.map(p=>p.join(',')).join(';');if(t.markorMask!==mask)t.ikonPalett=null;
            if(!fargeleggIkon(meta,t,y))continue;
            const ctx=t.canvas.getContext('2d');ctx.resetTransform();
            for(const[i,j]of hidden)ctx.clearRect(i*meta.scale,j*meta.scale,meta.scale,meta.scale);
            t.markorMask=mask;t.tex.needsUpdate=true;
            for(const p of visible)forData[p*4+3]=0;
            hdMarkor={x,y,meta,t,visible};hdKontroll.markorGodkjent=1;return;
        }
    }

    function gyldigPose(p) {
        const heltall = (v, min, max) => Number.isInteger(v) && v >= min && v <= max;
        const hash = (v) => typeof v === 'string' && /^[0-9a-f]{64}$/.test(v);
        if (!p || typeof p.id !== 'string' || !/^[a-z0-9_.-]{1,80}$/i.test(p.id) ||
            typeof p.image !== 'string' || !/^poses\/[a-z0-9_.-]+\.png$/i.test(p.image) || !hash(p.image_sha256) ||
            !heltall(p.width, 1, 320) || !heltall(p.height, 1, 200) || !['normal', 'mirrored', 'both'].includes(p.mirror) ||
            !Array.isArray(p.members) || p.members.length < 1 || p.members.length > 16 ||
            !p.palette || typeof p.palette !== 'object' || !Array.isArray(p.identity_indices) || !p.identity_indices.length) return false;
        if (p.identity_indices.some((c) => !heltall(c, 1, 31) || !Object.hasOwn(p.palette, c))) return false;
        for (const [k, rgba] of Object.entries(p.palette)) if (!/^[1-9][0-9]?$/.test(k) || +k > 31 ||
            !Array.isArray(rgba) || rgba.length !== 4 || rgba[3] !== 255 || rgba.some((v) => !heltall(v, 0, 255))) return false;
        for (const m of p.members) if (!m || typeof m.file !== 'string' || !/^[a-z0-9_.-]+$/i.test(m.file) ||
            !heltall(m.frame, 0, 1999) || !heltall(m.width, 1, 320) || !heltall(m.height, 1, 200) ||
            !heltall(m.x, 0, p.width - m.width) || !heltall(m.y, 0, p.height - m.height) ||
            !heltall(m.plane_mask, 1, 31) || (m.plane_mask & (m.plane_mask + 1)) || !hash(m.indices_sha256)) return false;
        if (Math.min(...p.members.map((m) => m.x)) !== 0 || Math.min(...p.members.map((m) => m.y)) !== 0 ||
            Math.max(...p.members.map((m) => m.x + m.width)) !== p.width || Math.max(...p.members.map((m) => m.y + m.height)) !== p.height) return false;
        return true;
    }

    /* HD-pakke: filer med stier som ".../kn1.ob/012.png" (som tools/gfx.py extract)
     * og ".../bg/1a2b3c4d.png" for bakgrunner (hash fra laget, se lagreBakgrunn) */
    async function lastHdPakke(filer) {
        let antall = 0;
        const alle = Array.from(filer), stiFor = (f) => (f.webkitRelativePath || f.name).replace(/\\/g, '/');
        const filKart = new Map(alle.map((f) => [stiFor(f).toLowerCase(), f]));
        // En delvis pakke erstatter bare metadata for sine egne bilder.
        // Andre standardikoner beholder palett, kildekontroll og spritepeker.
        hdIkonFeil = [];
        const pakkeIkoner = new Map();
        for (const f of alle.filter(f=>/(^|\/)icons\.json$/i.test(stiFor(f)))) {
            try {
                const data=JSON.parse(await f.text());
                if (data.schema!==1 || !Array.isArray(data.entries) || data.entries.length>200) throw new Error('Ugyldig ikonmanifest');
                const nyeIkoner = new Map();
                for (const m of data.entries) {
                    if (!m || typeof m.key!=='string' || !/^[a-z0-9_.-]+\/[0-9]{3}$/.test(m.key) ||
                        !Number.isInteger(m.width) || m.width<1 || m.width>320 || !Number.isInteger(m.height) || m.height<1 || m.height>200 ||
                        m.scale!==8 || !m.source || typeof m.source.file!=='string' || !/^[a-z0-9_.-]{1,80}$/.test(m.source.file) ||
                        !Number.isInteger(m.source.frame) || m.source.frame<0 || m.source.frame>1999 || !/^[0-9a-f]{64}$/.test(m.source.bank_sha256) ||
                        !/^[0-9a-f]{64}$/.test(m.indices_sha256) || ![0,16].includes(m.palette_offset||0) ||
                        !Array.isArray(m.paths) || m.paths.length>32 || !Number.isInteger(m.base_index) || m.base_index<0 || m.base_index>31 ||
                        typeof m.clip!=='string' || m.clip.length>100000 || m.paths.some(p=>!Number.isInteger(p.index)||p.index<0||p.index>31||typeof p.d!=='string'||p.d.length>100000)) throw new Error('Ugyldig ikonkontur');
                    if (m.dynamic !== undefined && typeof m.dynamic !== 'boolean' ||
                        m.dynamic && typeof m.scene !== 'string' ||
                        m.scene !== undefined && (typeof m.scene !== 'string' || !/^[a-z0-9_-]{1,80}$/.test(m.scene) ||
                            !Array.isArray(m.rect) || m.rect.length !== 4 || m.rect.some(v=>!Number.isInteger(v)) ||
                            m.rect[0] < 0 || m.rect[1] < 0 || m.rect[2] > 320 || m.rect[3] > 200 ||
                            m.rect[2] - m.rect[0] !== m.width || m.rect[3] - m.rect[1] !== m.height) ||
                        m.dynamic && (!Array.isArray(m.expected) || m.expected.length !== m.width * m.height ||
                            m.expected.some(v=>!Number.isInteger(v) || v < 0 || v > 31))) throw new Error('Ugyldig ikonfelt');
                    nyeIkoner.set(m.key,{...m,clipPath:new Path2D(m.clip),paths:m.paths.map(p=>({...p,path:new Path2D(p.d)}))});
                }
                for (const m of nyeIkoner.values()) if (!m.scene) {
                    const g=originalCel(m.source.file,new Map())?.[m.source.frame];
                    if (g) {
                        indeksHasher.set(g,await sha256(g.px));
                        await bankHash(originalCeler.get(m.source.file)).venter;
                    }
                }
                for (const [key,m] of nyeIkoner) pakkeIkoner.set(key,m);
            } catch(e) {hdIkonFeil.push(e.message);}
        }
        for (const f of alle.filter(f => /(^|\/)text\.json$/i.test(stiFor(f)))) {
            const tekst = JSON.parse(await f.text());
            hdTekstBanker.clear();
            for (const [navn, hash] of Object.entries(tekst.banks)) hdTekstBanker.set(navn, hash);
            hdTekstGlyfer = new Set(tekst.glyphs.map(g => g.file + '/' + String(g.frame).padStart(3, '0')));
            hdTekstMeta = new Map(tekst.glyphs.map(g => [g.file + '/' + String(g.frame).padStart(3, '0'), g]));
            for (const navn of hdTekstBanker.keys()) {
                if (originalCel(navn, new Map())) await bankHash(originalCeler.get(navn)).venter;
            }
        }
        // Pakkeinnlasting kan skje etter at tittelen er tegnet. Klargjor den
        // eksakte fontkilden foer fotobakgrunnen blir synlig, uten hash-venting
        // i renderlokka. Senere kildebytte valideres fortsatt av originalCel.
        if (alle.some((f) => /(^|\/)bg\/55bb9767\.png$/i.test(stiFor(f)))) {
            if (originalCel('bold.f', new Map())) await bankHash(originalCeler.get('bold.f')).venter;
        }
        const manifester = alle.filter((f) => /(^|\/)poses\.json$/i.test(stiFor(f)));
        if (manifester.length) {
            for (const p of hdPoser.values()) { p.texture.tex.dispose(); p.texture.mat.dispose(); }
            hdPoser.clear(); hdPoseKontrakter.clear(); hdPoseFeil = [];
            hdPoseLaster = true; hdPoseUgyldig = false;
        }
        for (const f of manifester) {
            try {
                const manifest = JSON.parse(await f.text());
                if (manifest.schema !== 1 || !Array.isArray(manifest.poses) || manifest.poses.length > 256) throw new Error('Ugyldig posemanifest');
                const prefiks = stiFor(f).slice(0, -'poses.json'.length);
                for (const p of manifest.poses) {
                    let texture = null;
                    try {
                        if (!gyldigPose(p) || hdPoseKontrakter.has(p.id)) {
                            hdPoseUgyldig = true;
                            throw new Error('Ugyldig eller duplisert pose');
                        }
                        const kontrakt = { ...p, members: p.members.map((m) => ({ ...m, file: m.file.toLowerCase() })) };
                        // Reserver rutene ogsaa hvis bildefilen mangler eller har feil hash.
                        hdPoseKontrakter.set(p.id, kontrakt);
                        const bilde = filKart.get((prefiks + p.image).toLowerCase());
                        if (!bilde || await sha256(await bilde.arrayBuffer()) !== p.image_sha256) throw new Error('Posebildet mangler eller har feil SHA256');
                        texture = await hdTekstur(bilde);
                        const r = p.raw_rect_px || [0, 0, texture.width, texture.height];
                        if (!Array.isArray(r) || r.length !== 4 || r.some((v) => !Number.isFinite(v)) || r[2] <= 0 || r[3] <= 0 ||
                            Math.abs(r[2] / p.width - r[3] / p.height) > 0.00001 ||
                            r[0] >= texture.width || r[1] >= texture.height || r[0] + r[2] <= 0 || r[1] + r[3] <= 0 ||
                            r[2] > texture.width * 4 || r[3] > texture.height * 4) throw new Error('Poseutsnittet mangler ensartet skala');
                        texture.mat.uniforms.imageRegion.value.set(r[0] / texture.width, r[1] / texture.height, r[2] / texture.width, r[3] / texture.height);
                        hdPoser.set(p.id, { ...kontrakt, texture });
                        antall++;
                    } catch (e) {
                        if (texture) { texture.tex.dispose(); texture.mat.dispose(); }
                        hdPoseFeil.push((p?.id || 'pose') + ': ' + e.message);
                    }
                }
            } catch (e) { hdPoseUgyldig = true; hdPoseFeil.push(stiFor(f) + ': ' + e.message); }
        }
        for (const f of filer) {
            const sti = (f.webkitRelativePath || f.name).split('/');
            if (sti.length < 2 || !/\.png$/i.test(sti[sti.length - 1])) continue;
            const nokkel = sti[sti.length - 2].toLowerCase() + '/' + sti[sti.length - 1].replace(/\.png$/i, '').toLowerCase();
            if (nokkel.startsWith('poses/')) continue;
            try {
                const t = await hdTekstur(f);
                const ikon=pakkeIkoner.get(nokkel);
                if (ikon && (t.width!==ikon.width*ikon.scale || t.height!==ikon.height*ikon.scale)) {t.tex.dispose();t.mat.dispose();hdIkonFeil.push(nokkel+': feil maal');continue;}
                const meta = hdTekstMeta.get(nokkel);
                if (meta?.raw_rect_px) {
                    const [x,y,w,h] = meta.raw_rect_px;
                    t.mat.uniforms.imageRegion.value.set(x/t.width,y/t.height,w/t.width,h/t.height);
                    t.mat.uniforms.alphaCutoff.value = meta.alpha_cutoff || 0;
                }
                const old = hdPakke.get(nokkel);
                if (old) { old.tex.dispose(); old.mat.dispose(); }
                hdPakke.set(nokkel, t);
                if (ikon) hdIkoner.set(nokkel,ikon);
                else hdIkoner.delete(nokkel);
                antall++;
            } catch (e) { /* ikke et bilde */ }
        }
        for (const [key,m] of pakkeIkoner) {
            const t=hdPakke.get(key);
            if (t && t.width===m.width*m.scale && t.height===m.height*m.scale) hdIkoner.set(key,m);
            else hdIkonFeil.push(key+': ikonbildet mangler eller har feil maal');
        }
        antallBg = [...hdPakke.keys()].filter((k) => k.startsWith('bg/')).length;
        hdPoseLaster = false;
        for (const [navn, kilde] of originalCeler) forvarmPoseIndekser(navn, kilde.bilder);
        maaTegnes = true;
        return antall;
    }

    function tomHdPakke() {
        hdIkoner.clear(); hdIkonFeil=[];
        for (const v of hdPakke.values()) { v.tex.dispose(); v.mat.dispose(); }
        hdPakke.clear();
        hdTekstBanker.clear(); hdTekstGlyfer.clear(); hdTekstMeta.clear();
        for (const p of hdPoser.values()) { p.texture.tex.dispose(); p.texture.mat.dispose(); }
        hdPoser.clear(); hdPoseKontrakter.clear(); hdPoseViste = []; hdPoseFeil = [];
        hdPoseLaster = hdPoseUgyldig = false;
        originalCeler.clear();
        nyesteMenypil++;
        for (const [k, p] of plasserte) {
            if (p.menypilKlar !== null) plasserte.delete(k);
            else p.underlag = null;
        }
        antallBg = 0;
        maaTegnes = true;
    }

    /* Standardpakken frigjør bare sine egne bakgrunner ved cacheutkast. */
    function fjernHdBilde(nokkel) {
        const t = hdPakke.get(nokkel);
        if (!t) return;
        t.tex.dispose(); t.mat.dispose();
        hdPakke.delete(nokkel);
        antallBg = [...hdPakke.keys()].filter(k => k.startsWith('bg/')).length;
        maaTegnes = true;
    }

    function bildeTilPng() {
        return renderer.domElement.toDataURL('image/png');
    }

    return {
        init, tegn, nyttBilde, tilpass, settFilter, settFormat, settHelt, settEffekter, bildeTilPng, lastHdPakke, tomHdPakke, fjernHdBilde,
        nullstillScene: () => { plasserte.clear(); visteListe = []; klynger = []; bildeNr = 0; sistTegnet = -99; sisteBakHash = -1; },
        tekstPlasseringer: () => visteListe.filter(d => /^(bold\.f|small\.font)$/i.test(d.fil)),
        settRammer: (on) => { visRammer = on; maaTegnes = true; }, hdAntall: () => hdPakke.size + hdPoser.size, scene: () => scene1,
        hdPoseInfo: () => ({ antall: hdPoser.size, kontrakter: hdPoseKontrakter.size, ugyldig: hdPoseUgyldig, feil: hdPoseFeil.slice() }),
        hdIkonInfo: () => ({ antall: hdIkoner.size, feil: hdIkonFeil.slice(),
            markor: hdMarkor ? {x:hdMarkor.x,y:hdMarkor.y,synlige:hdMarkor.visible.size} : null,
            kandidater: visteListe.filter(d=>hdIkoner.has(d.fil.toLowerCase()+'/'+String(d.bilde).padStart(3,'0'))).map(d=>({...d,godkjent:hdTegnbare.has(d)})),
            viste: visteListe.filter(d=>hdTegnbare.has(d)&&hdIkoner.has(d.fil.toLowerCase()+'/'+String(d.bilde).padStart(3,'0'))).map(d=>({fil:d.fil,bilde:d.bilde,x:d.x,y:d.y})) }),
        sceneIkoner: id => [...hdIkoner.values()].filter(m=>m.scene===id&&m.dynamic&&hdPakke.has(m.key)),
        sceneIkonKlar: (m,diw) => !!ikonPalett(m,m.rect[1],diw),
        hdBakgrunner: () => antallBg,
        hdKontroll: () => ({ ...hdKontroll }),      /* hvorfor en figur eventuelt bruker originalen */
        viste: () => visteListe.length,             /* figurer som vises med HD-bilde eller gult felt */
        maaTegnes: () => maaTegnes,
        utsnitt: () => crop.slice(),                /* delen av rammebufferet som vises (x0, y0, x1, y1) */
        brukerListe: () => hdPaa && (hdPakke.size > 0 || hdPoser.size > 0 || visRammer),   /* trengs tegnelisten fra kjernen? */
        /* trengs lagene fra kjernen? (HD-bakgrunner eller effekter som skiller lagene) */
        trengerLag: () => (hdPaa && (hdPakke.size > 0 || hdPoser.size > 0)) || effekter.skygge || effekter.dybde || tvungetLag,
        /* HD-grafikk eller originalen (bryteren i menyen) */
        settHd: (on) => { hdPaa = !!on; document.documentElement.classList.toggle('hd-tekst', hdPaa); maaTegnes = true; },
        hdPaa: () => hdPaa,
        lagNaa: () => lagNaa,
        settTvungetLag: (on) => { tvungetLag = on; maaTegnes = true; },
        /* grafikken (WebGL) ble borte og kom tilbake */
        vedGrafikk: (borte, tilbake) => { vedTapt = borte; vedTilbake = tilbake; },
        grafikkBorte: () => tapt,
    };
})();
