/* Avgrenset faktisk Ratmen063-proeve. Importerer bare kildekontrollerte kamp-
 * bilder, ikke hele HD-pakken. Original CPU tegner tre instanser i Practice.
 * MOONSTONE_BUILD velger fryst HTML. MOONSTONE_FOLIAGE_AUDIT_ONLY=1 registrerer
 * den gamle palettfeilen uten aa kalle den en bestaaende negativ kontroll.
 */
'use strict';
const fs=require('fs'),path=require('path'),crypto=require('crypto'),assert=require('assert/strict');
const {chromium}=require('playwright'),sharp=require('sharp');
const root=path.resolve(__dirname,'..'),art=root+'/art/hd-ratmen-foliage-2026-10-12';
const out=process.env.MOONSTONE_VERIFY_OUT||art+'/verification';
const key='RATMEN1.CEL/063.png',sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const report={scope:'Original CPU Practice med dokumenterte Ratmen-/terrengpekere. Ingen naturlig kartreise paastaas. Bare selektiv standardpakke og kandidat063 importeres. Samme CPU-tilstand brukes i alle bilde-/palett-/kildeproever.',checks:[],captures:[],errors:[]};
let browser,host;
function check(name,ok){assert(ok,name);report.checks.push(name);console.log('OK '+name);}
async function put(p,name,data){await p.evaluate(async({name,data})=>{const f=new File([Uint8Array.from(atob(data),c=>c.charCodeAt(0))],name);Object.defineProperty(f,'webkitRelativePath',{value:name});await moonDebug.Visning.lastHdPakke([f]);},{name,data:data.toString('base64')});}
async function capture(p,name,hd=true){
 const r=await p.evaluate(async hd=>{
  const{Kjerne:K,Visning:V,SceneHd:S}=moonDebug;V.settHd(hd);
  for(let n=0;n<5;n++){V.tegn(K.rammebuffer(),K.vindu(),S.korriger(K.rammebuffer(),K.vindu(),K.lag()));await new Promise(r=>setTimeout(r,0));}
  const scan=K.skanout(),diw=K.vindu(),palette={};
  for(const c of [5,22,24,25,28])palette[c]=Array.from(scan.pal.subarray(((diw[1]+30)*32+c)*4,((diw[1]+30)*32+c)*4+3));
  const saved_sha256=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',K.lagreTilstand())),b=>b.toString(16).padStart(2,'0')).join('');
  const lag=S.korriger(K.rammebuffer(),K.vindu(),K.lag());V.tegn(K.rammebuffer(),K.vindu(),lag);
  return{png:V.bildeTilPng(),frame:K.bildeNr(),state:K.sjekksum(),saved_sha256,palette,scene:S.info(),control:V.hdKontroll(),figures:V.hdFigurer(true).filter(d=>d.fil.toLowerCase()==='ratmen1.cel'&&d.bilde===63),raw_background:(K.lag().hash>>>0).toString(16),geometry:{vindu:Array.from(diw),utsnitt:V.utsnitt()}};
 },hd);
 const png=Buffer.from(r.png.split(',')[1],'base64');delete r.png;r.png_sha256=sha(png);r.path=name+'.png';fs.writeFileSync(out+'/'+r.path,png);report.captures.push(r);return r;
}
async function step(p,terrain,end){
 return p.evaluate(async({terrain,end})=>{
  const{Kjerne:K,Visning:V,SceneHd:S}=moonDebug,M=await K.last();
  K.start(false);K.menyPaa(false);K.lagPaa(true);V.nullstillScene();S.nullstill();V.settHd(true);
  const observed=[];
  while(K.bildeNr()<end){const n=K.bildeNr();
   if(n===100)K.tast(0x45,true);if(n===104)K.tast(0x45,false);
   K.inndata(0,((n>=700&&n<704)||(n>=760&&n<764)?2:0)|(n>=820&&n<824?16:0)|(n>=1200&&n<1320?4:0));
   const d=new DataView(M.HEAPU8.buffer),chip=M._ms_chip();
   if(n===900)for(const[a,v]of[[0x80172,0x8440a],[0x8d9ac,0x8d5b4],[0x8015c,0xc]])d.setUint32(chip+a,v,false);
   if(n===907&&terrain==='gll3')for(const[a,v]of[[0x95f12,0],[0x8fb4e,2],[0x8fb52,0x9005e]])d.setUint32(chip+a,v,false);
   K.bilde();const list=K.tegneliste();for(const d of list)if(d.fil.toLowerCase()==='ratmen1.cel'&&d.bilde===63&&observed.length<6)observed.push({frame:K.bildeNr(),...d});V.nyttBilde(list);
   if((n>=1100&&n%4===0)||n%20===0)V.tegn(K.rammebuffer(),K.vindu(),S.korriger(K.rammebuffer(),K.vindu(),K.lag()));
   if(n%20===0)await new Promise(r=>setTimeout(r,0));
  }
  return{frame:K.bildeNr(),observed,stopped:K.stoppet()};
 },{terrain,end});
}
async function pixelDiff(a,b){
 const [x,y]=await Promise.all([sharp(a).resize(320,200,{fit:'fill'}).removeAlpha().raw().toBuffer(),sharp(b).resize(320,200,{fit:'fill'}).removeAlpha().raw().toBuffer()]);
 const regions=[[137,20,155,55],[155,23,173,58],[173,16,217,51]];return regions.map(([x0,y0,x1,y1])=>{let n=0;for(let j=y0;j<y1;j++)for(let i=x0;i<x1;i++){const p=(j*320+i)*3;if(x[p]!==y[p]||x[p+1]!==y[p+1]||x[p+2]!==y[p+2])n++;}return n;});
}
(async()=>{
 fs.mkdirSync(out,{recursive:true});
 const manifestBytes=fs.readFileSync(root+'/web/hd/manifest.json'),manifest=JSON.parse(manifestBytes),candidate=fs.readFileSync(art+'/packed/'+key),old=fs.readFileSync(art+'/source/previous-active063.png'),v2=fs.readFileSync(art+'/source/candidate-v2.png');
 report.manifest_sha256=sha(manifestBytes);report.candidate_sha256=sha(candidate);report.previous_sha256=sha(old);
 const entries=manifest.files.filter(e=>/^(ratmen[12]\.cel\/|kn1\.ob\/0(?:0[0-9]|1[0-5])(?:\.mask)?\.png$|kn4\.ob\/001\.png$|bg\/(e8ac7fc2|6113f65e)\.png$)/i.test(e.path));
 let assets=entries.map(e=>{const b=fs.readFileSync(root+'/web/hd/'+e.path);assert(e.bytes===b.length&&e.sha256===sha(b),e.path);return{name:e.path,data:(e.path===key?candidate:b).toString('base64')};});
 report.selective_files=entries.length;report.selective_bytes=entries.reduce((n,e)=>n+e.bytes,0);
 if(!process.env.MOONSTONE_URL)host=await require('../art/hd-completion-figures-2026-10-11/figures/kn3-production/runtime-host.cjs')(process.env.MOONSTONE_BUILD||root+'/web/build');
 report.url=process.env.MOONSTONE_URL||host.url;
 if(process.env.MOONSTONE_URL){
  const read=async name=>{const response=await fetch(new URL('hd/'+name,report.url));assert(response.ok,'HTTP '+name);return Buffer.from(await response.arrayBuffer());};
  report.served_manifest_sha256=sha(await read('manifest.json'));assert.equal(report.served_manifest_sha256,report.manifest_sha256,'Offentlig manifest maa vaere den lokale fryste pakken');
  assets=[];for(const e of entries){const b=await read(e.path);assert(e.bytes===b.length&&sha(b)===e.sha256,'Offentlig SHA '+e.path);if(e.path===key)assert.equal(sha(b),sha(candidate),'Den aktiverte kandidaten maa faktisk serveres');assets.push({name:e.path,data:b.toString('base64')});}
  report.served_assets_verified=assets.length;
 }
 browser=await chromium.launch({headless:true,executablePath:process.env.CHROME||'/usr/bin/google-chrome',args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 const p=await browser.newPage({viewport:{width:1280,height:900}});p.on('pageerror',e=>report.errors.push(e.message));
 await p.addInitScript(()=>localStorage.setItem('moonstone.innstillinger',JSON.stringify({hd:'original',hdValgt:true})));
 const response=await p.goto(report.url);report.html_sha256=sha(await response.body());
 await p.waitForFunction(()=>{try{return window.moonDebug&&moonDebug.Kjerne.bildeNr()>1;}catch(_){return false;}},null,{timeout:60000});await p.keyboard.press('Pause');
 await p.evaluate(async assets=>{const{Visning:V,StandardHd:H}=moonDebug;await H.stopp();V.tomHdPakke();await V.lastHdPakke(assets.map(a=>{const f=new File([Uint8Array.from(atob(a.data),c=>c.charCodeAt(0))],a.name);Object.defineProperty(f,'webkitRelativePath',{value:a.name});return f;}));V.settTvungetLag(true);V.settHd(true);},assets);
 check('selective_candidate_imported',await p.evaluate(()=>moonDebug.Visning.harHdBilde('ratmen1.cel/063')));
 for(const terrain of ['wa2','gll3']){
  report[terrain+'_journey']=await step(p,terrain,1400);
  check(terrain+'_three_original_CPU_placements',new Set(report[terrain+'_journey'].observed.map(d=>[d.x,d.y].join(','))).size===3&&!report[terrain+'_journey'].stopped);
  const hd=await capture(p,terrain+'-candidate-hd'),original=await capture(p,terrain+'-original',false),restored=await capture(p,terrain+'-candidate-hd-return');
  check(terrain+'_rendering_preserves_full_saved_state',hd.state===original.state&&hd.saved_sha256===original.saved_sha256&&hd.saved_sha256===restored.saved_sha256);
  check(terrain+'_HD_original_HD_roundtrip',hd.png_sha256===restored.png_sha256&&hd.png_sha256!==original.png_sha256);
  check(terrain+'_HD_background_visible',hd.control.bakgrunn==='hd');
  if(terrain==='wa2'){
   check('Wa2_three_source_validated_HD_canopies',hd.figures.length>=3&&hd.figures.every(d=>d.hd&&d.w===44&&d.h===35)&&[[137,20],[155,23],[173,16]].every(([x,y])=>hd.figures.some(d=>d.x===x&&d.y===y)));
   await put(p,key,old);const previous=await capture(p,'wa2-previous-hd');
   await put(p,key,v2);await capture(p,'wa2-candidate-v2-shadow');
   await put(p,key,candidate);const again=await capture(p,'wa2-candidate-restored');
   check('candidate_actually_replaces_old_material',previous.png_sha256!==again.png_sha256&&again.png_sha256===hd.png_sha256);
   report.exclusive_visible_region_changed_pixels=await pixelDiff(out+'/'+previous.path,out+'/'+again.path);
   check('all_three_instances_show_new_photographic_material',report.exclusive_visible_region_changed_pixels.every(n=>n>30));
   // Bare frontend-kilden gjores utilgjengelig. Original CPU/minne er urort.
   await p.evaluate(()=>{const K=moonDebug.Kjerne;window.foliageFile=K.hentFil;window.foliageRevision=K.filRevisjon;K.hentFil=name=>name.toLowerCase()==='data/ratmen1.cel'?null:foliageFile(name);K.filRevisjon=()=>foliageRevision()+1;});
   const missing=await capture(p,'wa2-source-missing');
   check('missing_original_bank_rejects_foliage_HD',missing.figures.length>=3&&missing.figures.every(d=>!d.hd));
   await p.evaluate(()=>{moonDebug.Kjerne.hentFil=foliageFile;moonDebug.Kjerne.filRevisjon=foliageRevision;});
   const sourceRestored=await capture(p,'wa2-source-restored');
   check('restored_original_bank_restores_exact_HD',sourceRestored.figures.every(d=>d.hd)&&sourceRestored.png_sha256===hd.png_sha256);
   check('source_negative_preserves_full_saved_state',sourceRestored.saved_sha256===hd.saved_sha256&&missing.saved_sha256===hd.saved_sha256);
   if(process.env.MOONSTONE_FOLIAGE_AUDIT_ONLY!=='1'){
    await p.evaluate(()=>{const K=moonDebug.Kjerne,b=K.hentFil('data/ratmen1.cel').slice();b[b.length-1]^=1;window.foliageChangedBank=b;K.hentFil=name=>name.toLowerCase()==='data/ratmen1.cel'?foliageChangedBank:foliageFile(name);K.filRevisjon=()=>foliageRevision()+2;});
    const changed=await capture(p,'wa2-source-changed');
    check('modified_original_bank_SHA_rejects_foliage_HD',changed.figures.length>=3&&changed.figures.every(d=>!d.hd)&&changed.control.foliageAvvist>=3);
    await p.evaluate(()=>{moonDebug.Kjerne.hentFil=foliageFile;moonDebug.Kjerne.filRevisjon=foliageRevision;});
    const changedRestore=await capture(p,'wa2-changed-source-restored');
    check('changed_bank_restore_is_exact_and_CPU_unchanged',changedRestore.png_sha256===hd.png_sha256&&changed.saved_sha256===hd.saved_sha256&&changedRestore.saved_sha256===hd.saved_sha256);
    report.fading=await p.evaluate(async()=>{
     const{Kjerne:K,Visning:V}=moonDebug,read=K.skanout,scan=read(),base=V.lagNaa(),diw=K.vindu();
     const saved=async()=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',K.lagreTilstand())),b=>b.toString(16).padStart(2,'0')).join('');
     const before=await saved(),rows=[],fullSum=scan.pal.reduce((sum,v,i)=>sum+(i%4===3?0:v),0);
     // Eksakte kildefadingmodeller er maalt med original CPU i native-fades.json.
     // Her testes rendererens palettgate pa samme urorte CPU-tilstand. Bare
     // lokale skanout-/lagkopier tones; dette er ikke en naturlig kampsekvens.
     for(const model of ['channel_cap_in','channel_subtract_out'])for(let level=0;level<16;level++){
      const pal=scan.pal.slice();for(let i=0;i<pal.length;i++)if(i%4!==3){const n=pal[i]/17;pal[i]=(model==='channel_cap_in'?Math.min(n,level):Math.max(n-level,0))*17;}
      K.skanout=()=>({...scan,pal});const tone={...base,bak:base.bak.slice(),for:base.for.slice(),lysMaks:fullSum,lys:pal.reduce((sum,v,i)=>sum+(i%4===3?0:v),0)};
      for(const[name,indices]of[['bak',base.bakIdx],['for',base.forIdx]])if(indices)for(let q=0;q<64000;q++)if(indices[q]<32&&tone[name][q*4+3])tone[name].set(pal.subarray(((diw[1]+Math.floor(q/320))*32+indices[q])*4,((diw[1]+Math.floor(q/320))*32+indices[q])*4+3),q*4);
      V.tegn(K.rammebuffer(),diw,tone);const figs=V.hdFigurer(true).filter(d=>d.fil.toLowerCase()==='ratmen1.cel'&&d.bilde===63);rows.push({model,level,total:figs.length,approved:figs.filter(d=>d.hd).length,light:V.hdKontroll().hdLys,rejected:V.hdKontroll().foliageAvvist||0});
      await new Promise(r=>setTimeout(r,0));
     }
     K.skanout=read;return{scope:'32 exact source-model frontend palette probes, no emulated RAM/palette mutation',rows,full_saved_state_unchanged:before===await saved()};
    });
    check('all_32_original_fading_models_keep_HD_foliage',report.fading.rows.length===32&&report.fading.rows.every(r=>r.total>=3&&r.approved===r.total&&r.rejected===0));
    check('fading_probes_preserve_full_saved_state',report.fading.full_saved_state_unchanged);
    const fadeRestore=await capture(p,'wa2-fading-restored');
    check('fading_restore_is_exact',fadeRestore.png_sha256===hd.png_sha256&&fadeRestore.saved_sha256===hd.saved_sha256);
   }
  }else if(process.env.MOONSTONE_FOLIAGE_AUDIT_ONLY==='1'){
   report.known_pre_gate_palette_failure={unsupported_gll3_approved:hd.figures.filter(d=>d.hd).length};
  }else{
   check('Gll3_unsupported_palette_keeps_three_original_canopies',hd.figures.length>=3&&hd.figures.every(d=>!d.hd));
   check('Gll3_palette_rejection_recorded',hd.control.foliageAvvist>=3);
   report.clipped=await p.evaluate(async()=>{
    const{Kjerne:K,Visning:V}=moonDebug,read=K.skanout,scan=read(),base=V.lagNaa(),diw=K.vindu();
    const saved=async()=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',K.lagreTilstand())),b=>b.toString(16).padStart(2,'0')).join('');
    const before=await saved(),fixture={fil:'Ratmen1.cel',bilde:63,x:313,y:199,w:44,h:35,xoff:0,speilet:false,target:0xa2cd6,caller:0x87bf0};
    // Bare source[4,0]=5 blir opakt innen skjermen. Resten er original0 eller
    // klippet. Dette skiller palettgaten fra svart5 som er likt i begge terreng.
    const lag={...base,forIdx:new Uint8Array(64000).fill(255),for:new Uint8Array(64000*4),lysMaks:base.lys,lys:base.lys};
    const q=199*320+317;lag.forIdx[q]=5;lag.for.set([0,0,0,255],q*4);const rows=[];
    for(const terrain of ['gll3','wa2']){
     const pal=scan.pal.slice();if(terrain==='wa2')for(let y=0;y<288;y++)for(const[c,rgb]of[[5,[0,0,0]],[22,[34,153,85]],[24,[0,102,17]],[25,[0,68,0]],[28,[68,85,0]]])pal.set([...rgb,255],(y*32+c)*4);
     K.skanout=()=>({...scan,pal});V.nullstillScene();
     for(let n=0;n<6;n++){V.nyttBilde([fixture]);V.tegn(K.rammebuffer(),diw,lag);await new Promise(r=>setTimeout(r,0));}
     rows.push({terrain,figures:V.hdFigurer(true).filter(d=>d.fil.toLowerCase()==='ratmen1.cel'&&d.bilde===63),rejected:V.hdKontroll().foliageAvvist||0});
    }
    K.skanout=read;return{scope:'Controlled frontend clipping fixture from exact source row0; no emulated-memory changes, not a natural game frame',rows,full_saved_state_unchanged:before===await saved()};
   });
   check('clipped_black_only_Gll3_still_rejected',report.clipped.rows[0].figures.length===1&&!report.clipped.rows[0].figures[0].hd&&report.clipped.rows[0].rejected===1);
   check('same_clipped_geometry_Wa2_can_use_HD',report.clipped.rows[1].figures.length===1&&report.clipped.rows[1].figures[0].hd&&report.clipped.rows[1].rejected===0);
   check('clipped_palette_probes_preserve_full_saved_state',report.clipped.full_saved_state_unchanged);
  }
  fs.writeFileSync(out+'/progress.json',JSON.stringify(report,null,2)+'\n');
 }
 check('no_browser_errors',report.errors.length===0);report.status=process.env.MOONSTONE_FOLIAGE_AUDIT_ONLY==='1'?'audit_complete':'passed';
})().catch(e=>{report.status='failed';report.failure=String(e);console.error(e);process.exitCode=1;}).finally(async()=>{
 report.created_at=new Date().toISOString();fs.writeFileSync(out+'/report.json',JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({status:report.status,checks:report.checks.length,failure:report.failure}));if(browser)await browser.close();if(host)await host.close();
});
