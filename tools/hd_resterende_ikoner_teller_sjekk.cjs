/* Kroens nye sekk maa ligge under HD-tallene, uansett opprettelsesrekkefolge.
 * Original PIV og font brukes som frontend-fixture. Ingen spillminneskriving. */
'use strict';
const fs=require('fs'),path=require('path'),assert=require('assert/strict'),crypto=require('crypto'),{chromium}=require('playwright');
const root=path.resolve(__dirname,'..'),art=root+'/art/hd-remaining-icons-2026-10-11';
const out=path.resolve(root,process.env.MOONSTONE_HD_TEST_OUTPUT||'art/hd-remaining-icons-2026-10-11/research/runtime/counter-verification');
const url=process.env.MOONSTONE_URL||'http://127.0.0.1:8769/moonstone.html';
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const report={url,checks:[],samples:[],errors:[],scope:'Original tav.piv og Small.font/061 som tellerfixture. To HD-glyfer ved originalens (282,14). Begge opprettelsesrekkefolger, lagrekkefolge, Original/HD-retur og uendret emulator kontrolleres.'};
const check=(name,value=true)=>{assert(value,name);report.checks.push(name);};
let browser;
async function sample(order,meta,png){
 const p=await browser.newPage({viewport:{width:960,height:700}});p.on('pageerror',e=>report.errors.push(e.message));
 try{
  await p.addInitScript(()=>localStorage.setItem('moonstone.innstillinger',JSON.stringify({hd:'hd',hdValgt:true,sprak:'no'})));
  await p.goto(url);await p.waitForFunction(()=>window.moonDebug&&moonDebug.Kjerne.bildeNr()>1);await p.keyboard.press('Pause');
  await p.waitForFunction(()=>moonDebug.StandardHd.info().klar,null,{timeout:60000});
  const state=await p.evaluate(()=>moonDebug.Kjerne.sjekksum());
  await p.evaluate(async({meta,png})=>{const f=new File([Uint8Array.from(atob(png),c=>c.charCodeAt(0))],'000.png');Object.defineProperty(f,'webkitRelativePath',{value:'scene-icons/000.png'});await moonDebug.Visning.lastHdPakke([new File([JSON.stringify({schema:1,entries:[meta]})],'icons.json'),f]);},{meta,png});
  check(order+'_counter_import_accepted',await p.evaluate(()=>moonDebug.Visning.hdIkonInfo().feil.length===0));
  const row=await p.evaluate(async order=>{
   const {Kjerne:K,Visning:V,SceneHd:S,StandardHd:H}=moonDebug,scene=H.scener().find(s=>s.id==='tavern');
   const src=Spillgrafikk._piv(K.hentFil('data/tav.piv')),glyph=Spillgrafikk._cel(K.hentFil('data/small.font'))[61],diw=[70,19,710,219];
   const idx=new Uint8Array(720*288),fb=new Uint8Array(720*288*4),pal=new Uint8Array(288*32*4);
   for(let y=0;y<288;y++)for(let c=0;c<32;c++)pal.set([...(src.pal[c]||[0,0,0]),255],(y*32+c)*4);
   for(let y=0;y<200;y++)for(let x=0;x<320;x++){
    const c=src.px[y*320+x],q=(y+19)*720+70+x*2;idx[q]=idx[q+1]=c;
    fb.set([...src.pal[c],255],q*4);fb.set([...src.pal[c],255],(q+1)*4);
   }
   const ds=[];
   for(const x of [282,287]){
    ds.push({fil:'small.font',bilde:61,x,y:14,w:glyph.w,h:glyph.h,xoff:0,speilet:false});
    for(let y=0;y<glyph.h;y++)for(let i=0;i<glyph.w;i++){
     const c=glyph.px[y*glyph.w+i];if(!c)continue;const q=(14+y+19)*720+70+(x+i)*2;
     idx[q]=idx[q+1]=c;fb.set([...src.pal[c],255],q*4);fb.set([...src.pal[c],255],(q+1)*4);
    }
   }
   K.skanout=()=>({gyldig:true,idx,pal});K.rammebuffer=()=>fb;K.vindu=()=>diw;K.lag=()=>null;
   const addText=()=>{V.nullstillScene();V.nyttBilde(ds);for(let i=0;i<4;i++)V.nyttBilde([]);};
   if(order==='text-first'){
    // Originale indekslag oppretter tekstflatene foer kroens faste overlegg.
    const front=new Uint8Array(256000),back=new Uint8Array(256000),frontIdx=new Uint8Array(64000);
    for(let y=0;y<200;y++)for(let x=0;x<320;x++){
     const q=y*320+x,t=(y+19)*720+70+x*2;frontIdx[q]=idx[t];front.set(fb.subarray(t*4,t*4+4),q*4);back.set([...src.pal[src.px[q]],255],q*4);
    }
    const layer={hash:0xdeadbeef,for:front,bak:back,forIdx:frontIdx,bakIdx:src.px,scene:'tavern'};
    addText();for(let i=0;i<5;i++){V.tegn(fb,diw,layer);await new Promise(r=>setTimeout(r,30));}
   }
   V.nullstillScene();S.nullstill();
   const render=()=>{V.tegn(fb,diw,S.korriger(fb,diw,null));H.oppdater(V.lagNaa()?.hash);return V.bildeTilPng();};
   // Tom tegneliste gir scene-first-tilfellet ekte, tidligere sceneoverlegg.
   for(let i=0;i<10;i++){render();await new Promise(r=>setTimeout(r,30));}
   const until=Date.now()+30000;while(!H.info().bakgrunner.includes(scene.hash)&&Date.now()<until){render();await new Promise(r=>setTimeout(r,30));}
   if(!H.info().bakgrunner.includes(scene.hash))throw new Error('Kroens HD-bakgrunn mangler');
   addText();for(let i=0;i<30;i++)render();
   const control=V.hdKontroll(),layer=V.lagNaa(),meshes=[];
   V.scene().traverse(m=>{const im=m.material?.uniforms?.map?.value?.image;if(m.visible&&im?.toDataURL)meshes.push(m);});
   const counter=meshes.find(m=>m.material.uniforms.map.value.image.width===304&&m.material.uniforms.map.value.image.height===200);
   const text=meshes.filter(m=>m.renderOrder===4&&m.material.uniforms.map.value.image.width===30&&m.material.uniforms.map.value.image.height===36);
   if(!counter||text.length!==2)throw new Error('Teller eller to HD-glyfer mangler');
   let protectedPixels=0,overdrawnTexels=0,unprotectedInkTexels=0;
   for(let y=12;y<24;y++)for(let x=281;x<302;x++)if(layer.sceneVern[y*320+x])protectedPixels++;
   const ci=counter.material.uniforms.map.value.image,ca=ci.getContext('2d').getImageData(0,0,ci.width,ci.height).data;
   for(const [number,m] of text.slice().sort((a,b)=>a.position.x-b.position.x).entries()){
    const im=m.material.uniforms.map.value.image,a=im.getContext('2d').getImageData(0,0,im.width,im.height).data;
    // Fixtureposisjoner i spillet er faste; viewportens crop kan endres under testen.
    const x0=282+number*5,y0=14;
    for(let y=0;y<im.height;y++)for(let x=0;x<im.width;x++){
     const wx=x0+(x+.5)/6,wy=y0+(y+.5)/6,cx=Math.floor((wx-272)*8),cy=Math.floor((wy-4)*8);
     if(a[(y*im.width+x)*4+3]<=128||layer.sceneVern[Math.floor(wy)*320+Math.floor(wx)]||cx<0||cy<0||cx>=ci.width||cy>=ci.height||ca[(cy*ci.width+cx)*4+3]<=128)continue;
     unprotectedInkTexels++;
     if(counter.renderOrder>m.renderOrder||counter.renderOrder===m.renderOrder&&counter.id>m.id)overdrawnTexels++;
    }
   }
   const desc=m=>({id:m.id,renderOrder:m.renderOrder});
   const hd=render();V.settHd(false);for(let i=0;i<4;i++)render();const original=render();V.settHd(true);for(let i=0;i<4;i++)render();const hdRestored=render();V.settHd(false);for(let i=0;i<4;i++)render();const originalRestored=render();
   return {scene:S.info(),control,counter:desc(counter),text:text.map(desc),protectedPixels,unprotectedInkTexels,overdrawnTexels,hd,original,hdRestored,originalRestored};
  },order);
  check(order+'_two_HD_digits',row.control.tekstGodkjent===2&&row.control.tekstAvvist===0);
  check(order+'_counter_below_HD_text',row.text.every(m=>row.counter.renderOrder<m.renderOrder));
  check(order+'_requested_creation_order',row.text.every(m=>order==='text-first'?m.id<row.counter.id:m.id>row.counter.id));
  check(order+'_HD_edges_outside_original_mask_tested',row.unprotectedInkTexels>0);
  check(order+'_no_HD_text_overdraw',row.overdrawnTexels===0);
  check(order+'_Original_roundtrip_exact',row.original===row.originalRestored);
  check(order+'_HD_roundtrip_exact',row.hd===row.hdRestored);
  check(order+'_HD_changes_pixels',row.hd!==row.original);
  check(order+'_emulated_state_unchanged',await p.evaluate(()=>moonDebug.Kjerne.sjekksum())===state);
  for(const name of ['hd','original']){const bytes=Buffer.from(row[name].split(',')[1],'base64');fs.writeFileSync(out+'/'+order+'-'+name+'.png',bytes);row[name+'_sha256']=sha(bytes);}
  delete row.hd;delete row.original;delete row.hdRestored;delete row.originalRestored;report.samples.push({order,...row});
 }finally{await p.close();}
}
(async()=>{
 fs.mkdirSync(out,{recursive:true});const candidate=fs.readFileSync(art+'/candidate-icons.json'),meta=JSON.parse(candidate).entries.find(m=>m.key==='scene-icons/000');check('candidate_counter_found',!!meta&&meta.render_mode==='raster');
 report.candidate_icons_sha256=sha(candidate);report.html_sha256=sha(fs.readFileSync(root+'/web/build/moonstone.html'));
 browser=await chromium.launch({headless:true,executablePath:process.env.CHROME||'/usr/bin/google-chrome',args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 const png=fs.readFileSync(art+'/packed/scene-icons/000.png').toString('base64');for(const order of ['text-first','scene-first'])await sample(order,meta,png);
 check('no_browser_errors',report.errors.length===0);report.status='passed';
})().catch(e=>{report.status='failed';report.failure=String(e);console.error(e);process.exitCode=1;}).finally(async()=>{
 report.created_at=new Date().toISOString();fs.mkdirSync(out,{recursive:true});fs.writeFileSync(out+'/counter-test.json',JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({status:report.status,checks:report.checks.length,errors:report.errors,failure:report.failure}));if(browser)await browser.close();
});
