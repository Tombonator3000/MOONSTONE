/* Nytegnede motiver og stedsoeyler i faktisk karttur; kildesikring og forgrunn. */
'use strict';
const fs=require('fs'),path=require('path'),assert=require('assert/strict'),{chromium}=require('playwright');
const root=path.resolve(__dirname,'..'),out=root+'/art/faithful-hd-icons-2026-10-11/verification';
const url=process.env.MOONSTONE_URL||'http://127.0.0.1:8769/moonstone.html';
const metas=JSON.parse(fs.readFileSync(root+'/web/hd/icons.json')).entries.filter(m=>m.render_mode==='raster');
const report={url,checks:[],errors:[],scope:'Naturlig karttur, faktisk teksturtegning, originalfallback og uendret spilltilstand.'};
const check=(n,ok)=>{assert(ok,n);report.checks.push(n);};
let b;
async function render(p){return p.evaluate(()=>{const{Kjerne:K,Visning:V,SceneHd:S,StandardHd:H}=moonDebug;const fb=K.rammebuffer(),d=K.vindu();V.tegn(fb,d,S.korriger(fb,d,K.lag()));H.oppdater(V.lagNaa()?.hash);return V.bildeTilPng();});}
(async()=>{
 fs.mkdirSync(out,{recursive:true});
 b=await chromium.launch({headless:true,executablePath:'/usr/bin/google-chrome',args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 const p=await b.newPage({viewport:{width:960,height:700}});p.on('pageerror',e=>report.errors.push(e.message));
 await p.addInitScript(()=>localStorage.setItem('moonstone.innstillinger',JSON.stringify({hd:'hd',hdValgt:true})));
 await p.goto(url);await p.waitForFunction(()=>window.moonDebug&&moonDebug.Kjerne.bildeNr()>1);await p.keyboard.press('Pause');
 await p.waitForFunction(()=>moonDebug.StandardHd.info().klar,null,{timeout:60000});
 await p.evaluate(async()=>{const{Kjerne:K,Visning:V,SceneHd:S}=moonDebug;K.start(false);K.menyPaa(true);K.lagPaa(true);V.nullstillScene();S.nullstill();V.settHd(true);
  while(K.bildeNr()<2000){const n=K.bildeNr();if(n===100)K.tast(0x45,true);if(n===104)K.tast(0x45,false);
   const down=[700,760,820].some(f=>n>=f&&n<f+4),fire=[880,1100,1200].some(f=>n>=f&&n<f+4);K.inndata(0,down?2:fire?16:0);K.bilde();V.nyttBilde(K.tegneliste());
   if(n%20===0){const fb=K.rammebuffer();V.tegn(fb,K.vindu(),S.korriger(fb,K.vindu(),K.lag()));await new Promise(r=>setTimeout(r,0));}}
 });
 await render(p);await p.waitForFunction(()=>moonDebug.StandardHd.info().bakgrunner.includes('2c1e0fa5'));await p.waitForTimeout(100);
 const full=await render(p),state=await p.evaluate(()=>moonDebug.Kjerne.sjekksum());
 fs.writeFileSync(out+'/corrected-map-hd.png',Buffer.from(full.split(',')[1],'base64'));
 for(const m of metas){
  check(m.key+'_overlay_present',await p.evaluate(key=>moonDebug.Visning.lagNaa().overlays.some(o=>o.key===key),m.key));
  await p.evaluate(key=>moonDebug.Visning.fjernHdBilde(key),m.key);const without=await render(p);
  const diff=await p.evaluate(async({full,without})=>{const read=async src=>{const im=new Image();im.src=src;await im.decode();const c=document.createElement('canvas');c.width=im.width;c.height=im.height;c.getContext('2d').drawImage(im,0,0);return c.getContext('2d').getImageData(0,0,c.width,c.height).data;};
   const a=await read(full),z=await read(without);let n=0;for(let i=0;i<a.length;i+=4)if(a[i]!==z[i]||a[i+1]!==z[i+1]||a[i+2]!==z[i+2])n++;return n;},{full,without});
  check(m.key+'_actually_drawn',diff>50);
  const png=fs.readFileSync(root+'/web/hd/'+m.key+'.png').toString('base64');
  await p.evaluate(async({m,png})=>{const bytes=Uint8Array.from(atob(png),c=>c.charCodeAt(0));await moonDebug.Visning.lastHdPakke([
   new File([bytes],m.key+'.png'),new File([JSON.stringify({schema:1,entries:[m]})],'icons.json')]);},{m,png});
  check(m.key+'_restored',await render(p)===full);
 }
 const m=metas.find(m=>m.key==='map-landmarks/002');
 await p.evaluate(m=>{const K=moonDebug.Kjerne;window.landmarkScan=K.skanout;const s=K.skanout(),pal=s.pal.slice(),c=+Object.keys(m.reference_palette).find(c=>!(m.reference_palette_cycles||[]).flat().includes(+c)&&m.reference_palette[c].some(v=>v>50));
  for(let y=0;y<288;y++)pal[(y*32+c)*4]=(pal[(y*32+c)*4]+85)%256;K.skanout=()=>({...s,pal});},m);
 await render(p);
 const fallback=await p.evaluate(m=>{const lag=moonDebug.Visning.lagNaa(),s=moonDebug.Kjerne.skanout(),d=moonDebug.Kjerne.vindu();let n=0;
  for(let y=m.rect[1];y<m.rect[3];y++)for(let x=m.rect[0];x<m.rect[2];x++)if(lag.forIdx[y*320+x]===s.idx[(d[1]+y)*720+d[0]+x*2])n++;
  return{pixels:n,overlay:lag.overlays.some(o=>o.key===m.key)};},m);
 check('unsupported_palette_keeps_full_original_region',fallback.pixels===m.width*m.height&&!fallback.overlay);
 await p.evaluate(()=>{moonDebug.Kjerne.skanout=landmarkScan;delete window.landmarkScan;});check('palette_restore_exact',await render(p)===full);
 const pillar=metas.find(m=>m.key==='map-icons/018');
 if(pillar){
  const overlays=await p.evaluate(()=>moonDebug.Visning.lagNaa().overlays);
  check('23_standing_stones_present',metas.filter(m=>m.draw_rect).every(m=>overlays.some(o=>o.key===m.key&&o.rect.join()===m.draw_rect.join())));
  // Statusendring i den gamle markoeren skal bevare originalen og skjule soeylen.
  await p.evaluate(m=>{const K=moonDebug.Kjerne;window.pillarScan=K.skanout;const s=K.skanout(),idx=s.idx.slice(),d=K.vindu();
   const p=(d[1]+m.rect[1])*720+d[0]+m.rect[0]*2;idx[p]=(idx[p]+1)%32;K.skanout=()=>({...s,idx});},pillar);
  await render(p);check('changed_marker_keeps_original',await p.evaluate(m=>{const l=moonDebug.Visning.lagNaa(),d=moonDebug.Kjerne.vindu(),s=moonDebug.Kjerne.skanout();
   return !l.overlays.some(o=>o.key===m.key)&&l.forIdx[m.rect[1]*320+m.rect[0]]===s.idx[(d[1]+m.rect[1])*720+d[0]+m.rect[0]*2];},pillar));
  await p.evaluate(()=>{moonDebug.Kjerne.skanout=pillarScan;delete window.pillarScan;});check('marker_restore_exact',await render(p)===full);
  // En figur over kilderektangelet maa ikke skjules av den hoeyere HD-soeylen.
  const point=[pillar.draw_rect[0]+2,pillar.draw_rect[1]+3];
  await p.evaluate(([x,y])=>{const K=moonDebug.Kjerne;window.pillarScan=K.skanout;const s=K.skanout(),idx=s.idx.slice(),d=K.vindu(),p=(d[1]+y)*720+d[0]+x*2;
   idx[p]=(idx[p]+1)%32;K.skanout=()=>({...s,idx});},point);
  await render(p);check('foreground_above_marker_is_protected',await p.evaluate(({key,point:[x,y]})=>{const l=moonDebug.Visning.lagNaa();
   return l.overlays.some(o=>o.key===key)&&l.sceneVern[y*320+x]===1&&l.forIdx[y*320+x]!==255;},{key:pillar.key,point}));
  await p.evaluate(()=>{moonDebug.Kjerne.skanout=pillarScan;delete window.pillarScan;});check('foreground_restore_exact',await render(p)===full);
 }
 check('emulated_state_unchanged',await p.evaluate(()=>moonDebug.Kjerne.sjekksum())===state);
 check('no_page_errors',report.errors.length===0);report.status='passed';
})().catch(e=>{report.status='failed';report.failure=String(e);console.error(e);process.exitCode=1;}).finally(async()=>{report.created_at=new Date().toISOString();fs.writeFileSync(out+'/landmarks-test.json',JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report));if(b)await b.close();});
