/* Originaltro font i faktisk WASM-spill: naturlig tittel/kart/inventar og
 * eksplisitte frontend-fixturer for opphavsrettsfeltene. Ingen minneskriving. */
'use strict';
const fs = require('fs'), path = require('path'), assert = require('assert/strict'), crypto = require('crypto');
const {chromium} = require('playwright');
const root = path.resolve(__dirname, '../../..'), out = process.env.MOONSTONE_VERIFY_OUT || root+'/art/hd-faithful-text-2026-10-11/verification/runtime';
const url = process.env.MOONSTONE_URL || 'http://127.0.0.1:8773/moonstone.html';
const report = {url, scope: 'Naturlig tittel, kart og inventar. Opphavsrettsfeltene er kildebaserte frontend-fixturer. Ingen emulert minneskriving.', checks: [], captures: [], errors: []};
const sha = b => crypto.createHash('sha256').update(b).digest('hex');
report.manifest_sha256 = sha(fs.readFileSync(root+'/web/hd/manifest.json'));
report.html_sha256 = sha(fs.readFileSync(process.env.MOONSTONE_FONT_PACKAGE+'/moonstone.html'));
report.render_sha256=sha(fs.readFileSync(root+'/web/src/render.js'));
report.test_sha256=sha(fs.readFileSync(__filename));
const check = (name, ok) => {assert(ok, name); report.checks.push(name);};
let browser;
async function draw(p) {
    return p.evaluate(() => {
        const {Kjerne: K, Visning: V, SceneHd: S, StandardHd: H} = moonDebug;
        V.tegn(K.rammebuffer(), K.vindu(), S.korriger(K.rammebuffer(), K.vindu(), K.lag()));
        H.oppdater(V.lagNaa()?.hash);
        return {png: V.bildeTilPng(), state: K.sjekksum(), scene: S.info(), control: V.hdKontroll(),
            fonts: V.hdFigurer().filter(d => /^(bold\.f|small\.font)$/i.test(d.fil))};
    });
}
async function stable(p) {let state; for (let n=0;n<20;n++) state=await draw(p); return state;}
async function capture(p, name) {
    const hd = await stable(p);
    await p.locator('#hd-bryter').selectOption('original');
    const original = await stable(p);
    await p.locator('#hd-bryter').selectOption('hd');
    const restored = await stable(p);
    for (const [mode, value] of [['hd',hd],['original',original],['restored',restored]]) {
        fs.writeFileSync(out+'/'+name+'-'+mode+'.png', Buffer.from(value.png.split(',')[1],'base64'));
        report.captures.push({name,mode,state:value.state,scene:value.scene,control:value.control,fonts:value.fonts,sha256:sha(value.png)});
    }
    check(name+'_HD_restores_exactly', hd.png === restored.png);
    check(name+'_HD_changes_pixels', hd.png !== original.png);
    check(name+'_display_preserves_state', hd.state === original.state && hd.state === restored.state);
    // Den separate native-proben bruker et annet laggrunnlag enn SceneHd.
    // Kjoer den etter UI-bytterunden saa den ikke endrer vedvarende tegninger
    // midt i den flyten som faktisk skal testes.
    await p.locator('#hd-bryter').selectOption('original');
    const native = await p.evaluate(() => {const {Kjerne: K, Visning: V} = moonDebug; V.tegn(K.rammebuffer(), K.vindu(), K.lag()); return V.bildeTilPng();});
    check(name+'_Original_matches_native', original.png === native);
    await p.locator('#hd-bryter').selectOption('hd');
    return hd;
}
async function reset(p) {await p.evaluate(() => {const {Kjerne: K, Visning: V, SceneHd: S}=moonDebug; K.start(false);K.menyPaa(true);K.lagPaa(true);V.nullstillScene();S.nullstill();V.settHd(true);});}
async function step(p,end) {
    await p.evaluate(async end => {
        const {Kjerne: K, Visning: V, SceneHd: S, StandardHd: H}=moonDebug;
        while (K.bildeNr()<end) {
            const n=K.bildeNr();if(n===100)K.tast(0x45,true);if(n===104)K.tast(0x45,false);
            const down=[700,760,820].some(f=>n>=f&&n<f+4),fire=[880,1100,1200].some(f=>n>=f&&n<f+4);
            K.inndata(0,down?2:fire?16:0);K.bilde();V.nyttBilde(K.tegneliste());
            if(n%20===0){V.tegn(K.rammebuffer(),K.vindu(),S.korriger(K.rammebuffer(),K.vindu(),K.lag()));H.oppdater(V.lagNaa()?.hash);await new Promise(r=>setTimeout(r,0));}
        }
    },end);
}
async function copyrightFixture(p,c) {
    await p.evaluate(c=>{
        const {Kjerne:K,Visning:V,SceneHd:S}=moonDebug,diw=[70,19,710,219],x=16,y=90;
        const idx=new Uint8Array(720*288),fb=new Uint8Array(720*288*4),pal=new Uint8Array(288*32*4),bak=new Uint8Array(256000),foran=new Uint8Array(256000),forIdx=new Uint8Array(64000).fill(255),bakIdx=new Uint8Array(64000);
        for(let n=3;n<bak.length;n+=4)bak[n]=255;for(let n=3;n<fb.length;n+=4)fb[n]=255;
        for(let row=0;row<288;row++)for(let color=0;color<32;color++)pal.set([...(c.palette[color]||[0,0,0]),255],(row*32+color)*4);
        for(let j=0;j<c.height;j++)for(let i=0;i<c.width;i++){
            const color=c.indices[j*c.width+i];if(!color)continue;
            const n=(y+j)*320+x+i,screen=(diw[1]+y+j)*720+diw[0]+(x+i)*2,rgba=[...c.palette[color],255];
            forIdx[n]=color;foran.set(rgba,n*4);idx[screen]=idx[screen+1]=color;fb.set(rgba,screen*4);fb.set(rgba,(screen+1)*4);
        }
        const lag={bak,for:foran,forIdx,bakIdx,hash:0xc0000000+c.source.frame,lys:1,lysMaks:1};
        K.skanout=()=>({gyldig:true,idx,pal});K.rammebuffer=()=>fb;K.vindu=()=>diw;K.lag=()=>lag;
        S.nullstill();V.nullstillScene();V.nyttBilde([{fil:c.source.file,bilde:c.source.frame,x,y,w:c.width,h:c.height,xoff:0,speilet:false}]);
        V.nyttBilde([]);V.nyttBilde([]);V.nyttBilde([]);
    },c);
}
(async()=>{
    fs.mkdirSync(out,{recursive:true});
    browser=await chromium.launch({headless:true,executablePath:process.env.CHROME||'/usr/bin/google-chrome',args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
    const p=await browser.newPage({viewport:{width:960,height:700}});p.on('pageerror',e=>report.errors.push(e.message));
    await p.addInitScript(()=>localStorage.setItem('moonstone.innstillinger',JSON.stringify({hd:'hd',hdValgt:true})));
    const response=await p.goto(url);const loaded=await response.body();check('faktisk_HTML_SHA',sha(loaded)===report.html_sha256);check('faktisk_renderkode',loaded.toString().includes(fs.readFileSync(root+'/web/src/render.js','utf8')));await p.waitForFunction(()=>{try{return window.moonDebug&&moonDebug.Kjerne.bildeNr()>1;}catch(_){return false;}});
    await p.keyboard.press('Pause');await p.waitForFunction(()=>moonDebug.StandardHd.info().klar,null,{timeout:60000});await p.keyboard.press('Home');
    await reset(p);await step(p,600);await draw(p);await p.waitForFunction(()=>moonDebug.StandardHd.info().bakgrunner.includes('55bb9767'));
    const title=await capture(p,'title');
    check('title_has_at_least_40_HD_font_glyphs',title.control.tekstGodkjent>=40);
    check('title_has_no_rejected_font_rows',title.control.tekstAvvist===0);
    await p.evaluate(()=>{const K=moonDebug.Kjerne;window.fontOriginalFile=K.hentFil;K.hentFil=name=>{const d=fontOriginalFile(name);if(d&&name.toLowerCase()==='data/bold.f'){const changed=d.slice();changed[8]^=1;return changed;}return d;};});
    await draw(p);await p.waitForTimeout(150);const rejected=await stable(p);
    check('changed_bold_bank_is_rejected',rejected.fonts.filter(d=>d.fil==='bold.f').length===0);
    await p.evaluate(()=>{moonDebug.Kjerne.hentFil=fontOriginalFile;delete window.fontOriginalFile;});await draw(p);await p.waitForTimeout(150);
    check('restored_bold_bank_restores_HD_text',(await stable(p)).control.tekstGodkjent>=40);
    await step(p,2000);await draw(p);await p.waitForFunction(()=>moonDebug.StandardHd.info().bakgrunner.includes('2c1e0fa5'));
    const map=await capture(p,'world-map');check('natural_map_scene_matches',map.scene?.id==='world-map');check('map_has_no_rejected_font_rows',map.control.tekstAvvist===0);
    await p.evaluate(()=>moonDebug.Kjerne.tast(0x40,true));await step(p,2004);await p.evaluate(()=>moonDebug.Kjerne.tast(0x40,false));await step(p,2150);
    const inventory=await capture(p,'inventory');
    check('inventory_shows_original_small_font_shapes',inventory.fonts.some(d=>d.fil.toLowerCase()==='small.font'));
    check('inventory_has_no_rejected_font_rows',inventory.control.tekstAvvist===0);
    await p.evaluate(()=>{const K=moonDebug.Kjerne;window.fontFixtureOriginal={scan:K.skanout,fb:K.rammebuffer,diw:K.vindu,lag:K.lag};});
    const contracts=JSON.parse(fs.readFileSync(root+'/art/hd-faithful-text-2026-10-11/source-contracts.json'));
    for(const c of contracts.entries.filter(c=>c.source.file==='bold.f'&&c.source.frame>=74)){
        await copyrightFixture(p,c);const state=await capture(p,'copyright-'+c.source.frame);
        check('copyright_'+c.source.frame+'_uses_one_original_HD_field',state.control.tekstGodkjent===1&&state.fonts.length===1&&state.fonts[0].bilde===c.source.frame);
        check('copyright_'+c.source.frame+'_has_no_rejected_pixels',state.control.tekstAvvist===0);
    }
    await p.evaluate(()=>{const K=moonDebug.Kjerne,o=fontFixtureOriginal;K.skanout=o.scan;K.rammebuffer=o.fb;K.vindu=o.diw;K.lag=o.lag;moonDebug.Visning.nullstillScene();moonDebug.SceneHd.nullstill();delete window.fontFixtureOriginal;});
    check('no_browser_errors',report.errors.length===0);report.status='passed';
})().catch(e=>{report.status='failed';report.failure=String(e);console.error(e);process.exitCode=1;}).finally(async()=>{
    report.created_at=new Date().toISOString();report.disk_manifest_changed_during_run=report.manifest_sha256!==sha(fs.readFileSync(root+'/web/hd/manifest.json'));
    fs.mkdirSync(out,{recursive:true});fs.writeFileSync(out+'/font-runtime-test.json',JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({status:report.status,checks:report.checks.length,errors:report.errors,failure:report.failure}));if(browser)await browser.close();
});
