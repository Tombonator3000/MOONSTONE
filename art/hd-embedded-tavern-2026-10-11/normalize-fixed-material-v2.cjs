/* Kildebundne faste materialer faar ingen blaafarge fra den levende kappen. */
'use strict';
const fs = require('fs'), path = require('path'), crypto = require('crypto'), assert = require('assert/strict');
const {chromium} = require('playwright');
const art = __dirname, sha = b => crypto.createHash('sha256').update(b).digest('hex');
(async () => {
    const pngPath = art + '/packed/embedded/tav-player.png';
    const input = fs.readFileSync(art + '/verification/frozen-player-before-fixed/tav-player.png'), indices = fs.readFileSync(art + '/source/player-indices.bin');
    const saved = art + '/verification/frozen-player-before-fixed';
    fs.mkdirSync(saved, {recursive: true});
    if (!fs.existsSync(saved + '/tav-player.png')) {
        fs.writeFileSync(saved + '/tav-player.png', input);
        fs.copyFileSync(art + '/packed/embedded/tav-player.json', saved + '/tav-player.json');
    }
    assert.equal(sha(input), sha(fs.readFileSync(saved + '/tav-player.png')), 'Normaliseringen bruker bare den frosne fotokandidaten');
    const browser = await chromium.launch({headless: true, executablePath: '/usr/bin/google-chrome', args: ['--no-sandbox']});
    let result;
    try {
        const page = await browser.newPage();
        result = await page.evaluate(async ({photo, indices}) => {
            const image = new Image(); image.src = 'data:image/png;base64,' + photo; await image.decode();
            const canvas = document.createElement('canvas'); canvas.width = image.width; canvas.height = image.height;
            const ctx = canvas.getContext('2d'); ctx.drawImage(image, 0, 0);
            const data = ctx.getImageData(0, 0, canvas.width, canvas.height), pixels = data.data;
            const counts = {}; let liveChanged = 0, alphaChanged = 0;
            for (let y = 0; y < canvas.height; y++) for (let x = 0; x < canvas.width; x++) {
                const q = (y * canvas.width + x) * 4, c = indices[(y >> 2) * 135 + (x >> 2)];
                const r = pixels[q], g = pixels[q + 1], b = pixels[q + 2], a = pixels[q + 3];
                if (!a || c >= 6 && c <= 10) continue;
                const luma = r * .299 + g * .587 + b * .114;
                const blue = b > r * 1.35 + 1 && b > g * 1.1 + 1;
                let rgb = null;
                if (c === 11) rgb = [Math.min(63, Math.round(luma)), 0, 0];
                else if (c === 0 && blue) {const shadow = Math.min(30, Math.round(luma * .75)); rgb = [shadow, shadow, shadow];}
                else if (blue && [1, 3, 4, 5, 17].includes(c)) rgb = [Math.round(luma * .98), Math.round(luma), Math.round(luma * 1.05)];
                else if (blue && [12, 13, 27, 28].includes(c)) rgb = [Math.round(luma), Math.round(luma * .9), Math.round(luma * .7)];
                else if (blue) {const edge = Math.min(50, Math.round(luma * .45)); rgb = [edge, edge, edge];}
                if (!rgb) continue;
                pixels[q] = rgb[0]; pixels[q + 1] = rgb[1]; pixels[q + 2] = rgb[2];
                if (r !== pixels[q] || g !== pixels[q + 1] || b !== pixels[q + 2]) counts[c] = (counts[c] || 0) + 1;
                if (c >= 6 && c <= 10 && (r !== pixels[q] || g !== pixels[q + 1] || b !== pixels[q + 2])) liveChanged++;
                if (pixels[q + 3] !== a) alphaChanged++;
            }
            ctx.putImageData(data, 0, 0);
            return {image: canvas.toDataURL('image/png').split(',')[1], counts, liveChanged, alphaChanged};
        }, {photo: input.toString('base64'), indices: Array.from(indices)});
    } finally {await browser.close();}
    assert.equal(result.liveChanged, 0); assert.equal(result.alphaChanged, 0);
    const output = Buffer.from(result.image, 'base64'); fs.writeFileSync(art + '/packed/embedded/tav-player-fixed-v2.png', output);
    const record = {schema: 1, method: 'source_fixed_material_normalization', input: path.relative(art, saved + '/tav-player.png'),
        input_sha256: sha(input), output: 'packed/embedded/tav-player-fixed-v2.png', output_sha256: sha(output),
        source_indices_sha256: sha(indices), changes_by_source_index: result.counts,
        live_RGB_changed: 0, source_alpha_changed: 0,
        scope: 'Original11 er fast moerkeroedt kappeskyggemateriale. Bare feilblaatt original0-materiale nøytraliseres, mens fotografiske varme staal-/kullskygger beholdes. Feilblaatt fotomateriale paa staal/skum og antialias-kant nøytraliseres etter originalens materialklasse. Fotografisk tekstur og luminans brukes; original6..10-RGB, masken, geometrien og alfa bevares byteidentisk. Ingen ny figur eller egen nytegning paastaas.'};
    fs.writeFileSync(art + '/material/fixed-material-v2.json', JSON.stringify(record, null, 2) + '\n');
    console.log(JSON.stringify(record));
})().catch(e => {console.error(e); process.exitCode = 1;});
