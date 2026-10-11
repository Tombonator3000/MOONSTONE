/* Faktisk original intro/slutt, ny programtrace og kompositt-UV.
 * Slutt bruker kontrollert seiersflagg ved oppstart. Frontendfixturene er
 * uttrykkelige lesefunksjonskopier og skriver aldri til emulert spillminne. */
'use strict';
const fs=require('fs'),path=require('path'),crypto=require('crypto'),assert=require('assert/strict');
const {chromium}=require('playwright'),root=path.resolve(__dirname,'..');
const out=process.env.MOONSTONE_VERIFY_OUT||path.join(root,'art/hd-program-support-2026-10-11/verification/runtime');
const url=process.env.MOONSTONE_URL||'http://127.0.0.1:8773/moonstone-program-proof.html';
const input={intro:process.env.MOONSTONE_INTRO_SCROLL||path.join(root,'art/hd-completion-backgrounds-2026-10-11/packed/bg/6b258d27.png'),
 ending:process.env.MOONSTONE_ENDING_SCROLL||path.join(root,'art/hd-completion-backgrounds-2026-10-11/packed/bg/0df34a83.png')};
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const report={url,scope:'Nybygd WASM, naturlig intro og kontrollert seiersgren med to HD-kompositter. Ingen full gjennomspilling. Ukjent piksel/endret kilde/bank bruker uttrykkelige frontend-lesefixturer.',checks:[],errors:[],captures:[],traces:{},sources:{},assets:{}};
for(const rel of ['web/build/moonstone-core.js','web/src/core.js','web/src/scenes.js','web/src/render.js','port/src/game.c','port/src/hooks.c','port/src/lag.c','Moonstonecd32-AMIGA.zip'])report.sources[rel]=sha(fs.readFileSync(path.join(root,rel)));
for(const[mode,file]of Object.entries(input))report.assets[mode]={file,sha256:sha(fs.readFileSync(file))};
let browser,p;
const check=(name,ok)=>{assert(ok,name);report.checks.push(name);};
async function draw(){return p.evaluate(()=>{const{Kjerne:K,Visning:V,SceneHd:S,StandardHd:H}=moonDebug;const fb=K.rammebuffer(),diw=K.vindu(),l=S.korriger(fb,diw,K.lag());V.tegn(fb,diw,l);H.oppdater(l?.hash);let mismatch=0;
 if(l)for(let y=0;y<200;y++)for(let x=0;x<320;x++){const a=(y*320+x)*4,b=((diw[1]+y)*720+diw[0]+x*2)*4,u=l.for[a+3]?l.for:l.bak;for(let k=0;k<4;k++)if(u[a+k]!==fb[b+k])mismatch++;}
 const m=V.scene().children.find(m=>m.visible&&m.material?.uniforms?.sourceRegion);
 return{png:V.bildeTilPng(),state:K.sjekksum(),scene:S.info(),layers:!!K.lag(),hash:l?.hash,uv:l?.hdUv,
  sourceRegion:m?.material.uniforms.sourceRegion.value.toArray(),texel:m?.material.uniforms.texel.value.toArray(),control:V.hdKontroll(),mismatch};});}
async function stable(){let r;for(let n=0;n<30;n++)r=await draw();return r;}
async function capture(name){const r=await stable(),b=Buffer.from(r.png.split(',')[1],'base64');fs.writeFileSync(path.join(out,name+'.png'),b);const v={...r,name,sha256:sha(b)};delete v.png;report.captures.push(v);return r;}
async function reset(mode){await p.evaluate(mode=>{const{Kjerne:K,Visning:V,SceneHd:S}=moonDebug;K.start(false);K.menyPaa(false);K.lagPaa(true);V.nullstillScene();S.nullstill();window.programProofTrace={calls:0,files:{},fields:0,ending:mode==='ending'};},mode);}
async function step(frame){await p.evaluate(async frame=>{const{Kjerne:K,Visning:V,SceneHd:S,StandardHd:H}=moonDebug,t=window.programProofTrace,M=await K.last(),v=new DataView(M.HEAPU8.buffer);
 while(K.bildeNr()<frame){if(t.ending&&K.bildeNr()<125)v.setUint16(M._ms_chip()+0x3e0,0x80,false);K.inndata(0,0);K.bilde();const ds=K.tegneliste();V.nyttBilde(ds);
  for(const d of ds){t.calls++;t.files[d.fil]=(t.files[d.fil]||0)+1;if(d.target>0&&d.caller>0)t.fields++;}
  // Tegn under fremspoling ogsaa. Ellers vil 4000 historiske bilder leveres
  // til samme tekstbuffer uten at utgaatte plasseringer kan fjernes.
  if(K.bildeNr()%20===0){const fb=K.rammebuffer(),diw=K.vindu(),l=S.korriger(fb,diw,K.lag());V.tegn(fb,diw,l);H.oppdater(l?.hash);await new Promise(r=>setTimeout(r,0));}
 }} ,frame);}
async function roundTrip(mode,frame){await step(frame);await p.evaluate(()=>moonDebug.Visning.settHd(false));const original=await capture(mode+'-'+frame+'-original');
 await p.evaluate(()=>moonDebug.Visning.settHd(true));await draw();await p.waitForTimeout(100);const hd=await capture(mode+'-'+frame+'-hd');
 check(mode+frame+'_source_scene',hd.scene?.id===mode+'-scroll');check(mode+frame+'_original_layers_reconstruct_exactly',!original.mismatch&&!hd.mismatch);
 check(mode+frame+'_HD_background',hd.control.bakgrunn==='hd');check(mode+frame+'_UV_matches_visible_offset',Math.abs(hd.sourceRegion[1]-hd.scene.offset/1200)<1e-12&&hd.sourceRegion[3]===200/1200);
 check(mode+frame+'_full_composite_texel',Math.abs(hd.texel[1]-1/1200)<1e-12);check(mode+frame+'_render_does_not_change_state',original.state===hd.state);
 check(mode+frame+'_HD_visible',original.png!==hd.png);await p.evaluate(()=>moonDebug.Visning.settHd(false));const back=await capture(mode+'-'+frame+'-original-return');check(mode+frame+'_Original_exact_return',back.png===original.png);
 await p.evaluate(()=>moonDebug.Visning.settHd(true));return hd;}
(async()=>{fs.mkdirSync(out,{recursive:true});browser=await chromium.launch({headless:true,executablePath:process.env.CHROME||'/usr/bin/google-chrome',args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 p=await browser.newPage({viewport:{width:960,height:700}});p.on('pageerror',e=>report.errors.push(e.message));await p.addInitScript(()=>localStorage.setItem('moonstone.innstillinger',JSON.stringify({hd:'hd',hdValgt:true})));
 await p.goto(url);await p.waitForFunction(()=>{try{return window.moonDebug&&moonDebug.Kjerne.bildeNr()>1;}catch(_){return false;}});await p.keyboard.press('Pause');await p.waitForFunction(()=>moonDebug.StandardHd.info().klar);
 const html=await p.request.get(url);report.html_sha256=sha(await html.body());
 const files=Object.entries(input).map(([mode,file])=>({mode,base64:fs.readFileSync(file).toString('base64')}));
 await p.evaluate(async files=>{const{Visning:V,StandardHd:H}=moonDebug;await H.stopp();V.tomHdPakke();const fs=files.map(({mode,base64})=>{const name=(mode==='intro'?'6b258d27':'0df34a83')+'.png',b=Uint8Array.from(atob(base64),c=>c.charCodeAt(0)),f=new File([b],name,{type:'image/png'});Object.defineProperty(f,'webkitRelativePath',{value:'proof/bg/'+name});return f;});await V.lastHdPakke(fs);V.settHd(true);},files);
 await reset('intro');const a=await roundTrip('intro',1800),b=await roundTrip('intro',2000);check('intro_scroll_moves',b.scene.offset>a.scene.offset+300);check('intro_visible_offset_not_future_program_y',a.scene.offset<a.scene.hint);
 report.traces.intro=await p.evaluate(()=>window.programProofTrace);check('actual_WASM_intro_observer',report.traces.intro.calls>0&&report.traces.intro.calls===report.traces.intro.fields);check('actual_WASM_program_layers',a.layers&&b.layers);
 // Ukjent, bevegelig forgrunnspiksel skal beholdes over kompositten.
 const unknown=await p.evaluate(()=>{const{Kjerne:K,SceneHd:S}=moonDebug,fb=K.rammebuffer().slice(),s=K.skanout(),idx=s.idx.slice(),d=K.vindu(),x=41,y=71,p=y*320+x,q=(d[1]+y)*720+d[0]+x*2;fb.set([240,10,190,255],q*4);idx[q]=17;const old=K.skanout;K.skanout=()=>({...s,idx});const l=S.korriger(fb,d,K.lag());K.skanout=old;return l?.for[p*4]===240&&l.for[p*4+1]===10&&l.for[p*4+2]===190&&l.forIdx[p]===17;});check('unknown_foreground_fixture_preserved',unknown);
 await p.evaluate(()=>{const K=moonDebug.Kjerne;window.programProofGetFile=K.hentFil;window.programProofRevision=K.filRevisjon;K.hentFil=n=>{const b=window.programProofGetFile(n);if(n==='data/intro.stile'&&b){const c=b.slice();c[0]^=1;return c;}return b;};K.filRevisjon=()=>window.programProofRevision()+1;});await draw();await p.waitForTimeout(100);const bad=await draw();check('modified_source_map_rejected_without_manual_cache_reset',bad.scene?.id!=='intro-scroll');
 await p.evaluate(()=>{moonDebug.Kjerne.hentFil=window.programProofGetFile;moonDebug.Kjerne.filRevisjon=window.programProofRevision;});await draw();await p.waitForTimeout(100);check('source_restored_accepts_again',(await draw()).scene?.id==='intro-scroll');
 await step(2800);report.traces.intro=await p.evaluate(()=>window.programProofTrace);check('actual_WASM_intro_figure_trace',report.traces.intro.files['dw1.cel']>100&&report.traces.intro.calls===report.traces.intro.fields);
 await reset('ending');await roundTrip('ending',2900);await roundTrip('ending',3100);await roundTrip('ending',3300);report.traces.ending=await p.evaluate(()=>window.programProofTrace);check('actual_WASM_ending_observer',report.traces.ending.files['klift1.cel']>100&&report.traces.ending.files['co1.cel']>100);check('ending_flag_active',await p.evaluate(()=>moonDebug.Kjerne.iSlutt()));
 await p.evaluate(()=>{const K=moonDebug.Kjerne;window.programProofRoll=K.programRull;K.programRull=()=>{const r=window.programProofRoll(),bank0=r.bank0.slice();bank0[0]^=1;return{...r,bank0};};});check('modified_ending_bank_rejected',(await draw()).scene?.id!=='ending-scroll');await p.evaluate(()=>moonDebug.Kjerne.programRull=window.programProofRoll);check('restored_ending_bank_accepts_again',(await draw()).scene?.id==='ending-scroll');
 // Samme nybygde programtrace skal ogsaa levere den naturlige avslutningsteksten
 // til de allerede aktiverte, originalformede fontene.
 await p.evaluate(()=>{const{Visning:V,StandardHd:H}=moonDebug;V.tomHdPakke();H.start(V,()=>{});});await p.waitForFunction(()=>moonDebug.StandardHd.info().klar);await reset('ending');await step(4000);await draw();await p.waitForTimeout(100);await draw();
 await p.waitForFunction(()=>moonDebug.StandardHd.info().bakgrunner.includes('d0f67acb'));await p.evaluate(()=>moonDebug.Visning.settHd(true));const text=await capture('ending-text-4000-hd');
 check('natural_program_ending_text_HD',text.control.tekstGodkjent>60&&text.control.tekstAvvist===0);check('static_background_resets_full_source_UV',text.sourceRegion.every((v,i)=>v===[0,0,1,1][i]));
 await p.evaluate(()=>moonDebug.Visning.settHd(false));const textOriginal=await capture('ending-text-4000-original');await p.evaluate(()=>moonDebug.Visning.settHd(true));const textBack=await capture('ending-text-4000-hd-return');
 check('natural_program_text_changes_pixels',text.png!==textOriginal.png);check('natural_program_text_HD_return_exact',text.png===textBack.png);check('natural_program_text_preserves_state',text.state===textOriginal.state&&text.state===textBack.state);
 check('no_browser_errors',!report.errors.length);report.status='passed';
})().catch(e=>{report.status='failed';report.failure=String(e);console.error(e);process.exitCode=1;}).finally(async()=>{report.created_at=new Date().toISOString();fs.writeFileSync(path.join(out,'program-roll-test.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({status:report.status,checks:report.checks.length,traces:report.traces,failure:report.failure}));if(browser)await browser.close();});
