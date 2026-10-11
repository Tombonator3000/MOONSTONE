/* Kildepaletter og originalplasseringer fra introens faktiske CPU-kall. */
'use strict';
const fs=require('fs'),path=require('path'),crypto=require('crypto'),{chromium}=require('playwright');
const root=path.resolve(__dirname,'../../../..'),out=__dirname+'/source',sha=b=>crypto.createHash('sha256').update(b).digest('hex');
let browser,server;const report={status:'running',errors:[],scope:'Naturlig originalintro uten hopp, palett- eller minneskriving. Katalog for referanse og videre nytegning, ikke ferdige HD-ruter.'};
(async()=>{
 fs.mkdirSync(out,{recursive:true});server=await require('../../figures/kn3-production/runtime-host.cjs')(root+'/web/build');
 browser=await chromium.launch({headless:true,executablePath:'/usr/bin/google-chrome',args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});const p=await browser.newPage();p.on('pageerror',e=>report.errors.push(e.message));
 const loaded=await p.goto(server.url);report.html_sha256=sha(await loaded.body());await p.waitForFunction(()=>{try{return moonDebug.Kjerne.bildeNr()>1;}catch(e){return false;}});await p.keyboard.press('Pause');
 report.runtime=await p.evaluate(async()=>{
  const{Kjerne:K,Visning:V,SceneHd:S}=moonDebug;K.start(false);K.menyPaa(false);K.lagPaa(true);V.nullstillScene();S.nullstill();V.settHd(false);const records={},wanted=new Set(['au1.cel','da1.cel','dg1.cel','dw1.cel','li1.cel','co1.cel','ha1.cel','ov1.cel']);
  while(K.bildeNr()<15000){K.inndata(0,0);K.bilde();const ds=K.tegneliste();V.nyttBilde(ds);let scan,diw;for(const d of ds)if(wanted.has(d.fil.toLowerCase())){
   scan ||= K.skanout();diw ||= [...K.vindu()];const key=d.fil.toLowerCase()+'/'+String(d.bilde).padStart(3,'0')+'.png',row=records[key] ||= {key,first_frame:K.bildeNr(),calls:0};row.last_frame=K.bildeNr();row.calls++;
   const y=Math.max(0,Math.min(287,diw[1]+d.y+(d.h/2|0))),palette=Array.from({length:32},(_,i)=>Array.from(scan.pal.slice((y*32+i)*4,(y*32+i+1)*4))),light=palette.reduce((s,p)=>s+p[0]+p[1]+p[2],0);
   if(scan.gyldig&&(row.max_light===undefined||light>row.max_light)){Object.assign(row,{max_light:light,frame:K.bildeNr(),draw:{...d},diw,palette,scan_valid:true});}
  }if(K.bildeNr()%100===0)await new Promise(r=>setTimeout(r,0));}
  return{frame:K.bildeNr(),records:Object.values(records),state:K.sjekksum()};
 });if(report.errors.length)throw Error('Nettleserfeil');report.status='passed';
})().catch(e=>{report.status='failed';report.failure=String(e);process.exitCode=1;}).finally(async()=>{report.created_at=new Date().toISOString();report.runtime_script_sha256=sha(fs.readFileSync(__filename));fs.writeFileSync(out+'/intro-runtime-catalog-v1.json',JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({status:report.status,routes:report.runtime?.records.length,failure:report.failure}));if(browser)await browser.close();if(server)await server.close();});
