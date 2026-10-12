/* Lesbar HD-tekst og kildebekreftet peker i faktisk WASM-spill.
 * Naturlig tittel, kart og inventar; original CPU tegner loot fra encounter-fixture.
 *
 * Kjoering: MOONSTONE_URL=http://127.0.0.1:8773/moonstone.html node tools/hd_lesbar_tekst_sjekk.cjs
 * MOONSTONE_VERIFY_OUT velger rapport-/bildefolder. MOONSTONE_ROOT overstyrer repoet.
 * Standard er full runde. MOONSTONE_VERIFY_FOCUS=cursor hopper over allerede
 * kontrollerte tittel-/kartcapturer og negative fontbanktester, men sjekker fortsatt
 * naturlig inventar, tekst, kantpeker, normal soeyle, loot og negativ po.cel-bank.
 * MOONSTONE_LOOT_STATE kan peke til en native loot-redraw-ready.sav. Uten den
 * lager tools/lag_loot_fixture.py fixturen og dokumenterer native-kommandoene.
 * CHROME kan overstyre nettleserbanen. HTTP-respons og PNG-filer SHA-kontrolleres.
 */
'use strict';
const fs = require('fs'), path = require('path'), assert = require('assert/strict'), crypto = require('crypto');
const {chromium} = require('playwright'), {execFileSync}=require('child_process');
const root = process.env.MOONSTONE_ROOT || path.resolve(__dirname,'..'), out = process.env.MOONSTONE_VERIFY_OUT || '/tmp/moonstone-readable-text-check';
const url = process.env.MOONSTONE_URL || 'http://127.0.0.1:8773/moonstone.html';
const focus=process.env.MOONSTONE_VERIFY_FOCUS==='cursor';
const report = {url, focus:focus?'cursor':'full', created_at:new Date().toISOString(), scope: 'Naturlig tittel, kart og inventar. Kildebank-negative tester og Original-rundtur. Peker flyttes med original joystick; ekte loot tegnes av original CPU fra kontrollert encounter-fixture.', checks: [], captures: [], errors: []};
const sha = b => crypto.createHash('sha256').update(b).digest('hex');
report.manifest_sha256 = sha(fs.readFileSync(root+'/web/hd/manifest.json'));
// SHA registreres fra den faktiske HTTP-responsen, ogsaa ved offentlig URL.
const check = (name, ok) => {assert(ok, name); report.checks.push(name);console.log('OK '+name);};
let browser;
async function draw(p) {
    return p.evaluate(() => {
        const {Kjerne: K, Visning: V, SceneHd: S, StandardHd: H} = moonDebug;
        V.tegn(K.rammebuffer(), K.vindu(), S.korriger(K.rammebuffer(), K.vindu(), K.lag()));
        H.oppdater(V.lagNaa()?.hash);
        return {png: V.bildeTilPng(), state: K.sjekksum(), scene: S.info(), control: V.hdKontroll(),
            readable: V.lesbarTekst(), icons: V.hdIkonInfo(), fonts: V.hdFigurer().filter(d => /^(bold\.f|small\.font)$/i.test(d.fil))};
    });
}
async function stable(p) {let state; for (let n=0;n<5;n++) state=await draw(p); return state;}
async function capture(p, name) {
    const hd = await stable(p);
    await p.locator('#hd-bryter').selectOption('original');
    const original = await stable(p);
    await p.locator('#hd-bryter').selectOption('hd');
    const restored = await stable(p);
    for (const [mode, value] of [['hd',hd],['original',original],['restored',restored]]) {
        fs.writeFileSync(out+'/'+name+'-'+mode+'.png', Buffer.from(value.png.split(',')[1],'base64'));
        report.captures.push({name,mode,state:value.state,scene:value.scene,control:value.control,fonts:value.fonts,readable:value.readable,icons:value.icons,sha256:sha(Buffer.from(value.png.split(',')[1],'base64'))});
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
async function movePointer(p,x,y){
    const pos=await p.evaluate(async([x,y])=>{
        const{Kjerne:K,Visning:V,SceneHd:S,StandardHd:H}=moonDebug;
        for(let n=0;n<400;n++){
            const px=K.les16(0x98092),py=K.les16(0x98094);
            if(Math.abs(px-x)<=1&&Math.abs(py-y)<=1)return[px,py];
            const bits=(px>x+1?4:px<x-1?8:0)|(py>y+1?1:py<y-1?2:0),port=K.pekerPort();
            K.inndata(port===0?bits:0,port===1?bits:0);K.bilde();V.nyttBilde(K.tegneliste());
            if(n%20===0){V.tegn(K.rammebuffer(),K.vindu(),S.korriger(K.rammebuffer(),K.vindu(),K.lag()));H.oppdater(V.lagNaa()?.hash);await new Promise(r=>setTimeout(r,0));}
        }
        throw new Error('Originalpekeren naadde ikke maal');
    },[x,y]);
    await p.evaluate(()=>{const K=moonDebug.Kjerne;K.inndata(0,0);for(let n=0;n<4;n++){K.bilde();moonDebug.Visning.nyttBilde(K.tegneliste());}});
    return pos;
}
(async()=>{
    fs.mkdirSync(out,{recursive:true});
    browser=await chromium.launch({headless:true,executablePath:process.env.CHROME||'/usr/bin/google-chrome',args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
    const p=await browser.newPage({viewport:{width:1280,height:900}});p.on('pageerror',e=>report.errors.push(e.message));
    await p.addInitScript(()=>localStorage.setItem('moonstone.innstillinger',JSON.stringify({hd:'hd',hdValgt:true})));
    const response=await p.goto(url);report.html_sha256=sha(await response.body());await p.waitForFunction(()=>{try{return window.moonDebug&&moonDebug.Kjerne.bildeNr()>1;}catch(_){return false;}});
    await p.keyboard.press('Pause');await p.waitForFunction(()=>moonDebug.StandardHd.info().klar,null,{timeout:240000});await p.keyboard.press('Home');
    await reset(p);if(!focus){await step(p,600);await draw(p);await p.waitForFunction(()=>moonDebug.StandardHd.info().bakgrunner.includes('55bb9767'));
    const title=await capture(p,'title');
    check('title_has_at_least_40_HD_font_glyphs',title.control.tekstGodkjent>=40);
    check('title_has_no_rejected_font_rows',title.control.tekstAvvist===0);
    await p.evaluate(()=>{const K=moonDebug.Kjerne;window.fontOriginalFile=K.hentFil;K.hentFil=name=>{const d=fontOriginalFile(name);if(d&&name.toLowerCase()==='data/bold.f'){const changed=d.slice();changed[8]^=1;return changed;}return d;};});
    await draw(p);await p.waitForTimeout(150);const rejected=await stable(p);
    check('changed_bold_bank_is_rejected',rejected.fonts.filter(d=>d.fil==='bold.f').length===0);
    await p.evaluate(()=>{moonDebug.Kjerne.hentFil=fontOriginalFile;delete window.fontOriginalFile;});await draw(p);await p.waitForTimeout(150);
    check('restored_bold_bank_restores_HD_text',(await stable(p)).control.tekstGodkjent>=40);
    }
    await step(p,2000);await draw(p);await p.waitForFunction(()=>moonDebug.StandardHd.info().bakgrunner.includes('2c1e0fa5'));
    if(!focus){const map=await capture(p,'world-map');check('natural_map_scene_matches',map.scene?.id==='world-map');check('map_has_no_rejected_font_rows',map.control.tekstAvvist===0);}
    await p.evaluate(()=>moonDebug.Kjerne.tast(0x40,true));await step(p,2004);await p.evaluate(()=>moonDebug.Kjerne.tast(0x40,false));await step(p,2150);
    const inventory=await capture(p,'inventory');
    check('inventory_source_slash_is_clear_slash',inventory.readable.some(d=>d.fil.toLowerCase()==='small.font'&&d.bilde===71&&d.tegn==='/'));
    check('inventory_tooltip_retains_all_nine_letters',inventory.readable.filter(d=>d.y===3).map(d=>d.tegn).join('')==='LONGSWORD');
    check('inventory_shows_original_small_font_shapes',inventory.fonts.some(d=>d.fil.toLowerCase()==='small.font'));
    check('inventory_has_no_rejected_font_rows',inventory.control.tekstAvvist===0);
    await stable(p);
    const ready=await p.evaluate(()=>document.fonts.check('100px MoonstoneLesbar')&&document.fonts.check('100px MoonstoneHD'));
    check('embedded_readable_fonts_loaded',ready);
    if(!focus){await p.evaluate(()=>{const{Kjerne:K,Visning:V}=moonDebug;window.clearTextSource=K.hentFil;K.hentFil=n=>{const d=clearTextSource(n);if(d&&n.toLowerCase()==='data/small.font'){const c=d.slice();c[8]^=1;return c;}return d;};});
    await stable(p);check('changed_small_bank_rejected',!(await stable(p)).fonts.some(d=>d.fil.toLowerCase()==='small.font'));
    await p.evaluate(()=>{moonDebug.Kjerne.hentFil=clearTextSource;delete window.clearTextSource;});await stable(p);
    check('small_bank_restores_values',(await stable(p)).fonts.filter(d=>d.fil.toLowerCase()==='small.font').length===inventory.fonts.length);
    await p.evaluate(()=>{const{Kjerne:K}=moonDebug;window.clearKiSource=K.hentFil;K.hentFil=n=>{const d=clearKiSource(n);if(d&&n.toLowerCase()==='data/ki.cel'){const c=d.slice();c[8]^=1;return c;}return d;};});
    await stable(p);check('changed_KI_bank_rejects_clear_labels',await p.evaluate(()=>!moonDebug.Visning.hdIkonInfo().viste.some(d=>d.fil.toLowerCase()==='ki.cel'&&d.bilde>=38&&d.bilde<=43)));
    await p.evaluate(()=>{moonDebug.Kjerne.hentFil=clearKiSource;delete window.clearKiSource;});await stable(p);
    check('all_six_clear_labels_restore',await p.evaluate(()=>moonDebug.Visning.hdIkonInfo().viste.filter(d=>d.fil.toLowerCase()==='ki.cel'&&d.bilde>=38&&d.bilde<=43).length===6));
    }
    await p.setViewportSize({width:2048,height:1141});await stable(p);if(!focus)await capture(p,'inventory-large');
    // Kontroller aktiv peker ved nedre hoeyre kant; ankerpunktet er utenfor vinduet.
    await movePointer(p,314,195);
    const edge=await capture(p,'inventory-edge');
    check('clipped_edge_pointer_approved',edge.control.markorGodkjent===1&&edge.icons.markor.x>=311&&edge.icons.markor.y>=191);
    await movePointer(p,230,150);
    const column=await capture(p,'inventory-column');
    check('source_pointer_full_shape_above_column',column.control.markorGodkjent===1&&column.icons.markor.synlige===84&&column.icons.markor.kildeSynlige<84);
    let lootState=process.env.MOONSTONE_LOOT_STATE;
    if(!lootState){const fixture=JSON.parse(execFileSync('python3',[root+'/tools/lag_loot_fixture.py','--out',out+'/loot-fixture','--root',root],{encoding:'utf8'}));lootState=fixture.ready_sav;}
    if(lootState){
        const bytes=fs.readFileSync(lootState);report.loot_fixture={path:lootState,sha256:sha(bytes),scope:'Native encounter-fixture, original loot redraw, ingen buffer- eller palettpatch.'};
        check('loot_native_state_loads',await p.evaluate(bytes=>{const{Kjerne:K,Visning:V,SceneHd:S}=moonDebug;V.nullstillScene();S.nullstill();K.menyPaa(true);K.lagPaa(true);return K.lastTilstand(Uint8Array.from(bytes));},Array.from(bytes)));
        await p.evaluate(async()=>{const{Kjerne:K,Visning:V,SceneHd:S,StandardHd:H}=moonDebug;for(let n=0;n<200;n++){K.inndata(0,0);K.bilde();V.nyttBilde(K.tegneliste());if(n%10===0){V.tegn(K.rammebuffer(),K.vindu(),S.korriger(K.rammebuffer(),K.vindu(),K.lag()));H.oppdater(V.lagNaa()?.hash);await new Promise(r=>setTimeout(r,0));}}});
        await draw(p);await p.waitForFunction(()=>moonDebug.StandardHd.info().bakgrunner.includes('e868fda9')&&moonDebug.Visning.hdKontroll().bakgrunn==='hd',null,{timeout:240000});
        const loot=await capture(p,'loot-middle-column');
        check('loot_HD_background_actually_visible',loot.control.bakgrunn==='hd');
        check('loot_has_original_two_arch_background',await p.evaluate(()=>moonDebug.Kjerne.lag().hash===0xe868fda9));
        check('loot_pointer_full_shape_above_middle_column',loot.control.markorGodkjent===1&&loot.icons.markor.x===155&&loot.icons.markor.y===150&&loot.icons.markor.synlige===84&&loot.icons.markor.kildeSynlige<84);
        check('loot_has_clear_name_values_and_source_slash',loot.readable.some(d=>d.bilde===71&&d.tegn==='/')&&loot.readable.length>=20);
        check('loot_keeps_all_six_clear_labels',loot.icons.viste.filter(d=>d.fil.toLowerCase()==='ki.cel'&&d.bilde>=38&&d.bilde<=43).length===6);
    }
    await p.evaluate(()=>{const K=moonDebug.Kjerne;window.savedPointerBank=K.hentFil;K.hentFil=n=>{const d=savedPointerBank(n);if(d&&n.toLowerCase()==='data/po.cel'){const c=d.slice();c[8]^=1;return c;}return d;};});
    const rejectedPointer=await stable(p);report.pointer_rejection=rejectedPointer.control;check('changed_pointer_bank_rejected',!rejectedPointer.control.markorGodkjent);
    await p.evaluate(()=>{moonDebug.Kjerne.hentFil=savedPointerBank;delete window.savedPointerBank;});
    check('pointer_bank_restores_full_shape',(await stable(p)).control.markorGodkjent===1);
    report.inventoryDiagnostics=await p.evaluate(()=>({control:moonDebug.Visning.hdKontroll(),icons:moonDebug.Visning.hdIkonInfo(),fonts:moonDebug.Visning.hdFigurer(true).filter(d=>/font|bold/.test(d.fil)),spritePixels:[...moonDebug.Kjerne.skanout().idx].filter(i=>i&128).length}));
    check('no_browser_errors',report.errors.length===0);report.status='passed';
})().catch(e=>{report.status='failed';report.failure=String(e);console.error(e);process.exitCode=1;}).finally(async()=>{
    fs.mkdirSync(out,{recursive:true});fs.writeFileSync(out+'/font-runtime-test.json',JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({status:report.status,checks:report.checks.length,errors:report.errors,failure:report.failure,pointer:report.inventoryDiagnostics?.icons.markor}));if(browser)await browser.close();
});
