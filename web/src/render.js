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
    let palData, palTex, tomTex;            /* skjermens palett per linje (32 x H) til maskene, og en tom tekstur */
    let lagNaa = null;                      /* { hash, lys } for bildet som vises, eller null */
    const lysMaks = new Map();              /* bakgrunn -> lyseste stabile lysstyrke sett (fading av HD-bildene) */
    let lysForrige = { nokkel: null, lys: -1, fra: 0, fraTegn: 0 };  /* lik lysstyrke siden bilde fra / tegning fraTegn */
    let tegnNr = 0;                         /* tegninger (tegn), ogsaa naar spillet staar stille */
    let lysUkjent = false;                  /* skjermen toner inn foer fullt lys er kjent: originalen vises */
    const utsnittBg = new Set();            /* bakgrunner som bare dekker en del av skjermen (krever hdRect) */

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
    let hdFigurMaske = new Set();           /* godkjente figurer som farges fra paletten */
    const hdMasker = new Map();             /* "kn1.ob/012" -> maske-PNG (navn.mask.png), se fragHd */
    let palettKlar = false;                 /* palData er skjermens palett for dette bildet */
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
    /* Farge fra skjermens palett (docs/hd-grafikk.md, «Farge fra paletten»):
     *   maskeModus 1  maske-PNG ved siden av bildet (navn.mask.png), samme utsnitt som
     *                 bildet: R = palettindeks + 1 (0 = behold bildets farge), G = lysstyrke
     *                 (128 = fargen i paletten), B = hvor mye av palettfargen (255 = helt)
     *   maskeModus 2  posene: originalens indekser i lowres (maske, maskeStr), og fargene
     *                 bildet er tegnet med (ref). Fargen flyttes fra ref til skjermens farge.
     * Paletten (pal) er skjermens farger per linje, 32 x palH, ogsaa under toning. */
    const fragHd = `
        precision highp float;
        uniform sampler2D map, vern, maske, pal, ref;
        uniform vec2 lagPos, maskeStr;
        uniform float lys, maskeModus, palTop, palH;
        uniform vec4 imageRegion;
        uniform float alphaCutoff;
        uniform vec2 edgeFeather;
        varying vec2 vUv, vPos;
        vec3 palFarge(float i, float linje) {
            return texture2D(pal, vec2((i + 0.5) / 32.0, (clamp(palTop + linje, 0.0, palH - 1.0) + 0.5) / palH)).rgb;
        }
        void main() {
            vec2 p = vPos - lagPos;
            if (p.x >= 0.0 && p.y >= 0.0 && p.x < 320.0 && p.y < 200.0 &&
                texture2D(vern, (floor(p) + 0.5) / vec2(320.0, 200.0)).a > 0.5) discard;
            vec2 uv = imageRegion.xy + vUv * imageRegion.zw;
            if (uv.x < 0.0 || uv.y < 0.0 || uv.x > 1.0 || uv.y > 1.0) discard;
            vec4 c = texture2D(map, uv);
            if (c.a < alphaCutoff) discard;
            vec2 edge = min(vUv, 1.0 - vUv);
            if (edgeFeather.x > 0.0) c.a *= smoothstep(0.0, edgeFeather.x, edge.x);
            if (edgeFeather.y > 0.0) c.a *= smoothstep(0.0, edgeFeather.y, edge.y);
            vec3 rgb = c.rgb * lys;
            if (maskeModus > 0.5 && maskeModus < 1.5) {
                vec3 m = texture2D(maske, uv).rgb * 255.0;
                float i = floor(m.r + 0.5) - 1.0;
                if (i >= 0.0 && i < 32.0)
                    rgb = mix(rgb, min(palFarge(i, floor(p.y)) * m.g / 128.0, vec3(1.0)), m.b / 255.0);
            } else if (maskeModus > 1.5) {
                float i = floor(texture2D(maske, (floor(vUv * maskeStr) + 0.5) / maskeStr).r * 255.0 + 0.5);
                vec4 r = texture2D(ref, vec2((i + 0.5) / 32.0, 0.5));
                if (i > 0.0 && r.a > 0.5) {
                    // Lys og farge flyttes forholdsvis der referansen har farge, og som
                    // forskjell der den nesten er null (blaa ridder: ingen roedt og groent).
                    // Forskjellen fra referansen tones med lys, ellers ville detaljer i
                    // bildet bli staaende naar paletten er tonet helt ned.
                    vec3 a = palFarge(i, floor(p.y)), w = smoothstep(0.0, 0.25, r.rgb);
                    rgb = clamp(mix((c.rgb - r.rgb) * lys + a, c.rgb * a / max(r.rgb, vec3(0.004)), w), 0.0, 1.0);
                }
            }
            gl_FragColor = vec4(rgb, c.a);
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
        palData = new Uint8Array(32 * H * 4);
        palTex = dataTekstur(palData, 32, H);
        tomTex = dataTekstur(new Uint8Array(4), 1, 1);
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

    /* Tittelmenyen: bakgrunnskopien er ch.piv. Lasteskjermen viser samme bilde som
     * scene (SceneHd, lag.scene) med en annen tekst, og faar ikke tittelens saerregler. */
    const erTittel = (lag) => !!lag && lag.hash === 0x55bb9767 && !lag.scene;

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

    /* Staar figuren p fortsatt i forgrunnen? Alle ikke-gjennomsiktige kildepiksler maa
     * ha samme indeks i forgrunnen eller vaere lik bakgrunnen, og minst en maa vaere
     * forgrunn. En piksel som en annen plassert figur dekker med den viste indeksen
     * (nabobokstaven over skyggen), godtas ogsaa. Uten kilde (ukjent fil, feil maal)
     * regnes figuren som borte. */
    function kildePiksel(p, x, y, lest) {
        const d = p.d, g = originalCel(d.fil, lest)?.[d.bilde], i = x - p.x, j = y - p.y;
        if (!g || g.w !== d.w || g.h !== d.h || i < 0 || j < 0 || i >= d.w || j >= d.h) return 0;
        return g.px[j * d.w + (d.speilet ? d.w - 1 - i : i)];
    }
    function staarFortsatt(lag, p, lest) {
        const d = p.d, g = originalCel(d.fil, lest)?.[d.bilde];
        if (!g || g.w !== d.w || g.h !== d.h || !lag.forIdx || !Number.isInteger(p.x) || !Number.isInteger(p.y)) return false;
        let synlig = 0;
        for (let j = 0; j < d.h; j++) {
            const y = p.y + j;
            if (y < 0 || y >= 200) continue;
            for (let i = 0; i < d.w; i++) {
                const x = p.x + i;
                if (x < 0 || x >= 320) continue;
                const c = g.px[j * d.w + (d.speilet ? d.w - 1 - i : i)];
                if (!c) continue;
                const q = y * 320 + x, faktisk = lag.forIdx[q];
                if (faktisk === c) { synlig++; continue; }
                if (faktisk === 255 && lag.bakIdx?.[q] === c) continue;
                if (faktisk === 254) continue;      /* palettendring paa linjen ($FE): kontrolleres i forberedTekst */
                let dekket = false;
                for (const o of plasserte.values()) {
                    if (o !== p && x >= o.x && y >= o.y && x < o.x + o.w && y < o.y + o.h &&
                        kildePiksel(o, x, y, lest) === faktisk) { dekket = true; break; }
                }
                if (!dekket) return false;
            }
        }
        return synlig > 0;
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
        if (lag.hash !== sisteBakHash) {
            /* Ny bakgrunn: behold figurene som fortsatt staar i forgrunnen. Tekst tegnes
             * ofte like foer bakgrunnskopien byttes (Prepare yourself), og tegnes ikke
             * paa nytt. Hver kildepiksel maa ha samme indeks i forgrunnen, eller vaere
             * lik den nye bakgrunnen ($FF); ellers fjernes figuren. */
            const lest = new Map(), borte = [];
            for (const [k, p] of plasserte) if (p.menypilKlar !== null || !staarFortsatt(lag, p, lest)) borte.push(k);
            for (const k of borte) plasserte.delete(k);
            for (const p of plasserte.values()) p.hash = rektHash(lag.forIdx, p.x, p.y, p.w, p.h);
            menypilBakFra = bildeNr; sisteBakHash = lag.hash;
        }
        while (klynger.length && klynger[0].vis <= bildeNr) {
            for (const d of klynger.shift().liste) {
                const ventMenypil = erTittel(lag) && erTittelmenypil(d);
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
                plasserte.set(k, { d, x, y, w: d.w, h: d.h, hash, underlag, fra: bildeNr, sett: false,
                    menypilKlar: ventMenypil ? bildeNr + 2 : (bokstavPil?.menypilKlar ?? null),
                    ventPilNr: ventMenypil ? d.menypilNr : bokstavPil?.ventPilNr });
            }
        }
        const lestTekst = new Map(), borteTekst = [];
        for (const [k, p] of plasserte) {
            if (p.menypilKlar !== null) {
                if (p.ventPilNr !== nyesteMenypil) { plasserte.delete(k); continue; }
                if (bildeNr < p.menypilKlar) continue;
                // Menyen bygger skjermen over flere bilder. Ikke vis pilen foer
                // siste skjermbytte; deretter gjelder vanlig pikselvalidering.
                p.hash = rektHash(lag.forIdx, p.x, p.y, p.w, p.h);
                p.menypilKlar = null;
            }
            // Tekst bygges over flere bilder med overlappende skygger, saa rektangelet
            // endres naar nabotegnet tegnes. En bokstav fjernes derfor foerst naar den
            // ikke lenger staar der (staarFortsatt godtar nabotegnet over skyggen), og
            // hele raden kontrolleres i forberedTekst. Ellers ville tekst som ble staaende
            // gjennom et bakgrunnsbytte (Prepare yourself), bli liggende i kampen.
            // Bokstaven kan komme paa skjermen noen bilder etter at klyngen er plassert
            // (dobbel buffer). Den fjernes derfor bare naar den har staatt der og er
            // borte, eller aldri har vist seg i loepet av 50 bilder.
            const tekst = /^(bold\.f|small\.font)$/i.test(p.d.fil);
            if (tekst) {
                if (staarFortsatt(lag, p, lestTekst)) p.sett = true;
                else if (p.sett || bildeNr - p.fra > 50) borteTekst.push(k);
            } else if (rektHash(lag.forIdx, p.x, p.y, p.w, p.h) !== p.hash) borteTekst.push(k);
        }
        for (const k of borteTekst) plasserte.delete(k);
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
        if (erTittel(lag) && !visteListe.some(erTittelmenypil)) {
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
            if (lysUkjent) continue;        /* toner inn: originalteksten til lyset er kjent */
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
            // Raden kan stikke en linje under vinduet (Loading... i Prepare yourself paa
            // y 182, 19 hoey). Bare linjene som vises, kontrolleres.
            if (y < 0 || y >= 200 || w <= 0) continue;
            const hv = Math.min(h, 200 - y);
            const maske = new Uint8Array(w * h), medlemmer = new Set(gruppe.map(p => p.d));
            for (const p of gruppe) for (let j = 0; j < h; j++) for (let i = 0; i < p.d.w; i++) {
                const v = p.g.px[j * p.d.w + i], dx = p.x + i - x;
                if (v && dx >= 0 && dx < w) maske[j * w + dx] = v;
            }
            const over = visteListe.filter(d => !medlemmer.has(d) && overlapper(x, y, w, h, d))
                .map(d => ({d, g: originalCel(d.fil, lest)?.[d.bilde], x: d.x - d.xoff}));
            const fjern = [], vern = [];
            let gyldig = true;
            for (let j = 0; gyldig && j < hv; j++) for (let i = 0; i < w; i++) {
                let c = maske[j * w + i];
                const p = (y + j) * 320 + x + i;
                let faktisk = lag.forIdx[p];
                // $FE betyr en palettendring, mens den faktiske indeksen
                // fremdeles kan kontrolleres mot den originale glyfen.
                if (faktisk===254 && scan?.gyldig) faktisk=scan.idx[(diwNaa[1]+y+j)*720+diwNaa[0]+(x+i)*2];
                if (c && faktisk === c) { fjern.push(p); continue; }
                if (faktisk === 255 && (!c || lag.bakIdx?.[p] === c)) continue;
                // Et kildefast PIV-motiv kan bevares foran HD-bakgrunnen.
                // Slike originalpiksler bak tegnets transparente felt er underlag.
                if (!c && lag.scene && faktisk === lag.bakIdx?.[p]) continue;
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
        if (!erTittel(lag) || !hdPakke.has('bg/55bb9767') ||
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
                    // Med skjermens palett farges bildet om fra posens farger (fragHd,
                    // maskeModus 2), saa et hi eller en annen ridderfarge passer ogsaa.
                    // Uten den kreves fargene bildet er tegnet med, tonet med lysstyrken
                    // (hdLys, med slingringsmonn paa ett 4-bits Amiga-trinn), saa posene
                    // ikke avvises mens skjermen toner. Er fullt lys ukjent, vises originalen.
                    if (!forventet || (!palettKlar && (lysUkjent ||
                        forventet.some((v, n) => Math.abs(rgba[p * 4 + n] - v * hdLys) > 17)))) { gyldig = false; palettFeil = true; break; }
                    if (faktisk !== 255) { fjern.push(p); sett.add(c); }
                }
                if (gyldig && pose.identity_indices.some((c) => !sett.has(c))) { gyldig = false; palettFeil = true; }
                if (!gyldig || !fjern.length) { hdKontroll[palettFeil ? 'posePalett' : 'posePiksler']++; continue; }
                // Samme indeks fra en ukjent tegner er fortsatt uten eget pikseleierskap.
                // Ingen rektangler slettes: bare de kildepikslene som ble kontrollert over.
                if (palettKlar) poseIndekser(pose, indeks);
                kandidater.push({ pose, x, y, speilet, fjern, palett: palettKlar });
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

    /* Originalens indekser for posen (lowres, uspeilet) og fargene posebildet er
     * tegnet med, som teksturer til fragHd. Lages paa nytt bare naar de endres. */
    function poseIndekser(pose, indeks) {
        const t = pose.texture;
        if (!pose.indeksData || pose.indeksData.length !== indeks.length || pose.indeksData.some((v, i) => v !== indeks[i])) {
            pose.indeksData = indeks.slice();
            const data = new Uint8Array(indeks.length * 4);
            for (let i = 0; i < indeks.length; i++) { data[i * 4] = indeks[i]; data[i * 4 + 3] = 255; }
            if (pose.indeksTex) pose.indeksTex.dispose();
            pose.indeksTex = dataTekstur(data, pose.width, pose.height);
        }
        if (!pose.refTex) {
            const ref = new Uint8Array(32 * 4);
            for (const [k, rgba] of Object.entries(pose.palette)) ref.set([rgba[0], rgba[1], rgba[2], 255], +k * 4);
            pose.refTex = dataTekstur(ref, 32, 1);
        }
        t.mat.uniforms.maske.value = pose.indeksTex;
        t.mat.uniforms.ref.value = pose.refTex;
        t.mat.uniforms.maskeStr.value.set(pose.width, pose.height);
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

    /* Pikseleierskap i tegnerekkefoelge: for hver piksel den siste figuren i listen
     * som har en ikke-gjennomsiktig kildepiksel der (indeksen i figurNr), og hvilke
     * piksler som ligger i rektangelet til en figur uten paalitelig kilde (ukjent).
     * Speilingen og planmasken er de samme som i pikselkontrollen. */
    function eierskap(lest) {
        const eier = new Int16Array(320 * 200).fill(-1), ukjent = new Uint8Array(320 * 200);
        const kilder = [];
        for (let k = 0; k < visteListe.length && k < 32000; k++) {
            const o = visteListe[k], ox = o.x - o.xoff, og = originalCel(o.fil, lest)?.[o.bilde];
            const ok = !!og && og.w === o.w && og.h === o.h && Number.isInteger(ox) && Number.isInteger(o.y);
            kilder.push(ok ? og : null);
            const x0 = Math.floor(ox), y0 = Math.floor(o.y);
            for (let j = Math.max(0, -y0); j < o.h && y0 + j < 200; j++) {
                for (let i = Math.max(0, -x0); i < o.w && x0 + i < 320; i++) {
                    const p = (y0 + j) * 320 + x0 + i;
                    if (!ok) { ukjent[p] = 1; continue; }
                    if (og.px[j * o.w + (o.speilet ? o.w - 1 - i : i)]) eier[p] = k;
                }
            }
        }
        const farge = (k, p) => {
            const o = visteListe[k], g = kilder[k], i = p % 320 - (o.x - o.xoff), j = Math.floor(p / 320) - o.y;
            return g.px[j * o.w + (o.speilet ? o.w - 1 - i : i)];
        };
        return { eier, ukjent, farge };
    }

    /* Gjenkjente figurer kan erstattes. HD-figurene tegnes i samme rekkefoelge som
     * originalen, saa en senere figur (sverdet, kn4) ligger over en tidligere (kroppen,
     * kn1), ogsaa naar begge har HD. Piksler som eies av en senere figur uten HD, vernes
     * og ligger foran HD-bildene under. Hver piksel i rektangelet maa stemme med eieren
     * sin (eller vaere lik bakgrunnen, $FF); en ukjent forgrunnspiksel, en figur uten
     * paalitelig kilde i rektangelet eller feil indeks gir originalen for hele figuren.
     * Vi rydder bare piksler som eies av en figur som faar HD, og som har samme indeks
     * i den viste forgrunnen. Piksler som tilhoerer en figur uten HD, blir staaende. */
    function forberedHd(lag) {
        hdTegnbare = new Set();
        hdFigurLys = new Map();
        hdFigurMaske = new Set();
        hdPoseViste = [];
        hdKontroll = { godkjent: 0, utenLag: 0, kilde: 0, overlapp: 0, piksler: 0, maske: 0, masket: 0,
            poseGodkjent: 0, poseGruppe: 0, poseKilde: 0, posePalett: 0, poseOverlapp: 0, posePiksler: 0,
            tekstGodkjent: 0, tekstAvvist: 0, tekstFeil: [], lys: 0, lysUkjent, hdLys };
        hdKontroll.ikonGodkjent = 0; hdKontroll.ikonAvvist = 0;
        hdMarkor=null;
        vernData.fill(0);
        vernTex.needsUpdate = true;
        if (!hdPaa || (!hdPakke.size && !hdPoser.size)) return;
        const lest = new Map();
        palettKlar = oppdaterPalett();
        const reservert = forberedPoser(lag, lest);
        for (const d of forberedTekst(lag, lest)) reservert.add(d);
        forberedMarkor(lag,lest);
        const harLag = lag && lag.forIdx && lag.forIdx.length === 320 * 200;
        const eie = harLag ? eierskap(lest) : null;
        const figurHd = new Set();
        for (let nr = 0; nr < visteListe.length; nr++) {
            const d = visteListe[nr];
            if (reservert.has(d)) continue;
            const ikey = d.fil.toLowerCase() + '/' + String(d.bilde).padStart(3, '0');
            if (!hdPakke.has(ikey)) continue;
            if (!harLag) { hdKontroll.utenLag++; continue; }
            const g = originalCel(d.fil, lest)?.[d.bilde], x = d.x - d.xoff, y = d.y;
            // Gamle tegninger helt utenfor vinduet blir staaende i listen (tomt rektangel).
            if (x >= 320 || y >= 200 || x + d.w <= 0 || y + d.h <= 0) continue;
            if (!g || g.w !== d.w || g.h !== d.h || !Number.isInteger(x) || !Number.isInteger(y)) { hdKontroll.kilde++; continue; }
            const ikon = hdIkoner.get(ikey);
            if (ikon && (bankHash(originalCeler.get(d.fil.toLowerCase())).hash !== ikon.source.bank_sha256 ||
                indeksHash(g) !== ikon.indices_sha256 || g.planmaske !== ikon.plane_mask ||
                !fargeleggIkon(ikon, hdPakke.get(ikey), y))) { hdKontroll.ikonAvvist++; continue; }
            if (hdPakke.get(ikey).maske && !palettKlar) { hdKontroll.maske++; continue; }
            // Ukjent fullt lys (skjermen toner inn): bare bilder som farges fra paletten.
            if (lysUkjent && !ikon && !hdPakke.get(ikey).maske) { hdKontroll.lys++; continue; }
            if (d.fil.toLowerCase() === 'ki.cel' && d.bilde >= 45 && d.bilde <= 49) {
                const foran = visteListe.filter((o) => o !== d && overlapper(x, y, d.w, d.h, o));
                forberedMaane(d, g, lag, foran);
                continue;
            }
            let gyldig = true, tvetydig = false, egne = 0;
            for (let j = 0; gyldig && j < d.h; j++) {
                if (y + j < 0 || y + j >= 200) continue;
                for (let i = 0; i < d.w; i++) {
                    if (x + i < 0 || x + i >= 320) continue;
                    const p = (y + j) * 320 + x + i, indeks = lag.forIdx[p];
                    if (hdMarkor?.visible.has(p)) continue;
                    if (eie.ukjent[p]) { tvetydig = true; gyldig = false; break; }
                    const e = eie.eier[p];
                    if (e < 0) { if (indeks !== 255) { gyldig = false; break; } continue; }
                    if (indeks === 255) continue;
                    if (indeks !== eie.farge(e, p)) { gyldig = false; break; }
                    if (e === nr) egne++;
                }
            }
            if (tvetydig) { hdKontroll.overlapp++; continue; }
            if (!gyldig || !egne) { hdKontroll.piksler++; continue; }
            hdTegnbare.add(d);
            figurHd.add(nr);
            if (hdPakke.get(ikey).maske) { hdFigurMaske.add(d); hdKontroll.masket++; }
            if (ikon) { hdFigurLys.set(d, hdPakke.get(ikey).ikonLys ?? 1); hdKontroll.ikonGodkjent++; }
            hdKontroll.godkjent++;
        }
        if (figurHd.size) {
            // Den tidligste HD-figuren som dekker pikselen (rektangelet). Bare piksler
            // fra senere figurer uten HD skal ligge foran et HD-bilde.
            const forsteHd = new Int16Array(320 * 200).fill(32767);
            const ikonVern = visteListe.map(d => hdIkoner.get(d.fil.toLowerCase() + '/' +
                String(d.bilde).padStart(3, '0'))?.preserve_indices);
            visteListe.forEach((d, k) => {
                if (!hdTegnbare.has(d)) return;
                const x0 = d.x - d.xoff;
                if (!Number.isInteger(x0) || !Number.isInteger(d.y)) return;
                for (let j = Math.max(0, -d.y); j < d.h && d.y + j < 200; j++)
                    for (let i = Math.max(0, -x0); i < d.w && x0 + i < 320; i++) {
                        const p = (d.y + j) * 320 + x0 + i;
                        if (forsteHd[p] > k) forsteHd[p] = k;
                    }
            });
            for (let p = 0; p < 320 * 200; p++) {
                const e = eie.eier[p];
                if (e < 0) continue;
                if (figurHd.has(e)) {
                    if (lag.forIdx[p] !== 255 && !hdMarkor?.visible.has(p)) {
                        // Bare den validerte pikseleierens egne indeksvern gjelder.
                        // Valgkanter beholder originalens levende palett foran HD.
                        if (ikonVern[e]?.includes(lag.forIdx[p])) vernData[p * 4 + 3] = 255;
                        else forData[p * 4 + 3] = 0;
                    }
                }
                else if (forsteHd[p] < e && !hdTegnbare.has(visteListe[e])) vernData[p * 4 + 3] = 255;
            }
        }
        if (hdMarkor) for (const p of hdMarkor.visible) vernData[p*4+3]=0;
        return (erTittel(lag) && visteListe.some(d => d.fil.toLowerCase() === 'bold.f' &&
            d.bilde === 73 && hdTegnbare.has(d))) || bevarTitteltekst(lag, lest);
    }

    /* Skjermens palett per linje til maskene og posene. Uten gyldig skanout (HAM,
     * hires, flere plan) vises figurene med maske som originalen. */
    function oppdaterPalett() {
        if ((!hdMasker.size && !hdPoser.size) || typeof Kjerne === 'undefined') return false;
        const s = Kjerne.skanout();
        if (!s.gyldig || s.pal.length !== palData.length) return false;
        palData.set(s.pal);
        palTex.needsUpdate = true;
        return true;
    }

    let hdLys = 1;                          /* fading for HD-bildene, fra paletten (lagene) */

    /* Lysstyrken til HD-bildene. Kjernen og SceneHd gir summen av fargene bakgrunnen
     * bruker (lag.lys). Med lag.lysMaks (scenene: samme sum med PIV-filens egen palett)
     * er fullt lys kjent med en gang. Ellers er fullt lys det lyseste som har staatt
     * stille i minst ti bilder eller ti tegninger for denne bakgrunnen. Toner skjermen inn foer det er
     * kjent, vises originalen (lysUkjent), saa HD-bildene ikke lyser fullt over en
     * skjerm som fortsatt er moerk. Scenene og kjernen regner summen ulikt, og har
     * hver sin noekkel. */
    function beregnLys(lag) {
        lysUkjent = false;
        if (lag.lysMaks) { hdLys = Math.min(1, lag.lys / lag.lysMaks); return; }
        const nokkel = (lag.scene ? 's:' : 'k:') + (lag.hash >>> 0);
        if (lysForrige.nokkel !== nokkel || lysForrige.lys !== lag.lys) lysForrige = { nokkel, lys: lag.lys, fra: bildeNr, fraTegn: tegnNr };
        let maks = lysMaks.get(nokkel);
        /* ti bilder (spillet gaar) eller ti tegninger (spillet staar stille) med samme lys */
        if (bildeNr - lysForrige.fra >= 10 || tegnNr - lysForrige.fraTegn >= 10 || (maks !== undefined && lag.lys > maks)) {
            maks = Math.max(maks || 0, lag.lys);
            lysMaks.set(nokkel, maks);
        }
        if (maks === undefined) { lysUkjent = true; hdLys = 1; return; }
        hdLys = maks ? Math.min(1, lag.lys / maks) : 1;
    }
    function tegnHd() {
        let n = 0;
        for (const m of sceneFlater) m.visible = false;
        // Faste landemerker ligger over terrenget og under originale markorer.
        if (hdPaa && lagNaa?.overlays && hdPakke.has('bg/' + (lagNaa.hash >>> 0).toString(16).padStart(8,'0'))) {
            let i = 0;
            for (const o of lagNaa.overlays) {
                const t = hdPakke.get(o.key); if (!t) continue;
                const ikon = hdIkoner.get(o.key);
                if (ikon && !fargeleggIkon(ikon,t,ikon.dynamic ? ikon.rect[1] : o.rect[1])) continue;
                if (!sceneFlater[i]) {
                    const m = new THREE.Mesh(new THREE.PlaneGeometry(1,1),t.mat);
                    hdGruppe.add(m); sceneFlater[i] = m;
                }
                const m=sceneFlater[i++], [x0,y0,x1,y1]=o.rect;
                // Faste ikonoverlegg maa ligge under nye HD-glyfkanter i samme felt.
                m.renderOrder=o.foreground ? (ikon&&!ikon.dynamic ? 3.5 : 4) : 2.5;
                m.material=t.mat; t.mat.uniforms.imageRegion.value.set(...o.uv_rect);
                t.mat.uniforms.vern.value=o.foreground ? sceneVernTex : vernTex;
                t.mat.uniforms.alphaCutoff.value=o.alpha_cutoff || 0;
                t.mat.uniforms.edgeFeather.value.set(...(ikon?.edge_feather || [0,0]));
                t.mat.uniforms.lys.value=ikon ? (t.ikonLys ?? 1) : hdLys;
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
                // Samme rekkefoelge som originalen: en senere figur over en tidligere.
                m.renderOrder = 4 + n / 100000;
                if (t) {
                    t.mat.uniforms.lys.value = hdFigurLys.get(d) ?? hdLys;
                    t.mat.uniforms.lagPos.value.set(diwNaa[0] / 2 - ux(), diwNaa[1] - uy());
                    t.mat.uniforms.maskeModus.value = hdFigurMaske.has(d) ? 1 : 0;
                    t.mat.uniforms.palTop.value = diwNaa[1];
                }
                if (t?.fit) {
                    const h2 = d.w / t.fit;
                    plasser(m, x, y + (d.h - h2) / 2, d.w, h2);
                } else plasser(m, x, y, d.w, d.h);
                if (d.speilet) m.scale.x = -d.w;           /* negativ bredde snur bildet */
                m.visible = true;
            }
            for (const p of hdPoseViste) {
                const m = flate(n++), t = p.pose.texture;
                m.material = t.mat;
                m.renderOrder = 4.5;
                // Med skjermens palett foelger figuren fargene og toningen derfra, og bare
                // kanten utenfor originalens piksler tones med lysstyrken. Uten den er
                // fargene kontrollert mot posens farger tonet med hdLys, og hele bildet
                // tones like mye.
                t.mat.uniforms.maskeModus.value = p.palett ? 2 : 0;
                t.mat.uniforms.palTop.value = diwNaa[1];
                t.mat.uniforms.lys.value = hdLys;
                t.mat.uniforms.lagPos.value.set(diwNaa[0] / 2 - ux(), diwNaa[1] - uy());
                plasser(m, diwNaa[0] / 2 + p.x - ux(), diwNaa[1] + p.y - uy(), p.pose.width, p.pose.height);
                if (p.speilet) m.scale.x = -p.pose.width;
                m.visible = true;
            }
            if (hdMarkor) {
                const {x,y,meta,t}=hdMarkor,m=flate(n++);
                m.material=t.mat;m.renderOrder=4.6;t.mat.uniforms.lys.value=t.ikonLys ?? 1;
                t.mat.uniforms.lagPos.value.set(diwNaa[0]/2-ux(),diwNaa[1]-uy());
                plasser(m,diwNaa[0]/2+x-ux(),diwNaa[1]+y-uy(),meta.width,meta.height);m.visible=true;
            }
        }
        for (let i = n; i < flater.length; i++) flater[i].visible = false;
    }

    /* Kalles bare naar kjernen har laget et nytt bilde, eller maaTegnes() er sann.
     * lag: { bak, for (Uint8Array, 320 x 200 RGBA), hash, lys } eller null. */
    function forgrunnAndel(idx) {
        let n = 0;
        for (let p = 0; p < idx.length; p++) if (idx[p] !== 255) n++;
        return n / idx.length;
    }

    function tegn(fb, diw, lag) {
        tegnNr++;
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
            let hd = hdPaa ? hdPakke.get(nokkel) : null;
            /* Et utsnitt (byene, kroen) passer bare der scenen har gitt rektangelet. Uten
             * scenetreff vises originalbakgrunnen, ikke bildet strukket over hele skjermen. */
            if (hd && !lag.hdRect && utsnittBg.has(lag.hash >>> 0)) hd = null;
            /* Dekker forgrunnen det meste av skjermen, vises ikke bakgrunnskopien (en melding
             * eller lasteskjerm tegnet rett paa skjermen). Da ville HD-bildet av kopien skinne
             * gjennom der meldingen og kopien tilfeldigvis har samme indeks (svart). */
            if (hd && !lag.scene && lag.forIdx && forgrunnAndel(lag.forIdx) > 0.5) hd = null;
            beregnLys(lag);
            if (hd && !lysUkjent) {
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
        if (!lag) { hdLys = 1; lysUkjent = false; }
        oppdaterViste(lag);
        const titteltekstKlar = forberedHd(lag);
        // Ved sen pakkeinnlasting kan den opprinnelige engangstegningen av
        // pilen mangle i tegnelisten. Behold original bakgrunn til hele den
        // kjente tekstkontrakten passer, fremfor aa vise hull i svarte tegn.
        if (hdPaa && erTittel(lag) && hdPakke.has('bg/55bb9767') && !titteltekstKlar) {
            bakMesh.material = bakAmigaMat;
            bakData.set(lag.bak);
            bakTex.needsUpdate = true;
            bakAmigaMat.uniforms.uskarp.value = effekter.dybde ? 0.9 : 0;
        }
        hdKontroll.bakgrunn = !lag ? null : bakMesh.material === bakMat ? 'hd' : 'original';
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
                imageRegion: { value: region || new THREE.Vector4(0, 0, 1, 1) }, alphaCutoff: { value: 0 },
                maske: { value: tomTex }, pal: { value: palTex }, ref: { value: tomTex }, maskeStr: { value: new THREE.Vector2(1, 1) },
                maskeModus: { value: 0 }, palTop: { value: 0 }, palH: { value: H },
                edgeFeather: { value: new THREE.Vector2(0,0) } },
            vertexShader: vertHd, fragmentShader: fragHd, transparent: true, depthTest: false, depthWrite: false, side: THREE.DoubleSide,
        }) };
    }

    /* Masken leses uten fargestyring og uten forhaandsmultiplisert alfa, og med
     * naermeste piksel, saa indeksene i R ikke blandes. */
    async function maskeTekstur(f) {
        const bilde = await createImageBitmap(f, { premultiplyAlpha: 'none', colorSpaceConversion: 'none' });
        const lerret = document.createElement('canvas');
        lerret.width = bilde.width; lerret.height = bilde.height;
        lerret.getContext('2d').drawImage(bilde, 0, 0);
        bilde.close();
        const t = new THREE.Texture(lerret);
        t.colorSpace = THREE.NoColorSpace;
        t.flipY = false;
        t.generateMipmaps = false;
        t.magFilter = t.minFilter = THREE.NearestFilter;
        t.needsUpdate = true;
        return { tex: t, width: lerret.width, height: lerret.height };
    }

    function koblMaske(key, t) {
        const m = hdMasker.get(key);
        t.maske = m || null;
        t.mat.uniforms.maske.value = m ? m.tex : tomTex;
        if (!m) t.mat.uniforms.maskeModus.value = 0;
    }

    /* Konturer bruker skjermpaletten direkte. Rasterbilder kontrolleres mot
     * sin kildepalett og tones med den beregnede fadestyrken. */
    function ikonPalett(m,y,diw=diwNaa) {
        if (!Kjerne.skanout().gyldig) return null;
        const pal = Kjerne.skanout().pal, top = diw[1] + y;
        if (top < 0 || top + m.height > 288) return null;
        const colors = [...new Set([m.base_index,...m.paths.map(p=>p.index)])]
            .filter(c=>m.render_mode!=='raster'||!m.preserve_indices?.includes(c));
        const offset=m.palette_offset||0;
        const rgb = colors.map(c=>Array.from(pal.subarray((top*32+c+offset)*4,(top*32+c+offset)*4+3)));
        for (let j=1;j<m.height;j++) for (let k=0;k<colors.length;k++) for (let b=0;b<3;b++) {
            if (pal[((top+j)*32+colors[k]+offset)*4+b]!==rgb[k][b]) return null;
        }
        return {colors,rgb};
    }

    /* Nytegnede rasterikoner beholder bildefilens detaljer. En kjent
     * kildepalett tillater vanlig Amiga-fading, men avviser andre fargevarianter.
     * Avrunding i firebitsfargene kan avvike med ett trinn paa 17. */
    function rasterIkonVariant(m, palette) {
        if (m.render_mode !== 'raster') return {lys:1,key:m.key};
        let beste=null;
        for (const variant of m.palette_variants || [{key:m.key}]) {
            const referanse={...m.reference_palette};
            if (variant.indices) variant.indices.forEach((c,i)=>referanse[c]=variant.colors[i]);
            const sykluser=m.reference_palette_cycles||[];
            const syklus=c=>sykluser.find(gruppe=>gruppe.includes(c));
            let teller=0, nevner=0;
            for (let i=0;i<palette.colors.length;i++) {
                if (syklus(palette.colors[i])) continue;
                const ref=referanse[palette.colors[i]], rgb=palette.rgb[i];
                for (let c=0;c<3;c++) {teller+=ref[c]*rgb[c];nevner+=ref[c]*ref[c];}
            }
            const lys=nevner ? Math.max(0,Math.min(1,teller/nevner)) : 0;
            let gyldig=true,feil=0;
            for (let i=0;i<palette.colors.length;i++) {
                const ref=referanse[palette.colors[i]], rgb=palette.rgb[i];
                const gruppe=syklus(palette.colors[i]);
                const mulige=gruppe ? gruppe.map(c=>referanse[c]) : [ref];
                if (!mulige.some(f=>rgb.every((v,c)=>Math.abs(v-f[c]*lys)<=17.01))) {gyldig=false;break;}
                feil+=Math.min(...mulige.map(f=>rgb.reduce((sum,v,c)=>sum+(v-f[c]*lys)**2,0)));
            }
            if (gyldig&&(!beste||feil<beste.feil)) beste={lys,key:variant.key,feil};
        }
        return beste;
    }
    function rasterIkonLys(m,palette) {return rasterIkonVariant(m,palette)?.lys ?? null;}

    function fargeleggIkon(m, t, y) {
        if (!t) return false;
        const palette=ikonPalett(m,y);if(!palette)return false;
        const {colors,rgb}=palette;
        const key=rgb.flat().join(',');
        if (m.render_mode === 'raster') {
            const variant=rasterIkonVariant(m,palette);
            if (!variant) return false;
            const lys=variant.lys, bilde=variant.key===m.key?t:hdPakke.get(variant.key);
            if (!bilde||bilde.width!==t.width||bilde.height!==t.height) return false;
            if (!t.ikonOriginal) {
                t.ikonOriginal=document.createElement('canvas');
                t.ikonOriginal.width=t.width;t.ikonOriginal.height=t.height;
                t.ikonOriginal.getContext('2d').drawImage(t.canvas,0,0);
            }
            // Masken for hardware-pekeren kan ha skjult en annen del sist.
            if (t.ikonPalett!==key || t.ikonVariantBilde!==bilde) {
                const ctx=t.canvas.getContext('2d');ctx.resetTransform();
                ctx.clearRect(0,0,t.width,t.height);ctx.drawImage(bilde===t?t.ikonOriginal:bilde.canvas,0,0);
                t.tex.needsUpdate=true;
            }
            t.ikonLys=lys;t.ikonPalett=key;t.ikonVariantBilde=bilde;return true;
        }
        if (t.ikonPalett === key) return true;
        t.ikonLys=1;
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
                    if (m.render_mode!==undefined && m.render_mode!=='raster' && m.render_mode!=='contours' ||
                        m.render_mode==='raster' && (!m.reference_palette || typeof m.reference_palette!=='object' ||
                            [...new Set([m.base_index,...m.paths.map(p=>p.index)])].some(c=>
                                !Array.isArray(m.reference_palette[c]) || m.reference_palette[c].length!==3 ||
                                m.reference_palette[c].some(v=>!Number.isInteger(v)||v<0||v>255)))) throw new Error('Ugyldig rasterikonpalett');
                    if (m.reference_palette_cycles!==undefined &&
                        (!Array.isArray(m.reference_palette_cycles) || m.render_mode!=='raster' ||
                         m.reference_palette_cycles.some(g=>!Array.isArray(g)||g.length<2||g.length>32||
                            new Set(g).size!==g.length||g.some(c=>!Number.isInteger(c)||c<0||c>31||
                                !Array.isArray(m.reference_palette[c])||m.reference_palette[c].length!==3||
                                m.reference_palette[c].some(v=>!Number.isInteger(v)||v<0||v>255))) ||
                         new Set(m.reference_palette_cycles.flat()).size!==m.reference_palette_cycles.flat().length))
                        throw new Error('Ugyldig palettsyklus');
                    if (m.palette_variants!==undefined) {
                        // Livsymbolenes to paneler bruker bare disse fem kildeparene.
                        const side={'ki.cel/017':[28,29],'ki.cel/018':[30,31],'ki.cel/019':[28,29],'ki.cel/020':[30,31]}[m.key];
                        const par={blue:[[0,51,255],[0,34,136]],orange:[[255,187,0],[187,102,0]],green:[[68,204,51],[17,102,0]],red:[[255,0,0],[136,0,0]],purple:[[0,34,119],[0,0,51]]};
                        if (!side || m.render_mode!=='raster' || !Array.isArray(m.palette_variants) || m.palette_variants.length!==5 ||
                            new Set(m.palette_variants.map(v=>v?.id)).size!==5 || m.palette_variants.some(v=>
                                !v || !par[v.id] || JSON.stringify(v.indices)!==JSON.stringify(side) ||
                                JSON.stringify(v.colors)!==JSON.stringify(par[v.id]) ||
                                v.key!==(v.id==='blue'?m.key:'ki-palettes/'+m.key.slice(-3)+'-'+v.id)))
                            throw new Error('Ugyldig ridderpalettvariant');
                    }
                    if (m.preserve_indices!==undefined && (m.render_mode!=='raster' ||
                        !Array.isArray(m.preserve_indices) || !m.preserve_indices.length || m.preserve_indices.length>31 ||
                        new Set(m.preserve_indices).size!==m.preserve_indices.length ||
                        m.preserve_indices.some(c=>!Number.isInteger(c)||c<1||c>31||
                            ![m.base_index,...m.paths.map(p=>p.index)].includes(c)) ||
                        [m.base_index,...m.paths.map(p=>p.index)].every(c=>m.preserve_indices.includes(c))))
                        throw new Error('Ugyldig ikonindeksvern');
                    if (m.edge_feather!==undefined && (m.render_mode!=='raster' || !m.scene || m.dynamic ||
                        !Array.isArray(m.edge_feather) || m.edge_feather.length!==2 ||
                        m.edge_feather.some(v=>!Number.isFinite(v)||v<0||v>0.25)))
                        throw new Error('Ugyldig terrengkant');
                    // Visningsfeltet endrer bare HD-formen. Kildemoensteret beholder eget rect.
                    if (m.draw_rect!==undefined && (!m.dynamic || m.render_mode!=='raster' ||
                        !Array.isArray(m.draw_rect) || m.draw_rect.length!==4 || m.draw_rect.some(v=>!Number.isInteger(v)) ||
                        m.draw_rect[0]<0 || m.draw_rect[1]<0 || m.draw_rect[2]>320 || m.draw_rect[3]>200 ||
                        m.draw_rect[2]<=m.draw_rect[0] || m.draw_rect[3]<=m.draw_rect[1]))
                        throw new Error('Ugyldig ikonvisningsfelt');
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
            for (const p of hdPoser.values()) { p.texture.tex.dispose(); p.texture.mat.dispose(); p.indeksTex?.dispose(); p.refTex?.dispose(); }
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
            if (/\.mask$/.test(nokkel)) {
                try {
                    const m = await maskeTekstur(f), base = nokkel.slice(0, -'.mask'.length);
                    const old = hdMasker.get(base);
                    if (old) old.tex.dispose();
                    hdMasker.set(base, m);
                    antall++;
                } catch (e) { /* ikke et bilde */ }
                continue;
            }
            try {
                const t = await hdTekstur(f);
                const ikon=pakkeIkoner.get(nokkel);
                const ikonRect=ikon?.draw_rect;
                if (ikon && (t.width!==(ikonRect ? ikonRect[2]-ikonRect[0] : ikon.width)*ikon.scale ||
                    t.height!==(ikonRect ? ikonRect[3]-ikonRect[1] : ikon.height)*ikon.scale)) {t.tex.dispose();t.mat.dispose();hdIkonFeil.push(nokkel+': feil maal');continue;}
                const meta = hdTekstMeta.get(nokkel);
                if (meta?.raw_rect_px || nokkel === 'bold.f/073') {
                    // Standardmetadata gjelder det leverte standardbildet. Et eget
                    // bilde kan allerede vaere klippet til originalrutens format.
                    const r = meta?.raw_rect_px;
                    const gyldig = Array.isArray(r) && r.length === 4 && r.every(Number.isFinite) &&
                        r[0] >= 0 && r[1] >= 0 && r[2] > 0 && r[3] > 0 &&
                        r[0] + r[2] <= t.width && r[1] + r[3] <= t.height;
                    const [x,y,w,h] = gyldig ? r : [0,0,t.width,t.height];
                    t.mat.uniforms.imageRegion.value.set(x/t.width,y/t.height,w/t.width,h/t.height);
                    t.mat.uniforms.alphaCutoff.value = meta?.alpha_cutoff || 0;
                    /* fit "width": bildet har et annet sideforhold enn originalen (logoen
                     * bold.f/073). Det fyller bredden og sentreres i hoeyden, uten strekk. */
                    t.fit = meta?.fit === 'width' || nokkel === 'bold.f/073' ? w / h : 0;
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
            const r=m.draw_rect, w=r ? r[2]-r[0] : m.width, h=r ? r[3]-r[1] : m.height;
            if (t && t.width===w*m.scale && t.height===h*m.scale) hdIkoner.set(key,m);
            else hdIkonFeil.push(key+': ikonbildet mangler eller har feil maal');
        }
        for (const m of pakkeIkoner.values()) for (const v of m.palette_variants||[]) {
            const t=hdPakke.get(v.key);
            if (!t || t.width!==m.width*m.scale || t.height!==m.height*m.scale)
                hdIkonFeil.push(v.key+': palettbildet mangler eller har feil maal');
        }
        // Maskene kobles til bildet med samme navn, uansett hvilken som kom foerst.
        for (const [key, t] of hdPakke) koblMaske(key, t);
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
        for (const p of hdPoser.values()) { p.texture.tex.dispose(); p.texture.mat.dispose(); p.indeksTex?.dispose(); p.refTex?.dispose(); }
        hdPoser.clear(); hdPoseKontrakter.clear(); hdPoseViste = []; hdPoseFeil = [];
        for (const m of hdMasker.values()) m.tex.dispose();
        hdMasker.clear();
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
        sceneIkonKlar: (m,diw) => {const p=ikonPalett(m,m.rect[1],diw);return !!p&&rasterIkonLys(m,p)!==null;},
        sceneOverleggKlar: (key,diw) => {if(!hdPakke.has(key))return false;const m=hdIkoner.get(key);if(!m||m.render_mode!=='raster')return true;if(!m.scene||!m.rect)return false;const p=ikonPalett(m,m.rect[1],diw);return !!p&&rasterIkonLys(m,p)!==null;},
        harHdBilde: key => hdPakke.has(key),
        hdBakgrunner: () => antallBg,
        /* bakgrunner (hash) som bare dekker en del av skjermen og trenger rektangelet fra en scene */
        settUtsnittBakgrunner: (liste) => { utsnittBg.clear(); for (const h of liste) utsnittBg.add(h >>> 0); maaTegnes = true; },
        hdKontroll: () => ({ ...hdKontroll }),      /* hvorfor en figur eventuelt bruker originalen */
        /* figurene som vises med HD-bilde naa, i tegnerekkefoelge (testene); alle: ogsaa de uten */
        hdFigurer: (alle) => visteListe.filter((d) => alle || hdTegnbare.has(d)).map((d) => ({ fil: d.fil, bilde: d.bilde,
            x: d.x - d.xoff, y: d.y, w: d.w, h: d.h, speilet: !!d.speilet, hd: hdTegnbare.has(d), maske: hdFigurMaske.has(d) })),
        hdMasker: () => hdMasker.size,
        viste: () => visteListe.length,             /* figurer som vises med HD-bilde eller gult felt */
        maaTegnes: () => maaTegnes,
        utsnitt: () => crop.slice(),                /* delen av rammebufferet som vises (x0, y0, x1, y1) */
        brukerListe: () => hdPaa && (hdPakke.size > 0 || hdPoser.size > 0 || visRammer),   /* trengs tegnelisten fra kjernen? */
        /* Lastede pakker trenger lag ogsaa i Original for aa beholde plasseringen
         * av engangstegnet tekst naar HD slaas paa igjen. */
        trengerLag: () => hdPakke.size > 0 || hdPoser.size > 0 || effekter.skygge || effekter.dybde || tvungetLag,
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
