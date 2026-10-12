/* Produksjonslastingen med nett-/importfixturer, ikke et visuelt runtimebevis. */
'use strict';
const fs = require('fs'), path = require('path'), vm = require('vm'), crypto = require('crypto'), assert = require('assert/strict');
const { File } = require('buffer');
const root = path.resolve(__dirname, '..'), code = fs.readFileSync(root + '/web/src/hd.js', 'utf8');
const out = process.env.MOONSTONE_VERIFY_OUT || '/tmp/moonstone-hd-lasting';
const report = { checks: [], cases: [] }, check = (n, v) => { assert(v, n); report.checks.push(n); };
const bytes = { 'bold.f/000.png': Buffer.from([1, 2, 3]), 'poses.json': Buffer.from('{"poses":[]}'), 'bg/1234abcd.png': Buffer.from([4, 5, 6]), 'bg/89abcdef.png': Buffer.from([7, 8, 9]) };
const manifest = { images: 3, background_cache_limit: 4, scenes: [], files: Object.entries(bytes).map(([path, b]) => ({ path, bytes: b.length, sha256: crypto.createHash('sha256').update(b).digest('hex'), kind: path.startsWith('bg/') ? 'background' : 'base' })) };
async function settle(test, ready) { for (let i = 0; i < 500; i++) { if (ready()) return; await new Promise(r => setTimeout(r, 10)); } throw Error('Lastingen avsluttet ikke ' + test); }
function setup(mode) {
    const requests = {}, imported = [], images = new Set(); let imports = 0, maximumImports = 0;
    const V = { hdPaa: () => true, settTvungetLag: () => {}, lagNaa: () => ({ hash: 0x1234abcd }),
        hdAntall: () => images.size, hdPoseInfo: () => ({ antall: 0, ugyldig: false, feil: [] }), fjernHdBilde: key => images.delete(key),
        lastHdPakke: async files => {
            maximumImports = Math.max(maximumImports, ++imports);
            await new Promise(r => setTimeout(r, mode === 'base-corrupt' ? 50 : 5));
            imported.push(files.map(f => f.webkitRelativePath));
            let n = 0; for (const f of files) if (f.name.endsWith('.png')) { images.add(f.webkitRelativePath); n++; }
            imports--; return n;
        } };
    const context = { Promise, Map, Set, Error, TypeError, Uint8Array, AbortController, DOMException, File, setTimeout, clearTimeout,
        crypto: crypto.webcrypto, location: { protocol: 'http:' },
        fetch: async (url, { signal }) => {
            const path = url.slice(3).split('?')[0], count = requests[path] = (requests[path] || 0) + 1;
            if (signal.aborted) throw new DOMException('Avbrutt', 'AbortError');
            if (mode === 'temporary' && count === 1 && path.endsWith('.png')) return new Response('', { status: 503 });
            if (mode === 'base-corrupt' && path === 'bold.f/000.png') { await new Promise(r => setTimeout(r, 10)); return new Response(Buffer.from([1, 2, 4])); }
            if (mode === 'base-missing' && path === 'bold.f/000.png') return new Response('', { status: 404 });
            if (mode === 'background-corrupt' && path.startsWith('bg/')) return new Response(Buffer.from([4, 5, 7]));
            if (mode === 'stop-retry' && path === 'bold.f/000.png') return new Response('', { status: 503 });
            return new Response(bytes[path]);
        } };
    vm.createContext(context);
    const H = vm.runInContext(code.replace('%%HD_MANIFEST%%', JSON.stringify(manifest)) + '\nStandardHd;', context);
    return { H, V, requests, imported, concurrent: () => maximumImports };
}
(async () => {
    const t = setup('temporary'); t.H.start(t.V);
    await settle('temporary', () => t.H.info().klar && t.H.info().laster === 0);
    check('base_transient_503_retried_exactly_once', t.requests['bold.f/000.png'] === 2);
    check('background_transient_503_retried_exactly_once', t.requests['bg/1234abcd.png'] === 2);
    check('base_and_background_recover_without_error', !t.H.info().feil && t.H.info().bakgrunner.includes('1234abcd'));
    check('background_and_base_imports_are_serial', t.concurrent() === 1);
    check('priority_font_import_precedes_remaining_metadata', t.imported.findIndex(a => a.includes('standard/bold.f/000.png')) < t.imported.findIndex(a => a.includes('standard/poses.json')));
    report.cases.push({ mode: 'temporary', requests: t.requests, imported: t.imported, info: t.H.info() }); await t.H.stopp();
    const b = setup('base-corrupt'); b.H.start(b.V);
    await settle('base-corrupt', () => b.H.info().laster === 0);
    check('corrupt_base_SHA_is_not_retried', b.requests['bold.f/000.png'] === 1);
    check('background_success_cannot_hide_fatal_base_SHA_error', b.H.info().feil === 'Feil bilderevisjon' && !b.H.info().klar);
    b.H.oppdater(0x89abcdef);
    await settle('new-background-after-base-corrupt', () => b.H.info().bakgrunner.includes('89abcdef') && b.H.info().laster === 0);
    check('new_background_loads_after_fatal_base_SHA_error', b.requests['bg/89abcdef.png'] === 1 && b.imported.some(a => a.includes('standard/bg/89abcdef.png')));
    check('new_background_preserves_base_SHA_error', b.H.info().feil === 'Feil bilderevisjon' && !b.H.info().klar);
    report.cases.push({ mode: 'base-corrupt', requests: b.requests, info: b.H.info() }); await b.H.stopp();
    const m = setup('base-missing'); m.H.start(m.V);
    await settle('base-missing', () => m.H.info().laster === 0);
    m.H.oppdater(0x89abcdef);
    await settle('new-background-after-base-missing', () => m.H.info().bakgrunner.includes('89abcdef') && m.H.info().laster === 0);
    check('base_404_is_not_retried', m.requests['bold.f/000.png'] === 1);
    check('new_background_loads_after_fatal_base_404', m.requests['bg/89abcdef.png'] === 1 && m.imported.some(a => a.includes('standard/bg/89abcdef.png')));
    check('new_background_preserves_base_404_error', m.H.info().feil === 'HTTP 404' && !m.H.info().klar);
    report.cases.push({ mode: 'base-missing', requests: m.requests, info: m.H.info() }); await m.H.stopp();
    const c = setup('background-corrupt'); c.H.start(c.V);
    await settle('background-corrupt', () => c.H.info().klar && c.H.info().laster === 0);
    check('corrupt_background_SHA_is_not_retried', c.requests['bg/1234abcd.png'] === 1);
    check('corrupt_background_does_not_abort_valid_base', c.H.info().klar && c.H.info().feil === 'Feil bilderevisjon');
    check('corrupt_background_never_imported', c.imported.every(a => !a.includes('standard/bg/1234abcd.png')));
    report.cases.push({ mode: 'background-corrupt', requests: c.requests, info: c.H.info() }); await c.H.stopp();
    const d = setup('stop-retry'); d.H.start(d.V); await new Promise(r => setTimeout(r, 30)); await d.H.stopp();
    check('stop_aborts_pending_base_retry', !d.H.info().aktiv && d.H.info().laster === 0 && d.requests['bold.f/000.png'] === 1);
    report.status = 'passed';
})().catch(e => { report.status = 'failed'; report.failure = String(e); console.error(e); process.exitCode = 1; }).finally(() => {
    fs.mkdirSync(out, { recursive: true }); fs.writeFileSync(out + '/report.json', JSON.stringify(report, null, 2) + '\n');
    console.log(JSON.stringify({ status: report.status, checks: report.checks.length, failure: report.failure }));
});
