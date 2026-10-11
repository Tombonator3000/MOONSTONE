/* Stedsbakgrunner i faktisk WASM-side. PIV-fixturer skriver ikke i spillminnet. */
'use strict';
const fs=require('fs'),path=require('path'),assert=require('assert/strict'),{chromium}=require('playwright');
const root=path.resolve(__dirname,'..'),art=root+'/art/hd-all-locations-2026-10-11',out=path.resolve(root,process.env.MOONSTONE_HD_TEST_OUTPUT||'art/hd-all-locations-2026-10-11/verification');
const url=process.env.MOONSTONE_URL||'http://127.0.0.1:8769/moonstone.html';
const assets=JSON.parse(fs.readFileSync(art+'/assets.json')).assets.filter(a=>a.kind==='place');
const report={url,checks:[],errors:[],scope:'Originale PIV-visningsfixturer i faktisk frontend, ikke naturlig navigasjon til hvert sted. Spillminnet endres ikke.'};
const check=(n,v)=>{assert(v,n);report.checks.push(n);};
let b;
async function render(p){return p.evaluate(()=>{const{Kjerne:K,Visning:V,SceneHd:S,StandardHd:H}=moonDebug;V.tegn(K.rammebuffer(),K.vindu(),S.korriger(K.rammebuffer(),K.vindu(),K.lag()));H.oppdater(V.lagNaa()?.hash);return V.bildeTilPng();});}
// Vent på tekstfont, layout og GPU-tekstur før et pikselidentisk bilde sammenlignes.
async function stable(p){let last=await render(p);for(let n=0;n<20;n++){await p.waitForTimeout(100);const next=await render(p);if(next===last)return next;last=next;}throw Error('Visningen stabiliserte seg ikke');}
(async()=>{
 fs.mkdirSync(out,{recursive:true});
 b=await chromium.launch({headless:true,executablePath:'/usr/bin/google-chrome',args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 const p=await b.newPage({viewport:{width:960,height:700}});p.on('pageerror',e=>report.errors.push(e.message));
 await p.goto(url);await p.waitForFunction(()=>window.moonDebug&&moonDebug.Kjerne.bildeNr()>1);await p.keyboard.press('Pause');
 await p.keyboard.press('Home');await p.locator('#hd-bryter').selectOption('hd');await p.keyboard.press('Home');
 await p.waitForFunction(()=>moonDebug.StandardHd.info().klar,null,{timeout:60000});
 const state=await p.evaluate(()=>moonDebug.Kjerne.sjekksum());
 const rows=await p.evaluate(()=>moonDebug.StandardHd.scener());
 for(const asset of assets){
  const row=rows.find(s=>s.id===asset.id);check(asset.id+'_registered',!!row);
  await p.evaluate(row=>{const{Kjerne:K,Visning:V,SceneHd:S}=moonDebug;
   const src=Spillgrafikk._piv(K.hentFil('data/'+row.file)),idx=new Uint8Array(720*288),fb=new Uint8Array(720*288*4),pal=new Uint8Array(288*32*4);
   for(let y=0;y<288;y++)for(let c=0;c<32;c++)pal.set([...(src.pal[c]||[0,0,0]),255],(y*32+c)*4);
   for(let y=0;y<200;y++)for(let x=0;x<320;x++){const c=src.px[y*320+x],j=(y+19)*720+70+x*2;
    idx[j]=idx[j+1]=c;fb.set([...src.pal[c],255],j*4);fb.set([...src.pal[c],255],(j+1)*4);}
   K.skanout=()=>({gyldig:true,idx,pal});K.rammebuffer=()=>fb;K.vindu=()=>[70,19,710,219];K.lag=()=>null;
   window.placeFixture={idx,fb,pal,src};V.nullstillScene();S.nullstill();V.settHd(true);
  },row);
  await render(p);await p.waitForTimeout(100);await render(p);
  check(asset.id+'_source_recognized',await p.evaluate(hash=>moonDebug.SceneHd.info()?.hash===hash,row.hash));
  await p.waitForFunction(hash=>moonDebug.StandardHd.info().bakgrunner.includes(hash),row.hash,{timeout:30000});
  // Utsnittet stabiliseres over flere tegninger ved overgang fra forrige PIV.
  for(let n=0;n<40;n++)await render(p);
  const hd=await stable(p);fs.writeFileSync(out+'/'+asset.id+'-hd.png',Buffer.from(hd.split(',')[1],'base64'));
  await p.evaluate(()=>moonDebug.Visning.settHd(false));const original=await stable(p);
  fs.writeFileSync(out+'/'+asset.id+'-original.png',Buffer.from(original.split(',')[1],'base64'));
  check(asset.id+'_hd_changes_image',hd!==original);
  await p.evaluate(()=>moonDebug.Visning.settHd(true));check(asset.id+'_hd_restored_exactly',await stable(p)===hd);
  const guards=await p.evaluate(row=>{const l=moonDebug.Visning.lagNaa(),src=placeFixture.src;let required=0,preserved=0;
   for(let y=0;y<200;y++)for(let x=0;x<320;x++)if(x<row.rect[0]||y<row.rect[1]||x>=row.rect[2]||y>=row.rect[3]||
    (row.protected_indices||[]).includes(src.px[y*320+x])||(row.protected||[]).some(r=>x>=r[0]&&y>=r[1]&&x<r[2]&&y<r[3])||
    (row.preserve_regions||[]).some(({rect:r,indices})=>x>=r[0]&&y>=r[1]&&x<r[2]&&y<r[3]&&indices.includes(src.px[y*320+x]))){
     required++;if(l.forIdx[y*320+x]===src.px[y*320+x])preserved++;}
   return{required,preserved};},row);
  check(asset.id+'_dialogue_and_animation_sockets_preserved',guards.required===guards.preserved);
  await p.evaluate(()=>{const f=placeFixture,j=(19+10)*720+70+20;f.idx[j]=(f.idx[j]+1)%32;f.fb.set([255,0,255,255],j*4);});
  await render(p);check(asset.id+'_foreground_preserved',await p.evaluate(()=>moonDebug.Visning.lagNaa().forIdx[10*320+10]!==255));
  await p.evaluate(()=>{const f=placeFixture,j=(19+10)*720+70+20,c=f.src.px[3210];f.idx[j]=c;f.fb.set([...f.src.pal[c],255],j*4);});
  const restored=await stable(p);if(restored!==hd){fs.writeFileSync(out+'/'+asset.id+'-restore-failure.png',Buffer.from(restored.split(',')[1],'base64'));report.diagnostic=await p.evaluate(()=>({scene:moonDebug.SceneHd.info(),hd:moonDebug.StandardHd.info(),crop:moonDebug.Visning.utsnitt(),state:moonDebug.Kjerne.sjekksum()}));}
  check(asset.id+'_foreground_restored_exactly',restored===hd);
  // En bevegelig hånd/figur kan dekke mer enn tre prosent av PIV-en.
  await p.evaluate(()=>{const f=placeFixture;f.savedIdx=f.idx.slice();f.savedFb=f.fb.slice();for(let y=30;y<78;y++)for(let x=100;x<164;x++){
   const j=(19+y)*720+70+x*2;f.idx[j]=f.idx[j+1]=(f.idx[j]+1)%32;f.fb.set([255,0,255,255],j*4);f.fb.set([255,0,255,255],(j+1)*4);}});
  await render(p);check(asset.id+'_large_foreground_keeps_correct_scene',await p.evaluate(hash=>moonDebug.SceneHd.info()?.hash===hash,row.hash));
  await p.evaluate(()=>{const f=placeFixture;f.idx.set(f.savedIdx);f.fb.set(f.savedFb);});
  await p.evaluate(()=>moonDebug.Visning.settHd(false));check(asset.id+'_original_restored_exactly',await stable(p)===original);
 }
 check('emulated_state_unchanged',await p.evaluate(()=>moonDebug.Kjerne.sjekksum())===state);
 check('no_page_errors',report.errors.length===0);report.status='passed';
})().catch(e=>{report.status='failed';report.failure=String(e);console.error(e);process.exitCode=1;}).finally(async()=>{
 report.created_at=new Date().toISOString();fs.writeFileSync(out+'/places-test.json',JSON.stringify(report,null,2)+'\n');
 console.log(JSON.stringify({status:report.status,checks:report.checks.length,errors:report.errors,failure:report.failure}));if(b)await b.close();
});
