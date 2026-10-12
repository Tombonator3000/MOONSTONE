/* Vanlig aktiv Math-pakke gjennom den samme fryste HTTP-verten som TAV. */
'use strict';
const fs = require('fs'), path = require('path'), http = require('http');
const {spawn} = require('child_process');
const art = __dirname, root = path.resolve(art, '../..');
const snapshot = JSON.parse(fs.readFileSync(art + '/verification/runtime-v9-package/snapshot.json')).snapshot;
const server = http.createServer((req, res) => {
    const rel = decodeURIComponent(new URL(req.url, 'http://local').pathname).slice(1);
    const file = path.resolve(snapshot, rel);
    if (!file.startsWith(snapshot + path.sep) || !fs.existsSync(file)) {
        res.writeHead(404); res.end(); return;
    }
    res.setHeader('Content-Type', file.endsWith('.html') ? 'text/html' : file.endsWith('.json') ? 'application/json' : 'image/png');
    fs.createReadStream(file).pipe(res);
});
(async () => {
    await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
    const env = {...process.env, MOONSTONE_URL: 'http://127.0.0.1:' + server.address().port + '/moonstone.html',
        MOONSTONE_HD_TEST_OUTPUT: 'art/hd-math-figures-2026-10-11/verification/standard-v9'};
    delete env.MOONSTONE_MATH_CANDIDATE;
    delete env.MOONSTONE_MATH_STATIC;
    delete env.MOONSTONE_MATH_COLOR;
    const child = spawn(process.execPath, [root + '/tools/hd_math_figurer_sjekk.cjs'], {cwd: root, env, stdio: 'inherit'});
    process.exitCode = await new Promise(resolve => child.on('exit', code => resolve(code ?? 1)));
})().catch(e => {console.error(e); process.exitCode = 1;}).finally(() => server.close());
