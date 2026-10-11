/* Besøk Math med kontrollert kartposisjon, ellers original navigasjon og animasjon. */
'use strict';
const fs=require('fs'),path=require('path'),assert=require('assert/strict'),{chromium}=require('playwright');
const root=path.resolve(__dirname,'..'),out=path.resolve(root,process.env.MOONSTONE_HD_TEST_OUTPUT||'art/hd-all-locations-2026-10-11/verification');
const url=process.env.MOONSTONE_URL||'http://127.0.0.1:8769/moonstone.html';
const report={url,scope:'Original kartnavigasjon og Math-animasjon etter kontrollert flytting av aktiv ridder til kartposisjon 220,27. Ikke naturlig reise fra startstedet.',errors:[]};let b;
async function draw(p){return p.evaluate(()=>{const{Kjerne:K,Visning:V,SceneHd:S,StandardHd:H}=moonDebug;V.tegn(K.rammebuffer(),K.vindu(),S.korriger(K.rammebuffer(),K.vindu(),K.lag()));H.oppdater(V.lagNaa()?.hash);return V.bildeTilPng();});}
(async()=>{
 fs.mkdirSync(out,{recursive:true});
 b=await chromium.launch({headless:true,executablePath:process.env.CHROME||'/usr/bin/google-chrome',args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});const p=await b.newPage({viewport:{width:960,height:700}});p.on('pageerror',e=>report.errors.push(e.message));
 await p.addInitScript(()=>localStorage.setItem('moonstone.innstillinger',JSON.stringify({hd:'hd',hdValgt:true})));
 await p.goto(url);await p.waitForFunction(()=>{/* bildeNr kaster til kjernen er lastet */try{return window.moonDebug&&moonDebug.Kjerne.bildeNr()>1;}catch(e){return false;}});await p.keyboard.press('Pause');await p.waitForFunction(()=>moonDebug.StandardHd.info().klar);
 report.visit=await p.evaluate(async()=>{const{Kjerne:K,Visning:V,SceneHd:S,StandardHd:H}=moonDebug;K.start(false);K.menyPaa(true);K.lagPaa(true);V.nullstillScene();S.nullstill();
  while(K.bildeNr()<2000){const n=K.bildeNr();if(n===100)K.tast(0x45,true);if(n===104)K.tast(0x45,false);const down=[700,760,820].some(f=>n>=f&&n<f+4),fire=[880,1100,1200].some(f=>n>=f&&n<f+4);K.inndata(0,down?2:fire?16:0);K.bilde();V.nyttBilde(K.tegneliste());if(n%100===0)await new Promise(r=>setTimeout(r,0));}
  const M=await K.last(),chip=M._ms_chip(),d=new DataView(M.HEAPU8.buffer),r=d.getUint32(chip+0x8d9ac,false);d.setInt16(chip+r+0x7e,220,false);d.setInt16(chip+r+0x80,27,false);
  const seen=[],used=new Set();K.brukteFiler();for(let n=0;n<1000;n++){K.inndata(0,n<4?4:n>=150&&n<160?16:n>=500&&n<510?16:0);K.bilde();V.nyttBilde(K.tegneliste());for(const f of K.brukteFiler())used.add(f);
   if(n%25===0){V.tegn(K.rammebuffer(),K.vindu(),S.korriger(K.rammebuffer(),K.vindu(),K.lag()));H.oppdater(V.lagNaa()?.hash);const scene=S.info();if(scene&&!seen.some(v=>v.id===scene.id))seen.push({...scene,frame:K.bildeNr()});await new Promise(r=>setTimeout(r,0));}}
  return{seen,used:[...used],frame:K.bildeNr()};});
 assert(report.visit.seen.some(s=>s.id==='math-tower'));assert(report.visit.seen.some(s=>s.id==='math-balcony'));assert(report.visit.used.includes('data/Wi1.C'));
 await draw(p);await p.waitForFunction(()=>moonDebug.StandardHd.info().bakgrunner.includes('71970806'));for(let n=0;n<30;n++)await draw(p);
 const hd=await draw(p);const state=await p.evaluate(()=>moonDebug.Kjerne.sjekksum());
 report.text=await p.evaluate(()=>moonDebug.Visning.hdKontroll());
 assert.equal(report.text.tekstAvvist,0,'Alle synlige Math-tekstrader skal godkjennes samlet');
 assert(report.text.tekstGodkjent>60,'Math-dialogen skal vises med HD-font');
 report.foreground=await p.evaluate(()=>{const{Kjerne:K,Visning:V}=moonDebug,l=V.lagNaa(),s=K.skanout(),d=K.vindu();let pixels=0,exact=0;for(let y=38;y<150;y++)for(let x=95;x<210;x++){const c=l.forIdx[y*320+x];if(c!==255){pixels++;if(c===s.idx[(d[1]+y)*720+d[0]+x*2])exact++;}}return{pixels,exact};});
 assert(report.foreground.pixels>500);assert.equal(report.foreground.exact,report.foreground.pixels);
 await p.evaluate(()=>moonDebug.Visning.settHd(false));for(let n=0;n<30;n++)await draw(p);const original=await draw(p);await p.evaluate(()=>moonDebug.Visning.settHd(true));for(let n=0;n<30;n++)await draw(p);const restored=await draw(p);
 for(const[mode,data]of[['original',original],['hd',hd],['restored',restored]])fs.writeFileSync(out+'/math-animated-'+mode+'.png',Buffer.from(data.split(',')[1],'base64'));
 report.restored=restored===hd;report.diagnostic=await p.evaluate(()=>({scene:moonDebug.SceneHd.info(),cache:moonDebug.StandardHd.info(),crop:moonDebug.Visning.utsnitt()}));
 assert(restored===hd,'HD-bildet skal gjenopprettes eksakt');assert(original!==hd,'HD skal endre bildet');assert.equal(await p.evaluate(()=>moonDebug.Kjerne.sjekksum()),state);
 await p.evaluate(()=>moonDebug.Visning.settHd(false));
 const native=await p.evaluate(()=>{const{Kjerne:K,Visning:V}=moonDebug;V.tegn(K.rammebuffer(),K.vindu(),K.lag());return V.bildeTilPng();});
 report.original_matches_native=native===original;assert(report.original_matches_native,'Originalmodus skal tilsvare originalt lag');
 assert.equal(report.errors.length,0);report.status='passed';
})().catch(e=>{report.status='failed';report.failure=String(e);console.error(e);process.exitCode=1;}).finally(async()=>{report.created_at=new Date().toISOString();fs.writeFileSync(out+'/math-animated-test.json',JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report));if(b)await b.close();});
