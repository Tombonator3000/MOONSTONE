/* Hent faktisk nattpalett og synlig forgrunn fra den urorte introen. */
'use strict';
const fs=require('fs'),path=require('path'),crypto=require('crypto'),assert=require('assert/strict'),{chromium}=require('playwright');
const root=path.resolve(__dirname,'../../../..'),out=__dirname+'/source';
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
let browser,server;
(async()=>{
 fs.mkdirSync(out,{recursive:true});server=await require('../../figures/kn3-production/runtime-host.cjs')(root+'/web/build');
 browser=await chromium.launch({headless:true,executablePath:'/usr/bin/google-chrome',args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 const p=await browser.newPage({viewport:{width:960,height:700}});const errors=[];p.on('pageerror',e=>errors.push(e.message));
 await p.addInitScript(()=>localStorage.setItem('moonstone.innstillinger',JSON.stringify({hd:'hd',hdValgt:true})));
 const loaded=await p.goto(server.url),html=await loaded.body();await p.waitForFunction(()=>{try{return moonDebug.Kjerne.bildeNr()>1;}catch(e){return false;}});await p.keyboard.press('Pause');await p.waitForFunction(()=>moonDebug.StandardHd.info().klar);
 const result=await p.evaluate(async()=>{
  const{Kjerne:K,Visning:V,SceneHd:S,StandardHd:H}=moonDebug;K.start(false);K.menyPaa(false);K.lagPaa(true);V.nullstillScene();S.nullstill();V.settHd(false);const trace=[];
  const draw=()=>{const f=K.rammebuffer(),d=K.vindu(),l=S.korriger(f,d,K.lag());V.tegn(f,d,l);H.oppdater(l?.hash);};
  while(K.bildeNr()<3200){K.inndata(0,0);K.bilde();const ds=K.tegneliste();V.nyttBilde(ds);for(const d of ds)if(d.fil.toLowerCase()==='ov1.cel')trace.push({frame:K.bildeNr(),...d});if(K.bildeNr()%20===0){draw();await new Promise(r=>setTimeout(r,0));}}
  for(let q=0;q<30;q++)draw();const scan=K.skanout(),diw=[...K.vindu()],palettes=[];for(let y=0;y<200;y++)palettes.push(Array.from({length:32},(_,i)=>Array.from(scan.pal.slice(((diw[1]+y)*32+i)*4,((diw[1]+y)*32+i+1)*4))));
  return{frame:K.bildeNr(),diw,scan_valid:scan.gyldig,palettes,trace,png:V.bildeTilPng(),state:K.sjekksum(),scene:S.info()};
 });assert(result.scan_valid);assert.equal(new Set(result.trace.map(d=>d.bilde)).size,4);assert.equal(errors.length,0);
 const png=Buffer.from(result.png.split(',')[1],'base64');fs.writeFileSync(out+'/intro-3200-original.png',png);delete result.png;
 const report={schema:1,status:'passed',scope:'Original intro til3200 uten hopp, palett- eller minneskriving. Faktisk programtrace for alle fire OV1-ruter. Eksportfarger er lesedata fra synlig skanout.',html_sha256:sha(html),runtime_script_sha256:sha(fs.readFileSync(__filename)),screenshot_sha256:sha(png),errors,...result};
 fs.writeFileSync(out+'/actual-intro-palette.json',JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({status:report.status,frame:report.frame,diw:report.diw,draws:report.trace.length,unique_palettes:new Set(report.palettes.map(p=>JSON.stringify(p))).size}));
})().catch(e=>{console.error(e);process.exitCode=1;}).finally(async()=>{if(browser)await browser.close();if(server)await server.close();});
