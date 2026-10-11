/* Lokal PNG-import i faktisk WASM-side. PIV-fixturer endrer bare lesefunksjoner,
 * aldri emulert minne. Fargede testflater er tekniske proever, ikke spillgrafikk. */
'use strict';
const fs = require('fs'), path = require('path'), assert = require('assert/strict');
const crypto = require('crypto'), {chromium} = require('playwright');
const root = path.resolve(__dirname, '..');
const out = process.env.MOONSTONE_VERIFY_OUT || root + '/art/hd-ui-2026-10-11/verification/import';
const url = process.env.MOONSTONE_URL || 'http://127.0.0.1:8769/moonstone.html';
const report = {url, checks: [], errors: [], captures: [], scope: 'Naturlig tittel med importert logo. Math og intro bruker originale PIV-data som eksplisitte visningsfixturer. Ingen emulert minneskriving.'};
const sha = b => crypto.createHash('sha256').update(b).digest('hex');
const check = (name, ok) => { assert(ok, name); report.checks.push(name); };
let browser;

async function draw(p) {
    return p.evaluate(() => {
        const {Kjerne: K, Visning: V, SceneHd: S, StandardHd: H} = moonDebug;
        const fb = K.rammebuffer(), diw = K.vindu();
        V.tegn(fb, diw, S.korriger(fb, diw, K.lag()));
        H.oppdater(V.lagNaa()?.hash);
        return {png: V.bildeTilPng(), scene: S.info(), state: K.sjekksum()};
    });
}

async function stable(p) {
    let result;
    for (let n = 0; n < 30; n++) result = await draw(p);
    return result;
}

async function capture(p, name) {
    const result = await stable(p);
    fs.writeFileSync(out + '/' + name + '.png', Buffer.from(result.png.split(',')[1], 'base64'));
    report.captures.push({name, scene: result.scene, state: result.state, sha256: sha(result.png)});
    return result;
}

async function importDir(p, dir) {
    await p.locator('#velg-hd').setInputFiles(dir);
    await p.waitForFunction(() => !moonDebug.StandardHd.info().aktiv && document.getElementById('velg-hd').files.length === 0);
}

async function resetTitle(p) {
    await p.evaluate(async () => {
        const {Kjerne: K, Visning: V, SceneHd: S} = moonDebug;
        K.start(false); K.menyPaa(true); K.lagPaa(true); V.nullstillScene(); S.nullstill();
        while (K.bildeNr() < 700) {
            const n = K.bildeNr();
            if (n === 100) K.tast(0x45, true);
            if (n === 104) K.tast(0x45, false);
            K.inndata(0, 0); K.bilde(); V.nyttBilde(K.tegneliste());
            if (n % 100 === 0) await new Promise(r => setTimeout(r, 0));
        }
    });
}

async function fixture(p, row) {
    await p.evaluate(row => {
        const {Kjerne: K, Visning: V, SceneHd: S} = moonDebug;
        let data = window.importFixtureOriginal.file('data/' + row.file), pos = 0;
        for (let n = 0; n < row.frame; n++) {
            const planes = data[pos] * 256 + data[pos + 1];
            const size = ((data[pos + 2] << 24) | (data[pos + 3] << 16) | (data[pos + 4] << 8) | data[pos + 5]) >>> 0;
            pos += 6 + (1 << planes) * 2 + size;
        }
        const src = Spillgrafikk._piv(data.subarray(pos));
        const idx = new Uint8Array(720 * 288), fb = new Uint8Array(720 * 288 * 4), pal = new Uint8Array(288 * 32 * 4);
        for (let y = 0; y < 288; y++) for (let c = 0; c < 32; c++)
            pal.set([...(src.pal[c] || [0, 0, 0]), 255], (y * 32 + c) * 4);
        for (let y = 0; y < 200; y++) for (let x = 0; x < 320; x++) {
            const c = src.px[y * 320 + x], j = (y + 19) * 720 + 70 + x * 2;
            idx[j] = idx[j + 1] = c;
            fb.set([...src.pal[c], 255], j * 4); fb.set([...src.pal[c], 255], (j + 1) * 4);
        }
        K.skanout = () => ({gyldig: true, idx, pal}); K.rammebuffer = () => fb;
        K.vindu = () => [70, 19, 710, 219]; K.lag = () => null;
        V.nullstillScene(); S.nullstill(); V.settHd(true);
    }, row);
    await draw(p); await p.waitForTimeout(150);
}

(async () => {
    fs.mkdirSync(out, {recursive: true});
    browser = await chromium.launch({headless: true, executablePath: process.env.CHROME || '/usr/bin/google-chrome',
        args: ['--no-sandbox', '--use-angle=swiftshader', '--enable-unsafe-swiftshader']});
    const p = await browser.newPage({viewport: {width: 960, height: 700}});
    p.on('pageerror', e => report.errors.push(e.message));
    await p.addInitScript(() => localStorage.setItem('moonstone.innstillinger', JSON.stringify({hd: 'hd', hdValgt: true})));
    await p.goto(url);
    await p.waitForFunction(() => { try {return window.moonDebug && moonDebug.Kjerne.bildeNr() > 1;} catch (_) {return false;} });
    await p.keyboard.press('Pause');
    await p.waitForFunction(() => moonDebug.StandardHd.info().klar, null, {timeout: 60000});
    await p.keyboard.press('Home');
    await resetTitle(p);
    const standard = await capture(p, 'title-standard');
    check('natural_title_logo_is_drawn', await p.evaluate(() => moonDebug.Visning.hdFigurer().some(d => d.fil === 'bold.f' && d.bilde === 73)));
    const logo = await p.evaluate(() => {
        const c = document.createElement('canvas'); c.width = 1220; c.height = 216;
        const ctx = c.getContext('2d'); ctx.fillStyle = '#ff00ff'; ctx.fillRect(0, 0, 1220, 108);
        ctx.fillStyle = '#00ff88'; ctx.fillRect(0, 108, 1220, 108); return c.toDataURL();
    });
    const logoDir = out + '/custom-logo/bold.f'; fs.mkdirSync(logoDir, {recursive: true});
    fs.writeFileSync(logoDir + '/073.png', Buffer.from(logo.split(',')[1], 'base64'));
    await importDir(p, out + '/custom-logo');
    const custom = await capture(p, 'title-custom-logo');
    check('custom_logo_changes_actual_display', custom.png !== standard.png);
    check('custom_logo_uses_complete_texture', await p.evaluate(() => {
        let found = false;
        moonDebug.Visning.scene().traverse(m => {
            const u = m.material?.uniforms, im = u?.map?.value?.image;
            if (m.visible && im?.width === 1220 && im?.height === 216)
                found = JSON.stringify(u.imageRegion.value.toArray()) === '[0,0,1,1]';
        });
        return found;
    }));
    check('custom_logo_does_not_change_game_state', custom.state === standard.state);
    await p.locator('#hd-bryter').selectOption('original');
    const originalLogo = await stable(p);
    await p.locator('#hd-bryter').selectOption('hd');
    const restoredLogo = await capture(p, 'title-custom-logo-restored');
    check('logo_HD_toggle_restores_exactly', restoredLogo.png === custom.png);
    check('logo_Original_toggle_changes_pixels', originalLogo.png !== custom.png);

    // Tom pakke sikrer at egne bakgrunner ikke trenger tidligere standardteksturer.
    await p.locator('#tom-hd').click();
    await p.waitForFunction(() => !moonDebug.StandardHd.info().aktiv && moonDebug.Visning.hdAntall() === 0);
    await importDir(p, out + '/custom-logo');
    await resetTitle(p);
    await stable(p);
    check('logo_without_text_metadata_preserves_aspect_ratio', await p.evaluate(() => {
        let found = false;
        moonDebug.Visning.scene().traverse(m => {
            const u = m.material?.uniforms, im = u?.map?.value?.image;
            if (m.visible && im?.width === 1220 && im?.height === 216)
                found = JSON.stringify(u.imageRegion.value.toArray()) === '[0,0,1,1]' && Math.abs(m.scale.x / m.scale.y - 1220 / 216) < 0.00001;
        });
        return found;
    }));
    await p.locator('#tom-hd').click();
    await p.waitForFunction(() => moonDebug.Visning.hdAntall() === 0);
    await p.evaluate(() => {
        const K = moonDebug.Kjerne;
        window.importFixtureOriginal = {scan: K.skanout, fb: K.rammebuffer, diw: K.vindu, lag: K.lag, file: K.hentFil};
    });
    const rows = await p.evaluate(() => moonDebug.StandardHd.scener().filter(s => ['math-tower', 'stonehenge-overhead', 'waterdeep'].includes(s.id)));
    const dir = out + '/custom-scenes/bg'; fs.mkdirSync(dir, {recursive: true});
    const png = await p.evaluate(() => {
        const c = document.createElement('canvas'); c.width = 1280; c.height = 800;
        const ctx = c.getContext('2d'); ctx.fillStyle = '#dd00ff'; ctx.fillRect(0, 0, 1280, 800); return c.toDataURL();
    });
    for (const row of rows) fs.writeFileSync(dir + '/' + row.hash + '.png', Buffer.from(png.split(',')[1], 'base64'));
    let laterRequests = 0;
    p.on('request', r => { if (/\/hd\//.test(r.url())) laterRequests++; });
    await importDir(p, out + '/custom-scenes');
    check('custom_pack_has_only_own_backgrounds', await p.evaluate(n => moonDebug.Visning.hdAntall() === n && moonDebug.Visning.hdBakgrunner() === n, rows.length));
    for (const row of rows) {
        await fixture(p, row);
        const hd = await capture(p, row.id + '-custom');
        check(row.id + '_custom_scene_matches', hd.scene?.id === row.id);
        check(row.id + '_custom_background_loaded', await p.evaluate(hash => moonDebug.Visning.harHdBilde('bg/' + hash), row.hash));
        await p.locator('#hd-bryter').selectOption('original');
        const original = await capture(p, row.id + '-original');
        const native = await p.evaluate(() => {const {Kjerne: K, Visning: V} = moonDebug; V.tegn(K.rammebuffer(), K.vindu(), K.lag()); return V.bildeTilPng();});
        check(row.id + '_Original_matches_native', original.png === native);
        await p.locator('#hd-bryter').selectOption('hd');
        check(row.id + '_HD_restores_exactly', (await stable(p)).png === hd.png);
        check(row.id + '_HD_changes_pixels', hd.png !== original.png);
        check(row.id + '_display_preserves_game_state', await p.evaluate(state => moonDebug.Kjerne.sjekksum() === state, hd.state));
        check(row.id + '_missing_overlays_are_kept_original', await p.evaluate(() => moonDebug.Visning.lagNaa().overlays.length === 0));
        const rejected = await p.evaluate(row => {
            const {Kjerne: K, SceneHd: S} = moonDebug;
            K.hentFil = name => {
                const data = importFixtureOriginal.file(name);
                if (data && name.toLowerCase() === ('data/' + row.file).toLowerCase()) {const changed = data.slice(); changed[8] ^= 1; return changed;}
                return data;
            };
            S.nullstill();
        }, row);
        await draw(p); await p.waitForTimeout(150); await draw(p);
        check(row.id + '_changed_source_is_rejected', await p.evaluate(() => moonDebug.SceneHd.info() === null));
        await p.evaluate(() => {moonDebug.Kjerne.hentFil = importFixtureOriginal.file; moonDebug.SceneHd.nullstill();});
    }
    check('custom_pack_does_not_restart_standard_requests', laterRequests === 0);
    await p.evaluate(() => {
        const K = moonDebug.Kjerne, o = importFixtureOriginal;
        K.skanout = o.scan; K.rammebuffer = o.fb; K.vindu = o.diw; K.lag = o.lag; K.hentFil = o.file;
        moonDebug.Visning.nullstillScene(); moonDebug.SceneHd.nullstill(); delete window.importFixtureOriginal;
    });
    await p.locator('#standard-hd').click();
    await p.waitForFunction(() => moonDebug.StandardHd.info().klar, null, {timeout: 60000});
    await resetTitle(p);
    check('standard_button_restores_original_standard_logo', (await stable(p)).png === standard.png);
    check('no_browser_errors', report.errors.length === 0);
    report.status = 'passed';
})().catch(e => {report.status = 'failed'; report.failure = String(e); console.error(e); process.exitCode = 1;}).finally(async () => {
    report.created_at = new Date().toISOString();
    report.manifest_sha256 = sha(fs.readFileSync(root + '/web/hd/manifest.json'));
    report.html_sha256 = sha(fs.readFileSync(root + '/web/build/moonstone.html'));
    fs.mkdirSync(out, {recursive: true}); fs.writeFileSync(out + '/ui-import-test.json', JSON.stringify(report, null, 2) + '\n');
    console.log(JSON.stringify({status: report.status, checks: report.checks.length, errors: report.errors, failure: report.failure}));
    if (browser) await browser.close();
});
