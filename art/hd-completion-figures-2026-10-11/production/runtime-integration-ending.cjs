/* Standardpakken i faktisk originalavslutning, uten privat figurimport. */
'use strict';
const fs=require('fs'),path=require('path'),crypto=require('crypto'),assert=require('assert/strict'),{chromium}=require('playwright');
const here=__dirname,root=path.resolve(here,'../../..'),sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const base=process.env.MOONSTONE_HD_PACKAGE,out=process.env.MOONSTONE_HD_TEST_OUTPUT;
assert(base&&out,'Velg en fryst pakke og et nytt bevisomraade');
const manifest=JSON.parse(fs.readFileSync(base+'/hd/manifest.json'));
const sourceFiles=['web/src/core.js','web/src/render.js','web/src/scenes.js','web/src/hd.js','web/build/moonstone-core.js','Moonstonecd32-AMIGA.zip'];
const report={schema:1,status:'running',checks:[],errors:[],test_sha256:sha(fs.readFileSync(__filename)),source_files:Object.fromEntries(sourceFiles.map(p=>[p,sha(fs.readFileSync(root+'/'+p))])),manifest_sha256:sha(fs.readFileSync(base+'/hd/manifest.json')),assets:manifest.files,scope:'Standard HD assets only. Controlled ending selection by win flag0x3e0 during first125 boot frames. Original game executes all subsequent drawing. Exact Original/HD returns and unchanged CPU state; no claim of naturally completed game.'};
const check=(n,v)=>{assert(v,n);report.checks.push(n);};let browser,server;
(async()=>{
 fs.mkdirSync(out,{recursive:true});
 for(const f of manifest.files){const b=fs.readFileSync(base+'/hd/'+f.path);check('package_'+f.path,sha(b)===f.sha256&&b.length===f.bytes);}
 if(!process.env.MOONSTONE_HD_PUBLIC_URL)server=await require('../figures/kn3-production/runtime-host.cjs')(base);
 browser=await chromium.launch({headless:true,executablePath:'/usr/bin/google-chrome',args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 const page=await browser.newPage({viewport:{width:960,height:700}});page.on('pageerror',e=>report.errors.push(e.message));
 await page.addInitScript(()=>localStorage.setItem('moonstone.innstillinger',JSON.stringify({hd:'hd',hdValgt:true})));
 const response=await page.goto(process.env.MOONSTONE_HD_PUBLIC_URL||server.url),html=await response.body();report.url=process.env.MOONSTONE_HD_PUBLIC_URL||server.url;report.html_sha256=sha(html);check('frozen_HTML',report.html_sha256===sha(fs.readFileSync(base+'/moonstone.html')));
 for(const p of sourceFiles.filter(p=>p!=='Moonstonecd32-AMIGA.zip')){
  const code=fs.readFileSync(root+'/'+p).toString().replaceAll('</script','<\\/script');
  if(code.includes('%%HD_MANIFEST%%')){const[before,after]=code.split('%%HD_MANIFEST%%'),text=html.toString(),start=text.indexOf(before),end=text.indexOf(after,start+before.length);check('embedded_'+p,start>=0&&end>start&&JSON.stringify(JSON.parse(text.slice(start+before.length,end)))===JSON.stringify(manifest));}
  else check('embedded_'+p,html.includes(Buffer.from(code)));
 }
 await page.waitForFunction(()=>{try{return moonDebug.Kjerne.bildeNr()>1;}catch(e){return false;}});await page.keyboard.press('Pause');await page.waitForFunction(()=>moonDebug.StandardHd.info().klar,null,{timeout:60000});
 report.runtime=await page.evaluate(async()=>{
  const{Kjerne:K,Visning:V,SceneHd:S,StandardHd:H}=moonDebug;
  const packageInfo=H.info();K.start(false);K.menyPaa(false);K.lagPaa(true);V.nullstillScene();S.nullstill();V.settHd(true);
  const draw=()=>{const f=K.rammebuffer(),d=K.vindu(),l=S.korriger(f,d,K.lag());V.tegn(f,d,l);H.oppdater(l?.hash);};
  const stable=()=>{for(let i=0;i<12;i++)draw();return V.bildeTilPng();};
  const captures={},wanted=[1296,2133,2168,2650,2699,2750,2770,2800,2853];
  const M=await K.last(),memory=new DataView(M.HEAPU8.buffer);
  while(K.bildeNr()<2854){if(K.bildeNr()<125)memory.setUint16(M._ms_chip()+0x3e0,0x80,false);K.inndata(0,0);K.bilde();V.nyttBilde(K.tegneliste());if(K.bildeNr()%40===0||wanted.includes(K.bildeNr()))draw();
   if(wanted.includes(K.bildeNr())){
    // Kjernebildet er pauset mens den vanlige asynkrone bakgrunnslasteren fullfoerer.
    // Dette kontrollerer den ferdige standardscenen, ikke en lastingsfallback.
    for(let q=0;q<500&&!H.info().bakgrunner.includes(S.info()?.hash);q++){await new Promise(r=>setTimeout(r,10));draw();}
    const state=K.sjekksum();V.settHd(false);const original=stable();V.settHd(true);const hd=stable(),figures=V.hdFigurer(true),scene=S.info(),control=V.hdKontroll(),palette=V.hdPalettFigurInfo();V.settHd(false);const originalAgain=stable();V.settHd(true);const hdAgain=stable();captures[K.bildeNr()]={state,state_after:K.sjekksum(),original,hd,originalAgain,hdAgain,figures,scene,control,palette,standard:H.info()};}
   if(K.bildeNr()%80===0)await new Promise(r=>setTimeout(r,0));
  }return{packageInfo,captures};
 });
 const expected={1296:[0,1,2],2133:[6],2168:[27],2650:[28,29,30,36,37],2699:[38,39],2770:[43],2800:[47],2853:[53]};
 check('standard_package_ready',report.runtime.packageInfo.klar);
 for(const[n,c]of Object.entries(report.runtime.captures)){
  check(n+'_Original_exact',c.original===c.originalAgain);check(n+'_HD_exact',c.hd===c.hdAgain);check(n+'_CPU_unchanged',c.state===c.state_after);
  if(n==='2750')check(n+'_black_exact',c.original===c.hd);else{check(n+'_HD_background_used',c.control.bakgrunn==='hd');check(n+'_HD_changes',c.original!==c.hd);for(const frame of expected[n])check(n+'_standard_Klift_'+frame,c.figures.some(d=>d.fil.toLowerCase()==='klift1.cel'&&d.bilde===frame&&d.hd));}
  for(const mode of ['original','hd']){const bytes=Buffer.from(c[mode].split(',')[1],'base64');fs.writeFileSync(out+'/'+n+'-'+mode+'.png',bytes);c[mode+'_sha256']=sha(bytes);}
  for(const k of ['original','hd','originalAgain','hdAgain'])delete c[k];
 }
 for(const[p,h]of Object.entries(report.source_files))check('still_frozen_'+p,sha(fs.readFileSync(root+'/'+p))===h);
 check('no_browser_errors',report.errors.length===0);report.status='passed';
})().catch(e=>{report.status='failed';report.failure=String(e);process.exitCode=1;}).finally(async()=>{fs.mkdirSync(out,{recursive:true});fs.writeFileSync(out+'/test.json',JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({status:report.status,checks:report.checks.length,failure:report.failure}));if(browser)await browser.close();if(server)await server.close();});
