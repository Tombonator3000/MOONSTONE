/* Original TROLL-kamp, identiske inndata i Original/HD, eksakt BG-deltabevaring. */
'use strict';
const fs=require('fs'),path=require('path'),crypto=require('crypto'),assert=require('assert/strict'),{chromium}=require('playwright');
const art=__dirname,root=path.resolve(art,'../../../..'),host=process.env.MOONSTONE_HOST,out=process.env.MOONSTONE_OUT;
const sha=b=>crypto.createHash('sha256').update(b).digest('hex'),binding=require('./runtime-proof.cjs').bind(root,host,__filename);
const row=JSON.parse(fs.readFileSync(art+'/retention/combat-background-fixture-input.json')).entries.find(r=>r.hash==='e8ac7fc2');
const report={...binding,schema:1,status:'running',checks:[],errors:[],scope:'Original CPU TROLL-kamp med tre init-skrivinger ved900 og venstre1200:120, ellers original inndata. Ingen palett-/tegnelisteskriving eller privatimport. To komplette originalkjerneforloep med samme inndata, ett med Original og ett med HD. Ikke naturlig kartreise.'};
const check=(n,v)=>{assert(v,n);report.checks.push(n);};let browser,server,p;
(async()=>{
 fs.mkdirSync(out,{recursive:true});server=await require('./runtime-host.cjs')(host);browser=await chromium.launch({headless:true,executablePath:'/usr/bin/google-chrome',args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});p=await browser.newPage({viewport:{width:640,height:480}});p.on('pageerror',e=>report.errors.push(e.message));await p.addInitScript(()=>localStorage.setItem('moonstone.innstillinger',JSON.stringify({hd:'hd',hdValgt:true})));await p.goto(server.url);await p.waitForFunction(()=>{try{return moonDebug.Kjerne.bildeNr()>1;}catch{return false;}});await p.keyboard.press('Pause');await p.waitForFunction(()=>moonDebug.StandardHd.info().klar,null,{timeout:90000});
 report.runtime=await p.evaluate(async row=>{
  const{Kjerne:K,Visning:V,SceneHd:S,StandardHd:H}=moonDebug,M=await K.last(),clean=Uint8Array.from(atob(row.indices_base64),c=>c.charCodeAt(0));
  const draw=()=>{const fb=K.rammebuffer(),d=K.vindu(),lag=S.korriger(fb,d,K.lag());V.tegn(fb,d,lag);H.oppdater(lag?.hash);return lag;};
  const results=[];
  for(const mode of [false,true]){
   K.start(false);K.menyPaa(false);K.lagPaa(true);V.nullstillScene();S.nullstill();V.settHd(mode);V.settTvungetLag(true);V.settFilter('skarp');const states=[],trace=[];let capture;
   while(K.bildeNr()<1601){const n=K.bildeNr();if(n===100)K.tast(0x45,true);if(n===104)K.tast(0x45,false);K.inndata(0,((n>=700&&n<704)||(n>=760&&n<764)?2:0)|(n>=820&&n<824?16:0)|(n>=1200&&n<1320?4:0));
    if(n===900){const d=new DataView(M.HEAPU8.buffer),chip=M._ms_chip();for(const[a,v]of[[0x80172,0x84924],[0x8d9ac,0x8d5b4],[0x8015c,0xc]])d.setUint32(chip+a,v,false);}K.bilde();const draws=K.tegneliste();V.nyttBilde(draws);if(n>=1100)draw();const frame=K.bildeNr();if([1100,1250,1500,1600].includes(frame)){states.push({frame,checksum:K.sjekksum()});trace.push({frame,draws});}
    if(frame===1500){const lag=K.lag(),corrected=draw(),cells=[];
     for(let p=0;p<64000;p++)if(lag.bakIdx[p]!==clean[p])cells.push({p,x:p%320,y:p/320|0,before:clean[p],after:lag.bakIdx[p],rgba:Array.from(lag.bak.subarray(p*4,p*4+4))});
     const snap=()=>{draw();return V.bildeTilPng();},cs=K.sjekksum();V.settHd(false);const original=snap();V.settHd(true);for(let q=0;q<1000;q++){draw();if(V.hdKontroll().bakgrunn==='hd'&&!H.info().laster)break;await new Promise(r=>setTimeout(r,5));}const hd=snap(),control=V.hdKontroll();V.settHd(false);const restored=snap();V.settHd(true);const again=snap();capture={cells,source_hash:(lag.hash>>>0).toString(16).padStart(8,'0'),clean_hash:(corrected.hash>>>0).toString(16).padStart(8,'0'),scene:S.info(),control,original,hd,restored,again,checksum:cs,checksum_after:K.sjekksum()};V.settHd(mode);
    }if(n%100===0)await new Promise(r=>setTimeout(r,0));
   }results.push({mode,states,trace,capture});
  }return results;
 },row);
 const [baseline,hdRun]=report.runtime;check('Original_HD_full_CPU_checkpoints_equal',JSON.stringify(baseline.states)===JSON.stringify(hdRun.states));check('Original_HD_native_source_calls_equal',JSON.stringify(baseline.trace)===JSON.stringify(hdRun.trace));check('Original_image_equal_independent_baseline',baseline.capture.original===hdRun.capture.original);
 for(const r of report.runtime){const c=r.capture;check('actual_'+r.mode+'_exact_native_hash',c.source_hash==='b91f7ea2');check('actual_'+r.mode+'_HD_clean_identity',c.clean_hash==='e8ac7fc2'&&c.scene?.id==='combat-delta');check('actual_'+r.mode+'_all30_native_deltas_exact15',c.cells.length===30&&c.cells.every(p=>p.after===15&&JSON.stringify(p.rgba)==='[204,0,0,255]'));check('actual_'+r.mode+'_HD_background_visible',c.control.bakgrunn==='hd');check('actual_'+r.mode+'_Original_return',c.original===c.restored);check('actual_'+r.mode+'_HD_return',c.hd===c.again);check('actual_'+r.mode+'_CPU_unchanged_during_display',c.checksum===c.checksum_after);
  const exact=await p.evaluate(async({a,b,cells})=>{async function read(src){const im=new Image();im.src=src;await im.decode();if(im.width!==640||im.height!==400)throw Error('Uventet bildestoerrelse');const cv=document.createElement('canvas');cv.width=im.width;cv.height=im.height;const ct=cv.getContext('2d');ct.drawImage(im,0,0);return ct.getImageData(0,0,cv.width,cv.height).data;}const x=await read(a),y=await read(b);return cells.every(({x:cx,y:cy})=>[0,1].every(j=>[0,1].every(i=>[0,1,2,3].every(k=>x[((cy*2+j)*640+cx*2+i)*4+k]===y[((cy*2+j)*640+cx*2+i)*4+k]))));},{a:c.original,b:c.hd,cells:c.cells});check('actual_'+r.mode+'_all30_whole_cells_preserved',exact);
  for(const kind of ['original','hd']){const b=Buffer.from(c[kind].split(',')[1],'base64');fs.writeFileSync(out+'/'+(r.mode?'hd-run':'original-run')+'-'+kind+'.png',b);c[kind+'_sha256']=sha(b);}for(const k of ['original','hd','restored','again'])delete c[k];
 }
 check('no_browser_errors',!report.errors.length);require('./runtime-proof.cjs').checkFinal(root,host,__filename,binding);report.status='passed';
})().catch(e=>{report.status='failed';report.failure=String(e);console.error(e);process.exitCode=1;}).finally(async()=>{fs.mkdirSync(out,{recursive:true});fs.writeFileSync(out+'/test.json',JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({status:report.status,checks:report.checks.length,failure:report.failure}));if(browser)await browser.close();if(server)await server.close();});
