/* PIV-bakgrunner gjenkjennes fra faktisk viste indekser, aldri fra filprelasting.
 * Flyttede markorer, sprites og alle avvik beholdes fra originalrammen. */
const SceneHd = (() => {
    'use strict';
    const kilder = new Map();
    const bak = new Uint8Array(64000 * 4), foran = new Uint8Array(64000 * 4);
    const indeks = new Uint8Array(64000), maske = new Uint8Array(64000);
    const avvik = new Uint8Array(64000);
    const summer = new Uint32Array(321 * 201);
    let sist = null, epoch = 0, sisteMatcher = [], rull = null, rullVenter = false, rullSist = 0, kildeRevisjon = -1;
    const RULL_HASH = { intro: '6b258d27', ending: '0df34a83' }; // FNV1a av komposittens320x1200 indekser
    const RULL_KILDER = [
        ['program', 'b0a84503c0664515ef8b31072098acd62dbf50de3a36fe4ffe9492b094f593a6'],
        ['intro.stile', 'd98c0d0807f0a18eeb3c1ab519a76e4251fe82ffef28388b640c90b01614d7cc'],
        ['bg1a.PIV', '908c0333ed5ce11d345c14b62599df4674aa3039edc2e4c2eb624070ddd1ea66'],
        ['bg1c.PIV', '9046c965c730c323ea6b6d4b8d8da82b9d20c3b69f5d2f629d8aca224d09eede'],
        ['bg1b.PIV', '8c4418f7089f5fb5e60e1e166b8f253b1781b4971eaeee3198c0b60b04d555ac'],
        ['bg7.piv', '6f01ac4c36c9b33f9f11b812a717c0786c1f4afa663962f854ee73d26853fa52'],
        ['co.stile', '2401d7f897be714e5ffeac1d3a5ff5a60838e0ce690755e9f940a0888a2151f1']
    ];
    function nullstill() { kilder.clear(); sist = null; rull = null; rullVenter = false; rullSist = 0; epoch++; }
    async function klargjorRull() {
        if (rull || rullVenter) return;
        const data = RULL_KILDER.map(([fil]) => Kjerne.hentFil('data/' + fil));
        if (data.some(d => !d)) return;
        rullVenter = true;
        const egenEpoch = epoch;
        const hashes = await Promise.all(data.map(async d => [...new Uint8Array(await crypto.subtle.digest('SHA-256', d))]
            .map(v => v.toString(16).padStart(2, '0')).join('')));
        if (egenEpoch !== epoch) return;
        if (hashes.some((h, i) => h !== RULL_KILDER[i][1]) || data[1].length !== 960 || data[6].length !== 960) return;
        function bygg(tab, banker) {
            const px = new Uint8Array(320 * 1200);
            for (let n = 0; n < 480; n++) {
                const code = tab[n*2] * 256 + tab[n*2+1], b = Math.floor(code / 80), tile = code % 80;
                if (b >= banker.length) throw new Error('Ukjent flisbank');
                const sx = tile % 10 * 32, sy = Math.floor(tile / 10) * 25;
                const dx = n % 10 * 32, dy = Math.floor(n / 10) * 25;
                for (let y = 0; y < 25; y++) px.set(banker[b].px.subarray((sy+y)*320+sx, (sy+y)*320+sx+32), (dy+y)*320+dx);
            }
            return { px, pal: banker[0].pal };
        }
        const intro = bygg(data[1], data.slice(2,5).map(d => Spillgrafikk._piv(d)));
        // $08577a toemmer bank0, $085792 laster bg7.piv i den. co.stile
        // ruller stjernehimmel/vannvirvel, ikke bokstaver eller bg1a-fliser.
        const ending = bygg(data[6], [Spillgrafikk._piv(data[5])]);
        const bank0Px = Spillgrafikk._piv(data[5]).px;
        ending.bank0 = new Uint8Array(40000);
        for (let p=0; p<64000; p++) for (let b=0; b<5; b++) if (bank0Px[p] & (1<<b))
            ending.bank0[b*8000+Math.floor(p/8)] |= 0x80 >> (p%8);
        const digests = await Promise.all([intro, ending].map(async s => [...new Uint8Array(await crypto.subtle.digest('SHA-256', s.px))]
            .map(v => v.toString(16).padStart(2, '0')).join('')));
        if (egenEpoch !== epoch || digests[0] !== 'f6a55595b3492690984e8c1d470f88a6e4017867e8368f033b496a92ef00709d' ||
            digests[1] !== '0c1e689ad4290f6eded1e0ac7be25442dcd8c520502a63a1cc45d3cdc68e34b1') return;
        rull = { intro, ending };
    }
    function korrigerRull(fb, diw, lag, scan, standard) {
        const mode = Kjerne.iSlutt() ? 'ending' : Kjerne.iIntro() ? 'intro' : null, hash = RULL_HASH[mode];
        if (!mode || (!(standard.aktiv && standard.klar) && !Visning.harHdBilde('bg/' + hash))) return null;
        klargjorRull().catch(() => {});
        const hint = Kjerne.programRull();
        if (!rull || !hint) return null;
        const kilde = rull[mode];
        // Sluttfigurene dekker deler av stjernene. Lavere skjermterskel krever
        // i tillegg at HELE den faktiske bg7-flisbanken er byteidentisk.
        if (mode === 'ending' && (!hint.bank0 || !hint.bank0.every((v,i) => v === kilde.bank0[i]))) return null;
        // Hintet er foran skanout paa grunn av dobbelbuffer og blitteren. Kontroller
        // baade forrige utsnitt og et smalt soekefelt; aldri strekk raaflisbankene.
        const offsets = new Set([rullSist]);
        for (let y = Math.max(0, hint.y-32); y <= Math.min(1000, hint.y+(mode==='ending'?32:2)); y++) offsets.add(y);
        let valgt = -1, best = 0;
        for (const offset of offsets) {
            let n = 0, match = 0, detail = 0, detailMatch = 0;
            const vanligst = kilde.px[offset * 320];
            for (let y = 2; y < 200; y += 4) for (let x = 2; x < 320; x += 4) {
                const c = kilde.px[(offset+y)*320+x];
                // Rullekopien kan allerede inneholde neste utsnitt. Bare faktisk
                // skanout bestemmer hva spilleren ser i dette bildet.
                const actual = scan.idx[(diw[1]+y)*720+diw[0]+x*2];
                if (actual === c) match++;
                if (c !== vanligst) { detail++; if (actual === c) detailMatch++; }
                n++;
            }
            if (detail > 40 && detailMatch/detail >= (mode==='ending'?0.85:0.98) &&
                match/n >= (mode==='ending'?0.90:0.98) && match/n > best) { valgt = offset; best = match/n; }
        }
        if (valgt < 0) return null;
        rullSist = valgt;
        foran.fill(0); indeks.fill(255); avvik.fill(0);
        let lys = 0, lysMaks = 0, beholdt = 0;
        const px = kilde.px.subarray(valgt*320, (valgt+200)*320);
        for (let y=0; y<200; y++) for (let x=0; x<320; x++) {
            const p=y*320+x, fp=(diw[1]+y)*720+diw[0]+x*2, c=px[p], pal=((diw[1]+y)*32+c)*4;
            for (let k=0; k<4; k++) bak[p*4+k]=scan.pal[pal+k];
            lys+=scan.pal[pal]+scan.pal[pal+1]+scan.pal[pal+2];
            lysMaks+=kilde.pal[c][0]+kilde.pal[c][1]+kilde.pal[c][2];
            if (scan.idx[fp]!==c || fb[fp*4]!==bak[p*4] || fb[fp*4+1]!==bak[p*4+1] ||
                fb[fp*4+2]!==bak[p*4+2] || fb[fp*4+3]!==bak[p*4+3]) {
                for (let k=0; k<4; k++) foran[p*4+k]=fb[fp*4+k];
                indeks[p]=scan.idx[fp]; avvik[p]=1; beholdt++;
            }
        }
        sist={id:mode+'-scroll',hash,match:best,offset:valgt,hint:hint.y,preserved_pixels:beholdt,hd_icons:0};
        return {bak,for:foran,forIdx:indeks,bakIdx:px,hash:parseInt(hash,16),lys,lysMaks,
            hdRect:[0,0,320,200],hdUv:[0,valgt/1200,1,200/1200],sourceSize:[320,1200],scene:mode+'-scroll',sceneVern:avvik};
    }
    async function klargjor(row) {
        if (kilder.has(row.id)) return;
        const data = Kjerne.hentFil('data/' + row.file);
        if (!data) return;
        const egenEpoch = epoch;
        kilder.set(row.id, null);
        const digest = [...new Uint8Array(await crypto.subtle.digest('SHA-256', data))]
            .map(v => v.toString(16).padStart(2, '0')).join('');
        if (egenEpoch !== epoch || digest !== row.source_sha256) return;
        let pos = 0;
        for (let n = 0; n < row.frame; n++) {
            const planes = data[pos] * 256 + data[pos + 1];
            const size = ((data[pos + 2] << 24) | (data[pos + 3] << 16) | (data[pos + 4] << 8) | data[pos + 5]) >>> 0;
            pos += 6 + (1 << planes) * 2 + size;
        }
        const source = Spillgrafikk._piv(data.subarray(pos));
        const hist = new Uint32Array(32);
        for (const c of source.px) hist[c]++;
        const vanligst = hist.indexOf(Math.max(...hist));
        const lysMaks = source.pal.reduce((sum, rgb, c) =>
            sum + hist[c] * (rgb[0] + rgb[1] + rgb[2]), 0);
        kilder.set(row.id, { ...row, ...source, vanligst, lysMaks });
    }
    function korriger(fb, diw, lag) {
        // Egne/nettverts-filer kan skiftes uten omstart. Ingen kildecache skal
        // overleve en ny filrevisjon, heller ikke en ferdigdekodet flisrulle.
        const revisjon = Kjerne.filRevisjon();
        if (revisjon !== kildeRevisjon) { nullstill(); kildeRevisjon = revisjon; }
        sist = null;
        // Scenedefinisjonene foelger utgivelsen og kildefilen valideres med SHA256.
        // Egne PNG-er kan bruke samme scener etter at standardlastingen er stoppet.
        // Original bruker samme identitet ved bytte saa engangstegnet tekst bevares.
        const standard = StandardHd.info();
        if ((!(standard.aktiv && standard.klar) && !Visning.hdAntall()) ||
            diw[2] - diw[0] !== 640 || diw[3] - diw[1] !== 200 || diw[0] < 0 || diw[1] < 0) return lag;
        const scan = Kjerne.skanout();
        if (!scan.gyldig) return lag;
        const rullet = korrigerRull(fb, diw, lag, scan, standard);
        if (rullet) return rullet;
        const rows = StandardHd.scener();
        for (const row of rows) klargjor(row).catch(() => {});
        let valgt = null, best = 0, bestSkjerm = false; sisteMatcher = [];
        for (const s of kilder.values()) {
            if (!s) continue;
            // compare "screen": bildet ligger bare paa skjermen, ikke i bakgrunnskopien
            // (lasteskjermen viser ch.piv over en annen kopi, banneret i Prepare yourself
            // er message.piv). Er kopien selv bildet, gjelder den vanlige bakgrunnen.
            const skjerm = s.compare === 'screen';
            if (skjerm && lag && (lag.hash >>> 0) === parseInt(s.hash, 16)) continue;
            let match = 0, n = 0, detalj = 0, detaljMatch = 0;
            for (let y = 2; y < 200; y += 4) for (let x = 2; x < 320; x += 4) {
                if ((s.match_ignore_indices || []).includes(s.px[y * 320 + x])) continue;
                const actual = lag?.bakIdx && !skjerm ? lag.bakIdx[y * 320 + x] : scan.idx[(diw[1] + y) * 720 + diw[0] + x * 2];
                if (actual === s.px[y * 320 + x]) match++;
                if (s.px[y * 320 + x] !== s.vanligst) { detalj++; if (actual === s.px[y * 320 + x]) detaljMatch++; }
                n++;
            }
            const ratio = match / n;
            sisteMatcher.push({id:s.id, match:ratio, detail:detaljMatch/detalj});
            // En nesten svart skjerm maa ikke forveksles med en svart PIV.
            // En scene som stemmer med skjermen, gaar foran en som bare stemmer med
            // bakgrunnskopien (lasteskjermen over portalen fra introen).
            if (detalj > 40 && detaljMatch / detalj >= (s.minimum_detail || s.minimum_match || 0.98) &&
                ratio >= (s.minimum_match || 0.98) && (skjerm && !bestSkjerm || skjerm === bestSkjerm && ratio > best)) {
                best = ratio; valgt = s; bestSkjerm = skjerm;
            }
        }
        if (!valgt) return lag;
        const rect = valgt.rect || [0, 0, 320, 200];
        const faste = Visning.hdPaa() ? (valgt.overlays || []).filter(o=>Visning.sceneOverleggKlar(o.key,diw)) : [];
        const originaleFelt = (valgt.overlays || []).filter(o=>!faste.includes(o));
        const vernedeFelt = [...(valgt.protected || []),...originaleFelt.map(o=>o.rect)];
        // Originalmarkorene beholdes til bakgrunnen og HD-overlegg kan vises sammen.
        const ikoner = (Visning.hdPaa() && Visning.harHdBilde('bg/' + valgt.hash)
            ? Visning.sceneIkoner(valgt.id) : []).filter(m=>{
            if (m.source.bank_sha256!==valgt.source_sha256 || !m.expected || m.expected.length!==m.width*m.height || !Visning.sceneIkonKlar(m,diw)) return false;
            const [x,y]=m.rect;
            for (let j=0;j<m.height;j++) for (let i=0;i<m.width;i++) {
                if (scan.idx[(diw[1]+y+j)*720+diw[0]+(x+i)*2]!==m.expected[j*m.width+i]) return false;
            }
            return true;
        });
        foran.fill(0); indeks.fill(255); maske.fill(0); avvik.fill(0);
        let lys = 0;
        for (let y = 0; y < 200; y++) for (let x = 0; x < 320; x++) {
            const p = y * 320 + x, fp = (diw[1] + y) * 720 + diw[0] + x * 2, c = valgt.px[p];
            const pal = (diw[1] + y) * 32 * 4 + c * 4;
            for (let k=0;k<4;k++) bak[p*4+k]=scan.pal[pal+k];
            lys += scan.pal[pal] + scan.pal[pal + 1] + scan.pal[pal + 2];
            const actual = scan.idx[fp];
            const protectedPixel = x < rect[0] || y < rect[1] || x >= rect[2] || y >= rect[3] ||
                (valgt.protected_indices || []).includes(c) ||
                vernedeFelt.some(r => x >= r[0] && y >= r[1] && x < r[2] && y < r[3]) ||
                (valgt.preserve_regions || []).some(({rect:r,indices}) =>
                    x >= r[0] && y >= r[1] && x < r[2] && y < r[3] && indices.includes(c));
            if (actual !== c || fb[fp*4]!==bak[p*4] || fb[fp*4+1]!==bak[p*4+1] ||
                fb[fp*4+2]!==bak[p*4+2] || fb[fp*4+3]!==bak[p*4+3]) avvik[p] = 1;
            if (protectedPixel || avvik[p]) maske[p] = 1;
        }
        if (valgt.foreground_padding) {
            summer.fill(0);
            for (let y=0;y<200;y++) {
                let sum=0;
                for (let x=0;x<320;x++) { sum+=maske[y*320+x]; summer[(y+1)*321+x+1]=summer[y*321+x+1]+sum; }
            }
        }
        // Bare et helt, eksakt markoermoenster faar ny kontur. En markoer
        // under en ridder eller en ny status beholder hele originalbildet.
        for (const m of ikoner) {
            const [x,y]=m.rect;
            for (let j=0;j<m.height;j++) for (let i=0;i<m.width;i++) {
                const p=(y+j)*320+x+i, bevar=(m.preserve_indices||[]).includes(m.expected[j*m.width+i]);
                // Pulserende valgkanter beholder originalpalett og pikselvern.
                // Hele kildefeltet er allerede kontrollert eksakt over.
                maske[p]=bevar?1:0;avvik[p]=bevar?1:0;
            }
        }
        // En liten sikkerhetskant bevarer svarte hull og kanter i forgrunnsfigurer.
        let beholdt = 0;
        for (let y = 0; y < 200; y++) for (let x = 0; x < 320; x++) {
            const p = y * 320 + x;
            let vern = maske[p];
            if (!vern && valgt.foreground_padding) {
                const d = valgt.foreground_padding;
                const x0=Math.max(0,x-d), y0=Math.max(0,y-d), x1=Math.min(320,x+d+1), y1=Math.min(200,y+d+1);
                vern=summer[y1*321+x1]-summer[y0*321+x1]-summer[y1*321+x0]+summer[y0*321+x0];
            }
            if (!vern) continue;
            const fp = (diw[1] + y) * 720 + diw[0] + x * 2;
            for (let k=0;k<4;k++) foran[p*4+k]=fb[fp*4+k];
            indeks[p] = scan.idx[fp] & 31;
            beholdt++;
        }
        sist = { id: valgt.id, match: best, preserved_pixels: beholdt, hash: valgt.hash, hd_icons: ikoner.length };
        return { bak, for: foran, forIdx: indeks, bakIdx: valgt.px,
            hash: parseInt(valgt.hash, 16), lys, lysMaks: valgt.lysMaks,
            hdRect: valgt.uv_rect || rect, scene: valgt.id,
            overlays: [...faste,...ikoner.map(m=>({key:m.key,rect:m.draw_rect||m.rect,uv_rect:[0,0,1,1],foreground:true}))], sceneVern: avvik };
    }
    return { korriger, nullstill, info: () => sist, matcher: () => sisteMatcher.slice() };
})();
