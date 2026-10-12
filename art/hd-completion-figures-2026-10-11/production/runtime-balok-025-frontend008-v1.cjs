/* Sjuende Balok-leveranse fra standardpakken, lokalt eller offentlig. Ingen import. */
'use strict';
const fs = require('fs'), path = require('path'), crypto = require('crypto');
const assert = require('assert/strict'), {chromium} = require('playwright');
const art = __dirname, root = path.resolve(art, '../../..');
const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const read = file => fs.readFileSync(file), json = file => JSON.parse(read(file));
const pkg = path.resolve(process.env.MOONSTONE_BALOK_PACKAGE || art + '/../verification/integration-007-final/package');
const out = path.resolve(process.env.MOONSTONE_HD_TEST_OUTPUT || art + '/verification/standard-public-007-' + Date.now());
const publicURL = process.env.MOONSTONE_HD_PUBLIC_URL || null;
const expectedHtml = process.env.MOONSTONE_HD_PUBLIC_HTML_SHA256 || process.env.MOONSTONE_HD_EXPECTED_HTML_SHA256 || (publicURL ? null : sha(read(pkg + '/moonstone.html')));
const sourceFreeze = path.resolve(process.env.MOONSTONE_HD_SOURCE_FREEZE || root);
const manifestBytes = read(pkg + '/hd/manifest.json'), manifest = JSON.parse(manifestBytes);
const caseBytes = read(art + '/../palettes/cases/balok.json'), combat = JSON.parse(caseBytes);
const queue = json(art + '/../queue.json').entries;
const contracts = {
    'activation-set-balok-019-b2-seven-v7.json': 'acd7f78f22cd3bf301578fe3c856a585c36a368268f0e440cde137075e0e48fb',
    'activation-set-balok-020-baked-two-v7.json': 'bc28983c374d2e7ae50c725106111b73e7925bff45fe7d04039c0f73da1382f3',
    'activation-set-balok-021-arm029-v7.json': '5dac03456fa7376134978a6c2457b1280b3e706433e272c1c3af9f9605459ab5',
    'activation-set-balok-022-b2-ten-v7.json': '8a831f39593962d45dc5f00561d7bf00359854e9331be2c75c005dbc87f376ad',
    'activation-set-balok-023-five-aliases-v7.json': '822794ad2944158cdb5e77279944c8c35fd8fefb0d2ee786ac9f030fa8774882'
};
const all = new Map(), assets = new Map();
let productionHashes, wasmHash;
for (const [name, expected] of Object.entries(contracts)) {
    const bytes = read(art + '/' + name), value = JSON.parse(bytes);
    assert.equal(sha(bytes), expected, 'Endret frossen kontrakt: ' + name);
    productionHashes ||= value.production_code_sha256;
    wasmHash ||= value.wasm_core_sha256;
    assert.deepEqual(value.production_code_sha256, productionHashes);
    assert.equal(value.wasm_core_sha256, wasmHash);
    for (const entry of value.entries.filter(e => !e.existing_master)) {
        assert(!all.has(entry.key), 'Duplikat i leveransen: ' + entry.key);
        const q = queue.find(r => r.key === entry.key);
        assert(q && q.indices_sha256 === entry.indices_sha256);
        all.set(entry.key, {...entry, width: q.width, height: q.height, plane_mask: q.plane_mask});
        for (const [key, file, hash] of [[entry.key, entry.png, entry.png_sha256], ...(entry.mask ? [[entry.key.replace('.png', '.mask.png'), entry.mask, entry.mask_sha256]] : [])]) {
            assert.equal(sha(read(root + '/' + file)), hash, 'Endret fotofil: ' + file);
            const m = manifest.files.find(f => f.path === key);
            assert(m && m.kind === 'base' && m.sha256 === hash && m.bytes === read(root + '/' + file).length, 'Aktiv standardfil mangler: ' + key);
            assert.equal(sha(read(pkg + '/hd/' + key)), hash, 'Pakkefil har feil SHA: ' + key);
            assets.set(key, {path: key, sha256: hash, bytes: m.bytes, candidate: file});
        }
    }
}
assert.equal(all.size, 25); // Beistkopien kildeprøves, men kreves ikke observert i kamp.
const historicalProductionHashes = productionHashes;
productionHashes = {"web/src/core.js": "487969759645af593a2b7cb88b697e30852ae39a8a3fa359483a2f2413410e97", "web/src/render.js": "6b93be5b0e12b458b8005fd891a15c0f5a454e35baa2a2d93cdf33666c5b416c", "web/src/scenes.js": "189eed863fa34e74900f221f7f6078e46036adb41537cb9e27e8f7d5a06eff5f"};
const sources = {};
const mapPath = fs.statSync(sourceFreeze).isFile() ? sourceFreeze : sourceFreeze + '/source-map.json';
if (fs.existsSync(mapPath)) {
    const map = json(mapPath);
    assert.equal(map.status, 'frozen');
    for (const f of map.files) {
        const file = path.isAbsolute(f.frozen_path) ? f.frozen_path : root + '/' + f.frozen_path;
        assert.equal(sha(read(file)), f.sha256, 'Endret kildefrys: ' + file);
        sources[f.path] = {file, sha256: f.sha256};
    }
} else {
    for (const f of [...Object.keys(productionHashes), 'web/src/hd.js']) {
        const file = sourceFreeze + '/' + f;
        sources[f] = {file, sha256: sha(read(file))};
    }
}
for (const [f, hash] of Object.entries(productionHashes)) assert.equal(sources[f]?.sha256, hash, 'Feil frontendversjon: ' + f);
assert.equal(sources['web/src/hd.js']?.sha256, 'bb9f22560e9dd669ba075dedf9d644abce72fbdc3fbf43d8a8a961052e1b34ac');
assert(/^[a-f0-9]{64}$/.test(expectedHtml || ''), 'Oppgi uavhengig verifisert HTML-SHA ved offentlig prøve');
if (publicURL) {
    assert(/^https?:\/\//.test(publicURL));
    assert(process.env.MOONSTONE_HD_SOURCE_FREEZE, 'Offentlig prøve krever eksplisitt kildefrys');
}
assert(!fs.existsSync(out), 'Bevar tidligere prøve: ' + out);
const key = (bank, n) => bank + '/' + String(n).padStart(3, '0') + '.png';
const allFlows = [
    {name: 'seventeen-knight-parts', stop: 1680, start: 1330, end: 1660, attack: [1350, 1950, 16], keys: [...Array.from({length: 7}, (_, i) => key('Balok2.CEL', i + 7)), ...Array.from({length: 10}, (_, i) => key('Balok2.CEL', i + 16))]},
    {name: 'arm029', stop: 1680, start: 1330, end: 1660, attack: [1350, 1950, 16], extraLeft: [1530, 1570], keys: [key('Balok1.CEL', 29)]},
    {name: 'baked-blood', stop: 2800, start: 1330, end: 2780, attack: [1550, 2150, 17], keys: [key('Balok1.CEL', 67), key('Balok1.CEL', 68)]},
    {name: 'four-Balok3-aliases', stop: 2240, start: 2190, end: 2235, keys: [24, 25, 26, 27].map(n => key('Balok3.CEL', n))}
];
const report = {
    schema: 1, status: 'running', checks: [], errors: [], flows: [], historical_production_code_sha256:historicalProductionHashes,
    manifest_sha256: sha(manifestBytes), manifest_pngs: manifest.images,
    local_html_sha256: sha(read(pkg + '/moonstone.html')), expected_html_sha256: expectedHtml,
    source_freeze: sourceFreeze, production_code_sha256: Object.fromEntries(Object.entries(sources).map(([f, v]) => [f, v.sha256])),
    source_zip_sha256: combat.source_zip_sha256, wasm_core_sha256: wasmHash,
    test_sha256: sha(read(__filename)), contracts, assets: [...assets.values()],
    palette_case_sha256: sha(caseBytes),
    scope: 'Standardpakken alene. Tjue nye Balok-mastere og fire Balok3-aliaser kreves faktisk vist gjennom fire kontrollerte originalkampforløp. Tre kildebeviste init-skrivinger ved900, deretter original inndata, CPU og tegneliste. Ingen kandidatimport, palettskriving eller naturlig kartreise. be1/057 er byte-/manifestkontrollert, men bare kilde- og frontendfixture er tidligere bevist for denne aliasen.'
};
const check = (name, ok) => {assert(ok, name); report.checks.push(name);};
let browser, server;
function verifyHtml(bytes) {
    check('faktisk_HTML_SHA', sha(bytes) === expectedHtml);
    const text = bytes.toString();
    const core = read(root + '/web/build/moonstone-core.js');
    check('innebygd_originalWASM_SHA', sha(core) === wasmHash);
    check('innebygd_originalWASM_bytes', text.includes(core.toString().replaceAll('</script', '<\\/script')));
    for (const [f, value] of Object.entries(sources)) {
        const code = read(value.file).toString().replaceAll('</script', '<\\/script');
        if (f !== 'web/src/hd.js') check('innebygd_' + f, text.includes(code));
        else {
            const [before, after] = code.split('%%HD_MANIFEST%%'), start = text.indexOf(before);
            const end = text.indexOf(after, start + before.length);
            check('innebygd_standardkode', start >= 0 && end > start);
            check('innebygd_manifest', JSON.stringify(JSON.parse(text.slice(start + before.length, end))) === JSON.stringify(manifest));
        }
    }
}
(async () => {
    fs.mkdirSync(out, {recursive: true});
    if (!publicURL) server = await require('../figures/kn3-production/runtime-host.cjs')(pkg);
    report.url = publicURL || server.url;
    browser = await chromium.launch({headless: true, executablePath: '/usr/bin/google-chrome', args: ['--no-sandbox', '--use-angle=swiftshader', '--enable-unsafe-swiftshader']});
    for (const flow of [{...allFlows[3],keys:[key('Balok3.CEL',25)]}]) {
        const p = await browser.newPage({viewport: {width: 960, height: 700}});
        p.on('pageerror', e => report.errors.push(flow.name + ': ' + e.message));
        await p.addInitScript(() => localStorage.setItem('moonstone.innstillinger', JSON.stringify({hd: 'hd', hdValgt: true})));
        const response = await p.goto(report.url), html = await response.body();
        verifyHtml(html);
        report.html_sha256 = sha(html);
        if (!report.flows.length) {
            fs.writeFileSync(out + '/loaded.html', html);
            const response = await p.request.get(new URL('hd/manifest.json', report.url).href), bytes = await response.body();
            check('faktisk_standardmanifest', response.ok() && sha(bytes) === report.manifest_sha256);
            for (const asset of assets.values()) {
                const response = await p.request.get(new URL('hd/' + asset.path, report.url).href), bytes = await response.body();
                check('faktisk_standardfil_' + asset.path, response.ok() && sha(bytes) === asset.sha256 && bytes.length === asset.bytes);
            }
        }
        await p.waitForFunction(() => {try {return moonDebug.Kjerne.bildeNr() > 1;} catch {return false;}}, null, {timeout: 120000});
        await p.keyboard.press('Pause');
        await p.waitForFunction(() => moonDebug.StandardHd.info().klar, null, {timeout: 120000});
        console.log(JSON.stringify({phase: 'originalkamp', flow: flow.name}));
        const routes = flow.keys.map(k => all.get(k));
        const result = await p.evaluate(async ({flow, routes, combat, backgrounds}) => {
            const {Kjerne: K, Visning: V, StandardHd: H, SceneHd: S} = moonDebug, M = await K.last();
            const before = H.info(), sourceRows = {}, samples = {}, trace = [];
            if (!before.aktiv || !before.klar || before.feil) throw Error('Standardpakken er ikke klar');
            const digest = async b => [...new Uint8Array(await crypto.subtle.digest('SHA-256', b))].map(v => v.toString(16).padStart(2, '0')).join('');
            for (const route of routes) {
                const bank = K.hentFil('data/' + route.bank.toLowerCase()), source = Spillgrafikk._cel(bank)[route.frame];
                const bits = Array.from({length: 5}, (_, n) => 1 << n).filter(n => route.plane_mask & n);
                const indices = Uint8Array.from(source.px, v => bits.reduce((sum, bit, n) => sum | ((v & (1 << n)) ? bit : 0), 0));
                sourceRows[route.key] = {bank_sha256: await digest(bank), indices_sha256: await digest(indices), used: [...new Set(indices)].sort((a, b) => a - b), image_loaded: V.harHdBilde(route.key.toLowerCase().replace('.png', ''))};
            }
            K.start(false); K.menyPaa(false); K.lagPaa(true); V.nullstillScene(); S.nullstill();
            V.settHd(true); V.settTvungetLag(true); V.settFilter('skarp');
            const lookup = Object.fromEntries(routes.map(r => [r.key.toLowerCase().replace('.png', ''), r.key]));
            const draw = () => {const f = K.rammebuffer(), d = K.vindu(), l = S.korriger(f, d, K.lag()); V.tegn(f, d, l); H.oppdater(l?.hash);};
            const capture = () => {for (let i = 0; i < 3; i++) draw(); const a = V.bildeTilPng(); draw(); const b = V.bildeTilPng(); if (a !== b) throw Error('Ustabilt Balok-bilde'); return b;};
            let warmed = false;
            while (K.bildeNr() < flow.stop) {
                const n = K.bildeNr();
                if (n === 100) K.tast(0x45, true);
                if (n === 104) K.tast(0x45, false);
                let input = ((n >= 700 && n < 704) || (n >= 760 && n < 764) ? 2 : 0) | (n >= 820 && n < 824 ? 16 : 0) | (n >= 1200 && n < 1320 ? 4 : 0);
                if (flow.attack && n >= flow.attack[0] && n < flow.attack[1]) input |= flow.attack[2];
                if (flow.extraLeft && n >= flow.extraLeft[0] && n < flow.extraLeft[1]) input |= 4;
                K.inndata(0, input);
                if (n === 900) {
                    const view = new DataView(M.HEAPU8.buffer), chip = M._ms_chip();
                    for (const w of combat.test_writes) view.setUint32(chip + parseInt(w.address), parseInt(w.value), false);
                }
                K.bilde(); const draws = K.tegneliste(); V.nyttBilde(draws);
                if (K.bildeNr() >= 1200 && draws.some(d => d.fil.toLowerCase().startsWith('balok'))) trace.push({frame: K.bildeNr(), draws: draws.filter(d => d.fil.toLowerCase().startsWith('balok'))});
                if (K.bildeNr() >= 1330 && !warmed) {
                    let ready = false;
                    for (let q = 0; q < 1200; q++) {
                        draw(); const info = H.info(), hash = (V.lagNaa()?.hash >>> 0).toString(16).padStart(8, '0');
                        if (info.feil) throw Error('Standardpakken feilet: ' + info.feil);
                        if (info.aktiv && info.klar && !info.laster && (!backgrounds.includes(hash) || info.bakgrunner.includes(hash))) {ready = true; break;}
                        await new Promise(resolve => setTimeout(resolve, 10));
                    }
                    if (!ready) throw Error('Balok-bakgrunnen er ikke klar');
                    for (let q = 0; q < 30; q++) draw();
                    warmed = true;
                }
                if (K.bildeNr() >= flow.start && K.bildeNr() <= flow.end) {
                    draw(); const visible = V.hdFigurer(true);
                    for (const hit of visible.filter(d => d.hd && lookup[d.fil.toLowerCase() + '/' + String(d.bilde).padStart(3, '0')])) {
                        const name = lookup[hit.fil.toLowerCase() + '/' + String(hit.bilde).padStart(3, '0')];
                        if (samples[name]) continue;
                        const scan = K.skanout(), diw = K.vindu(), row = Math.max(0, Math.min(287, diw[1] + hit.y + (hit.h / 2 | 0)));
                        const palette = Array.from({length: 32}, (_, i) => Array.from(scan.pal.slice((row * 32 + i) * 4, (row * 32 + i + 1) * 4)));
                        const state = K.sjekksum();
                        V.settHd(false); const original = capture(); V.settHd(true); const hd = capture();
                        const control = V.hdKontroll(); V.settHd(false); const originalAgain = capture(); V.settHd(true); const hdAgain = capture();
                        samples[name] = {frame: K.bildeNr(), source: hit, draws, visible, control, scan_valid: scan.gyldig, palette, state, state_after: K.sjekksum(), original, hd, originalAgain, hdAgain, background_hash: (V.lagNaa()?.hash >>> 0).toString(16).padStart(8, '0'), diagnostic: (()=>{const l=V.lagNaa(), cells=[];for(const [x,y] of [[161,125],[150,125],[155,130],[175,155],[178,165]]){const z=y*320+x,k=z*4;cells.push({x,y,forIdx:l.forIdx[z],bakIdx:l.bakIdx[z],forRGBA:Array.from(l.for.slice(k,k+4)),bakRGBA:Array.from(l.bak.slice(k,k+4)),kampDeltaVern:l.kampDeltaVern?.[z]||0});}const meshes=[];V.scene().traverse(o=>{if(!o.visible||!o.material?.uniforms)return;const u=o.material.uniforms,v=u.vern?.value?.image, map=u.map?.value?.image;meshes.push({order:o.renderOrder,pos:o.position.toArray(),scale:o.scale.toArray(),lagPos:u.lagPos?.value?.toArray(),imageRegion:u.imageRegion?.value?.toArray(),mapSize:map?[map.width,map.height]:null,vernSize:v?[v.width,v.height]:null,points:cells.filter(c=>[[161,125],[150,125],[155,130],[175,155],[178,165]].some(z=>z[0]===c.x&&z[1]===c.y)).map(c=>({x:c.x,y:c.y,vern:v?.data?.[(c.y*320+c.x)*4+3],mapRGBA:map?.data&&map.width===320?Array.from(map.data.slice((c.y*320+c.x)*4,(c.y*320+c.x)*4+4)):null}))});});return {lagKeys:Object.keys(l),cells,meshes};})()};
                    }
                }
                if (Object.keys(samples).length === routes.length) break;
                if (n % 100 === 0) await new Promise(resolve => setTimeout(resolve, 0));
            }
            return {before, after: H.info(), source_rows: sourceRows, samples, trace, frame: K.bildeNr()};
        }, {flow, routes, combat, backgrounds: manifest.files.filter(f => f.kind === 'background').map(f => f.path.slice(3, -4))});
        report.flows.push({name: flow.name, ...result});
        check(flow.name + '_standard_foer', result.before.aktiv && result.before.klar && !result.before.feil);
        check(flow.name + '_standard_etter', result.after.aktiv && result.after.klar && !result.after.feil);
        for (const route of routes) {
            const src = result.source_rows[route.key], s = result.samples[route.key];
            check(route.key + '_kildebank_SHA', src.bank_sha256 === route.source_bank_sha256);
            check(route.key + '_kildeindeks_SHA', src.indices_sha256 === route.indices_sha256);
            check(route.key + '_standardbilde_lastet', src.image_loaded);
            check(route.key + '_faktisk_HD', !!s && s.source.hd && s.source.maske === !!route.mask);
            const sameSource = d => d.fil.toLowerCase() === route.bank.toLowerCase() && d.bilde === route.frame &&
                d.x - d.xoff === s.source.x && d.y === s.source.y && d.w === s.source.w && d.h === s.source.h && !!d.speilet === s.source.speilet;
            const calls = result.trace.filter(t => t.frame <= s.frame).flatMap(t => t.draws.filter(sameSource).map(d => ({frame: t.frame, ...d})));
            s.source_calls = calls;
            check(route.key + '_originalkall_med_anker_speil_buffer', calls.some(d => d.caller === 0x087bf0 && d.target === 0x0a2cd6));
            if (route.bank === 'Balok1.CEL' && [67, 68].includes(route.frame)) check(route.key + '_original_bakgrunnsbaking', calls.some(d => d.caller === 0x087b34 && d.target === 0x0a2cd6));
            check(route.key + '_originalgeometri', s.source.w === route.width && s.source.h === route.height);
            check(route.key + '_faste_kildefarger', s.scan_valid && src.used.filter(i => i && ![6, 7, 8].includes(i)).every(i => JSON.stringify(s.palette[i].slice(0, 3)) === JSON.stringify(combat.colors[i])));
            check(route.key + '_HD_endrer_bilde', s.original !== s.hd);
            check(route.key + '_Original_retur', s.original === s.originalAgain);
            check(route.key + '_HD_retur', s.hd === s.hdAgain);
            check(route.key + '_CPU_urort', s.state === s.state_after);
            for (const mode of ['original', 'hd']) {
                const bytes = Buffer.from(s[mode].split(',')[1], 'base64');
                fs.writeFileSync(out + '/' + route.key.replace('/', '-').replace('.png', '') + '-' + mode + '.png', bytes);
                s[mode + '_sha256'] = sha(bytes);
            }
            for (const mode of ['original', 'hd', 'originalAgain', 'hdAgain']) delete s[mode];
        }
        await p.close();
    }
    check('en_faktisk_Balok025_pose_diagnostisert', report.flows.reduce((n, f) => n + Object.keys(f.samples).length, 0) === 1);
    check('ingen_nettleserfeil', report.errors.length === 0);
    for (const [f, value] of Object.entries(sources)) check('uendret_frys_' + f, sha(read(value.file)) === value.sha256);
    for (const asset of assets.values()) check('uendret_kandidat_' + asset.path, sha(read(root + '/' + asset.candidate)) === asset.sha256);
    check('uendret_originalZIP', sha(read(root + '/Moonstonecd32-AMIGA.zip')) === combat.source_zip_sha256);
    check('uendret_originalWASM', sha(read(root + '/web/build/moonstone-core.js')) === wasmHash);
    check('uendret_standardmanifest', sha(read(pkg + '/hd/manifest.json')) === report.manifest_sha256);
    check('uendret_testskript', sha(read(__filename)) === report.test_sha256);
    report.status = 'passed';
})().catch(e => {
    report.status = 'failed'; report.failure = String(e); console.error(e); process.exitCode = 1;
}).finally(async () => {
    report.created_at = new Date().toISOString();
    fs.mkdirSync(out, {recursive: true}); fs.writeFileSync(out + '/test.json', JSON.stringify(report, null, 2) + '\n');
    console.log(JSON.stringify({status: report.status, checks: report.checks.length, actual: report.flows.flatMap(f => Object.entries(f.samples).map(([key, s]) => ({key, frame: s.frame}))), output: out, failure: report.failure}));
    if (browser) await browser.close(); if (server) await server.close();
});
