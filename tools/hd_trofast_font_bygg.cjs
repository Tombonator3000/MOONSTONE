/* Pakk originaltro fontkonturer og kontroller selvstendig CEL/planmaske,
 * alle pikselmidtpunkter, sammenhengende stroek og originale hull. */
'use strict';
const fs = require('fs'), path = require('path'), assert = require('assert/strict');
const crypto = require('crypto'), {execFileSync} = require('child_process'), {chromium} = require('playwright');
const root = path.resolve(__dirname, '..'), art = root + '/art/hd-faithful-text-2026-10-11';
const sha = b => crypto.createHash('sha256').update(b).digest('hex');
const python = "import sys,json,base64\nsys.path.insert(0,sys.argv[1]+'/tools')\nimport moonfiles as m\ns=m.Spill(sys.argv[1]+'/Moonstonecd32-AMIGA.zip')\nprint(json.dumps({n:base64.b64encode(s.les(n)).decode() for n in ['bold.f','small.font']}))";

(async () => {
    const source = JSON.parse(fs.readFileSync(art + '/source-contracts.json'));
    const contours = JSON.parse(fs.readFileSync(art + '/contours.json'));
    const fragment = JSON.parse(fs.readFileSync(art + '/fragment-text.json'));
    const rawBanks = JSON.parse(execFileSync('python3', ['-c', python, root], {encoding: 'utf8'}));
    assert.equal(source.original_zip_sha256, sha(fs.readFileSync(root + '/Moonstonecd32-AMIGA.zip')));
    for (const [bank, raw] of Object.entries(rawBanks)) assert.equal(sha(Buffer.from(raw, 'base64')), source.banks[bank]);
    assert.equal(fragment.glyphs.length, 144);
    const report = {scope: '142 fontglyfer og to opphavsrettsfelt. Originale former med kantutjevning; ingen ny skrifttype. Kandidat, ikke aktivering.', assets: [], checks: 0};
    const browser = await chromium.launch({headless: true, executablePath: process.env.CHROME || '/usr/bin/google-chrome', args: ['--no-sandbox']});
    try {
        const p = await browser.newPage();
        await p.addScriptTag({content: fs.readFileSync(root + '/web/src/grafikk.js', 'utf8')});
        for (const m of contours.entries) {
            const c = source.entries.find(c => c.key === m.key);
            const svg = fs.readFileSync(art + '/svg/' + m.key + '.svg', 'utf8');
            const result = await p.evaluate(async ({svg, m, c, raw}) => {
                const data = Uint8Array.from(atob(raw), s => s.charCodeAt(0));
                const parsed = Spillgrafikk._cel(data)[c.source.frame];
                const mask = data[19 + c.source.frame * 10], bits = [1, 2, 4, 8, 16].filter(b => mask & b);
                const indices = parsed.px.map(v => bits.reduce((sum, bit, n) => sum | (v & (1 << n) ? bit : 0), 0));
                const sourceExact = parsed.w === m.width && parsed.h === m.height && mask === c.plane_mask && indices.every((v, i) => v === c.indices[i]);
                const image = new Image(); image.src = 'data:image/svg+xml;base64,' + btoa(svg); await image.decode();
                const canvas = document.createElement('canvas'); canvas.width = m.width * 8; canvas.height = m.height * 8;
                const ctx = canvas.getContext('2d'); ctx.drawImage(image, 0, 0);
                const pixels = ctx.getImageData(0, 0, canvas.width, canvas.height).data;
                let exact = 0, transparent = 0; const bad = [];
                for (let y = 0; y < m.height; y++) for (let x = 0; x < m.width; x++) {
                    const idx = indices[y * m.width + x], at = ((y * 8 + 4) * canvas.width + x * 8 + 4) * 4;
                    const got = Array.from(pixels.slice(at, at + 4));
                    const ok = idx ? got.every((v, k) => v === (k === 3 ? 255 : c.palette[idx][k])) : got[3] === 0;
                    if (ok) {exact++; if (!idx) transparent++;} else if (bad.length < 8) bad.push({x, y, idx, got});
                }
                const components = (mask, w, h, eight = false) => {
                    const seen = new Uint8Array(mask.length), steps = [[1, 0], [-1, 0], [0, 1], [0, -1]];
                    if (eight) steps.push([1, 1], [1, -1], [-1, 1], [-1, -1]);
                    let total = 0, internal = 0;
                    for (let start = 0; start < mask.length; start++) {
                        if (!mask[start] || seen[start]) continue;
                        total++; let edge = false; const todo = [start]; seen[start] = 1;
                        for (let q = 0; q < todo.length; q++) {
                            const at = todo[q], x = at % w, y = Math.floor(at / w);
                            if (x === 0 || y === 0 || x === w - 1 || y === h - 1) edge = true;
                            for (const [dx, dy] of steps) {
                                const xx = x + dx, yy = y + dy, next = yy * w + xx;
                                if (xx >= 0 && xx < w && yy >= 0 && yy < h && mask[next] && !seen[next]) {seen[next] = 1; todo.push(next);}
                            }
                        }
                        if (!edge) internal++;
                    }
                    return {total, internal};
                };
                const before = Uint8Array.from(indices, v => v ? 1 : 0);
                const after = Uint8Array.from({length: canvas.width * canvas.height}, (_, i) => pixels[i * 4 + 3] >= 128 ? 1 : 0);
                const topology = {source_components: components(before, m.width, m.height, true).total,
                    packed_components: components(after, canvas.width, canvas.height).total,
                    source_holes: components(before.map(v => 1 - v), m.width, m.height).internal,
                    packed_holes: components(after.map(v => 1 - v), canvas.width, canvas.height).internal};
                const faceBefore = Uint8Array.from(indices, v => v && (c.source.file !== 'bold.f' || v !== 5) ? 1 : 0);
                const faceAfter = Uint8Array.from(after, (v, i) => v && pixels[i*4]+pixels[i*4+1]+pixels[i*4+2] > 25 ? 1 : 0);
                const faceTopology = {source_components: components(faceBefore, m.width, m.height, true).total,
                    packed_components: components(faceAfter, canvas.width, canvas.height).total,
                    source_holes: components(faceBefore.map(v => 1 - v), m.width, m.height).internal,
                    packed_holes: components(faceAfter.map(v => 1 - v), canvas.width, canvas.height).internal};
                return {png: canvas.toDataURL('image/png').split(',')[1], sourceExact, exact, transparent, bad, topology, faceTopology};
            }, {svg, m, c, raw: rawBanks[c.source.file]});
            assert(result.sourceExact, m.key + ': uavhengig CEL-/planmaskekontroll feilet');
            assert.equal(result.exact, m.width * m.height, m.key + ': feil kildepikselmidtpunkter ' + JSON.stringify(result.bad));
            assert.equal(result.topology.source_components, result.topology.packed_components, m.key + ': diagonalt stroek brutt');
            assert.equal(result.topology.source_holes, result.topology.packed_holes, m.key + ': originalt hull endret');
            assert.equal(result.faceTopology.source_components, result.faceTopology.packed_components, m.key + ': synlig bokstavstroek brutt');
            assert.equal(result.faceTopology.source_holes, result.faceTopology.packed_holes, m.key + ': hull i bokstavformen endret');
            const file = art + '/packed/' + m.key + '.png', bytes = Buffer.from(result.png, 'base64');
            fs.mkdirSync(path.dirname(file), {recursive: true}); fs.writeFileSync(file, bytes);
            fragment.glyphs.find(g => g.file + '/' + String(g.frame).padStart(3, '0') === m.key).sha256 = sha(bytes);
            report.assets.push({key: m.key, width: m.width * 8, height: m.height * 8, sha256: sha(bytes), bytes: bytes.length,
                source_midpoints: result.exact, transparent_midpoints: result.transparent, topology: result.topology, face_topology: result.faceTopology});
            report.checks += result.exact + 7;
        }
        fs.writeFileSync(art + '/fragment-text.json', JSON.stringify(fragment, null, 2) + '\n');
        report.status = 'passed'; report.created_at = new Date().toISOString();
        fs.writeFileSync(art + '/packing-report.json', JSON.stringify(report, null, 2) + '\n');
        execFileSync('python3', [root + '/tools/hd_trofast_font_bygg.py', '--preview-only']);
        console.log(JSON.stringify({status: report.status, assets: report.assets.length, checks: report.checks}));
    } finally {await browser.close();}
})().catch(e => {console.error(e); process.exitCode = 1;});
