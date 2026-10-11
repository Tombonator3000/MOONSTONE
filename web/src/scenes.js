/* PIV-bakgrunner gjenkjennes fra faktisk viste indekser, aldri fra filprelasting.
 * Flyttede markorer, sprites og alle avvik beholdes fra originalrammen. */
const SceneHd = (() => {
    'use strict';
    const kilder = new Map();
    const bak = new Uint8Array(64000 * 4), foran = new Uint8Array(64000 * 4);
    const indeks = new Uint8Array(64000), maske = new Uint8Array(64000);
    const avvik = new Uint8Array(64000);
    const summer = new Uint32Array(321 * 201);
    let sist = null, epoch = 0, sisteMatcher = [];
    function nullstill() { kilder.clear(); sist = null; epoch++; }
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
        kilder.set(row.id, { ...row, ...source, vanligst });
    }
    function korriger(fb, diw, lag) {
        sist = null;
        if (!Visning.hdPaa() || !StandardHd.info().aktiv || !StandardHd.info().klar ||
            diw[2] - diw[0] !== 640 || diw[3] - diw[1] !== 200 || diw[0] < 0 || diw[1] < 0) return lag;
        const scan = Kjerne.skanout();
        if (!scan.gyldig) return lag;
        const rows = StandardHd.scener();
        for (const row of rows) klargjor(row).catch(() => {});
        let valgt = null, best = 0; sisteMatcher = [];
        for (const s of kilder.values()) {
            if (!s) continue;
            let match = 0, n = 0, detalj = 0, detaljMatch = 0;
            for (let y = 2; y < 200; y += 4) for (let x = 2; x < 320; x += 4) {
                const actual = lag?.bakIdx ? lag.bakIdx[y * 320 + x] : scan.idx[(diw[1] + y) * 720 + diw[0] + x * 2];
                if (actual === s.px[y * 320 + x]) match++;
                if (s.px[y * 320 + x] !== s.vanligst) { detalj++; if (actual === s.px[y * 320 + x]) detaljMatch++; }
                n++;
            }
            const ratio = match / n;
            sisteMatcher.push({id:s.id, match:ratio, detail:detaljMatch/detalj});
            // En nesten svart skjerm maa ikke forveksles med en svart PIV.
            if (detalj > 40 && detaljMatch / detalj >= (s.minimum_detail || s.minimum_match || 0.98) &&
                ratio > best && ratio >= (s.minimum_match || 0.98)) { best = ratio; valgt = s; }
        }
        if (!valgt) return lag;
        const rect = valgt.rect || [0, 0, 320, 200];
        // Originalmarkorene beholdes til bakgrunnen og HD-overlegg kan vises sammen.
        const ikoner = (StandardHd.info().bakgrunner.includes(valgt.hash)
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
            if (y === 100) lys += scan.pal[pal] + scan.pal[pal + 1] + scan.pal[pal + 2];
            const actual = scan.idx[fp];
            const protectedPixel = x < rect[0] || y < rect[1] || x >= rect[2] || y >= rect[3] ||
                (valgt.protected || []).some(r => x >= r[0] && y >= r[1] && x < r[2] && y < r[3]);
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
                const p=(y+j)*320+x+i;maske[p]=0;avvik[p]=0;
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
            hash: parseInt(valgt.hash, 16), lys, hdRect: rect, scene: valgt.id,
            overlays: [...(valgt.overlays || []),...ikoner.map(m=>({key:m.key,rect:m.rect,uv_rect:[0,0,1,1],foreground:true}))], sceneVern: avvik };
    }
    return { korriger, nullstill, info: () => sist, matcher: () => sisteMatcher.slice() };
})();
