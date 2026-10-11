/* Foerste nye vaapenrute med ekte original kropp og tegnerekkefoelge i WASM. */
'use strict';
const fs=require('fs'),path=require('path'),assert=require('assert/strict'),crypto=require('crypto'),{chromium}=require('playwright');
const route=Number(process.env.KN4_ROUTE||0),id=String(route).padStart(3,'0');
const art=__dirname,root=path.resolve(art,'../../../..'),out=process.env.MOONSTONE_HD_TEST_OUTPUT||art+'/verification/'+('standard-contact-'+id),url=process.env.MOONSTONE_URL||'http://127.0.0.1:8773/moonstone.html';
const sha=b=>crypto.createHash('sha256').update(b).digest('hex'),check=(name,v)=>{assert(v,name);report.checks.push(name);};
const host=root+'/web/build';
const png=fs.readFileSync(art+'/packed/KN4.ob/'+id+'.png'),source=fs.readFileSync(art+'/source-contracts.json'),contract=JSON.parse(source).entries.find(c=>c.frame===route);
const caseBytes=fs.readFileSync(root+'/art/hd-completion-figures-2026-10-11/palettes/cases/troll.json'),combat=JSON.parse(caseBytes);
const production=Object.fromEntries(['web/src/core.js','web/src/render.js','web/src/scenes.js'].map(f=>[f,sha(fs.readFileSync(root+'/'+f))]));
const report={schema:1,status:'running',checks:[],errors:[],url,wasm_core_sha256:sha(fs.readFileSync(host+'/moonstone-core.js')),html_sha256:sha(fs.readFileSync(host+'/moonstone.html')),source_contracts_sha256:sha(source),packed_png_sha256:sha(png),palette_case_sha256:sha(caseBytes),scope:'Original troll-kamp initialiseres med tre kildebaserte testskrivinger, deretter ekte original inndata og full tegneliste. Bare KN4/000 importeres. Ikke et naturlig kartbesoek.'};
let browser;
(async()=>{
 report.production_code_sha256=production;
 fs.mkdirSync(out,{recursive:true});browser=await chromium.launch({headless:true,executablePath:'/usr/bin/google-chrome',args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});const p=await browser.newPage({viewport:{width:960,height:700}});p.on('pageerror',e=>report.errors.push(e.message));
 await p.addInitScript(()=>localStorage.setItem('moonstone.innstillinger',JSON.stringify({hd:'hd',hdValgt:true})));await p.goto(url);await p.waitForFunction(()=>{try{return window.moonDebug&&moonDebug.Kjerne.bildeNr()>1;}catch(e){return false;}});await p.keyboard.press('Pause');await p.waitForFunction(()=>moonDebug.StandardHd.info().klar,null,{timeout:60000});
 report.html_sha256=sha(await(await p.request.get(url)).body());
 const result=await p.evaluate(async({bytes,combat,contract,route,id})=>{
  const {Kjerne:K,Visning:V,StandardHd:H,SceneHd:S}=moonDebug,M=await K.last();
  const imported=0;
  K.start(false);K.menyPaa(false);K.lagPaa(true);V.nullstillScene();S.nullstill();V.settHd(true);V.settTvungetLag(true);V.settFilter('skarp');
  const trace=[],calls=[];let found=null;const digest=async bytes=>[...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))].map(b=>b.toString(16).padStart(2,'0')).join('');
  const pressed=n=>((n>=700&&n<704)||(n>=760&&n<764)?2:0)|(n>=820&&n<824?16:0)|(route===1?(n>=1200&&n<1320?4:0):((n>=1280&&n<1284?8:0)|(n>=1310&&n<1360?17:0)|(n>=1400&&n<1450?16:0)));
  while(K.bildeNr()<1450){const n=K.bildeNr();if(n===100)K.tast(0x45,true);if(n===104)K.tast(0x45,false);K.inndata(0,pressed(n));
   if(n===900){const d=new DataView(M.HEAPU8.buffer),chip=M._ms_chip();for(const w of combat.test_writes)d.setUint32(chip+parseInt(w.address),parseInt(w.value),false);}
   K.bilde();const draws=K.tegneliste();V.nyttBilde(draws);if(n>=1100){V.tegn(K.rammebuffer(),K.vindu(),K.lag());H.oppdater(K.lag().hash);}
   if(n>1170){const hd=V.hdFigurer(true),weapons=draws.filter(d=>d.fil.toLowerCase()==='kn4.ob');for(const d of weapons)calls.push({frame:n,...d});if(weapons.length||hd.some(d=>d.fil.toLowerCase()==='kn4.ob'))trace.push({frame:n,draws,visible:hd,control:V.hdKontroll()});
    if(hd.some(d=>d.fil.toLowerCase()==='kn4.ob'&&d.bilde===route&&(d.hd||(route===1&&V.hdKontroll().poseGodkjent>0))&&d.x>=0&&d.x+d.w<=320&&(route!==1||(n>=1250&&d.speilet)))){found={frame:n,draws,visible:hd,control:V.hdKontroll(),checksum:K.sjekksum(),background_hash:K.lag().hash};break;}}
   if(n%100===0)await new Promise(r=>setTimeout(r,0));
  }
  if(!found)return{imported,found,trace,calls};
  // Samme uendrede kjernebilde tegnes i Original og HD for direkte sammenligning.
  const draw=()=>{V.tegn(K.rammebuffer(),K.vindu(),K.lag());return V.bildeTilPng();};
  V.settHd(false);const original=draw();V.settHd(true);const hd=draw();V.settHd(false);const restored=draw();V.settHd(true);const again=draw();
  return{imported,found,trace,calls,original,hd,restored,again,checksum_after:K.sjekksum(),source_bank_sha256:await digest(K.hentFil('data/kn4.ob')),texture_loaded:V.harHdBilde('kn4.ob/'+id)};
 },{bytes:png.toString('base64'),combat,contract,route,id});
 report.scope='Original troll-kamp initialiseres med tre kildebaserte testskrivinger, deretter ekte original inndata og full tegneliste. Vanlig standardlasting av KN4/'+id+'. Ingen kandidatimport. Ikke et naturlig kartbesoek.';
 report.runtime=result;check('no_candidate_import',result.imported===0);check('original_KN4_'+id+'_drawn_and_visible',!!result.found);check('original_bank_exact',result.source_bank_sha256===contract.source_bank.sha256);check('candidate_loaded',result.texture_loaded);check('candidate_changes_frame',result.hd!==result.original);if(route===1){report.scope+=' Eksisterende helpose prioriteres under gange; den separate001-teksturen er lastet og kontrollert isolert i contact-001.';check('existing_complete_pose_priority',result.found.control.poseGodkjent>0);}check('original_exact_return',result.restored===result.original);check('hd_exact_return',result.again===result.hd);check('emulated_state_unchanged_by_toggle',result.checksum_after===result.found.checksum);
 for(const k of ['original','hd']){const b=Buffer.from(result[k].split(',')[1],'base64');fs.writeFileSync(out+'/'+k+'.png',b);report[k+'_sha256']=sha(b);}
 for(const k of ['original','hd','restored','again'])delete report.runtime[k];check('no_browser_errors',report.errors.length===0);check('all_frozen_production_sources_unchanged',Object.entries(production).every(([f,h])=>sha(fs.readFileSync(root+'/'+f))===h));check('packed_PNG_unchanged',sha(fs.readFileSync(art+'/packed/KN4.ob/'+id+'.png'))===report.packed_png_sha256);report.status='passed';
})().catch(e=>{report.status='failed';report.failure=String(e);console.error(e);process.exitCode=1;}).finally(async()=>{report.created_at=new Date().toISOString();fs.mkdirSync(out,{recursive:true});fs.writeFileSync(out+'/test.json',JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({status:report.status,checks:report.checks.length,frame:report.runtime?.found?.frame,failure:report.failure}));if(browser)await browser.close();});
