/* Kildebasert UI-pakke i faktisk WASM-frontend, uten spillminneskriving. */
'use strict';
const fs=require('fs'),path=require('path'),assert=require('assert/strict'),crypto=require('crypto'),{chromium}=require('playwright');
const root=path.resolve(__dirname,'..'),art=path.resolve(root,process.env.MOONSTONE_UI_ART||'art/hd-ui-followup-2026-10-11'),out=path.resolve(root,process.env.MOONSTONE_HD_TEST_OUTPUT||path.relative(root,art)+'/verification/bound-runtime');
const url=process.env.MOONSTONE_URL||'http://127.0.0.1:8769/moonstone.html',sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const contracts=JSON.parse(fs.readFileSync(art+'/source-contracts.json')),fragment=JSON.parse(fs.readFileSync(art+'/fragment-icons.json'));
const packedPng=Object.fromEntries(fragment.entries.map(m=>[m.key,fs.readFileSync(art+'/packed/'+m.key+'.png')]));
const productionFiles=['web/src/render.js','web/src/scenes.js'];
const productionSources=Object.fromEntries(productionFiles.map(f=>[f,fs.readFileSync(root+'/'+f,'utf8')]));
const {render,stable}=require('./hd_resterende_ikoner_fixture.cjs');
const check=(name,value=true)=>{assert(value,name);report.checks.push(name);};
const report={url,status:'running',checks:[],assets:[],errors:[],scope:'Originale CEL-fixturer i faktisk frontend, speiling, Original/HD-retur, levende valgpalett, kildevern. Ingen naturlig gjennomspilling eller fotografisk materialgodkjenning.',fragment_icons_sha256:sha(fs.readFileSync(art+'/fragment-icons.json')),source_contracts_sha256:sha(fs.readFileSync(art+'/source-contracts.json')),packed_png_sha256:Object.fromEntries(Object.entries(packedPng).map(([k,b])=>[k,sha(b)])),production_code_sha256:Object.fromEntries(productionFiles.map(f=>[f,sha(productionSources[f])]))};
let browser;
async function fixture(p,c,mirror=false){await p.evaluate(({c,mirror})=>{
 const K=moonDebug.Kjerne,V=moonDebug.Visning,diw=[70,19,710,219],x=Math.min(148,320-c.width-4),y=Math.min(90,200-c.height);
 const idx=new Uint8Array(720*288),fb=new Uint8Array(720*288*4),pal=new Uint8Array(288*32*4),bak=new Uint8Array(256000),foran=new Uint8Array(256000),forIdx=new Uint8Array(64000);forIdx.fill(255);
 for(let i=3;i<bak.length;i+=4)bak[i]=255;for(let i=3;i<fb.length;i+=4)fb[i]=255;
 for(let row=0;row<288;row++)for(let col=0;col<32;col++)pal.set([...(c.palette[col]||[0,0,0]).slice(0,3),255],(row*32+col)*4);
 for(let j=0;j<c.height;j++)for(let i=0;i<c.width;i++){
  const col=c.indices[j*c.width+(mirror?c.width-1-i:i)];if(!col)continue;const n=(y+j)*320+x+i,s=(diw[1]+y+j)*720+diw[0]+(x+i)*2;
  forIdx[n]=col;foran.set([...c.palette[col].slice(0,3),255],n*4);idx[s]=idx[s+1]=col;fb.set([...c.palette[col].slice(0,3),255],s*4);fb.set([...c.palette[col].slice(0,3),255],(s+1)*4);
 }
 const lag={bak,for:foran,forIdx,hash:0xd2000000+c.source.frame,lys:1,lysMaks:1};K.skanout=()=>({gyldig:true,idx,pal});K.rammebuffer=()=>fb;K.vindu=()=>diw;K.lag=()=>lag;
 const d={fil:c.source.file,bilde:c.source.frame,x,y,w:c.width,h:c.height,xoff:0,speilet:mirror};window.uiFixture={c,mirror,idx,fb,pal,lag,d,diw};
 if(!window.uiCropReady){for(let i=0;i<26;i++)V.tegn(fb,diw,lag);window.uiCropReady=true;}V.nullstillScene();V.nyttBilde([d]);for(let i=0;i<4;i++)V.nyttBilde([]);
},{c,mirror});}
async function textureCenter(p,c,color){return p.evaluate(({c,color})=>{
 let found=null;moonDebug.Visning.scene().traverse(m=>{const im=m.material?.uniforms?.map?.value?.image;if(m.visible&&im?.width===c.width*8&&im?.height===c.height*8&&im.getContext){const at=c.indices.indexOf(color),x=at%c.width,y=Math.floor(at/c.width);found=Array.from(im.getContext('2d').getImageData(x*8+4,y*8+4,1,1).data);}});return found;
},{c,color});}
(async()=>{
 fs.mkdirSync(out,{recursive:true});browser=await chromium.launch({headless:true,executablePath:process.env.CHROME||'/usr/bin/google-chrome',args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});const p=await browser.newPage({viewport:{width:960,height:700}});p.on('pageerror',e=>report.errors.push(e.message));
 const servedHtml=await(await p.request.get(url)).text();report.served_html_sha256=sha(servedHtml);
 for(const f of productionFiles)check('served_production_source_'+f,servedHtml.includes(productionSources[f]));
 await p.addInitScript(()=>localStorage.setItem('moonstone.innstillinger',JSON.stringify({hd:'hd',hdValgt:true})));await p.goto(url);await p.waitForFunction(()=>{try{return window.moonDebug&&moonDebug.Kjerne.bildeNr()>1;}catch(e){return false;}});await p.keyboard.press('Pause');await p.waitForFunction(()=>moonDebug.StandardHd.info().klar,null,{timeout:60000});const state=await p.evaluate(()=>moonDebug.Kjerne.sjekksum());
 const imports=[{name:'icons.json',bytes:Buffer.from(JSON.stringify(fragment)).toString('base64')},...fragment.entries.map(m=>({name:m.key+'.png',bytes:packedPng[m.key].toString('base64')}))];
 await p.evaluate(async imports=>{await moonDebug.Visning.lastHdPakke(imports.map(i=>{const f=new File([Uint8Array.from(atob(i.bytes),c=>c.charCodeAt(0))],i.name.split('/').pop());Object.defineProperty(f,'webkitRelativePath',{value:i.name});return f;}));},imports);check('fragment_import_accepted',await p.evaluate(()=>moonDebug.Visning.hdIkonInfo().feil.length===0));
 let selected=contracts.entries;if(process.env.MOONSTONE_UI_KEYS){const keys=new Set(process.env.MOONSTONE_UI_KEYS.split(','));selected=selected.filter(c=>keys.has(c.key));check('requested_keys_found',selected.length===keys.size);}
 for(const c of selected){
  const row={key:c.key,quality_status:c.quality_status,samples:[]};
  for(const mirror of [false,true]){
   await fixture(p,c,mirror);await p.evaluate(()=>moonDebug.Visning.settHd(false));const original=await stable(p);await p.evaluate(()=>moonDebug.Visning.settHd(true));const hd=await stable(p);
   check(c.key+'_approved_'+mirror,await p.evaluate(c=>moonDebug.Visning.hdIkonInfo().viste.some(d=>d.fil===c.source.file&&d.bilde===c.source.frame),c));check(c.key+'_HD_changes_pixels_'+mirror,hd!==original);
   await p.evaluate(()=>moonDebug.Visning.settHd(false));check(c.key+'_Original_exact_'+mirror,await stable(p)===original);await p.evaluate(()=>moonDebug.Visning.settHd(true));check(c.key+'_HD_exact_'+mirror,await stable(p)===hd);
   const name=c.key.replace('/','-')+(mirror?'-mirrored':'');fs.writeFileSync(out+'/'+name+'-original.png',Buffer.from(original.split(',')[1],'base64'));fs.writeFileSync(out+'/'+name+'-hd.png',Buffer.from(hd.split(',')[1],'base64'));row.samples.push({mirror,original_sha256:sha(Buffer.from(original.split(',')[1],'base64')),hd_sha256:sha(Buffer.from(hd.split(',')[1],'base64'))});
  }
  await fixture(p,c);await stable(p);
  if(c.alternate_palettes?.length){row.palette_variants=[];for(const variant of c.alternate_palettes){
   const variantContract={...c,palette:variant.palette};await fixture(p,variantContract);await stable(p);
   check(c.key+'_palette_'+variant.id+'_approved',await p.evaluate(()=>moonDebug.Visning.hdIkonInfo().viste.length===1));const color=c.source_colors[0];
   check(c.key+'_palette_'+variant.id+'_texture_exact',JSON.stringify(await textureCenter(p,c,color))===JSON.stringify([...variant.palette[color].slice(0,3),255]));row.palette_variants.push(variant.id);
  }await fixture(p,c);await stable(p);}
  if(c.live_palette){row.pulses=[];for(let n=0;n<16;n++){
   const rgb=[n*17,((n*7)%16)*17,((n*11)%16)*17];await p.evaluate(rgb=>{const f=uiFixture;for(let y=0;y<288;y++)f.pal.set([...rgb,255],(y*32+31)*4);for(let j=0;j<f.c.height;j++)for(let i=0;i<f.c.width;i++)if(f.c.indices[j*f.c.width+i]===31){const q=(f.d.y+j)*320+f.d.x+i,s=(f.diw[1]+f.d.y+j)*720+f.diw[0]+(f.d.x+i)*2;f.lag.for.set([...rgb,255],q*4);f.fb.set([...rgb,255],s*4);f.fb.set([...rgb,255],(s+1)*4);}},rgb);await render(p);
   check(c.key+'_pulse_approved_'+n,await p.evaluate(()=>moonDebug.Visning.hdIkonInfo().viste.length===1));check(c.key+'_pulse_texture_exact_'+n,JSON.stringify(await textureCenter(p,c,31))===JSON.stringify([...rgb,255]));row.pulses.push(rgb);
  }}
  await p.evaluate(bank=>{const K=moonDebug.Kjerne;window.uiOriginalRead=K.hentFil;K.hentFil=n=>{const b=uiOriginalRead(n);if(b&&n.toLowerCase()==='data/'+bank){const a=b.slice();a[8]^=1;return a;}return b;};},c.source.file);await stable(p);check(c.key+'_changed_source_rejected',await p.evaluate(()=>moonDebug.Visning.hdIkonInfo().viste.length===0));await p.evaluate(()=>{moonDebug.Kjerne.hentFil=uiOriginalRead;});await stable(p);await p.waitForTimeout(30);await stable(p);check(c.key+'_restored_source_accepted',await p.evaluate(()=>moonDebug.Visning.hdIkonInfo().viste.length===1));
  await p.evaluate(()=>{const f=uiFixture,at=f.c.indices.findIndex(v=>v),i=at%f.c.width,j=Math.floor(at/f.c.width),q=(f.d.y+j)*320+f.d.x+i;f.lag.forIdx[q]=(f.c.indices[at]+1)&31;f.lag.for.set([255,0,255,255],q*4);moonDebug.Visning.nullstillScene();moonDebug.Visning.nyttBilde([f.d]);for(let i=0;i<4;i++)moonDebug.Visning.nyttBilde([]);});await stable(p);check(c.key+'_unknown_foreground_rejected',await p.evaluate(()=>moonDebug.Visning.hdIkonInfo().viste.length===0));report.assets.push(row);
 }
 check('emulated_state_unchanged',await p.evaluate(()=>moonDebug.Kjerne.sjekksum())===state);check('no_browser_errors',report.errors.length===0);
 for(const f of productionFiles)check('production_source_unchanged_'+f,sha(fs.readFileSync(root+'/'+f))===report.production_code_sha256[f]);
 check('fragment_metadata_unchanged',sha(fs.readFileSync(art+'/fragment-icons.json'))===report.fragment_icons_sha256);
 check('source_contracts_unchanged',sha(fs.readFileSync(art+'/source-contracts.json'))===report.source_contracts_sha256);
 for(const [key,hash]of Object.entries(report.packed_png_sha256))check('packed_png_unchanged_'+key,sha(fs.readFileSync(art+'/packed/'+key+'.png'))===hash);
 report.status='passed';
})().catch(e=>{report.status='failed';report.failure=String(e);console.error(e);process.exitCode=1;}).finally(async()=>{report.created_at=new Date().toISOString();fs.mkdirSync(out,{recursive:true});fs.writeFileSync(out+'/ui-fixtures-test.json',JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({status:report.status,assets:report.assets.length,checks:report.checks.length,errors:report.errors,failure:report.failure}));if(browser)await browser.close();});
