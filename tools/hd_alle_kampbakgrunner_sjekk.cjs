/* Alle 56 terrengvarianter velges av originalkoden i faktisk WASM.
 * Kontrollerte terreng/teller/filpekere brukes bare i denne testen. */
'use strict';
const fs=require('fs'),path=require('path'),assert=require('assert/strict'),crypto=require('crypto'),{chromium}=require('playwright');
const root=path.resolve(__dirname,'..'),art=root+'/art/hd-all-locations-2026-10-11',out=path.resolve(root,process.env.MOONSTONE_HD_TEST_OUTPUT||'art/hd-all-locations-2026-10-11/verification/combat');
const url=process.env.MOONSTONE_URL||'http://127.0.0.1:8769/moonstone.html';
const refs=JSON.parse(fs.readFileSync(art+'/references/combat-runtime.json')).scenes;
const files=JSON.parse(fs.readFileSync(root+'/web/hd/manifest.json')).files;
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const report={url,scenes:[],errors:[],scope:'Faktisk originalt scenevalg i WASM ved bilde 1200 med kontrollerte terreng/teller/filpekere, ikke naturlig besøk til alle steder. HD hentes gjennom standardpakkens vanlige rute.'};
let b;
async function draw(p){return p.evaluate(()=>{const{Kjerne:K,Visning:V,StandardHd:H,SceneHd:S}=moonDebug;V.tegn(K.rammebuffer(),K.vindu(),S.korriger(K.rammebuffer(),K.vindu(),K.lag()));H.oppdater(K.lag()?.hash);return V.bildeTilPng();});}
(async()=>{
 fs.mkdirSync(out,{recursive:true});assert.equal(refs.length,56);
 b=await chromium.launch({headless:true,executablePath:process.env.CHROME||'/usr/bin/google-chrome',args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 const p=await b.newPage({viewport:{width:960,height:700}});p.on('pageerror',e=>report.errors.push(e.message));
 await p.addInitScript(()=>localStorage.setItem('moonstone.innstillinger',JSON.stringify({hd:'hd',hdValgt:true})));
 await p.goto(url);await p.waitForFunction(()=>window.moonDebug&&moonDebug.Kjerne.bildeNr()>1);await p.keyboard.press('Pause');
 await p.waitForFunction(()=>moonDebug.StandardHd.info().klar,null,{timeout:60000});
 const selected=refs.filter(r=>!process.env.SCENE||process.env.SCENE.split(',').some(n=>r.source==='data/'+n));
 assert(selected.length>0,'Minst én kampvariant skal velges');
 for(const ref of selected){
  const name=ref.source.split('/').pop(),route='bg/'+ref.background_hash+'.png',file=files.find(f=>f.path===route);
  assert(file,name+': registrert HD-rute');const png=fs.readFileSync(root+'/art/photoreal/references/runtime_background/'+name+'.png');assert.equal(sha(png),ref.png_sha256);
  const loading=await p.evaluate(async({ref,reference})=>{
   const{Kjerne:K,Visning:V,SceneHd:S}=moonDebug,M=await K.last();K.start(false);K.menyPaa(false);K.lagPaa(true);V.nullstillScene();S.nullstill();V.settHd(false);V.settTvungetLag(true);V.settFilter('skarp');
   const digest=async bytes=>[...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))].map(b=>b.toString(16).padStart(2,'0')).join('');
   const accessed=new Set();K.brukteFiler();let applied=null;
   while(K.bildeNr()<1200){const n=K.bildeNr();if(n===100)K.tast(0x45,true);if(n===104)K.tast(0x45,false);
    K.inndata(0,((n>=700&&n<704)||(n>=760&&n<764))?2:(n>=820&&n<824)?16:0);
    if(n===ref.selection.selection_frame){const s=ref.selection,d=new DataView(M.HEAPU8.buffer),chip=M._ms_chip();
     const write=(a,v,n)=>n===1?d.setUint8(chip+parseInt(a),v):n===2?d.setUint16(chip+parseInt(a),v,false):d.setUint32(chip+parseInt(a),v,false);
     write(s.terrain_address,s.terrain,4);write(s.mode_address,s.mode,4);
     if(s.lair)write(s.filename_pointer_address,parseInt(s.filename_pointer),4);else write(s.counter_address,s.counter,s.counter_bytes);
     applied={frame:n,terrain:s.terrain,mode:s.mode};}
    K.bilde();V.nyttBilde(K.tegneliste());for(const f of K.brukteFiler())accessed.add(f);
    if(n%100===0)await new Promise(r=>setTimeout(r,0));
   }
   K.lagBygg();for(let n=0;n<40;n++)V.tegn(K.rammebuffer(),K.vindu(),K.lag());
   const im=await createImageBitmap(new Blob([Uint8Array.from(atob(reference),c=>c.charCodeAt(0))],{type:'image/png'})),cv=document.createElement('canvas');cv.width=im.width;cv.height=im.height;cv.getContext('2d').drawImage(im,0,0);im.close();
   return{applied,accessed:[...accessed],source_sha256:await digest(K.hentFil(ref.source)),hash:K.lag().hash.toString(16).padStart(8,'0'),original_rgba:await digest(K.lag().bak),reference_rgba:await digest(cv.getContext('2d').getImageData(0,0,cv.width,cv.height).data)};
  },{ref,reference:png.toString('base64')});
  assert.equal(loading.hash,ref.background_hash,name+': faktisk originalhash');assert.equal(loading.source_sha256,ref.source_sha256);assert.equal(loading.original_rgba,loading.reference_rgba);
  assert(loading.accessed.some(f=>f.toLowerCase()===ref.source.toLowerCase()),name+': originalfil lastet');
  const state=await p.evaluate(()=>({hash:moonDebug.Kjerne.sjekksum(),frame:moonDebug.Kjerne.bildeNr()}));
  const original=await draw(p);await p.evaluate(()=>moonDebug.Visning.settHd(true));await draw(p);
  await p.waitForFunction(hash=>moonDebug.StandardHd.info().bakgrunner.includes(hash),ref.background_hash,{timeout:30000});
  const hd=await draw(p);
  const texture=await p.evaluate(async route=>{const V=moonDebug.Visning;const active=V.scene().children.find(o=>o.visible&&o.material?.uniforms?.map?.value?.image?.width>320),im=active?.material.uniforms.map.value.image;if(!im)throw Error('HD-teksturen vises ikke');
   const digest=async bytes=>[...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))].map(b=>b.toString(16).padStart(2,'0')).join('');
   const b=await fetch('hd/'+route).then(r=>r.blob()),bm=await createImageBitmap(b),c=document.createElement('canvas');c.width=bm.width;c.height=bm.height;c.getContext('2d').drawImage(bm,0,0);bm.close();
   return{size:[im.width,im.height],actual:await digest(im.getContext('2d').getImageData(0,0,im.width,im.height).data),expected:await digest(c.getContext('2d').getImageData(0,0,c.width,c.height).data)};
  },route);
  await p.evaluate(()=>moonDebug.Visning.settHd(false));const restored=await draw(p);
  assert(restored===original,name+': Original gjenopprettet');assert.notEqual(hd,original,name+': HD endrer bildet');assert.equal(texture.actual,texture.expected,name+': riktig aktiv GPU-tekstur');
  assert.deepEqual(await p.evaluate(()=>({hash:moonDebug.Kjerne.sjekksum(),frame:moonDebug.Kjerne.bildeNr()})),state,name+': HD endrer ikke spilltilstanden');
  for(const[mode,data]of[['original',original],['hd',hd]])fs.writeFileSync(out+'/'+name+'-'+mode+'.png',Buffer.from(data.split(',')[1],'base64'));
  report.scenes.push({source:ref.source,route,source_sha256:loading.source_sha256,hd_sha256:file.sha256,original_rgba:loading.original_rgba,selection:ref.selection,texture,state,restored:true,status:'passed'});
  console.log(name+' bestått ('+report.scenes.length+'/'+refs.length+')');
 }
 assert.equal(report.scenes.length,selected.length);assert.equal(report.errors.length,0);report.status='passed';
})().catch(e=>{report.status='failed';report.failure=String(e);console.error(e);process.exitCode=1;}).finally(async()=>{report.created_at=new Date().toISOString();fs.writeFileSync(out+'/combat-test'+(process.env.SCENE?'-'+process.env.SCENE:'')+'.json',JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({status:report.status,scenes:report.scenes.length,errors:report.errors,failure:report.failure}));if(b)await b.close();});
