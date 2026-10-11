/* Original kartreise med kontrollert rundeteller for originalens dragevilkaar. */
'use strict';
const fs=require('fs'),path=require('path'),{chromium}=require('playwright');
const art=__dirname,root=path.resolve(art,'../../../..');
let browser,server;
(async()=>{
 server=await require('../../figures/kn3-production/runtime-host.cjs')(root+'/web/build');
 browser=await chromium.launch({headless:true,executablePath:'/usr/bin/google-chrome',args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 const p=await browser.newPage({viewport:{width:960,height:700}});await p.addInitScript(()=>localStorage.setItem('moonstone.innstillinger',JSON.stringify({hd:'hd',hdValgt:true})));
 await p.goto(server.url);await p.waitForFunction(()=>{try{return moonDebug.Kjerne.bildeNr()>1;}catch(e){return false;}});await p.keyboard.press('Pause');await p.waitForFunction(()=>moonDebug.StandardHd.info().klar);
 const result=await p.evaluate(async()=>{
  const {Kjerne:K,Visning:V,SceneHd:S}=moonDebug,M=await K.last();K.start(false);K.menyPaa(true);K.lagPaa(true);V.nullstillScene();S.nullstill();V.settHd(true);
  const memory=new DataView(M.HEAPU8.buffer),chip=M._ms_chip(),trace=[],frames=new Set(),samples={};
  while(K.bildeNr()<4000){const n=K.bildeNr();if(n===100)K.tast(0x45,true);if(n===104)K.tast(0x45,false);
   const down=[700,760,820].some(f=>n>=f&&n<f+4),fire=[880,1100,1200].some(f=>n>=f&&n<f+4);K.inndata(0,down?2:fire?16:0);
   if(n===1250)memory.setUint16(chip+0x08f150,2,false);
   K.bilde();const list=K.tegneliste();V.nyttBilde(list);
   const drag=list.filter(d=>d.fil?.toLowerCase()==='mi.c'&&d.bilde>=34&&d.bilde<=41);
   if(n%100===0||drag.some(d=>!frames.has(d.bilde))){trace.push({frame:K.bildeNr(),round:K.les16(0x08f150),flag:K.les16(0x08e7c8),list,drag});}
   if(n%16===0||drag.length){const fb=K.rammebuffer(),diw=K.vindu();V.tegn(fb,diw,S.korriger(fb,diw,K.lag()));await new Promise(r=>setTimeout(r,0));}
   for(const d of drag)if(!frames.has(d.bilde)){frames.add(d.bilde);samples[d.bilde]={frame:K.bildeNr(),png:V.bildeTilPng(),list};}
   if(frames.size===8)break;
  }return{trace,samples};
 });
 const out=art+'/verification/runtime-trace';fs.mkdirSync(out,{recursive:true});for(const [n,s]of Object.entries(result.samples)){fs.writeFileSync(out+'/'+n+'.png',Buffer.from(s.png.split(',')[1],'base64'));delete s.png;}fs.writeFileSync(out+'/trace.json',JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify({frames:Object.keys(result.samples),trace:result.trace.map(t=>({frame:t.frame,round:t.round,flag:t.flag,dragon:t.drag}))}));
})().catch(e=>{console.error(e);process.exitCode=1;}).finally(async()=>{if(browser)await browser.close();if(server)await server.close();});
