/* Ny selvstendig ti-rutersgruppe016..025 mot endelig007-v7, eldre proof bevares. */
/* Endelig007-frys med original data/mog-SHA, eldre proof bevares. */
/* Kildebevist levende riddermaske importeres sammen med eget foto. */
/* Original Balok-reaksjon etter spillerens faktiske opp+slag-inndata. */
/* Ny Balok-bevisserie etter LI1-retensjonsretting. */
/* Ny samlet Balok-prøve mot frosset frontend etter bakgrunnsretting. */
/* Ny bevisserie etter LI1-presentasjonsretting, uten overskriving av eldre proever. */
/* Faktisk original Balok-kamp med separat importerte, kildebundne kandidater. */
'use strict';
const fs=require('fs'),path=require('path'),assert=require('assert/strict'),crypto=require('crypto'),{chromium}=require('playwright');
const art=__dirname,root=path.resolve(art,'../../..'),url=process.env.MOONSTONE_URL||'http://127.0.0.1:8872/moonstone.html',indexPath=process.env.MOONSTONE_CANDIDATE_INDEX||art+'/candidates.json';
const sha=b=>crypto.createHash('sha256').update(b).digest('hex'),indexBytes=fs.readFileSync(indexPath),index=JSON.parse(indexBytes),caseBytes=fs.readFileSync(art+'/../palettes/cases/balok.json'),combat=JSON.parse(caseBytes),files=index.entries.flatMap(r=>[{key:r.key,path:r.candidate,sha:r.candidate_sha256},...(r.mask?[{key:r.key.replace('.png','.mask.png'),path:r.mask,sha:r.mask_sha256}]:[])]).map(r=>{const b=fs.readFileSync(root+'/'+r.path);assert.equal(sha(b),r.sha);return{key:r.key,candidate:r.path,candidate_sha256:r.sha,base64:b.toString('base64')};}),out=art+'/verification/runtime-'+sha(indexBytes).slice(0,16)+'-'+sha(fs.readFileSync(__filename)).slice(0,8);
const report={schema:1,status:'running',url,index_sha256:sha(indexBytes),palette_case_sha256:sha(caseBytes),source_zip_sha256:combat.source_zip_sha256,assets:files.map(({key,candidate,candidate_sha256})=>({key,candidate,candidate_sha256})),checks:[],errors:[],scope:'Original kampstart via tre kontrollerte testskrivinger; deretter original inndata, lag og tegneliste. Privat kandidatimport, ingen produksjonsaktivering. Ingen naturlig kartreise eller full animasjonsdekning.'};
const check=(n,v)=>{assert(v,n);report.checks.push(n);};let browser;
(async()=>{
 fs.mkdirSync(out,{recursive:true});fs.writeFileSync(out+'/input-index.json',indexBytes);browser=await chromium.launch({headless:true,executablePath:'/usr/bin/google-chrome',args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});const p=await browser.newPage({viewport:{width:960,height:700}});p.on('pageerror',e=>report.errors.push(e.message));
 await p.addInitScript(()=>localStorage.setItem('moonstone.innstillinger',JSON.stringify({hd:'original',hdValgt:true})));const loaded=await p.goto(url);const htmlBytes=await loaded.body();report.html_sha256=sha(htmlBytes);fs.writeFileSync(out+'/loaded.html',htmlBytes);report.runtime_script_sha256=sha(fs.readFileSync(__filename));await p.waitForFunction(()=>{try{return window.moonDebug&&moonDebug.Kjerne.bildeNr()>1;}catch(e){return false;}});await p.keyboard.press('Pause');
 report.standard_before_stop=await p.evaluate(()=>moonDebug.StandardHd.info());await p.evaluate(()=>moonDebug.StandardHd.stopp());

 console.log(JSON.stringify({phase:'original_core_started',standard:report.standard_before_stop}));
 await p.exposeFunction('balokProofProgress',n=>console.log(JSON.stringify({phase:'original_frames',frame:n})));
 const result=await p.evaluate(async({files,combat})=>{
  const {Kjerne:K,Visning:V,StandardHd:H,SceneHd:S}=moonDebug,M=await K.last();H.oppdater=()=>{};V.tomHdPakke();
  const imported=await V.lastHdPakke(files.map(({key,base64})=>{const f=new File([Uint8Array.from(atob(base64),c=>c.charCodeAt(0))],key.split('/').pop());Object.defineProperty(f,'webkitRelativePath',{value:key});return f;}));
  K.start(false);K.menyPaa(false);K.lagPaa(true);V.nullstillScene();S.nullstill();V.settHd(true);V.settTvungetLag(true);V.settFilter('skarp');
  const samples={},trace=[],sourceTrace=[],keys=files.filter(f=>!f.key.endsWith('.mask.png')).map(f=>f.key.toLowerCase().replace(/\.png$/,''));let cropStable=false;
  const digest=async b=>[...new Uint8Array(await crypto.subtle.digest('SHA-256',b))].map(v=>v.toString(16).padStart(2,'0')).join('');
  const draw=()=>{V.tegn(K.rammebuffer(),K.vindu(),K.lag());return V.bildeTilPng();};
  const pressed=n=>((n>=700&&n<704)||(n>=760&&n<764)?2:0)|(n>=820&&n<824?16:0)|(n>=1200&&n<1320?4:0)|(n>=1350&&n<1950?16:0);
  while(K.bildeNr()<1680){const n=K.bildeNr();if(n===100)K.tast(0x45,true);if(n===104)K.tast(0x45,false);K.inndata(0,pressed(n));
   if(n===900){const d=new DataView(M.HEAPU8.buffer),chip=M._ms_chip();for(const w of combat.test_writes)d.setUint32(chip+parseInt(w.address),parseInt(w.value),false);}
   K.bilde();const draws=K.tegneliste();V.nyttBilde(draws);if(K.bildeNr()>1200&&draws.some(d=>d.fil.toLowerCase().startsWith('balok')))sourceTrace.push({frame:K.bildeNr(),draws});const sampleWindow=K.bildeNr()>=1330&&K.bildeNr()<=1660;
   if(sampleWindow){if(!cropStable){for(let q=0;q<30;q++)V.tegn(K.rammebuffer(),K.vindu(),K.lag());cropStable=true;}V.tegn(K.rammebuffer(),K.vindu(),K.lag());const visible=V.hdFigurer(true);const hd=visible.filter(d=>d.hd&&keys.includes(d.fil.toLowerCase()+'/'+String(d.bilde).padStart(3,'0')));if(hd.length)trace.push({frame:K.bildeNr(),draws,visible,control:V.hdKontroll()});
    for(const d of hd){const key=d.fil.toLowerCase()+'/'+String(d.bilde).padStart(3,'0');if(samples[key]&&samples[key].hd_keys.length>=hd.length)continue;const state=K.sjekksum();V.settHd(false);const original=draw();V.settHd(true);const candidate=draw();V.settHd(false);const original_again=draw();V.settHd(true);const hd_again=draw();samples[key]={frame:K.bildeNr(),draws,visible,hd_keys:hd.map(d=>d.fil+'/'+d.bilde),control:V.hdKontroll(),palette_words:Array.from({length:32},(_,i)=>new DataView(M.HEAPU8.buffer).getUint16(M._ms_chip()+0x961a0+i*2,false)),state,state_after:K.sjekksum(),original,candidate,original_again,hd_again};}
   }if(Object.keys(samples).length===keys.length&&Object.values(samples).every(s=>s.hd_keys.length===keys.length))break;
   if(n%200===0){await window.balokProofProgress(K.bildeNr());await new Promise(r=>setTimeout(r,0));}
  }
  return{imported,trace,sourceTrace,samples,source_banks_sha256:Object.fromEntries(await Promise.all(['Balok1.CEL','Balok2.CEL','Balok3.CEL'].map(async bank=>[bank,await digest(K.hentFil('data/'+bank.toLowerCase()))]))),frame:K.bildeNr()};
 },{files,combat});report.runtime=result;check('all_candidates_imported',result.imported===files.length);check('all_original_balok_banks_exact',Object.entries(result.source_banks_sha256).every(([bank,digest])=>digest===combat.source_banks[bank]));check('actual_balok_palette_per_sample',Object.values(result.samples).every(s=>s.palette_words.slice(9,15).join(',')===[0xf96,0xc63,0x930,0x842,0x521,0xf63].join(',')));
 for(const e of index.entries){const key=e.key.toLowerCase().replace(/\.png$/,''),s=result.samples[key];check(key+'_visible_in_original_combat',!!s);check(key+'_changes_frame',s.original!==s.candidate);check(key+'_original_exact_return',s.original===s.original_again);check(key+'_hd_exact_return',s.candidate===s.hd_again);check(key+'_emulated_state_unchanged',s.state===s.state_after);
  const name=e.key.replace('/','-').replace('.png','');for(const mode of ['original','candidate']){const b=Buffer.from(s[mode].split(',')[1],'base64');fs.writeFileSync(out+'/'+name+'-'+mode+'.png',b);s[mode+'_sha256']=sha(b);}for(const k of ['original','candidate','original_again','hd_again'])delete s[k];}
 check('no_browser_errors',report.errors.length===0);report.status='passed';
})().catch(e=>{report.status='failed';report.failure=String(e);console.error(e);process.exitCode=1;}).finally(async()=>{report.created_at=new Date().toISOString();fs.mkdirSync(out,{recursive:true});fs.writeFileSync(out+'/test.json',JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({status:report.status,checks:report.checks.length,frames:Object.fromEntries(Object.entries(report.runtime?.samples||{}).map(([k,v])=>[k,v.frame])),output:out,failure:report.failure}));if(browser)await browser.close();});
