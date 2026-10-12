/* Faktisk WASM/GPU-frontend med originale indekslag, uten emulert minneskriving. */
'use strict';
const fs=require('fs'),path=require('path'),crypto=require('crypto'),assert=require('assert/strict'),{chromium}=require('playwright');
const art=__dirname,root=path.resolve(art,'../../../..'),host=process.env.MOONSTONE_HOST,out=process.env.MOONSTONE_OUT;
const sha=b=>crypto.createHash('sha256').update(b).digest('hex'),binding=require('./runtime-proof.cjs').bind(root,host,__filename);
const input=JSON.parse(fs.readFileSync(art+'/retention/combat-background-fixture-input.json')),row=input.entries.find(r=>r.hash==='e8ac7fc2');
const c=JSON.parse(fs.readFileSync(art+'/source-contracts.json')).entries.find(c=>c.bank==='DRAGON2.CEL'&&c.frame===5),colors=JSON.parse(fs.readFileSync(root+'/art/hd-completion-figures-2026-10-11/palettes/cases/troll.json')).colors;
const report={...binding,schema:1,status:'running',checks:[],errors:[],scope:'Standardpakken i faktisk WASM/GPU. Syntetiske kildeindekslag fra original Wa2.t, ekte Dragon2/005-kilde og originalpalett. Ingen spillminneskriving. Ikke en naturlig kampsekvens; separat original CPU-kamp kreves.'};
const check=(n,v)=>{assert(v,n);report.checks.push(n);};let browser,server,p;
async function draw(){return p.evaluate(()=>{const{Kjerne:K,SceneHd:S,StandardHd:H,Visning:V}=moonDebug,fb=K.rammebuffer(),diw=K.vindu(),lag=S.korriger(fb,diw,K.lag());V.tegn(fb,diw,lag);H.oppdater(lag?.hash);return V.bildeTilPng();});}
async function stable(){let prev=await draw();for(let i=0;i<15;i++){const a=await draw();if(i>2&&a===prev)return a;prev=a;}throw Error('Ustabil GPU-fixtur');}
(async()=>{
 fs.mkdirSync(out,{recursive:true});server=await require('./runtime-host.cjs')(host);browser=await chromium.launch({headless:true,executablePath:'/usr/bin/google-chrome',args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});p=await browser.newPage({viewport:{width:640,height:480}});p.on('pageerror',e=>report.errors.push(e.message));await p.addInitScript(()=>localStorage.setItem('moonstone.innstillinger',JSON.stringify({hd:'hd',hdValgt:true})));await p.goto(server.url);await p.waitForFunction(()=>{try{return moonDebug.Kjerne.bildeNr()>1;}catch{return false;}});await p.keyboard.press('Pause');await p.waitForFunction(()=>moonDebug.StandardHd.info().klar,null,{timeout:90000});
 const before=await p.evaluate(()=>moonDebug.Kjerne.sjekksum());
 await require(root+'/tools/hd_resterende_ikoner_fixture.cjs').fixture(p,{source:{file:c.bank.toLowerCase(),frame:c.frame},width:c.width,height:c.height,indices:c.indices},false,colors);
 await p.evaluate(({row})=>{
  const{Kjerne:K,SceneHd:S,Visning:V}=moonDebug,f=remainingIconFixture;K.iIntro=()=>false;K.iSlutt=()=>false;
  f.lag.bakIdx=Uint8Array.from(atob(row.indices_base64),c=>c.charCodeAt(0));f.lag.hash=parseInt(row.hash,16);f.lag.lysMaks=1;
  for(let y=0;y<200;y++)for(let x=0;x<320;x++){const n=y*320+x,col=f.lag.bakIdx[n],rgba=[...f.colors[col].slice(0,3),255];f.lag.bak.set(rgba,n*4);if(f.lag.forIdx[n]!==255)continue;const s=(19+y)*720+70+x*2;f.idx[s]=f.idx[s+1]=col;f.fb.set(rgba,s*4);f.fb.set(rgba,(s+1)*4);}
  f.d.target=0xa2cd6;f.d.caller=0x87bf0;S.nullstill();V.nullstillScene();V.nyttBilde([f.d]);for(let i=0;i<3;i++)V.nyttBilde([]);V.settHd(true);
 },{row});
 for(let n=0;n<100;n++){await draw();const ready=await p.evaluate(()=>moonDebug.Visning.hdKontroll().bakgrunn==='hd');if(ready)break;await p.waitForTimeout(15);}
 check('clean_original_HD_background',await p.evaluate(()=>moonDebug.Visning.hdKontroll().bakgrunn==='hd'));
 await p.waitForTimeout(30);await stable();
 const cells=await p.evaluate(()=>{const f=remainingIconFixture,cells=[];for(const opaque of [false,true]){const q=f.c.indices.findIndex(v=>opaque?v!==0:v===0),x=f.d.x+q%f.c.width,y=f.d.y+(q/f.c.width|0),p=y*320+x;cells.push({x,y,p,opaque});f.lag.bakIdx[p]=15;f.lag.bak.set([204,0,0,255],p*4);if(!opaque){const s=(19+y)*720+70+x*2;f.idx[s]=f.idx[s+1]=15;f.fb.set([204,0,0,255],s*4);f.fb.set([204,0,0,255],(s+1)*4);}}f.lag.hash=0x11112222;return cells;});
 await p.evaluate(()=>moonDebug.Visning.settHd(false));const original=await stable();await p.evaluate(()=>moonDebug.Visning.settHd(true));const hd=await stable();
 const detail=await p.evaluate(()=>({scene:moonDebug.SceneHd.info(),control:moonDebug.Visning.hdKontroll(),visible:moonDebug.Visning.hdFigurer(true)}));report.detail=detail;
 check('delta_exact_clean_identity',detail.scene?.hash==='e8ac7fc2'&&detail.scene.preserved_pixels===2);check('delta_HD_background',detail.control.bakgrunn==='hd');check('source_CEL_still_strictly_accepted',detail.visible.some(d=>d.fil.toLowerCase()==='dragon2.cel'&&d.bilde===5&&d.hd));check('HD_visible_change',hd!==original);
 for(const cell of cells){const same=await p.evaluate(async({a,b,cell})=>{async function pixels(src){const im=new Image();im.src=src;await im.decode();if(im.width!==640||im.height!==400)throw Error('Uventet visningsmaal');const cv=document.createElement('canvas');cv.width=im.width;cv.height=im.height;const ct=cv.getContext('2d');ct.drawImage(im,0,0);return Array.from(ct.getImageData(cell.x*2,cell.y*2,2,2).data);}const x=await pixels(a),y=await pixels(b);return x.every((v,i)=>v===y[i]);},{a:original,b:hd,cell});check('whole_delta_cell_preserved_'+cell.opaque,same);}
 for(const[k,v]of Object.entries({original,hd}))fs.writeFileSync(out+'/delta-'+k+'.png',Buffer.from(v.split(',')[1],'base64'));
 await p.evaluate(()=>moonDebug.Visning.settHd(false));check('Original_exact_return',await stable()===original);await p.evaluate(()=>moonDebug.Visning.settHd(true));check('HD_exact_return',await stable()===hd);
 await p.evaluate(({p})=>{remainingIconFixture.lag.bakIdx[p]=14;},cells[0]);await stable();check('one_non15_delta_falls_back',await p.evaluate(()=>moonDebug.SceneHd.info()===null&&moonDebug.Visning.hdKontroll().bakgrunn!=='hd'));
 check('emulated_state_unchanged',before===await p.evaluate(()=>moonDebug.Kjerne.sjekksum()));check('no_browser_errors',!report.errors.length);require('./runtime-proof.cjs').checkFinal(root,host,__filename,binding);report.status='passed';
})().catch(e=>{report.status='failed';report.failure=String(e);console.error(e);process.exitCode=1;}).finally(async()=>{fs.mkdirSync(out,{recursive:true});fs.writeFileSync(out+'/test.json',JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({status:report.status,checks:report.checks.length,failure:report.failure}));if(browser)await browser.close();if(server)await server.close();});
