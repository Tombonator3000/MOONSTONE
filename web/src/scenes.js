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
    // Bare komplette, kildeverifiserte kampbakgrunner kan forankre denne broen.
    // FNV velger en kontrakt; SHA256 kontrollerer samtlige64000 kildeindekser.
    const KAMP_KILDER = new Map([["bae52e65","5b798d4228e048276d6b52782eff393a471c41bac99e94ea0f7cc43728e7acc0","GL1.t","ecc0442bf591a4ce609d8c34c0319db4bdb464f2bcf5f4fbc8154bf9cc10ce29"],["a154a2e3","1967d2f6e205ec80b7f4eb27f5ab415aadbfb95ba7af777ee97a4ed19e38444e","GL2.t","a52903fa8a495050afe4adf11b1880eca6cc2470c4b7a08363e8ff6b305be1aa"],["92934a24","f7ec2618254ef8efb04094b9fa5126dad079b45aa6fb46904ceb840945af08bf","GL3.t","2b4abc84cc3f16beecc0e3d6ea2c4ed61449f08ad4b695fa25a08727b3f02da7"],["c6493055","2e7d3ff59c3d78fb9e8c55691e3bc94fd5c95a9b0e8c2299892e52d12a059fd3","GL4.t","51d0bdd4591955f6a9953af8be0a4c9189574cda8cda6a4d13b23d43235d55b1"],["3bf300f2","d0d9a1f79aea4889a96fb7617f26684fd3d71da69a91034658b4e6d5a7388ba1","GL5.t","f26fc92144daa6fc25565e5cae3027ca78ce31bbf24d364de1537ddc523f48db"],["1d517809","c315a9c47fc50e0e49170a8d3eb0853b85f277dde8a977e68abd9899b0a461ed","GL6.t","20fccc795a8e74644e7e8bd5605e49ef8cc8e8e58173d2065b4a71566036ac22"],["78b34d44","221b03b74e76f7caf69db30373d74e5b399c8d32b539d682422e6e25d5ba9e43","GL7.t","43481e8262f4366ce8fbbf981e9e766aab78072254ed625c515650283ed8e07c"],["57a0be97","ebaf53555d7af8197a68c49b914c8c2a9b7d27a6933c18490d1f2099c40207ed","GL8.t","43270061c28921fad3cd59535a382eb8ec3706aea3b77390fb41e921ea1c78dc"],["5847ed29","40c2c342e090ab02f20ba56a42f20cf3eaf34c35a7a06663f195628f01afcd6c","FO1.t","48c8a553ea6fb205429d50b1d7c4cff7db4e977e727c22cf74d963cc305dbd5a"],["4035f361","07fdd4b0073d3ad465fb8ce8ea752c798808c21ec0a7bd6640c026d84188f49f","FO2.t","5b3fa0bed0217ab186380fc470b689237097620171490860cec64655f7c14aac"],["e3876748","432499291d221d72a1743e3ab546e3a28161560b838dafa7ecbfb42b648429f4","FO3.t","f460bec019f637279e817d039403d92f727d2fd51a8e6f2a108d17e486d440f3"],["3e773c83","1233ed7dd285262430ecda3ec186cb6e82e5a9e4ddb5edd50ec8ce5e3a470ba3","FO4.t","4fa445ebc7ae8c8fada16871b8900ccd5c2a8265335103500ebbe68671e52de0"],["fc7a454e","bbd04be31886137b9b58fab8558a93cf42f583dbed935590b73954003788b75a","FO5.t","649db769f4123bb991dfa8413c5e0122e0b033e427114cb9624fddf2cbec1789"],["df2273a5","8fbf68edccbd93639892d0381a34dea01456cf2ecd732e07967b264d79539200","FO6.t","16af9293fe383f9cb4e9022f4f9d71f92732dc07722a9c48bcee0b0658e79f30"],["a1b0c591","280b6e0d1e686696befb71d206cd4cf12fd11dfdfa601db72af7239304af2748","FO7.t","536f40e5e2588b9902a890299cdd41152d243f72a4ff34a6ada348cd8d573e77"],["be1046fc","ae38bcc762daecd097f294a18c77de9526a9550997b3dea5abbd4e1754e2be7b","FO8.t","7faffb06392e98d1189db8a077cb9bfa6203b0031163faf85b5f0b810c45842a"],["c12077ae","d621d148b2fdf4de7c0f318e2a42ac616f20cce7a2f49f444c528d4f383f104b","Sw1.t","21f33c843dba9523768d449f3af9ecd4824f6a02555d1cae1fe29781ad504ece"],["013ee13a","03f1d66bbd12815a15ca914661b5bfb163435ea6086ec0f054745d5711be10a4","Sw2.t","09518117c9ea142ef5c92a197dbd782b0b6dee050deee26a0d48e4b5b1b57270"],["e7920704","5dcde7fd25b1bbfef68869824100cc4d65bc3a7cf622e7983949f6f60caea03a","Sw3.t","1f4addb6c4ec8c067e24b4d04104a9df2a4172457a9829ff2ff5c0affcb2447b"],["c83d312d","a255538e865777ce60f4760285b6e313fe1a94d9c93dfe3e40d68cfbcb7e0a1f","Sw4.t","8fbdb7e8a27289f5302386ef187d361524b58a05d614323787a16a570cc21667"],["1be5b7a8","9303f395c8590830a0576732b964914be694ce8952faef8080ddb8797897e4b5","Sw5.t","39fac4f64eb9147f57cbb6b9b0d836fd66f55770923b7a512b56d6f56384e210"],["aac884f0","384ee234ec62a6b88727e02c0d7d2f7ae4290b10b9909cd951c8e0ce2f7e8195","Sw6.t","41be43b2cd73b05cfa48db312faaf193a5d408547851d597dd32780795e76bab"],["a529be52","86ccc48d7caec982c5cc1c4c86dff3de312e19a4941ff5d413e41a101fc682d1","Sw7.t","c9c00a8a327aaa0625732ae38d6c2a7ebc32d96a21683dea1de9768cc5945650"],["354c4fc5","4a507fd2e5e938d8c8f075e189ca8ac6fe1efaa77ccb8939074a910609c1c6db","Sw8.t","dcf35f2207e5d455edb297ffd751cd92a95c2274eac03beb89fdb37e8c9c3350"],["62d8d655","912ceef979a52b07230f055f2e6e3b9e0a87a32a6bd815d854f4386a73d788cf","Wa1.t","388ea4621929bceb99b1d23bbd95530a72e31822b3592f971ef2d2ff60a8ad19"],["e8ac7fc2","57848e6ae3393eaadd4255b9964e795edd749f30c2060138e6a6625de8e23d11","Wa2.t","7efdfdf2e8d53264ba56e1a089b193c208adf559495376e0108f4118e3ec127c"],["ab7792c8","57868a9a756d5c818bde7ede2476eb76f07704db28a2e120e2c5f59863b4ad69","Wa3.t","ace6c13aa8ae464c25439e1b15fc6f2f25e5951b02d681354427e8ab0e088b2e"],["4596c7a5","5fae16fe047e36cf63fcb62680135f1db796154bad8285ea738d8e87638d58c9","Wa4.t","f2d432ed854bc9da3d6e06f70b7c72f52b19cf24f9d4d180d67c95e8cc5973cc"],["86052b52","766647439316fbf27321cccee9f477b16235bb0910aa997aeeb916303b955561","Wa5.t","ad4698ae3a1aa0e533230b7ce76876e92f2468c6c88686e872ce7b596104ced8"],["50bee2c7","d25db91ac17da5918ce56fab2330f9a643d5a74e4e219bd5030307cbeb45c2a8","Wa6.t","c56dc853bb8a0572faf904c58ed66577e6cfb0f17bbc1ad0b450cd50f089fdce"],["5e409196","0e6d837af947e27beeeda1b3a0f2e8f230c878516d960912bccf8cdbe1c8c270","Wa7.t","289e0e01c6297e94e1fc2792cdbd7caa3f771b6d6f1038d182167c9280996fcc"],["2bbbb748","99ee9da46a83192a7477c4c3370713375dd672afc162f674a3b6a54ad3601019","Wa8.t","ea77beaff196d7098331a050df6bd8a7a88631eb644baa9fd09b924e5fd0ec07"],["cbc31cbf","6ce8ac139e20774e0dd1a5b59c73fad088dd35d978e90b595866e5cf1dab41fe","test","8e8d950fb3dfb1b24b3a866c42254e8fc76d9f5d4567cef7843a08f61fd072a5"]].map(([hash,sha,fil,filSha])=>[parseInt(hash,16),{sha,fil,filSha}]));
    let kampRen = null, kampVenter = null, kampSekvens = 0;
    // Bare disse to kildeobserverte Ratmen-bakingene kan bevise svart indeks5.
    // De gir ingen HD-eier; originalcellene beholdes foran terrengbildet.
    const RATMENS_BAKING = [
        {fil:'ratmen2.cel',nr:56,w:24,h:2,x:15,y:185,speilet:false,
            bank:'fdfccce1758ce662cc4777ca82fef14c3ed73476767a179df07967a464289f58',
            indeks:'f8309f49b5784273f46aa28a0fa6cc3a270ddf3f0c1d7624fc6b6e68143dc6bb'},
        {fil:'ratmen1.cel',nr:51,w:28,h:3,x:114,y:182,speilet:true,
            bank:'6b59eb2aee821f94e9f5ce0fbea17eba0239ce4759a54e7dc2c057c69865f6ab',
            indeks:'6c7369d2f81a8655771f6605544cfb60022e8b0aa4060259a3749070c10c44fc'}
    ];
    let ratmenKilder=null, ratmenVenter=false, ratmenBilde=-1;
    const ratmenObservert=new Set();
    async function klargjorRatmen() {
        if (ratmenKilder || ratmenVenter || typeof Spillgrafikk==='undefined') return;
        const data=RATMENS_BAKING.map(r=>Kjerne.hentFil('data/'+r.fil)?.slice());
        if (data.some(d=>!d)) return;
        ratmenVenter=true; const egenEpoch=epoch;
        const sha=async d=>[...new Uint8Array(await crypto.subtle.digest('SHA-256',d))].map(v=>v.toString(16).padStart(2,'0')).join('');
        try {
            const banker=await Promise.all(data.map(sha));
            if (!banker.every((h,i)=>h===RATMENS_BAKING[i].bank)) return;
            const ruter=data.map((b,i)=>Spillgrafikk._cel(b)[RATMENS_BAKING[i].nr]);
            if (!ruter.every((g,i)=>g?.w===RATMENS_BAKING[i].w && g.h===RATMENS_BAKING[i].h &&
                data[i][19+RATMENS_BAKING[i].nr*10]===15)) return;
            const hashes=await Promise.all(ruter.map(g=>sha(g.px)));
            if (egenEpoch===epoch && hashes.every((h,i)=>h===RATMENS_BAKING[i].indeks)) ratmenKilder=ruter.map((g,i)=>({px:g.px.slice(),data:data[i]}));
        } finally { if (egenEpoch===epoch) ratmenVenter=false; }
    }
    function observerRatmen() {
        if (typeof Kjerne.bildeNr!=='function' || typeof Kjerne.tegneliste!=='function') return;
        const bilde=Kjerne.bildeNr();
        if (bilde<ratmenBilde) ratmenObservert.clear();
        if (bilde===ratmenBilde) return;
        ratmenBilde=bilde;
        for (const d of Kjerne.tegneliste()) for (let i=0;i<RATMENS_BAKING.length;i++) {
            const r=RATMENS_BAKING[i];
            if (d.fil.toLowerCase()===r.fil && d.bilde===r.nr && d.w===r.w && d.h===r.h &&
                d.x-(d.xoff||0)===r.x && d.y===r.y && !!d.speilet===r.speilet &&
                d.caller===0x087b34 && d.target===0x0a2cd6) ratmenObservert.add(i);
        }
    }
    function ratmenKomposisjon(lag) {
        if (kampRen?.hash!==0xe8ac7fc2 || !ratmenKilder || !ratmenObservert.size) return false;
        const px=kampRen.px.slice();
        for (const i of ratmenObservert) {
            const r=RATMENS_BAKING[i], kilde=ratmenKilder[i], data=Kjerne.hentFil('data/'+r.fil);
            if (!data || data.length!==kilde.data.length || !data.every((v,j)=>v===kilde.data[j])) return false;
            for (let y=0;y<r.h;y++) for (let x=0;x<r.w;x++) {
                const c=kilde.px[y*r.w+(r.speilet?r.w-1-x:x)];
                if (c) px[(r.y+y)*320+r.x+x]=c;
            }
        }
        return lag.bakIdx.every((v,p)=>v===px[p]);
    }
    const kampFor = new Uint8Array(64000*4);
    const kampIndeks = new Uint8Array(64000), kampVern = new Uint8Array(64000);
    async function huskRenKamp(lag, row) {
        const hash=lag.hash>>>0;
        if (kampRen?.hash===hash || kampVenter===hash) return;
        kampRen=null; kampVenter=hash;
        const egenEpoch=epoch, sekvens=++kampSekvens, px=lag.bakIdx.slice();
        const filer=[['program','b0a84503c0664515ef8b31072098acd62dbf50de3a36fe4ffe9492b094f593a6'],
            ['test','8e8d950fb3dfb1b24b3a866c42254e8fc76d9f5d4567cef7843a08f61fd072a5'],
            ['mog','d8cc4ec9f848ee30032f1e0c0db4e37c2484114910d314760956da9fee96da81'],[row.fil,row.filSha]];
        const data=filer.map(([f])=>Kjerne.hentFil('data/'+f));
        if (data.some(d=>!d)) { kampVenter=null; return; }
        const sha=async d=>[...new Uint8Array(await crypto.subtle.digest('SHA-256',d))].map(v=>v.toString(16).padStart(2,'0')).join('');
        const hashes=await Promise.all([...data,px].map(sha));
        if (egenEpoch!==epoch || sekvens!==kampSekvens) return;
        kampVenter=null;
        if (hashes[filer.length]===row.sha && hashes.slice(0,filer.length).every((h,i)=>h===filer[i][1])) {
            kampRen={hash,px}; ratmenObservert.clear(); ratmenBilde=-1;
            if (hash===0xe8ac7fc2) klargjorRatmen().catch(()=>{});
        }
    }
    function korrigerKamp(lag,scan,diw) {
        if (!lag?.bakIdx || lag.bakIdx.length!==64000 || lag.bak?.length!==256000 ||
            lag.forIdx?.length!==64000 || lag.for?.length!==256000 || lag.scene) return null;
        const hash=lag.hash>>>0, row=KAMP_KILDER.get(hash);
        if (row) { huskRenKamp(lag,row).catch(()=>{}); return null; }
        if (!kampRen) return null;
        if (kampRen.hash===0xe8ac7fc2) observerRatmen();
        const ratmen=ratmenKomposisjon(lag);
        kampVern.fill(0);
        let n=0;
        for (let p=0;p<64000;p++) if (lag.bakIdx[p]!==kampRen.px[p]) {
            const c=lag.bakIdx[p], k=p*4, pal=((diw[1]+Math.floor(p/320))*32+c)*4;
            // Andre effekter, toning og andre paletter faar originalbakgrunnen.
            if ((c!==15 && !(ratmen && c===5)) || scan.pal[pal]!== (c===15?204:0) || scan.pal[pal+1]!==0 ||
                scan.pal[pal+2]!==0 || scan.pal[pal+3]!==255 || lag.bak[k]!== (c===15?204:0) ||
                lag.bak[k+1]!==0 || lag.bak[k+2]!==0 || lag.bak[k+3]!==255) return null;
            kampVern[p]=1; n++;
        }
        if (!n) return null;
        kampFor.set(lag.for); kampIndeks.set(lag.forIdx);
        for (let p=0;p<64000;p++) if (kampVern[p] && kampIndeks[p]===255) {
            kampFor.set(lag.bak.subarray(p*4,p*4+4),p*4); kampIndeks[p]=lag.bakIdx[p];
        }
        // Bakgrunnsindeksene beholdes urort til CEL-eierskapsporten. Originale
        // deltaceller vernes i sin helhet foran HD, ogsaa i transparente figurhull.
        sist={id:'combat-delta',hash:kampRen.hash.toString(16).padStart(8,'0'),actual_hash:hash.toString(16).padStart(8,'0'),preserved_pixels:n};
        return {...lag,for:kampFor,forIdx:kampIndeks,hash:kampRen.hash,sceneVern:kampVern,kampDeltaVern:kampVern};
    }
    function nullstill() { kampRen=null; kampVenter=null; kampSekvens++; ratmenKilder=null; ratmenVenter=false; ratmenBilde=-1; ratmenObservert.clear(); kilder.clear(); sist = null; rull = null; rullVenter = false; rullSist = 0; epoch++; }
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
        if (!mode || (!standard.aktiv && !Visning.harHdBilde('bg/' + hash))) return null;
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
        // Kildeidentiteten trengs ogsaa mens figurpakken lastes: den lar
        // StandardHd hente riktig bakgrunn med en gang, uten aa vente paa alle CEL.
        if ((!standard.aktiv && !Visning.hdAntall()) ||
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
            // er message.piv). Er kopien selv bildet, gjelder den vanlige bakgrunnen, eller
            // med "copy_scene" scenen sammenlignet med kopien (banneret i en melding).
            let skjerm = s.compare === 'screen';
            if (skjerm && lag && (lag.hash >>> 0) === parseInt(s.hash, 16)) {
                if (!s.copy_scene) continue;
                skjerm = false;
            }
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
        if (!valgt) return korrigerKamp(lag,scan,diw) || lag;
        // LI1-ritualets originale palett blinker hvit/sort. En vanlig RGB-
        // bakgrunn kan bare tones fra normalpaletten, ikke gjengi dette blinket.
        // Bare disse SHA-bekreftede PIV-scenene bruker originalbakgrunn ved
        // annen palett. Identitet/lagdeling er lik i Original og HD.
        const li1Scene = (valgt.id==='altar' && valgt.source_sha256==='59d17f17600ae46b60667992364e6b360529df12d9ea41b976c01f1d2527b051') ||
            (valgt.id==='portal' && valgt.source_sha256==='aec20997ca0dd954b1bc81cc8137d51f74eca0a8f4a94866f91487d3fa1c972d');
        const hdBackgroundOriginal=li1Scene && !Visning.li1NormalPalett(scan,diw);
        // Kandidatens alfakontur eier sin kant. PIV-piksler utenfor kanten
        // skal ikke danne en tre-pikslers blaa/sort glorie rundt HD-fotoet.
        const padding=li1Scene?0:valgt.foreground_padding;
        const rect = valgt.rect || [0, 0, 320, 200];
        const faste = Visning.hdPaa() ? (valgt.overlays || []).filter(o=>Visning.sceneOverleggKlar(o.key,diw,o.palette_mask)) : [];
        // Tilgjengelighet er lik i Original og HD. Ellers ville Original utvide
        // forgrunnsrektangelet og avlyse de plasserte animasjonsfragmentene.
        const originaleFelt = (valgt.overlays || []).filter(o=>!Visning.sceneOverleggKlar(o.key,diw,o.palette_mask));
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
        if (padding) {
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
            if (!vern && padding) {
                const d = padding;
                const x0=Math.max(0,x-d), y0=Math.max(0,y-d), x1=Math.min(320,x+d+1), y1=Math.min(200,y+d+1);
                vern=summer[y1*321+x1]-summer[y0*321+x1]-summer[y1*321+x0]+summer[y0*321+x0];
            }
            if (!vern) continue;
            const fp = (diw[1] + y) * 720 + diw[0] + x * 2;
            for (let k=0;k<4;k++) foran[p*4+k]=fb[fp*4+k];
            indeks[p] = scan.idx[fp] & 31;
            beholdt++;
        }
        sist = { id: valgt.id, match: best, preserved_pixels: beholdt, hash: valgt.hash, hd_icons: ikoner.length,
            ...(li1Scene?{hd_background_original:hdBackgroundOriginal}: {}) };
        return { bak, for: foran, forIdx: indeks, bakIdx: valgt.px,
            hash: parseInt(valgt.hash, 16), lys, lysMaks: valgt.lysMaks,
            hdRect: valgt.uv_rect || rect, scene: valgt.id, hdBackgroundOriginal,
            overlays: [...faste,...ikoner.map(m=>({key:m.key,rect:m.draw_rect||m.rect,uv_rect:[0,0,1,1],foreground:true}))], sceneVern: avvik };
    }
    return { korriger, nullstill, info: () => sist, matcher: () => sisteMatcher.slice() };
})();
