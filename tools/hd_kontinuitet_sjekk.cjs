/* Naturlige Next Day-faser og bakgrunnslasting med treg figurpakke/nettfeil. */
'use strict';
const fs = require('fs'), path = require('path'), crypto = require('crypto'), assert = require('assert/strict');
const { chromium } = require('playwright');
const root = path.resolve(__dirname, '..');
const out = process.env.MOONSTONE_VERIFY_OUT || '/tmp/moonstone-hd-kontinuitet';
const report = { checks: [], errors: [], phases: [] };
let browser, server, releaseBase;
const check = (name, value) => { assert(value, name); report.checks.push(name); };
async function draw(p) {
    return p.evaluate(() => {
        const { Kjerne: K, Visning: V, SceneHd: S, StandardHd: H } = moonDebug;
        const lag = S.korriger(K.rammebuffer(), K.vindu(), K.lag());
        V.tegn(K.rammebuffer(), K.vindu(), lag); H.oppdater(lag?.hash);
        return { scene: S.info(), control: V.hdKontroll(), hd: H.info(), png: V.bildeTilPng() };
    });
}
async function step(p, end) {
    return p.evaluate(async end => {
        const { Kjerne: K, Visning: V, SceneHd: S, StandardHd: H } = moonDebug;
        while (K.bildeNr() < end) {
            const n = K.bildeNr();
            if (n === 100) K.tast(0x45, true);
            if (n === 104) K.tast(0x45, false);
            const down = [700, 760, 820].some(f => n >= f && n < f + 4);
            const fire = [880, 1100, 1200].some(f => n >= f && n < f + 4) || (n >= 4000 && n % 600 < 4);
            K.inndata(0, down ? 2 : fire ? 16 : 0);
            if (n === 2100) K.tast(0x40, true);
            if (n === 2104) K.tast(0x40, false);
            if (n === 3400) K.tast(0x32, true);
            if (n === 3404) K.tast(0x32, false);
            if (n >= 3500 && (n - 3500) % 400 === 0) K.tast(0x12, true);
            if (n >= 3504 && (n - 3504) % 400 === 0) K.tast(0x12, false);
            K.bilde();
            const list = K.tegneliste();
            for (const d of list) if (d.fil.toLowerCase() === 'ki.cel' && d.bilde >= 45) window.lastNaturalMoon = { frame: K.bildeNr(), ...d };
            V.nyttBilde(list);
            if (n % 20 === 0) {
                const lag = S.korriger(K.rammebuffer(), K.vindu(), K.lag());
                V.tegn(K.rammebuffer(), K.vindu(), lag); H.oppdater(lag?.hash);
                await new Promise(r => setTimeout(r, 0));
            }
        }
        return { frame: K.bildeNr(), last: window.lastNaturalMoon, stopped: K.stoppet() };
    }, end);
}
(async () => {
    fs.mkdirSync(out, { recursive: true });
    if (!process.env.MOONSTONE_URL) server = await require('../art/hd-completion-figures-2026-10-11/figures/kn3-production/runtime-host.cjs')(process.env.MOONSTONE_BUILD || root + '/web/build');
    const url = process.env.MOONSTONE_URL || server.url;
    browser = await chromium.launch({ headless: true, executablePath: process.env.CHROME || '/usr/bin/google-chrome', args: ['--no-sandbox', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'] });
    const p = await browser.newPage({ viewport: { width: 640, height: 500 } });
    p.on('pageerror', e => report.errors.push(e.message));
    await p.addInitScript(() => localStorage.setItem('moonstone.innstillinger', JSON.stringify({ hd: 'hd', hdValgt: true })));
    const baseGate = new Promise(r => { releaseBase = r; });
    let requests = 0, baseRequests = 0;
    await p.route('**/hd/**', async route => {
        const url = new URL(route.request().url());
        if (url.pathname.endsWith('/bg/55bb9767.png') && requests++ === 0) await route.fulfill({ status: 503, body: 'Temporary outage' });
        else {
            if (!url.pathname.includes('/bg/') && !/\/(text\.json|bold\.f\/[^/]+|small\.font\/[^/]+|sel\.cel\/00[01]\.png)$/.test(url.pathname)) await baseGate;
            if (url.pathname.endsWith('/bold.f/000.png') && baseRequests++ === 0) await route.fulfill({ status: 503, body: 'Temporary font outage' });
            else await route.continue();
        }
    });
    const response = await p.goto(url);
    report.html_sha256 = crypto.createHash('sha256').update(await response.body()).digest('hex');
    await p.waitForFunction(() => { try { return window.moonDebug && moonDebug.Kjerne.bildeNr() > 1; } catch (_) { return false; } });
    await p.keyboard.press('Pause');
    await p.evaluate(() => {
        const { Kjerne: K, Visning: V, SceneHd: S } = moonDebug;
        K.start(false); K.menyPaa(false); K.lagPaa(true); V.nullstillScene(); S.nullstill();
    });
    await p.evaluate(async () => {
        const { Kjerne: K, Visning: V, SceneHd: S, StandardHd: H } = moonDebug;
        while (K.bildeNr() < 1800) {
            K.inndata(0, 0); K.bilde(); V.nyttBilde(K.tegneliste());
            if (K.bildeNr() % 20 === 0) {
                const lag = S.korriger(K.rammebuffer(), K.vindu(), K.lag()); V.tegn(K.rammebuffer(), K.vindu(), lag); H.oppdater(lag?.hash);
                await new Promise(r => setTimeout(r, 0));
            }
        }
    });
    let intro;
    for (let i = 0; i < 100; i++) { intro = await draw(p); if (intro.scene?.id === 'intro-scroll' && intro.control.bakgrunn === 'hd') break; await p.waitForTimeout(50); }
    report.intro = { scene: intro.scene, control: intro.control, hd: intro.hd };
    check('natural_scroll_intro_HD_before_slow_base_package', intro.scene?.id === 'intro-scroll' && intro.control.bakgrunn === 'hd' && !intro.hd.klar);
    fs.writeFileSync(out + '/intro-early-hd.png', Buffer.from(intro.png.split(',')[1], 'base64'));
    const originalIntro = await p.evaluate(() => {
        const { Kjerne: K, Visning: V, SceneHd: S } = moonDebug, fb = K.rammebuffer(), diw = K.vindu(), before = K.sjekksum();
        V.settHd(false); const l = S.korriger(fb, diw, K.lag()); V.tegn(fb, diw, l);
        let mismatch = 0;
        for (let y = 0; y < 200; y++) for (let x = 0; x < 320; x++) {
            const p = (y * 320 + x) * 4, q = ((diw[1] + y) * 720 + diw[0] + x * 2) * 4, src = l.for[p + 3] ? l.for : l.bak;
            for (let k = 0; k < 4; k++) if (src[p + k] !== fb[q + k]) mismatch++;
        }
        V.settHd(true); return { mismatch, stateUnchanged: K.sjekksum() === before };
    });
    check('early_scroll_original_pixels_and_state_preserved', originalIntro.mismatch === 0 && originalIntro.stateUnchanged);
    await p.evaluate(() => {
        const K = moonDebug.Kjerne; window.rollFileRead = K.hentFil; window.rollRevision = K.filRevisjon;
        K.hentFil = name => { const bytes = rollFileRead(name); if (name === 'data/intro.stile' && bytes) { const altered = bytes.slice(); altered[0] ^= 1; return altered; } return bytes; };
        K.filRevisjon = () => rollRevision() + 1;
    });
    await draw(p); await p.waitForTimeout(100);
    check('early_scroll_modified_source_still_rejected', (await draw(p)).scene?.id !== 'intro-scroll');
    await p.evaluate(() => { moonDebug.Kjerne.hentFil = rollFileRead; moonDebug.Kjerne.filRevisjon = rollRevision; });
    await draw(p); await p.waitForTimeout(100);
    check('early_scroll_source_restore_recovers_HD', (await draw(p)).scene?.id === 'intro-scroll');
    await p.evaluate(() => {
        const { Kjerne: K, Visning: V, SceneHd: S } = moonDebug;
        K.start(false); K.menyPaa(false); K.lagPaa(true); V.nullstillScene(); S.nullstill();
    });
    await step(p, 600);
    for (let i = 0; i < 100; i++) { await draw(p); if (await p.evaluate(() => moonDebug.StandardHd.info().bakgrunner.includes('55bb9767'))) break; await p.waitForTimeout(50); }
    const early = await draw(p); delete early.png; report.early = { ...early, requests };
    check('background_loaded_before_slow_base_package', early.hd.bakgrunner.includes('55bb9767') && !early.hd.klar);
    check('temporary_background_503_recovers_automatically', requests === 2 && early.hd.feil === null);
    // menyPaa(false) gir originalens fire rader, 35 tegn. Options-raden i
    // nettmenyen ville gitt flere, men den brukes ikke av denne sekvensen.
    for (let i = 0; i < 300; i++) { const d = await draw(p); if (d.control.bakgrunn === 'hd' && d.control.tekstGodkjent >= 35) break; await p.waitForTimeout(50); }
    const priority = await draw(p); delete priority.png; report.priority = { ...priority, baseRequests };
    check('HD_title_and_text_before_monster_and_portrait_download', priority.control.bakgrunn === 'hd' && priority.control.tekstGodkjent >= 35 && priority.control.tekstAvvist === 0 && !priority.hd.klar);
    check('temporary_base_503_recovers_automatically', baseRequests === 2 && priority.hd.feil === null);
    if (process.env.MOONSTONE_HD_EARLY_ONLY === '1') {
        check('no_browser_errors', report.errors.length === 0);
        report.scope = 'Natural intro scroll and title while remaining base files are blocked; five moon phases and combat are a separate full run';
        report.status = 'passed'; return;
    }
    releaseBase();
    await p.waitForFunction(() => moonDebug.StandardHd.info().klar, null, { timeout: 180000 });
    for (const [end, phase] of [[4053, 45], [6755, 46], [11558, 47], [19406, 48], [23739, 49]]) {
        const journey = await step(p, end);
        check('natural_moon_phase_' + phase, journey.last?.bilde === phase && !journey.stopped);
        let sample;
        for (let i = 0; i < 60; i++) { sample = await draw(p); if (sample.control.bakgrunn === 'hd') break; await p.waitForTimeout(50); }
        check('phase_' + phase + '_verified_HD_sky', sample.scene?.id === 'loading' && sample.control.bakgrunn === 'hd');
        const state = await p.evaluate(() => moonDebug.Kjerne.sjekksum());
        const evidence = await p.evaluate(phase => {
            const V = moonDebug.Visning, moon = V.hdFigurer().filter(d => d.fil.toLowerCase() === 'ki.cel' && d.bilde === phase);
            const front = V.scene().children.find(m => m.renderOrder === 3).material.uniforms.map.value.image.data;
            let transparent = 0;
            for (let y = 12; y < 56; y++) for (let x = 119; x < 176; x++) if (front[(y * 320 + x) * 4 + 3] === 0) transparent++;
            return { moon, transparent };
        }, phase);
        check('phase_' + phase + '_HD_moon_approved', evidence.moon.length === 1);
        check('phase_' + phase + '_no_blue_rectangle', evidence.transparent === 57 * 44);
        fs.writeFileSync(out + '/phase-' + phase + '-hd.png', Buffer.from(sample.png.split(',')[1], 'base64'));
        await p.evaluate(() => moonDebug.Visning.settHd(false));
        const original = await draw(p);
        await p.evaluate(() => moonDebug.Visning.settHd(true));
        const restored = await draw(p);
        check('phase_' + phase + '_HD_original_roundtrip', restored.png === sample.png && original.png !== sample.png);
        check('phase_' + phase + '_emulated_state_unchanged', await p.evaluate(() => moonDebug.Kjerne.sjekksum()) === state);
        report.phases.push({ phase, journey, scene: sample.scene, control: sample.control, evidence });
        fs.writeFileSync(out + '/progress.json', JSON.stringify(report, null, 2));
        console.log(JSON.stringify({ phase, frame: journey.frame, checks: report.checks.length }));
    }
    // Avgrenset kampfixtur: tre dokumenterte originalpekere velger Ratmen og
    // Wa2-terreng i Practice. Deretter kjoerer original CPU/animasjon uendret.
    const combat = await p.evaluate(async () => {
        const { Kjerne: K, Visning: V, SceneHd: S, StandardHd: H } = moonDebug;
        const M = await K.last(); K.start(false); K.menyPaa(false); K.lagPaa(true); V.nullstillScene(); S.nullstill();
        const samples = [], raw = new Set(), scenes = new Set(); let checked = 0;
        while (K.bildeNr() < 1801) {
            const n = K.bildeNr();
            if (n === 100) K.tast(0x45, true); if (n === 104) K.tast(0x45, false);
            K.inndata(0, ((n >= 700 && n < 704) || (n >= 760 && n < 764) ? 2 : 0) | (n >= 820 && n < 824 ? 16 : 0) | (n >= 1200 && n < 1320 ? 4 : 0));
            if (n === 900) {
                const d = new DataView(M.HEAPU8.buffer), chip = M._ms_chip();
                for (const [a, v] of [[0x80172, 0x8440a], [0x8d9ac, 0x8d5b4], [0x8015c, 0xc]]) d.setUint32(chip + a, v, false);
            }
            K.bilde(); V.nyttBilde(K.tegneliste());
            if (n >= 1100 || n % 20 === 0) {
                const lag = S.korriger(K.rammebuffer(), K.vindu(), K.lag()); V.tegn(K.rammebuffer(), K.vindu(), lag); H.oppdater(lag?.hash);
                if (n === 1199) {
                    for (let q = 0; q < 200; q++) {
                        const l = S.korriger(K.rammebuffer(), K.vindu(), K.lag()); V.tegn(K.rammebuffer(), K.vindu(), l); H.oppdater(l?.hash);
                        if (V.hdKontroll().bakgrunn === 'hd') break; await new Promise(r => setTimeout(r, 10));
                    }
                }
                if (n >= 1200) {
                    checked++; raw.add((K.lag().hash >>> 0).toString(16)); scenes.add(S.info()?.id || 'clean');
                    if (!V.hdPaa() || V.hdKontroll().bakgrunn !== 'hd') samples.push({ n, scene: S.info(), control: V.hdKontroll(), hd: H.info() });
                }
            }
            if (n % 20 === 0) await new Promise(r => setTimeout(r, 0));
        }
        return { scope: 'Original CPU Practice, fixture sets Ratmen/terrain with three pointers at frame900; no natural travel claim', checked, failures: samples.slice(0, 10), raw: [...raw], scenes: [...scenes], stopped: K.stoppet(), lastVisible: V.hdFigurer(true) };
    });
    report.combat = combat;
    check('Ratmen_original_CPU_601_frames_keep_HD_enabled_and_background', combat.checked === 601 && !combat.failures.length && !combat.stopped);
    check('Ratmen_original_background_baking_exercised', combat.raw.length > 1 && combat.scenes.includes('combat-delta'));
    const combatImage = await draw(p);
    fs.writeFileSync(out + '/ratmen-hd.png', Buffer.from(combatImage.png.split(',')[1], 'base64'));
    check('no_browser_errors', report.errors.length === 0);
    report.status = 'passed';
})().catch(e => { report.status = 'failed'; report.failure = String(e); console.error(e); process.exitCode = 1; }).finally(async () => {
    releaseBase?.();
    report.created_at = new Date().toISOString();
    fs.writeFileSync(out + '/report.json', JSON.stringify(report, null, 2) + '\n');
    console.log(JSON.stringify({ status: report.status, checks: report.checks.length, failure: report.failure }));
    if (browser) await browser.close(); if (server) await server.close();
});
