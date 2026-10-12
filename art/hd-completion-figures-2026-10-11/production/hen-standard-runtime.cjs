/* Faktisk originalslutt med18 individuelle flammer. Bare seiersflagget er testoppsett. */
'use strict';
const fs=require('fs'),path=require('path'),crypto=require('crypto'),assert=require('assert/strict');
const {chromium}=require('playwright'),root=path.resolve(__dirname,'../../..'),art=__dirname;
const mode=process.env.MOONSTONE_HEN_CONTEXT||'ending',bank=mode==='ending'?'klift1.cel':'hen1.c';
const out=process.env.MOONSTONE_HD_TEST_OUTPUT||path.join(art,'verification',mode==='ending'?'standard-ending':'standard-stonehenge'),sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const report={status:'running',scope:'Kontrollert originalt seiersflagg, faktisk programtrace og18 Klift-flammer. Ingen full gjennomspilling eller hen1-stedsbesoek.',checks:[],errors:[],routes:{},source_files:{},assets:{}};
if(mode!=='ending')report.scope='Kontrollert originalkall fra080170 til stonehenge_druider08a802 ved900, aktiv ridderpeker08d5b4. Original kode laster Hen1.p/Hen1.c og palett. Ingen naturlig kartreise eller palettskriving.';
for(const f of ['web/build/moonstone-core.js','web/src/core.js','web/src/render.js','web/src/scenes.js','Moonstonecd32-AMIGA.zip'])report.source_files[f]=sha(fs.readFileSync(root+'/'+f));
let browser;
(async()=>{
 fs.mkdirSync(out,{recursive:true});
 browser=await chromium.launch({headless:true,executablePath:'/usr/bin/google-chrome',args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 const p=await browser.newPage({viewport:{width:960,height:700}});p.on('pageerror',e=>report.errors.push(e.message));
 await p.addInitScript(()=>localStorage.setItem('moonstone.innstillinger',JSON.stringify({hd:'hd',hdValgt:true})));
 const url=process.env.MOONSTONE_URL||'http://127.0.0.1:8773/moonstone.html';await p.goto(url);
 await p.waitForFunction(()=>{try{return window.moonDebug&&moonDebug.Kjerne.bildeNr()>1;}catch(e){return false;}});
 await p.keyboard.press('Pause');await p.waitForFunction(()=>moonDebug.StandardHd.info().klar);
 report.html_sha256=sha(await(await p.request.get(url)).body());
 for(let n=7;n<=24;n++){const name=String(n).padStart(3,'0')+'.png';report.assets['hen1.c/'+name]=sha(fs.readFileSync(art+'/packed/hen1.c/'+name));}
 await p.evaluate(()=>{const{Kjerne:K,Visning:V,SceneHd:S}=moonDebug;K.start(false);K.menyPaa(false);K.lagPaa(true);V.nullstillScene();S.nullstill();V.settHd(true);});
 report.standard_pack=await p.evaluate(()=>moonDebug.StandardHd.info());assert.equal(report.standard_pack.tilgjengelige,481);assert.equal(report.standard_pack.feil,null);
 await p.evaluate(mode=>moonDebug.Kjerne.menyPaa(mode!=='ending'),mode);
 const result=await p.evaluate(async({mode,bank})=>{
  const{Kjerne:K,Visning:V,SceneHd:S,StandardHd:H}=moonDebug,M=await K.last(),dv=new DataView(M.HEAPU8.buffer),seen={},trace=[];
  function draw(){const fb=K.rammebuffer(),diw=K.vindu(),l=S.korriger(fb,diw,K.lag());V.tegn(fb,diw,l);H.oppdater(l?.hash);}
  function stable(){for(let j=0;j<30;j++)draw();}
  while(K.bildeNr()<(mode==='ending'?2800:3300)){
   const n=K.bildeNr();
   if(mode==='ending'&&n<125)dv.setUint16(M._ms_chip()+0x3e0,0x80,false);
   if(mode!=='ending'&&n===100)K.tast(0x45,true);if(mode!=='ending'&&n===104)K.tast(0x45,false);
   if(mode!=='ending'&&n===900){const chip=M._ms_chip();if(dv.getUint32(chip+0x80172,false)!==0x83d6e)throw Error('Originalt oppstartskall endret');dv.setUint32(chip+0x80172,0x8a802,false);dv.setUint32(chip+0x8d9ac,0x8d5b4,false);}
   const down=mode!=='ending'&&[700,760].some(f=>n>=f&&n<f+4),fire=mode!=='ending'&&[820].some(f=>n>=f&&n<f+4);
   K.inndata(0,down?2:fire?16:0);K.bilde();const ds=K.tegneliste();V.nyttBilde(ds);
   for(const d of ds)if(d.fil.toLowerCase()===bank&&d.bilde>=7&&d.bilde<=24)trace.push({...d,frame:K.bildeNr()});
   if(K.bildeNr()%20===0||K.bildeNr()>=(mode==='ending'?1280:1100)&&K.bildeNr()<(mode==='ending'?1500:1800)){draw();
    const figures=V.hdFigurer(true).filter(d=>d.fil.toLowerCase()===bank&&d.bilde>=7&&d.bilde<=24&&d.hd&&!seen[d.bilde]);
    if(figures.length){stable();const active=V.hdFigurer(true),hd=V.bildeTilPng(),state=K.sjekksum(),control=V.hdKontroll();
     V.settHd(false);stable();const original=V.bildeTilPng();V.settHd(true);stable();const restored=V.bildeTilPng();
     const scan=K.skanout(),diw=K.vindu();
     for(const d of figures){if(hd===original)continue;const offset=(diw[1]+Math.max(0,d.y))*128;
      seen[d.bilde]={frame:K.bildeNr(),figure:d,active,control,state,state_after:K.sjekksum(),hd,original,restored,palette:Array.from(scan.pal.subarray(offset,offset+128))};}
    }
    await new Promise(r=>setTimeout(r,0));
   }
  }
  return{seen,trace,scene:S.info(),used:K.brukteFiler()};
 },{mode,bank});
 report.scope+=' Vanlig standardlasting; ingen kandidatimport.';report.visit={scene:result.scene,used:result.used,trace_calls:result.trace.length};report.trace=result.trace;
 for(let n=7;n<=24;n++){
  const r=result.seen[n];assert(r,'Ruten skal faktisk tegnes med HD: '+n);
  assert(r.hd!==r.original,'HD skal endre bildet: '+n);assert.equal(r.hd,r.restored,'Eksakt HD-retur: '+n);assert.equal(r.state,r.state_after,'Uendret state: '+n);
  for(const mode of ['hd','original','restored']){const b=Buffer.from(r[mode].split(',')[1],'base64');fs.writeFileSync(out+'/'+String(n).padStart(3,'0')+'-'+mode+'.png',b);r[mode]=sha(b);}
  report.routes[n]=r;report.checks.push(n+'_actual_HD',n+'_exact_return',n+'_state_unchanged');
 }
 report.trace=result.trace;assert.equal(report.errors.length,0);report.status='passed';
})().catch(e=>{report.status='failed';report.failure=String(e);process.exitCode=1;console.error(e);}).finally(async()=>{
 fs.writeFileSync(out+'/hen-flames-runtime.json',JSON.stringify(report,null,2)+'\n');
 console.log(JSON.stringify({status:report.status,checks:report.checks.length,routes:Object.keys(report.routes).length,failure:report.failure}));if(browser)await browser.close();
});
