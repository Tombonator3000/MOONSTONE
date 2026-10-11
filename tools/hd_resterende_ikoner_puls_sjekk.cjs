/* Originalens pulserende MI009-kant foran en kildebasert rasterprobe.
 * Proben er originalgrafikk, ikke en fotografisk eller produksjonsklar hjelm. */
'use strict';
const fs=require('fs'),path=require('path'),assert=require('assert/strict'),crypto=require('crypto'),{chromium}=require('playwright');
const root=path.resolve(__dirname,'..'),dir=root+'/art/hd-remaining-icons-2026-10-11/research/runtime';
const out=path.resolve(root,process.env.MOONSTONE_HD_TEST_OUTPUT||'art/hd-remaining-icons-2026-10-11/research/runtime/pulse-verification');
const url=process.env.MOONSTONE_URL||'http://127.0.0.1:8769/moonstone.html';
const contracts=JSON.parse(fs.readFileSync(dir+'/source-contracts.json')),contract=contracts.entries.find(c=>c.key==='mi.c/009');
const art=root+'/art/hd-remaining-icons-2026-10-11',actualArt=process.env.MOONSTONE_PULSE_ART==='1';
const probe=actualArt?{schema:1,entries:JSON.parse(fs.readFileSync(art+'/candidate-icons.json')).entries.filter(m=>m.key==='mi.c/009')}:JSON.parse(fs.readFileSync(dir+'/mi009-preserved-probe-icons.json'));
assert.equal(probe.entries.length,1);
const report={url,checks:[],pulses:[],errors:[],candidate_icons_sha256:actualArt?crypto.createHash('sha256').update(fs.readFileSync(art+'/candidate-icons.json')).digest('hex'):null,scope:actualArt?'Gjennomgaatt generert MI009-kropp med original19ytterkant og31pulskant i faktisk frontend og isolert SceneHd. Ingen spillminneskriving.':'Original MI009-CEL som rasterprobe med original kropp og vernet31kant. Ingen nytt kunstmotiv eller produksjonsmetadata. Faktisk frontend og isolert SceneHd kontrolleres; ingen spillminneskriving.'};
report.art=actualArt?'Gjennomgaatt generert hjelm-body master':'Original rasterprobe';
const check=(n,v=true)=>{assert(v,n);report.checks.push(n);};let browser;
async function render(p){return p.evaluate(()=>{const K=moonDebug.Kjerne,V=moonDebug.Visning;V.tegn(K.rammebuffer(),K.vindu(),K.lag());return V.hdIkonInfo();});}
(async()=>{
 fs.mkdirSync(out,{recursive:true});browser=await chromium.launch({headless:true,executablePath:'/usr/bin/google-chrome',args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 const p=await browser.newPage({viewport:{width:960,height:700}});p.on('pageerror',e=>report.errors.push(e.message));
 await p.addInitScript(()=>localStorage.setItem('moonstone.innstillinger',JSON.stringify({hd:'hd',hdValgt:true})));
 await p.goto(url);await p.waitForFunction(()=>window.moonDebug&&moonDebug.Kjerne.bildeNr()>1);await p.keyboard.press('Pause');await p.waitForFunction(()=>moonDebug.StandardHd.info().klar,null,{timeout:60000});
 const state=await p.evaluate(()=>moonDebug.Kjerne.sjekksum());
 await p.evaluate(async({json,png})=>{const file=(name,bytes)=>{const f=new File([Uint8Array.from(atob(bytes),c=>c.charCodeAt(0))],name.split('/').pop());Object.defineProperty(f,'webkitRelativePath',{value:name});return f;};await moonDebug.Visning.lastHdPakke([file('icons.json',json),file('mi.c/009.png',png)]);},{json:Buffer.from(JSON.stringify(probe)).toString('base64'),png:fs.readFileSync(actualArt?art+'/packed/mi.c/009.png':dir+'/mi009-preserved-probe.png').toString('base64')});
 check('probe_import_accepted',await p.evaluate(()=>moonDebug.Visning.hdIkonInfo().feil.length===0));
 await p.evaluate(({c,colors,bevar})=>{
  const K=moonDebug.Kjerne,V=moonDebug.Visning,x=148,y=90,diw=[70,19,710,219],idx=new Uint8Array(720*288),fb=new Uint8Array(720*288*4),pal=new Uint8Array(288*32*4),bak=new Uint8Array(256000),foran=new Uint8Array(256000),forIdx=new Uint8Array(64000);forIdx.fill(255);
  for(let i=3;i<bak.length;i+=4)bak[i]=255;for(let i=3;i<fb.length;i+=4)fb[i]=255;
  for(let row=0;row<288;row++)for(let col=0;col<32;col++)pal.set([...colors[col].slice(0,3),255],(row*32+col)*4);
  for(let j=0;j<c.height;j++)for(let i=0;i<c.width;i++){const col=c.indices[j*c.width+i];if(!col)continue;const n=(y+j)*320+x+i,screen=(diw[1]+y+j)*720+diw[0]+(x+i)*2;forIdx[n]=col;foran.set([...colors[col].slice(0,3),255],n*4);idx[screen]=idx[screen+1]=col;fb.set([...colors[col].slice(0,3),255],screen*4);fb.set([...colors[col].slice(0,3),255],(screen+1)*4);}
  const lag={bak,for:foran,forIdx,hash:0xd1000009,lys:1,lysMaks:1};K.skanout=()=>({gyldig:true,idx,pal});K.rammebuffer=()=>fb;K.vindu=()=>diw;K.lag=()=>lag;
  window.pulseFixture={c,colors,x,y,diw,idx,fb,pal,lag,bevar};V.nullstillScene();V.nyttBilde([{fil:'mi.c',bilde:9,x,y,w:c.width,h:c.height,xoff:0,speilet:false}]);for(let i=0;i<4;i++)V.nyttBilde([]);
 },{c:contract,colors:contracts.palettes.map.palette,bevar:probe.entries[0].preserve_indices});
 for(let i=0;i<40;i++)await render(p);
 for(let n=0;n<32;n++){
  const rgb=[((n*7)%16)*17,((n*11)%16)*17,((n*13)%16)*17];
  await p.evaluate(rgb=>{const f=pulseFixture;for(let y=0;y<288;y++)f.pal.set([...rgb,255],(y*32+31)*4);for(let j=0;j<f.c.height;j++)for(let i=0;i<f.c.width;i++)if(f.c.indices[j*f.c.width+i]===31){const p=(f.y+j)*320+f.x+i,s=(f.diw[1]+f.y+j)*720+f.diw[0]+(f.x+i)*2;f.lag.for.set([...rgb,255],p*4);f.fb.set([...rgb,255],s*4);f.fb.set([...rgb,255],(s+1)*4);}},rgb);
  const info=await render(p);check('MI009_stays_raster_pulse_'+n,info.viste.some(d=>d.fil==='mi.c'&&d.bilde===9));
  const pixels=await p.evaluate(()=>{const V=moonDebug.Visning,f=pulseFixture,front=V.scene().children.find(m=>m.renderOrder===3).material.uniforms.map.value.image.data;let kept=0,body=0;for(let j=0;j<f.c.height;j++)for(let i=0;i<f.c.width;i++){const c=f.c.indices[j*f.c.width+i],p=(f.y+j)*320+f.x+i;if(c===31){if([0,1,2,3].every(k=>front[p*4+k]===f.lag.for[p*4+k]))kept++;}else if(c&&!f.bevar.includes(c)&&front[p*4+3]===0)body++;}return{kept,body};});
  check('original_pulse_pixels_kept_'+n,pixels.kept===contract.indices.filter(c=>c===31).length);check('body_replaced_'+n,pixels.body===contract.indices.filter(c=>c&&!probe.entries[0].preserve_indices.includes(c)).length);report.pulses.push({rgb,...pixels});
 }
 // Samme kildeindeks, men feil kroppsfarge skal fortsatt avvise rasteren.
 await p.evaluate(()=>{const f=pulseFixture;for(let y=0;y<288;y++)f.pal[(y*32+24)*4]^=85;});await render(p);check('unknown_body_palette_rejected',await p.evaluate(()=>moonDebug.Visning.hdIkonInfo().viste.length===0));
 // Kjor den virkelige SceneHd-modulen med en eksplisitt kartfixture og rasterprobe.
 const scenes=fs.readFileSync(root+'/web/src/scenes.js','utf8');
 const sceneResult=await p.evaluate(async({scenes,c,meta})=>{
  const realK=moonDebug.Kjerne,row=moonDebug.StandardHd.scener().find(s=>s.id==='world-map');
  const bytes=realK.hentFil('data/'+row.file);let pos=0;for(let n=0;n<row.frame;n++){const b=bytes[pos]*256+bytes[pos+1],size=((bytes[pos+2]<<24)|(bytes[pos+3]<<16)|(bytes[pos+4]<<8)|bytes[pos+5])>>>0;pos+=6+(1<<b)*2+size;}
  const source=Spillgrafikk._piv(bytes.subarray(pos)),diw=[70,19,710,219],x=120,y=80,idx=new Uint8Array(720*288),fb=new Uint8Array(720*288*4),pal=new Uint8Array(288*32*4);
  for(let yy=0;yy<288;yy++)for(let col=0;col<32;col++)pal.set([...(source.pal[col]||[0,0,0]),255],(yy*32+col)*4);
  for(let yy=0;yy<200;yy++)for(let xx=0;xx<320;xx++){const col=source.px[yy*320+xx],p=(diw[1]+yy)*720+diw[0]+xx*2;idx[p]=idx[p+1]=col;fb.set([...source.pal[col],255],p*4);fb.set([...source.pal[col],255],(p+1)*4);}
  for(let j=0;j<c.height;j++)for(let i=0;i<c.width;i++){const col=c.indices[j*c.width+i],p=(diw[1]+y+j)*720+diw[0]+(x+i)*2;idx[p]=idx[p+1]=col;fb.set([...source.pal[col],255],p*4);fb.set([...source.pal[col],255],(p+1)*4);}
  const m={...meta,scene:'world-map',rect:[x,y,x+c.width,y+c.height],dynamic:true,expected:c.indices,source:{...meta.source,bank_sha256:row.source_sha256}};
  const K={hentFil:realK.hentFil,skanout:()=>({gyldig:true,idx,pal})},H={info:()=>({aktiv:true,klar:true,bakgrunner:[row.hash]}),scener:()=>[{...row,overlays:[]}]},V={hdPaa:()=>true,sceneIkoner:()=>[m],sceneIkonKlar:()=>true,sceneOverleggKlar:()=>true};
  const S=new Function('Kjerne','StandardHd','Visning','Spillgrafikk',scenes+';return SceneHd;')(K,H,V,Spillgrafikk);
  S.korriger(fb,diw,null);await new Promise(r=>setTimeout(r,50));const l=S.korriger(fb,diw,null);let kept=0,body=0;
  for(let j=0;j<c.height;j++)for(let i=0;i<c.width;i++){const col=c.indices[j*c.width+i],p=(y+j)*320+x+i;if(col===31&&l.forIdx[p]===31&&l.sceneVern[p]===1)kept++;if(!meta.preserve_indices.includes(col)&&l.forIdx[p]===255)body++;}
  const accepted=S.info()?.hd_icons;const changed=c.indices.findIndex(v=>v!==0),p=(diw[1]+y+Math.floor(changed/c.width))*720+diw[0]+(x+changed%c.width)*2;idx[p]=idx[p+1]=(c.indices[changed]+1)&31;const bad=S.korriger(fb,diw,null);return{accepted,kept,body,bad_rejected:S.info()?.hd_icons===0};
 },{scenes,c:contract,meta:probe.entries[0]});
 report.scene=sceneResult;check('SceneHd_accepts_exact_marker',sceneResult.accepted===1);check('SceneHd_preserves_pulse_mask',sceneResult.kept===contract.indices.filter(c=>c===31).length);check('SceneHd_clears_only_unprotected_marker',sceneResult.body===contract.indices.filter(c=>!probe.entries[0].preserve_indices.includes(c)).length);check('SceneHd_rejects_unknown_marker',sceneResult.bad_rejected);
 // Manifestvalideringen avviser ukjente, dupliserte og tomme vern.
 for(const invalid of [[32],[31,31],[],[1,2,3,19,24,31]]){
  const bad={...probe,entries:probe.entries.map(m=>({...m,preserve_indices:invalid}))};
  await p.evaluate(async bad=>{await moonDebug.Visning.lastHdPakke([new File([JSON.stringify(bad)],'icons.json')]);},bad);
  check('invalid_preserve_indices_rejected_'+invalid.join(','),await p.evaluate(()=>moonDebug.Visning.hdIkonInfo().feil.includes('Ugyldig ikonindeksvern')));
 }
 check('emulated_state_unchanged',await p.evaluate(()=>moonDebug.Kjerne.sjekksum())===state);check('no_browser_errors',report.errors.length===0);report.status='passed';
})().catch(e=>{report.status='failed';report.failure=String(e);console.error(e);process.exitCode=1;}).finally(async()=>{report.created_at=new Date().toISOString();fs.mkdirSync(out,{recursive:true});fs.writeFileSync(out+'/pulse-test.json',JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({status:report.status,checks:report.checks.length,errors:report.errors,failure:report.failure}));if(browser)await browser.close();});
