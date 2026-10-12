/* Kildebundne tekst-/figurfixturer, ingen emulert minneskriving eller bildeimport. */
'use strict';
const fs=require('fs'),path=require('path'),crypto=require('crypto'),assert=require('assert/strict');
const {chromium}=require('playwright');
const root=path.resolve(__dirname,'../../..'),pkg=process.env.MOONSTONE_FONT_PACKAGE;
const out=process.env.MOONSTONE_VERIFY_OUT,url=process.env.MOONSTONE_URL;
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const queue=JSON.parse(fs.readFileSync(__dirname+'/../queue.json')).entries;
const palette=JSON.parse(fs.readFileSync(__dirname+'/../palettes/cases/balok.json')).colors;
const keys=['bold.f/039.png','Balok1.CEL/004.png'];
const fontContracts=JSON.parse(fs.readFileSync(root+'/art/hd-faithful-text-2026-10-11/source-contracts.json')).entries;
const sources=keys.map(key=>{const r=queue.find(v=>v.key===key),font=fontContracts.find(v=>v.key+'.png'===key);assert(r||font);return {key,bank:key.split('/')[0],bank_sha256:r?r.source_bank.sha256:font.source.bank_sha256,indices_sha256:r?r.indices_sha256:font.indices_sha256};});
const report={schema:1,status:'running',scope:'Kildebaserte frontendfixturer, ikke naturlige kampsekvenser. Ekte CEL og aktiv standardpakke. Ingen import, original CPU urort.',checks:[],cases:[],errors:[],html_sha256:sha(fs.readFileSync(pkg+'/moonstone.html')),render_sha256:sha(fs.readFileSync(root+'/web/src/render.js')),test_sha256:sha(fs.readFileSync(__filename)),sources};
const check=(name,ok)=>{assert(ok,name);report.checks.push(name);};
let browser;
async function capture(p,hd){return p.evaluate(hd=>{const {Kjerne:K,Visning:V}=moonDebug;V.settHd(hd);let png;for(let n=0;n<12;n++){V.tegn(K.rammebuffer(),K.vindu(),K.lag());png=V.bildeTilPng();}return {png,state:K.sjekksum(),control:V.hdKontroll(),visible:V.hdFigurer(true)};},hd);}
async function install(p,mode){await p.evaluate(({mode,palette})=>{
 const {Kjerne:K,Visning:V}=moonDebug,diw=[70,19,710,219];
 const glyph={fil:'bold.f',bilde:39,x:146,y:115,xoff:0,speilet:false};
 const body={fil:'Balok1.CEL',bilde:4,x:mode==='partial'?153:126,y:111,xoff:0,speilet:true};
 const decode=d=>{const bank=K.hentFil('data/'+d.fil.toLowerCase()),g=Spillgrafikk._cel(bank)[d.bilde],mask=bank[19+d.bilde*10],bits=[1,2,4,8,16].filter(b=>mask&b);return {...g,px:Uint8Array.from(g.px,v=>bits.reduce((n,b,i)=>n|((v&(1<<i))?b:0),0))};};
 const g=decode(glyph),b=decode(body);Object.assign(glyph,{w:g.w,h:g.h});Object.assign(body,{w:b.w,h:b.h});
 const list=mode==='glyph'?[glyph]:mode==='body'?[body]:mode==='reverse'?[body,glyph]:[glyph,body];
 const actual=mode==='stale'?[body]:list;
 const idx=new Uint8Array(720*288),fb=new Uint8Array(720*288*4),pal=new Uint8Array(288*32*4),bak=new Uint8Array(256000),foran=new Uint8Array(256000),forIdx=new Uint8Array(64000).fill(255),bakIdx=new Uint8Array(64000);
 for(let p=3;p<fb.length;p+=4)fb[p]=255;for(let p=3;p<bak.length;p+=4)bak[p]=255;
 for(let y=0;y<288;y++)for(let c=0;c<32;c++)pal.set([...palette[c],255],(y*32+c)*4);
 for(const d of actual){const g=d===glyph?decode(glyph):decode(body);for(let j=0;j<d.h;j++)for(let i=0;i<d.w;i++){const c=g.px[j*d.w+(d.speilet?d.w-1-i:i)];if(!c)continue;const p=(d.y+j)*320+d.x+i,s=(diw[1]+d.y+j)*720+diw[0]+(d.x+i)*2,rgba=[...palette[c],255];forIdx[p]=c;foran.set(rgba,p*4);idx[s]=idx[s+1]=c;fb.set(rgba,s*4);fb.set(rgba,(s+1)*4);}}
 const lag={bak,for:foran,forIdx,bakIdx,hash:0xd3110000,lys:1,lysMaks:1};
 K.skanout=()=>({gyldig:true,idx,pal});K.rammebuffer=()=>fb;K.vindu=()=>diw;K.lag=()=>lag;
 window.textOwnerFixture={list,glyph,body,g,b,lag,idx,fb,pal,diw};
 for(let n=0;n<26;n++)V.tegn(fb,diw,lag);V.nullstillScene();V.nyttBilde(list);for(let n=0;n<4;n++)V.nyttBilde([]);
},{mode,palette});}
async function cycle(p,name){const original=await capture(p,false),hd=await capture(p,true),originalAgain=await capture(p,false),hdAgain=await capture(p,true);check(name+'_Original_eksakt',original.png===originalAgain.png);check(name+'_HD_eksakt',hd.png===hdAgain.png);check(name+'_CPU_urort',[hd,originalAgain,hdAgain].every(v=>v.state===original.state));const row={name,original_sha256:sha(Buffer.from(original.png.split(',')[1],'base64')),hd_sha256:sha(Buffer.from(hd.png.split(',')[1],'base64')),control:hd.control,visible:hd.visible};report.cases.push(row);return {original,hd,row};}
function glyphCount(v){return v.visible.filter(d=>d.fil.toLowerCase()==='bold.f'&&d.hd).length;}
function bodyCount(v){return v.visible.filter(d=>d.fil.toLowerCase()==='balok1.cel'&&d.hd).length;}
(async()=>{
 assert(!fs.existsSync(out),'Bevar forrige prove');fs.mkdirSync(out,{recursive:true});
 browser=await chromium.launch({headless:true,executablePath:'/usr/bin/google-chrome',args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 const p=await browser.newPage({viewport:{width:960,height:700}});p.on('pageerror',e=>report.errors.push(e.message));
 await p.addInitScript(()=>localStorage.setItem('moonstone.innstillinger',JSON.stringify({hd:'hd',hdValgt:true})));
 const response=await p.goto(url),html=await response.body();check('faktisk_HTML_SHA',sha(html)===report.html_sha256);check('faktisk_renderkode',html.toString().includes(fs.readFileSync(root+'/web/src/render.js','utf8')));
 await p.waitForFunction(()=>{try{return moonDebug.Kjerne.bildeNr()>1;}catch{return false;}},null,{timeout:120000});await p.keyboard.press('Pause');await p.waitForFunction(()=>moonDebug.StandardHd.info().klar,null,{timeout:120000});
 await p.evaluate(()=>{moonDebug.StandardHd.oppdater=()=>{};window.textOwnerOriginalRead=moonDebug.Kjerne.hentFil;});
 const hashes=await p.evaluate(async sources=>{const digest=async b=>[...new Uint8Array(await crypto.subtle.digest('SHA-256',b))].map(v=>v.toString(16).padStart(2,'0')).join('');const result=[];for(const r of sources){const file=r.key.split('/')[0],n=parseInt(r.key.split('/')[1]),bank=moonDebug.Kjerne.hentFil('data/'+file.toLowerCase()),g=Spillgrafikk._cel(bank)[n],bits=[1,2,4,8,16].filter(b=>bank[19+n*10]&b),ix=Uint8Array.from(g.px,v=>bits.reduce((x,b,i)=>x|((v&(1<<i))?b:0),0));result.push({bank:await digest(bank),indices:await digest(ix)});}return result;},sources);
 for(let n=0;n<sources.length;n++){check(sources[n].key+'_bank_SHA',hashes[n].bank===sources[n].bank_sha256);check(sources[n].key+'_indeks_SHA',hashes[n].indices===sources[n].indices_sha256);}
 await install(p,'glyph');const glyph=await cycle(p,'ekte_glyf');check('ekte_glyf_HD',glyphCount(glyph.hd)===1&&glyph.hd.png!==glyph.original.png);
 await install(p,'body');const body=await cycle(p,'ren_figur');check('ren_figur_HD',bodyCount(body.hd)===1);
 await install(p,'stale');const stale=await cycle(p,'foreldet_glyf');check('foreldet_glyf_avvist',glyphCount(stale.hd)===0&&stale.hd.control.tekstGodkjent===0);check('foreldet_glyf_endrer_ikke_foto',stale.hd.png===body.hd.png);check('foreldet_glyf_endrer_ikke_Original',stale.original.png===body.original.png);
 await install(p,'partial');const partial=await cycle(p,'delvis_dekket_ekte_tekst');check('delvis_ekte_tekst_HD',glyphCount(partial.hd)===1);check('delvis_figur_HD',bodyCount(partial.hd)===1);
 const protectedPixels=await p.evaluate(()=>{const f=textOwnerFixture,V=moonDebug.Visning;let vern;V.scene().traverse(o=>{if(o.visible&&o.material?.uniforms?.map?.value?.image?.width===f.b.w*4)vern=o.material.uniforms.vern?.value?.image?.data;});let count=0,blocked=0;for(let j=0;j<f.body.h;j++)for(let i=0;i<f.body.w;i++){const x=f.body.x+i,y=f.body.y+j,c=f.b.px[j*f.body.w+f.body.w-1-i];if(!c||x<f.glyph.x||x>=f.glyph.x+f.glyph.w||y<f.glyph.y||y>=f.glyph.y+f.glyph.h)continue;count++;blocked+=!!vern?.[(y*320+x)*4+3];}return {count,blocked};});report.partial_figure_vern=protectedPixels;check('delvis_HD_figur_uten_tekstklippefelt',protectedPixels.count>0&&protectedPixels.blocked===0);
 await install(p,'partial');await p.evaluate(()=>{const f=textOwnerFixture;for(let j=0;j<f.body.h;j++)for(let i=0;i<f.body.w;i++){const x=f.body.x+i,y=f.body.y+j,c=f.b.px[j*f.body.w+f.body.w-1-i];if(c&&(x>=f.glyph.x+f.glyph.w||y>=f.glyph.y+f.glyph.h)){const z=y*320+x;f.lag.forIdx[z]=31;f.lag.for.set([255,0,255,255],z*4);return;}}throw Error('Mangler egen negativ figurcelle');});const rejectedBody=await cycle(p,'delvis_tekst_med_avvist_HD_figur');check('delvis_tekst_fortsatt_HD',glyphCount(rejectedBody.hd)===1);check('avvist_delvis_figur_Original',bodyCount(rejectedBody.hd)===0);
 const retained=await p.evaluate(()=>{const f=textOwnerFixture;let vern;moonDebug.Visning.scene().traverse(o=>{if(o.visible&&o.material?.uniforms?.map?.value?.image?.width===f.g.w*8)vern=o.material.uniforms.vern?.value?.image?.data;});let count=0,protectedCount=0;for(let j=0;j<f.body.h;j++)for(let i=0;i<f.body.w;i++){const x=f.body.x+i,y=f.body.y+j,c=f.b.px[j*f.body.w+f.body.w-1-i];if(!c||x<f.glyph.x||x>=f.glyph.x+f.glyph.w||y<f.glyph.y||y>=f.glyph.y+f.glyph.h)continue;count++;protectedCount+=!!vern?.[(y*320+x)*4+3];}return {count,protectedCount};});report.rejected_partial_figure_vern=retained;check('avvist_delvis_figur_beholder_Originalvern',retained.count>0&&retained.count===retained.protectedCount);
 await install(p,'reverse');const reverse=await cycle(p,'ekte_tekst_foran_figur');check('senere_ekte_tekst_HD',glyphCount(reverse.hd)===1);check('senere_figur_HD',bodyCount(reverse.hd)===1);
 await install(p,'glyph');await p.evaluate(()=>{const f=textOwnerFixture,n=f.g.px.findIndex(v=>v),x=f.glyph.x+n%f.g.w,y=f.glyph.y+(n/f.g.w|0),z=y*320+x;f.lag.forIdx[z]=31;f.lag.for.set([255,0,255,255],z*4);});const unknown=await cycle(p,'ukjent_opak_tekstcelle');check('ukjent_opak_tekstcelle_avvist',glyphCount(unknown.hd)===0);check('ukjent_opak_tekstcelle_Original',unknown.hd.png===unknown.original.png);
 await install(p,'glyph');await p.evaluate(()=>{const f=textOwnerFixture,V=moonDebug.Visning;V.nullstillScene();V.nyttBilde([...f.list,{...f.glyph,fil:'ukjent.cel',bilde:0}]);for(let n=0;n<4;n++)V.nyttBilde([]);});const unknownSource=await cycle(p,'ukjent_figurkilde');check('ukjent_figurkilde_tekst_avvist',glyphCount(unknownSource.hd)===0);check('ukjent_figurkilde_Original',unknownSource.hd.png===unknownSource.original.png);
 await install(p,'glyph');await p.evaluate(()=>{const K=moonDebug.Kjerne;K.hentFil=n=>{const b=textOwnerOriginalRead(n);if(b&&n.toLowerCase()==='data/bold.f'){const x=b.slice();x[8]^=1;return x;}return b;};});const changed=await cycle(p,'endret_fontbank');check('endret_fontbank_avvist',glyphCount(changed.hd)===0);await p.evaluate(()=>moonDebug.Kjerne.hentFil=textOwnerOriginalRead);await capture(p,true);await p.waitForTimeout(50);check('gjenopprettet_fontbank_HD',glyphCount(await capture(p,true))===1);
 await install(p,'body');await p.evaluate(()=>{const K=moonDebug.Kjerne;K.hentFil=n=>n.toLowerCase()==='data/balok1.cel'?null:textOwnerOriginalRead(n);});const missing=await cycle(p,'manglende_figurkilde');check('manglende_figurkilde_avvist',bodyCount(missing.hd)===0);check('manglende_figurkilde_Original',missing.hd.png===missing.original.png);await p.evaluate(()=>moonDebug.Kjerne.hentFil=textOwnerOriginalRead);
 check('ingen_nettleserfeil',report.errors.length===0);check('renderkode_urort_under_test',sha(fs.readFileSync(root+'/web/src/render.js'))===report.render_sha256);report.status='passed';
})().catch(e=>{report.status='failed';report.failure=String(e);console.error(e);process.exitCode=1;}).finally(async()=>{report.created_at=new Date().toISOString();fs.mkdirSync(out,{recursive:true});fs.writeFileSync(out+'/text-owner-fixtures.json',JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({status:report.status,checks:report.checks.length,cases:report.cases.length,failure:report.failure}));if(browser)await browser.close();});
