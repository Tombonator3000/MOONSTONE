/* Gjennomgaatte inventarruter i faktisk WASM-frontend som originale CEL-fixturer.
 * Ingen spillminneskriving. Kandidatimport endrer bare denne testnettleseren. */
'use strict';
const fs=require('fs'),path=require('path'),assert=require('assert/strict'),crypto=require('crypto'),{chromium}=require('playwright');
const root=path.resolve(__dirname,'..'),art=root+'/art/hd-remaining-icons-2026-10-11';
const out=path.resolve(root,process.env.MOONSTONE_HD_TEST_OUTPUT||'art/hd-remaining-icons-2026-10-11/research/runtime/verification');
const url=process.env.MOONSTONE_URL||'http://127.0.0.1:8769/moonstone.html';
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const contracts=JSON.parse(fs.readFileSync(art+'/research/runtime/source-contracts.json'));
const report={url,checks:[],assets:[],errors:[],scope:'Originale CEL-/inventarpalettfixturer i faktisk WASM-side. Kandidat-PNG importeres bare i testnettleseren. Dette er ikke naturlig bruk av alle gjenstander.'};
report.production_code_sha256=Object.fromEntries(['web/src/render.js','web/src/scenes.js'].map(f=>[f,sha(fs.readFileSync(root+'/'+f))]));
const check=(name,value=true)=>{assert(value,name);report.checks.push(name);};
let browser;
const {render,stable,fixture}=require('./hd_resterende_ikoner_fixture.cjs');
(async()=>{
 fs.mkdirSync(out,{recursive:true});
 const candidates=JSON.parse(fs.readFileSync(art+'/candidate-icons.json')),packing=JSON.parse(fs.readFileSync(art+'/packing-report.json'));
 let assets=packing.assets.filter(a=>a.key.startsWith('ki.cel/')||a.key.startsWith('mi.c/'));
 if(process.env.MOONSTONE_ICON_KEYS){const keys=new Set(process.env.MOONSTONE_ICON_KEYS.split(','));assets=assets.filter(a=>keys.has(a.key));check('all_requested_keys_selected',assets.length===keys.size);}
 check('inventory_candidates_exist',assets.length>0);
 report.candidate_icons_sha256=sha(fs.readFileSync(art+'/candidate-icons.json'));
 browser=await chromium.launch({headless:true,executablePath:process.env.CHROME||'/usr/bin/google-chrome',args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 const p=await browser.newPage({viewport:{width:960,height:700}});p.on('pageerror',e=>report.errors.push(e.message));
 await p.addInitScript(()=>localStorage.setItem('moonstone.innstillinger',JSON.stringify({hd:'hd',hdValgt:true,sprak:'no'})));
 await p.goto(url);await p.waitForFunction(()=>window.moonDebug&&moonDebug.Kjerne.bildeNr()>1);await p.keyboard.press('Pause');
 await p.waitForFunction(()=>moonDebug.StandardHd.info().klar,null,{timeout:60000});
 const state=await p.evaluate(()=>moonDebug.Kjerne.sjekksum());
 const imports=[{name:'icons.json',bytes:fs.readFileSync(art+'/candidate-icons.json').toString('base64')},...packing.assets.flatMap(a=>[a,...(a.variants||[])].map(v=>({name:v.key+'.png',bytes:fs.readFileSync(art+'/packed/'+v.key+'.png').toString('base64')})))];
 await p.evaluate(async imports=>{const files=imports.map(i=>{const f=new File([Uint8Array.from(atob(i.bytes),c=>c.charCodeAt(0))],i.name.split('/').pop());Object.defineProperty(f,'webkitRelativePath',{value:i.name});return f;});await moonDebug.Visning.lastHdPakke(files);},imports);
 check('candidate_import_has_no_errors',await p.evaluate(()=>moonDebug.Visning.hdIkonInfo().feil.length===0));
 for(const asset of assets){
  const c=contracts.entries.find(c=>c.key===asset.key);check(asset.key+'_source_contract_found',!!c);
  const row={key:asset.key,samples:[]};
  const baseColors=structuredClone(contracts.palettes[c.source.file==='mi.c'?'map':'inventory'].palette);
  const blue=asset.palette_variants?.find(v=>v.id==='blue');if(blue)blue.indices.forEach((n,i)=>baseColors[n]=blue.colors[i]);
  for(const mirror of [false,true]){
   await fixture(p,c,mirror,baseColors);await p.evaluate(()=>moonDebug.Visning.settHd(false));const original=await stable(p);
   await p.evaluate(()=>moonDebug.Visning.settHd(true));const hd=await stable(p),info=await p.evaluate(()=>({icons:moonDebug.Visning.hdIkonInfo(),control:moonDebug.Visning.hdKontroll()}));
   check(asset.key+'_HD_approved_'+mirror,info.icons.viste.some(d=>d.fil===c.source.file&&d.bilde===c.source.frame));
   if(hd===original){fs.writeFileSync(out+'/failed-unchanged.png',Buffer.from(hd.split(',')[1],'base64'));report.unchanged_debug=await p.evaluate(()=>({width:document.querySelector('canvas')?.width,height:document.querySelector('canvas')?.height,hd:moonDebug.Visning.hdPaa(),control:moonDebug.Visning.hdKontroll()}));}
   check(asset.key+'_HD_changes_pixels_'+mirror,hd!==original);
   await p.evaluate(()=>moonDebug.Visning.settHd(false));check(asset.key+'_Original_exact_'+mirror,await stable(p)===original);
   await p.evaluate(()=>moonDebug.Visning.settHd(true));check(asset.key+'_HD_exact_'+mirror,await stable(p)===hd);
   const name=asset.key.replace('/','-')+(mirror?'-mirrored':'');
   fs.writeFileSync(out+'/'+name+'-original.png',Buffer.from(original.split(',')[1],'base64'));fs.writeFileSync(out+'/'+name+'-hd.png',Buffer.from(hd.split(',')[1],'base64'));
   row.samples.push({mirror,original_sha256:sha(Buffer.from(original.split(',')[1],'base64')),hd_sha256:sha(Buffer.from(hd.split(',')[1],'base64')),control:info.control});
  }
  if(asset.palette_variants){
   row.palette_samples=[];const seen=new Set();
   for(const variant of asset.palette_variants){
    const colors=structuredClone(baseColors);variant.indices.forEach((n,i)=>colors[n]=variant.colors[i]);await fixture(p,c,false,colors);await p.evaluate(()=>moonDebug.Visning.settHd(true));
    const hd=await stable(p);check(asset.key+'_'+variant.id+'_HD_approved',await p.evaluate(()=>moonDebug.Visning.hdIkonInfo().viste.length===1));
    const expected=fs.readFileSync(art+'/packed/'+(variant.id==='blue'?asset.key:'ki-palettes/'+asset.key.slice(-3)+'-'+variant.id)+'.png').toString('base64');
    const exact=await p.evaluate(async({expected,w,h})=>{const i=new Image();i.src='data:image/png;base64,'+expected;await i.decode();const c=document.createElement('canvas');c.width=w;c.height=h;c.getContext('2d').drawImage(i,0,0);let found=false;moonDebug.Visning.scene().traverse(m=>{const im=m.material?.uniforms?.map?.value?.image;if(m.visible&&im?.width===w&&im?.height===h&&im.toDataURL&&im.toDataURL()===c.toDataURL())found=true;});return found;},{expected,w:c.width*8,h:c.height*8});
    check(asset.key+'_'+variant.id+'_actual_texture_exact',exact);seen.add(hd);
    const name=asset.key.replace('/','-')+'-'+variant.id;fs.writeFileSync(out+'/'+name+'-hd.png',Buffer.from(hd.split(',')[1],'base64'));row.palette_samples.push({id:variant.id,hd_sha256:sha(Buffer.from(hd.split(',')[1],'base64'))});
   }
   check(asset.key+'_five_distinct_generated_color_images',seen.size===5);
   await fixture(p,c,false,baseColors);await stable(p);
  }
  // Endret kildebank maa avvise HD i stedet for aa fjerne originalen.
  await p.evaluate(bank=>{const K=moonDebug.Kjerne;window.remainingOriginalRead=K.hentFil;K.hentFil=n=>{const b=remainingOriginalRead(n);if(b&&n.toLowerCase()==='data/'+bank){const changed=b.slice();changed[8]^=1;return changed;}return b;};},c.source.file);
  await stable(p);check(asset.key+'_modified_source_rejected',await p.evaluate(()=>moonDebug.Visning.hdIkonInfo().viste.length===0));
  await p.evaluate(()=>{moonDebug.Kjerne.hentFil=remainingOriginalRead;});await stable(p);await p.waitForTimeout(30);await stable(p);
  check(asset.key+'_source_restores_HD',await p.evaluate(()=>moonDebug.Visning.hdIkonInfo().viste.length===1));
  // Ukjent piksel innenfor originalfeltet skal aldri slettes.
  await p.evaluate(()=>{const f=remainingIconFixture;f.lag.forIdx[(f.d.y+2)*320+f.d.x+2]=(f.lag.forIdx[(f.d.y+2)*320+f.d.x+2]+1)&31;f.lag.for.set([255,0,255,255],((f.d.y+2)*320+f.d.x+2)*4);moonDebug.Visning.nullstillScene();moonDebug.Visning.nyttBilde([f.d]);for(let i=0;i<4;i++)moonDebug.Visning.nyttBilde([]);});
  await stable(p);check(asset.key+'_unknown_foreground_rejects_HD',await p.evaluate(()=>moonDebug.Visning.hdIkonInfo().viste.length===0));
  report.assets.push(row);
 }
 check('emulated_state_unchanged',await p.evaluate(()=>moonDebug.Kjerne.sjekksum())===state);check('no_browser_errors',report.errors.length===0);report.status='passed';
})().catch(e=>{report.status='failed';report.failure=String(e);console.error(e);process.exitCode=1;}).finally(async()=>{report.created_at=new Date().toISOString();fs.mkdirSync(out,{recursive:true});fs.writeFileSync(out+'/inventory-fixtures-test.json',JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({status:report.status,assets:report.assets.length,checks:report.checks.length,errors:report.errors,failure:report.failure}));if(browser)await browser.close();});
