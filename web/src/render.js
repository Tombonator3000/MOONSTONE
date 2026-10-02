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
    let crop = [70, 19, 710, 219];
    let stabil = 0, nyCrop = null;

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
    }

    function settFilter(f) {
        filter = f;
        mat.uniforms.mode.value = { skarp: 0, piksel: 1, myk: 2, crt: 3 }[f] ?? 0;
        const lin = f !== 'piksel';
        tex.magFilter = tex.minFilter = lin ? THREE.LinearFilter : THREE.NearestFilter;
        tex.needsUpdate = true;
    }

    function settFormat(f) { format = f; tilpass(); }
    function settHelt(on) { helt = on; nyCrop = null; stabil = 99; }

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

    function tegn(fb, diw) {
        data.set(fb);
        tex.needsUpdate = true;
        if (diw) oppdaterUtsnitt(diw);
        renderer.render(scene, camera);
    }

    function bildeTilPng() {
        return renderer.domElement.toDataURL('image/png');
    }

    return { init, tegn, tilpass, settFilter, settFormat, settHelt, bildeTilPng, scene: () => scene };
})();
