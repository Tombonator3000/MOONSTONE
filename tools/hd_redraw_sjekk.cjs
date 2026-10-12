/* Vedvarende HD-figurer etter faktiske valg og inventarklikk i original CPU.
 * MOONSTONE_BUILD peker til mappen med fryst moonstone.html og hd/.
 * MOONSTONE_URL velger en eksisterende lokal eller offentlig nettside i stedet.
 * MOONSTONE_VERIFY_OUT velger kvitteringsmappe. MOONSTONE_DIAGNOSE=1
 * samler ogsaa feilende foerbevis. Alle bilder skal vaere lastet foer klikkene.
 * MOONSTONE_VERIFY_KNIGHTS=2 kan avgrense en diagnostisk foerrunde til groenn.
 * MOONSTONE_VERIFY_COLD_KI=1 blokkerer KI til etter inventarklikk, og slipper
 * pakken mens original CPU er pauset. KI-HD maa komme uten en original redraw.
 */
'use strict';
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const {chromium}=require('playwright');
const root=path.resolve(__dirname,'..');
const out=process.env.MOONSTONE_VERIFY_OUT||'/tmp/moonstone-hd-redraw';
const report={created_at:new Date().toISOString(),scope:'Faktiske tastatur-/musevalg etter komplett HD-innlasting. Samme original-CPU startes paa nytt mellom ridderne. Ingen buffer-/spillregelpatch i brukerflyten. Separate negative presentasjonsprober paavirker ikke CPU.',checks:[],captures:[],errors:[]};
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
let browser,host,releaseBlocked=()=>{};
function check(name,ok,detail){report.checks.push({name,ok:!!ok,detail});console.log((ok?'OK ':'FEIL ')+name+(!ok&&detail?' '+JSON.stringify(detail):''));}
async function press(p,key){await p.keyboard.down(key);await p.waitForTimeout(120);await p.keyboard.up(key);await p.waitForTimeout(900);}
async function click(p,x,y){const q=await p.evaluate(([x,y])=>{const r=document.querySelector('#lerret').getBoundingClientRect(),c=moonDebug.Visning.utsnitt(),v=moonDebug.Kjerne.vindu();return{x:r.left+(v[0]+2*x-c[0])/(c[2]-c[0])*r.width,y:r.top+(v[1]+y-c[1])/(c[3]-c[1])*r.height};},[x,y]);await p.mouse.click(q.x,q.y);await p.waitForTimeout(900);}
async function snapshot(p,name){
 const d=await p.evaluate(()=>{const{Kjerne:K,Visning:V,SceneHd:S}=moonDebug;for(let n=0;n<5;n++)V.tegn(K.rammebuffer(),K.vindu(),S.korriger(K.rammebuffer(),K.vindu(),K.lag()));return{png:V.bildeTilPng(),frame:K.bildeNr(),state:K.sjekksum(),figures:V.hdFigurer(true),icons:V.hdIkonInfo(),control:V.hdKontroll(),draws:K.tegneliste(),knight_name:K.navn(),lag:K.lag().hash};});
 const png=Buffer.from(d.png.split(',')[1],'base64');delete d.png;fs.writeFileSync(out+'/'+name+'.png',png);d.name=name;d.sha256=sha(png);report.captures.push(d);
 return d;
}
async function capture(p,name){await p.keyboard.press('Pause');const d=await snapshot(p,name);await p.keyboard.press('Pause');return d;}
async function bankProbe(p,fil){
 await p.keyboard.press('Pause');
 const draw=()=>p.evaluate(fil=>{const{Kjerne:K,Visning:V,SceneHd:S}=moonDebug;for(let n=0;n<5;n++)V.tegn(K.rammebuffer(),K.vindu(),S.korriger(K.rammebuffer(),K.vindu(),K.lag()));return{state:K.sjekksum(),shown:V.hdFigurer().filter(d=>d.fil.toLowerCase()===fil).length};},fil);
 const before=await draw();
 await p.evaluate(fil=>{window.redrawFileSource=moonDebug.Kjerne.hentFil;moonDebug.Kjerne.hentFil=n=>{const d=redrawFileSource(n);if(d&&n.toLowerCase()==='data/'+fil){const c=d.slice();c[8]^=1;return c;}return d;};},fil);
 await draw();await p.waitForTimeout(200);const changed=await draw();
 await p.evaluate(()=>{moonDebug.Kjerne.hentFil=redrawFileSource;delete window.redrawFileSource;});await draw();await p.waitForTimeout(200);const restored=await draw();
 check(fil+'_modified_bank_rejected',before.shown>0&&changed.shown===0,{before,changed,restored});check(fil+'_source_restores_without_CPU_change',restored.shown===before.shown&&before.state===changed.state&&before.state===restored.state);
 await p.keyboard.press('Pause');
}
const portraits=d=>d.figures.filter(g=>g.fil.toLowerCase()==='sel.cel'&&g.bilde>=2&&g.bilde<=5);
const ki=d=>d.figures.filter(g=>g.fil.toLowerCase()==='ki.cel');
(async()=>{
 fs.mkdirSync(out,{recursive:true});if(!process.env.MOONSTONE_URL)host=await require('../art/hd-completion-figures-2026-10-11/figures/kn3-production/runtime-host.cjs')(process.env.MOONSTONE_BUILD||root+'/web/build');report.url=process.env.MOONSTONE_URL||host.url;
 browser=await chromium.launch({executablePath:process.env.CHROME||'/usr/bin/google-chrome',args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 const p=await browser.newPage({viewport:{width:640,height:500}});p.on('pageerror',e=>report.errors.push(e.message));await p.addInitScript(()=>localStorage.setItem('moonstone.innstillinger',JSON.stringify({hd:'hd',hdValgt:true,sprak:'no'})));
 const cold=process.env.MOONSTONE_VERIFY_COLD_KI==='1',blockedKi=[];report.cold_ki=cold;
 if(cold){const gate=new Promise(resolve=>{releaseBlocked=resolve;});await p.route(url=>/\/hd\/ki\.cel\/.*\.png$/.test(url.pathname),async route=>{blockedKi.push(route.request().url());await gate;await route.continue().catch(()=>{});});}
 const response=await p.goto(report.url);report.html_sha256=sha(await response.body());const manifest=await p.request.get(new URL('hd/manifest.json',report.url).href);if(!manifest.ok())throw new Error('HD-manifest HTTP '+manifest.status());report.manifest_sha256=sha(await manifest.body());await p.waitForFunction(()=>window.moonDebug&&moonDebug.modus()==='alene'&&moonDebug.Kjerne.bildeNr()>0);await press(p,'Escape');await p.waitForFunction(()=>moonDebug.Kjerne.menyKlar(),null,{timeout:60000});
 if(cold)await p.waitForFunction(()=>moonDebug.Visning.harHdBilde('sel.cel/005'),null,{timeout:240000});
 else{await p.waitForFunction(()=>moonDebug.StandardHd.info().klar||moonDebug.StandardHd.info().feil,null,{timeout:240000});report.loader=await p.evaluate(()=>moonDebug.StandardHd.info());check('complete_HD_package_before_input',report.loader.klar&&!report.loader.feil,report.loader);}
 for(let n=0;n<3;n++)await press(p,'ArrowDown');await press(p,'ControlLeft');await p.waitForFunction(()=>moonDebug.Kjerne.velgerRidder()&&!moonDebug.Kjerne.navnAktiv());await p.waitForTimeout(900);
 function verifyInventory(d){const icons=ki(d);check(d.name+'_five_HD_helmets',icons.filter(g=>g.bilde===17&&g.hd).length===5,icons);check(d.name+'_six_HD_labels',icons.filter(g=>g.bilde>=38&&g.bilde<=43&&g.hd).length===6);check(d.name+'_HD_sword_and_armour',icons.some(g=>g.bilde===22&&g.hd)&&icons.some(g=>g.bilde===27&&g.hd));}
 if(cold){
  report.scope='Kald KI-innlasting: faktisk groent riddervalg og inventarklikk med tidlige HD-fonte/portretter. KI blokkeres til original CPU er pauset. Full KI-HD skal komme uten noen ny originaltegning.';
  let d=await capture(p,'cold-portraits-initial');check('cold_four_HD_portraits_before_click',portraits(d).length===4&&portraits(d).every(g=>g.hd));
  await click(p,await p.evaluate(()=>moonDebug.Kjerne.les16(0x8f51a)+32),118);await p.waitForFunction(()=>moonDebug.Kjerne.navnKlar());d=await capture(p,'cold-portraits-name');check('cold_four_HD_portraits_after_click',portraits(d).length===4&&portraits(d).every(g=>g.hd));
  await press(p,'Enter');await p.waitForFunction(()=>moonDebug.Kjerne.kartAktiv());await press(p,'Space');await p.waitForFunction(()=>moonDebug.Kjerne.pekerAktiv());await p.waitForTimeout(1600);
  for(const[x,y]of[[120,66],[147,99],[120,125]])await click(p,x,y);
  await p.waitForTimeout(1600);await p.keyboard.press('Pause');const before=await snapshot(p,'cold-inventory-blocked');
  const deadline=Date.now()+180000;while(!blockedKi.length&&Date.now()<deadline)await p.waitForTimeout(100);check('cold_KI_request_blocked',blockedKi.length>0);report.blocked_ki_requests_before_release=blockedKi.length;
  check('cold_KI_absent_while_fonts_HD',await p.evaluate(()=>!moonDebug.StandardHd.info().klar&&!moonDebug.Visning.harHdBilde('ki.cel/017')&&moonDebug.Visning.hdIkonInfo().antall===0&&moonDebug.Visning.hdKontroll().tekstGodkjent>=20));
  releaseBlocked();await p.waitForFunction(()=>moonDebug.StandardHd.info().klar||moonDebug.StandardHd.info().feil,null,{timeout:240000});report.loader=await p.evaluate(()=>moonDebug.StandardHd.info());check('cold_complete_HD_package_after_release',report.loader.klar&&!report.loader.feil);await snapshot(p,'cold-inventory-imported');await p.waitForTimeout(300);const after=await snapshot(p,'cold-inventory-ready');verifyInventory(after);check('cold_no_CPU_redraw_after_release',before.frame===after.frame&&before.state===after.state,{before:{frame:before.frame,state:before.state},after:{frame:after.frame,state:after.state}});
  check('no_browser_errors',report.errors.length===0,report.errors);report.status=report.checks.every(c=>c.ok)?'passed':'failed';if(report.status==='failed'&&!process.env.MOONSTONE_DIAGNOSE)process.exitCode=1;return;
 }
 const knights=process.env.MOONSTONE_VERIFY_KNIGHTS?process.env.MOONSTONE_VERIFY_KNIGHTS.split(',').map(Number):[2,0,1,3];if(!knights.length||knights.some(k=>!Number.isInteger(k)||k<0||k>3))throw new Error('Ugyldig ridderliste');report.knights=knights;
 for(let number=0;number<knights.length;number++){
  const k=knights[number];
  if(number){
   // Bare fixturoppsett: start samme originale CPU paa nytt, med ferdiglastet HD.
   // Meny, portrett, navn og inventar styres deretter med faktiske brukerhendelser.
   await p.keyboard.press('Pause');await p.evaluate(()=>{const{Kjerne:K,Visning:V,SceneHd:S}=moonDebug;K.start(false);K.menyPaa(true);K.lagPaa(true);V.nullstillScene();S.nullstill();});await p.keyboard.press('Pause');await press(p,'Escape');await p.waitForFunction(()=>moonDebug.Kjerne.menyKlar());for(let n=0;n<3;n++)await press(p,'ArrowDown');await press(p,'ControlLeft');await p.waitForFunction(()=>moonDebug.Kjerne.velgerRidder()&&!moonDebug.Kjerne.navnAktiv());await p.waitForTimeout(900);
  }
  let d=await capture(p,'portraits-initial-'+k);check(d.name+'_four_HD_portraits',portraits(d).length===4&&portraits(d).every(g=>g.hd),portraits(d));
  if(k===3)await bankProbe(p,'sel.cel');
  if(k===0)for(const direction of ['ArrowRight','ArrowRight','ArrowRight','ArrowLeft','ArrowLeft','ArrowLeft']){await press(p,direction);d=await capture(p,'portraits-switch-'+report.captures.length);check(d.name+'_four_HD_portraits',portraits(d).length===4&&portraits(d).every(g=>g.hd),portraits(d));}
  const x=await p.evaluate(k=>moonDebug.Kjerne.les16(0x8f516+2*k)+32,k);await click(p,x,118);await p.waitForFunction(()=>moonDebug.Kjerne.navnKlar());d=await capture(p,'portraits-name-'+k);check(d.name+'_four_HD_portraits',portraits(d).length===4&&portraits(d).every(g=>g.hd),portraits(d));check(d.name+'_correct_name',d.name!==undefined&&await p.evaluate(k=>moonDebug.Kjerne.navn().includes(['GODBER','RICHARD','JEFFREY','EDWARD'][k]),k));
  await press(p,'Enter');await p.waitForFunction(()=>moonDebug.Kjerne.kartAktiv(),null,{timeout:30000});await press(p,'Space');await p.waitForFunction(()=>moonDebug.Kjerne.pekerAktiv());await p.waitForTimeout(800);d=await capture(p,'inventory-initial-'+k);verifyInventory(d);
  if(k===2)for(const [name,x,y]of[['helmet',120,66],['sword',147,99],['armour',120,125],['blank',295,170]]){await click(p,x,y);await p.waitForTimeout(1500);if(!await p.evaluate(()=>moonDebug.Kjerne.pekerAktiv())){await p.waitForFunction(()=>moonDebug.Kjerne.kartAktiv());await press(p,'Space');await p.waitForFunction(()=>moonDebug.Kjerne.pekerAktiv());await p.waitForTimeout(1200);}d=await capture(p,'inventory-click-'+name);verifyInventory(d);}
 }
 await bankProbe(p,'ki.cel');
 await p.keyboard.press('Pause');
 const roundtrip=await p.evaluate(()=>{const{Kjerne:K,Visning:V,SceneHd:S}=moonDebug;const draw=()=>{for(let n=0;n<5;n++)V.tegn(K.rammebuffer(),K.vindu(),S.korriger(K.rammebuffer(),K.vindu(),K.lag()));return V.bildeTilPng();};const state=K.sjekksum(),hd=draw();V.settHd(false);const original=draw();V.tegn(K.rammebuffer(),K.vindu(),K.lag());const native=V.bildeTilPng();V.settHd(true);const restored=draw();return{state_unchanged:state===K.sjekksum(),original_native:original===native,hd_restores:hd===restored,hd_changes:hd!==original,original_png:original,restored_png:restored};});
 for(const mode of ['original','restored']){fs.writeFileSync(out+'/inventory-'+mode+'.png',Buffer.from(roundtrip[mode+'_png'].split(',')[1],'base64'));delete roundtrip[mode+'_png'];}report.roundtrip=roundtrip;for(const[name,ok]of Object.entries(roundtrip))check('inventory_'+name,ok);
 const pixel=await p.evaluate(()=>{const{Kjerne:K,Visning:V,SceneHd:S}=moonDebug;const lag=S.korriger(K.rammebuffer(),K.vindu(),K.lag());const draw=l=>V.tegn(K.rammebuffer(),K.vindu(),l);draw(lag);const before=V.hdFigurer().filter(d=>d.fil.toLowerCase()==='ki.cel'&&d.bilde===17);const d=before[0],g=Spillgrafikk._cel(K.hentFil('data/ki.cel'))[17],i=g.px.findIndex(c=>c!==0),q=(d.y+Math.floor(i/g.w))*320+d.x+i%g.w;const bad={...lag,forIdx:lag.forIdx.slice()};bad.forIdx[q]=253;const state=K.sjekksum();draw(bad);const changed=V.hdFigurer().filter(d=>d.fil.toLowerCase()==='ki.cel'&&d.bilde===17).length;draw(lag);const restored=V.hdFigurer().filter(d=>d.fil.toLowerCase()==='ki.cel'&&d.bilde===17).length;return{before:before.length,changed,restored,state_unchanged:state===K.sjekksum()};});report.pixel_guard=pixel;check('changed_opaque_UI_pixel_rejects_only_its_helmet',pixel.changed===pixel.before-1&&pixel.restored===pixel.before&&pixel.state_unchanged,pixel);
 check('no_browser_errors',report.errors.length===0,report.errors);report.status=report.checks.every(c=>c.ok)?'passed':'failed';if(report.status==='failed'&&!process.env.MOONSTONE_DIAGNOSE)process.exitCode=1;
})().catch(e=>{report.status='failed';report.failure=String(e.stack||e);process.exitCode=1;console.error(e);}).finally(async()=>{releaseBlocked();fs.mkdirSync(out,{recursive:true});fs.writeFileSync(out+'/report.json',JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({status:report.status,checks:report.checks.length,failed:report.checks.filter(c=>!c.ok).map(c=>c.name),out}));if(browser)await browser.close();if(host)await host.close();});
