/* Naturlig intro og starttur: faktisk kildematching, teksturer og grafikkbytte. */
'use strict';
const fs=require('fs'),path=require('path'),assert=require('assert/strict'),{chromium}=require('playwright');
const root=path.resolve(__dirname,'..'),out=path.resolve(root,process.env.MOONSTONE_HD_TEST_OUTPUT||'art/hd-all-locations-2026-10-11/verification/intro');
const url=process.env.MOONSTONE_URL||'http://127.0.0.1:8769/moonstone.html';
const wanted=['mindscape-logo','intro-stars','stonehenge-knight','stonehenge-overhead','message-banner'];
const report={url,scope:'Original intro uten hopp, starttur og Practice med vanlige tastetrykk. Sluttgrenen kjøres separat med kontrollert seiersflagg ved oppstart, uten full gjennomspilling.',scenes:{},best_matches:{},max_exposure:{},used:[],fades:[],errors:[]};let browser;
async function draw(p){return p.evaluate(()=>{const{Kjerne:K,Visning:V,SceneHd:S,StandardHd:H}=moonDebug;V.tegn(K.rammebuffer(),K.vindu(),S.korriger(K.rammebuffer(),K.vindu(),K.lag()));H.oppdater(V.lagNaa()?.hash);return V.bildeTilPng();});}
async function journey(p,end,skip,mode='journey'){
 await p.evaluate(mode=>{const{Kjerne:K,Visning:V,SceneHd:S}=moonDebug;K.start(false);K.menyPaa(mode!=='practice');K.lagPaa(true);V.nullstillScene();S.nullstill();V.settHd(true);K.brukteFiler();},mode);
 for(let frame=25;frame<=end;frame+=25){
  const state=await p.evaluate(async({frame,skip,mode})=>{const{Kjerne:K,Visning:V,SceneHd:S,StandardHd:H}=moonDebug;
   while(K.bildeNr()<frame){const n=K.bildeNr();if(skip&&n===100)K.tast(0x45,true);if(skip&&n===104)K.tast(0x45,false);
    if(mode==='ending'&&n<125){const M=await K.last();new DataView(M.HEAPU8.buffer).setUint16(M._ms_chip()+0x3e0,0x80,false);}
    const down=skip&&(mode==='practice'?[700,760]:[700,760,820]).some(f=>n>=f&&n<f+4),fire=skip&&(mode==='practice'?[820]:[880,1100,1200]).some(f=>n>=f&&n<f+4);K.inndata(0,down?2:fire?16:0);K.bilde();V.nyttBilde(K.tegneliste());}
   V.tegn(K.rammebuffer(),K.vindu(),S.korriger(K.rammebuffer(),K.vindu(),K.lag()));H.oppdater(V.lagNaa()?.hash);await new Promise(r=>setTimeout(r,0));
   const l=V.lagNaa(),mesh=V.scene().children.find(o=>o.visible&&o.material?.uniforms?.texel&&o.material.uniforms.lys);
   return{frame:K.bildeNr(),scene:S.info(),scan:K.skanout().gyldig,diw:[...K.vindu()],matches:S.matcher(),used:K.brukteFiler(),ending:K.iSlutt(),exposure:l?.lysMaks?l.lys/l.lysMaks:null,shader_light:mesh?.material.uniforms.lys.value};},{frame,skip,mode});
  for(const m of state.matches)if(wanted.includes(m.id)&&m.match>(report.best_matches[m.id]?.match||0))report.best_matches[m.id]={...m,frame,mode};
  for(const f of state.used)if(!report.used.includes(f))report.used.push(f);
  delete state.matches;delete state.used;state.mode=mode;
  if(state.exposure!==null&&state.exposure<0.8&&state.shader_light!==undefined){assert(Math.abs(state.shader_light-state.exposure)<0.00001,'HD skal følge originalens toning fra første bilde');report.fades.push({frame,mode,id:state.scene.id,exposure:state.exposure,shader_light:state.shader_light});}
  const id=state.scene?.id;
  if(id)report.max_exposure[id]=Math.max(report.max_exposure[id]||0,state.exposure||0);
  if(!wanted.includes(id)||report.scenes[id]||state.scene.preserved_pixels>60000||state.exposure<0.1)continue;
  await p.waitForFunction(hash=>moonDebug.StandardHd.info().bakgrunner.includes(hash),state.scene.hash,{timeout:30000});
  for(let n=0;n<30;n++)await draw(p);const hd=await draw(p),checksum=await p.evaluate(()=>moonDebug.Kjerne.sjekksum());
  await p.evaluate(()=>moonDebug.Visning.settHd(false));const original=await draw(p);
  await p.evaluate(()=>moonDebug.Visning.settHd(true));const restored=await draw(p);
  assert(restored===hd,id+': HD gjenopprettet');assert(original!==hd,id+': synlig HD-bakgrunn');assert.equal(await p.evaluate(()=>moonDebug.Kjerne.sjekksum()),checksum);
  for(const[mode,data]of[['original',original],['hd',hd]])fs.writeFileSync(out+'/'+id+'-'+mode+'.png',Buffer.from(data.split(',')[1],'base64'));
  report.scenes[id]={...state,restored:true,state_unchanged:true};console.log(id+' ved bilde '+frame);
 }
}
(async()=>{
 fs.mkdirSync(out,{recursive:true});browser=await chromium.launch({headless:true,executablePath:'/usr/bin/google-chrome',args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 const p=await browser.newPage({viewport:{width:960,height:700}});p.on('pageerror',e=>report.errors.push(e.message));
 await p.addInitScript(()=>localStorage.setItem('moonstone.innstillinger',JSON.stringify({hd:'hd',hdValgt:true})));
 await p.goto(url);await p.waitForFunction(()=>window.moonDebug&&moonDebug.Kjerne.bildeNr()>1);await p.keyboard.press('Pause');await p.waitForFunction(()=>moonDebug.StandardHd.info().klar);
 await journey(p,6000,false);await journey(p,2000,true);await journey(p,1800,true,'practice');await journey(p,6000,false,'ending');
 report.not_seen=wanted.filter(id=>!report.scenes[id]);
 assert(report.scenes['mindscape-logo']&&report.scenes['stonehenge-overhead'],'Naturlig intro skal vise logo og steinsirkel');
 assert.equal(report.not_seen.length,0,'Alle fem faste bilder skal være synlige');assert(report.fades.length>10,'Faktiske inn-/uttoninger skal kontrolleres');
 assert.equal(report.errors.length,0);report.status='passed';
})().catch(e=>{report.status='failed';report.failure=String(e);console.error(e);process.exitCode=1;}).finally(async()=>{report.created_at=new Date().toISOString();fs.writeFileSync(out+'/intro-test.json',JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report));if(browser)await browser.close();});
