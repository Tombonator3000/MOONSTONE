/* Fire nye bakgrunner: originale PIV- og bygde bakgrunnsfixturer i faktisk WASM-side. */
'use strict';
const fs=require('fs'),path=require('path'),crypto=require('crypto'),assert=require('assert/strict'),{chromium}=require('playwright');
const root=path.resolve(__dirname,'..'),art=root+'/art/hd-ui-backgrounds-2026-10-11';
const out=process.env.MOONSTONE_VERIFY_OUT||art+'/verification/backgrounds',url=process.env.MOONSTONE_URL||'http://127.0.0.1:8773/moonstone.html';
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const report={url,checks:[],assets:[],errors:[],scope:'Originale kilde-PIV og kilde-PNG som frontend-fixturer. Ingen emulert minneskriving, naturlig navigasjon eller full gjennomspilling.'};
const check=(n,v)=>{assert(v,n);report.checks.push(n);};
let browser;
async function draw(p){return p.evaluate(()=>{const{Kjerne:K,Visning:V,SceneHd:S,StandardHd:H}=moonDebug;V.tegn(K.rammebuffer(),K.vindu(),S.korriger(K.rammebuffer(),K.vindu(),K.lag()));H.oppdater(V.lagNaa()?.hash);return V.bildeTilPng();});}
async function stable(p){let last;for(let i=0;i<45;i++){const next=await draw(p);if(i>27&&next===last)return next;last=next;}return last;}
(async()=>{
 fs.mkdirSync(out,{recursive:true});browser=await chromium.launch({headless:true,executablePath:'/usr/bin/google-chrome',args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 const p=await browser.newPage({viewport:{width:960,height:700}});p.on('pageerror',e=>report.errors.push(e.message));
 await p.addInitScript(()=>localStorage.setItem('moonstone.innstillinger',JSON.stringify({hd:'hd',hdValgt:true})));await p.goto(url);await p.waitForFunction(()=>window.moonDebug&&moonDebug.Kjerne.bildeNr()>1);await p.keyboard.press('Pause');await p.waitForFunction(()=>moonDebug.StandardHd.info().klar,null,{timeout:60000});
 const state=await p.evaluate(()=>{window.newBackgroundRead=moonDebug.Kjerne.hentFil;return moonDebug.Kjerne.sjekksum();});
 const rows=[{hash:'e868fda9'},{hash:'94e65527'},{hash:'d744b02e',id:'intro-forest'},{hash:'e2e904b2',id:'intro-water'}];
 for(const row of rows){
  const png=fs.readFileSync(art+'/references/bg/'+row.hash+'.png');
  await p.evaluate(async({row,png})=>{
   const{Kjerne:K,Visning:V,SceneHd:S,StandardHd:H}=moonDebug;const s=row.id?H.scener().find(s=>s.id===row.id):null;
   let src;
   if(s)src=Spillgrafikk._piv(newBackgroundRead('data/'+s.file));
   else{const im=new Image();im.src='data:image/png;base64,'+png;await im.decode();const c=document.createElement('canvas');c.width=320;c.height=200;c.getContext('2d').drawImage(im,0,0);const rgba=c.getContext('2d').getImageData(0,0,320,200).data,pal=[[0,0,0]],px=new Uint8Array(64000);for(let i=0;i<64000;i++){const rgb=Array.from(rgba.slice(i*4,i*4+3));let n=pal.findIndex(v=>v.every((x,j)=>x===rgb[j]));if(n<0){n=pal.length;pal.push(rgb);}px[i]=n;}src={pal,px};}
   const idx=new Uint8Array(720*288),fb=new Uint8Array(720*288*4),pal=new Uint8Array(288*32*4),bak=new Uint8Array(256000),foran=new Uint8Array(256000),forIdx=new Uint8Array(64000);forIdx.fill(255);
   for(let y=0;y<288;y++)for(let c=0;c<32;c++)pal.set([...(src.pal[c]||[0,0,0]),255],(y*32+c)*4);
   for(let y=0;y<200;y++)for(let x=0;x<320;x++){const n=y*320+x,col=src.px[n],j=(y+19)*720+70+x*2,rgb=[...src.pal[col],255];idx[j]=idx[j+1]=col;fb.set(rgb,j*4);fb.set(rgb,(j+1)*4);bak.set(rgb,n*4);}
   const lag=s?null:{bak,for:foran,forIdx,hash:parseInt(row.hash,16),lys:1,lysMaks:1};
   K.skanout=()=>({gyldig:true,idx,pal});K.rammebuffer=()=>fb;K.vindu=()=>[70,19,710,219];K.lag=()=>lag;V.nullstillScene();S.nullstill();V.settHd(true);window.newBgFixture={idx,fb,pal,src,lag,row};
  },{row,png:png.toString('base64')});
  // Kildebankens SHA-kontroll er asynkron. En pauset side maa tegnes igjen
  // etter kontrollen foer scenen kan starte bakgrunnslastingen.
  for(let i=0;i<50;i++){await draw(p);if(await p.evaluate(h=>moonDebug.StandardHd.info().bakgrunner.includes(h),row.hash))break;await p.waitForTimeout(100);}
  check(row.hash+'_background_ready',await p.evaluate(h=>moonDebug.StandardHd.info().bakgrunner.includes(h),row.hash));
  const hd=await stable(p);check(row.hash+'_loaded',await p.evaluate(h=>moonDebug.Visning.harHdBilde('bg/'+h),row.hash));
  if(row.id)check(row.hash+'_trusted_source_scene',await p.evaluate(id=>moonDebug.SceneHd.info()?.id===id,row.id));
  await p.evaluate(()=>moonDebug.Visning.settHd(false));const original=await stable(p);check(row.hash+'_HD_changes_pixels',hd!==original);
  await p.evaluate(()=>moonDebug.Visning.settHd(true));check(row.hash+'_HD_restored_exactly',await stable(p)===hd);
  if(row.id)check(row.hash+'_protected_source_regions',await p.evaluate(()=>{const r=moonDebug.StandardHd.scener().find(s=>s.id===newBgFixture.row.id),l=moonDebug.Visning.lagNaa();let ok=true;for(let y=0;y<200;y++)for(let x=0;x<320;x++)if(x<r.rect[0]||y<r.rect[1]||x>=r.rect[2]||y>=r.rect[3])ok&&=l.forIdx[y*320+x]===newBgFixture.src.px[y*320+x];return ok;}));
  await p.evaluate(()=>{const f=newBgFixture,x=160,y=170,j=(19+y)*720+70+x*2;f.idx[j]=f.idx[j+1]=(f.idx[j]+1)%16;f.fb.set([255,0,255,255],j*4);f.fb.set([255,0,255,255],(j+1)*4);if(f.lag){f.lag.forIdx[y*320+x]=1;f.lag.for.set([255,0,255,255],(y*320+x)*4);}});await stable(p);
  check(row.hash+'_moving_foreground_preserved',await p.evaluate(()=>moonDebug.Visning.lagNaa().forIdx[170*320+160]!==255));
  await p.evaluate(()=>{const f=newBgFixture,x=160,y=170,j=(19+y)*720+70+x*2,col=f.src.px[y*320+x];f.idx[j]=f.idx[j+1]=col;f.fb.set([...f.src.pal[col],255],j*4);f.fb.set([...f.src.pal[col],255],(j+1)*4);if(f.lag){f.lag.forIdx[y*320+x]=255;f.lag.for.fill(0,(y*320+x)*4,(y*320+x+1)*4);}});check(row.hash+'_foreground_restored',await stable(p)===hd);
  await p.evaluate(()=>moonDebug.Visning.settHd(false));check(row.hash+'_Original_restored_exactly',await stable(p)===original);
  fs.writeFileSync(out+'/'+row.hash+'-original.png',Buffer.from(original.split(',')[1],'base64'));fs.writeFileSync(out+'/'+row.hash+'-hd.png',Buffer.from(hd.split(',')[1],'base64'));report.assets.push({...row,source_sha256:sha(png),hd_sha256:sha(hd),original_sha256:sha(original)});
 }
 check('emulated_state_unchanged',await p.evaluate(()=>moonDebug.Kjerne.sjekksum())===state);check('no_browser_errors',report.errors.length===0);report.status='passed';
})().catch(e=>{report.status='failed';report.failure=String(e);console.error(e);process.exitCode=1;}).finally(async()=>{report.created_at=new Date().toISOString();report.manifest_sha256=sha(fs.readFileSync(root+'/web/hd/manifest.json'));report.html_sha256=sha(fs.readFileSync(root+'/web/build/moonstone.html'));fs.mkdirSync(out,{recursive:true});fs.writeFileSync(out+'/backgrounds-test.json',JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({status:report.status,checks:report.checks.length,errors:report.errors,failure:report.failure}));if(browser)await browser.close();});
