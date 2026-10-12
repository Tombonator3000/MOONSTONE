/* Eksakt Ratmen-baking og strenge negativeporter, ingen emulert minneskriving. */
'use strict';
const fs=require('fs'),path=require('path'),crypto=require('crypto'),vm=require('vm'),assert=require('assert/strict'),zlib=require('zlib'),{execFileSync}=require('child_process');
const art=__dirname,root=path.resolve(art,'../../../..'),sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const scene=fs.readFileSync(root+'/web/src/scenes.js','utf8'),gfx=fs.readFileSync(root+'/web/src/grafikk.js','utf8');
const oldBytes=zlib.gunzipSync(fs.readFileSync(art+'/../dragon-production/retention/combat-background-fixture-input.json.gz'));
assert.equal(sha(oldBytes),'d503998d637fa0125bbb3b25ac139879e74491981118846adc0d7c99a385e1df');
const input=JSON.parse(oldBytes),cleanRow=input.entries.find(r=>r.hash==='e8ac7fc2'),sources=JSON.parse(fs.readFileSync(art+'/source-contracts.json')).entries;
const sourceFiles=JSON.parse(execFileSync('python3',['-c',"import sys,json,base64;sys.path.insert(0,'tools');import moonfiles as m;g=m.Spill('Moonstonecd32-AMIGA.zip');print(json.dumps({f:base64.b64encode(g.les(f)).decode()for f in ['ratmen1.cel','ratmen2.cel']}))"],{cwd:root}));
const rows=[{key:'RATMEN2.CEL/056.png',x:15,y:185,mirror:false},{key:'RATMEN1.CEL/051.png',x:114,y:182,mirror:true}].map(r=>({...r,...sources.find(c=>c.key===r.key)}));
const checks=[],check=(n,v)=>{assert(v,n);checks.push(n);};
function setup(bad){
 const files=Object.fromEntries(Object.entries({...input.files,...sourceFiles}).map(([f,b])=>[f.toLowerCase(),Uint8Array.from(Buffer.from(b,'base64'))]));
 if(bad==='missing_bank')delete files['ratmen2.cel'];
 if(bad==='wrong_bank')files['ratmen2.cel'][files['ratmen2.cel'].length-1]^=1;
 const pal=new Uint8Array(288*128);for(let y=0;y<288;y++){pal.set([0,0,0,255],(y*32+5)*4);pal.set([204,0,0,255],(y*32+15)*4);}
 let frame=1200,trace=[],rev=0,hd=true;
 const context={crypto:crypto.webcrypto,console,Uint8Array,Uint32Array,Map,Set,Math,Promise,StandardHd:{info:()=>({aktiv:true,klar:true}),scener:()=>[]},Visning:{hdAntall:()=>1,hdPaa:()=>hd,harHdBilde:()=>true},Kjerne:{hentFil:n=>files[n.slice(5).toLowerCase()],filRevisjon:()=>rev,skanout:()=>({gyldig:true,pal}),iIntro:()=>false,iSlutt:()=>false,bildeNr:()=>frame,tegneliste:()=>trace}};
 vm.createContext(context);vm.runInContext(gfx,context);const S=vm.runInContext(scene+'\nSceneHd;',context),clean=Uint8Array.from(Buffer.from(cleanRow.indices_base64,'base64'));
 if(bad==='changed_clean')clean[0]^=1;
 const lag={hash:0xe8ac7fc2,bakIdx:clean.slice(),bak:new Uint8Array(256000),forIdx:new Uint8Array(64000).fill(255),for:new Uint8Array(256000)};
 for(let p=0;p<64000;p++)lag.bak.set([20,30,40,255],p*4);
 const draw=l=>S.korriger(new Uint8Array(720*288*4),[0,0,640,200],l);
 function baked(count=2,wrong){
  const d={...lag,hash:0xe52767d5,bakIdx:lag.bakIdx.slice(),bak:lag.bak.slice(),for:lag.for.slice(),forIdx:lag.forIdx.slice()};trace=[];
  for(const r of rows.slice(0,count)){
   const t={fil:r.bank,bilde:r.frame,x:r.x,y:r.y,w:r.width,h:r.height,xoff:0,speilet:r.mirror,caller:0x87b34,target:0xa2cd6};
   if(wrong==='caller')t.caller=0x87bf0;if(wrong==='target')t.target++;if(wrong==='width')t.w++;if(wrong==='height')t.h++;if(wrong==='anchor')t.x++;if(wrong==='mirror')t.speilet=!t.speilet;if(wrong==='unknown_source')t.fil='unknown.cel';if(wrong==='source_frame')t.bilde++;
   trace.push(t);
   for(let y=0;y<r.height;y++)for(let x=0;x<r.width;x++){const c=r.indices[y*r.width+(r.mirror?r.width-1-x:x)];if(c){const p=(r.y+y)*320+r.x+x;d.bakIdx[p]=c;d.bak.set([c===15?204:0,0,0,255],p*4);}}
  }
  if(wrong==='missing_trace')trace=[];
  frame++;return d;
 }
 return{S,lag,clean,pal,draw,baked,files,revisit:()=>rev++,hd:v=>hd=v,advance:()=>frame++,clear:()=>S.nullstill()};
}
async function settle(f){f.draw(f.lag);await new Promise(r=>setTimeout(r,25));}
(async()=>{
 for(const count of [1,2]){const f=setup();await settle(f);const d=f.baked(count),before=sha(d.bak),o=f.draw(d),delta=[];for(let p=0;p<64000;p++)if(d.bakIdx[p]!==f.clean[p])delta.push(p);
  check(count+'_source_composition_HD_identity',o.hash===0xe8ac7fc2&&o.kampDeltaVern);
  check(count+'_all_original_delta_cells',delta.every(p=>o.kampDeltaVern[p]&&o.forIdx[p]===d.bakIdx[p]&&o.for.slice(p*4,p*4+4).every((v,k)=>v===d.bak[p*4+k])));
  check(count+'_only_delta_cells_protected',o.kampDeltaVern.reduce((n,v)=>n+v,0)===delta.length);
  check(count+'_unchanged_original_background',o.bak===d.bak&&o.bakIdx===d.bakIdx&&sha(d.bak)===before);
  if(count===2){check('late_entire_original_indices_SHA',sha(d.bakIdx)==='0d4adbce1bffc70b8bd8582938709402189539bdaa42ad16e4869b77cb092e91');check('late_exact_96_cells',delta.length===96&&delta.filter(p=>d.bakIdx[p]===5).length===19&&delta.filter(p=>d.bakIdx[p]===15).length===77);}
  f.hd(false);check(count+'_Original_same_source_identity',f.draw(d).hash===o.hash);f.hd(true);check(count+'_HD_same_source_identity',f.draw(d).hash===o.hash);
  const p=delta.find(p=>d.bakIdx[p]===5);d.forIdx[p]=7;d.for.set([0,0,119,255],p*4);const fg=f.draw(d);check(count+'_original_foreground_over_black_delta',fg.forIdx[p]===7&&fg.for[p*4+2]===119&&fg.kampDeltaVern[p]);
 }
 for(const wrong of ['caller','target','width','height','anchor','mirror','unknown_source','source_frame','missing_trace']){const f=setup();await settle(f);const d=f.baked(2,wrong);check('wrong_'+wrong+'_rejected',f.draw(d)===d);}
 for(const bad of ['missing_bank','wrong_bank','changed_clean']){const f=setup(bad);await settle(f);const d=f.baked();check(bad+'_rejected',f.draw(d)===d);}
 for(const wrong of ['extra5','extra14','extra15','wrong5_RGBA','wrong15_RGBA','wrong5_palette','wrong15_palette','wrong5_alpha','wrong_dimensions']){const f=setup();await settle(f);const d=f.baked(),p=d.bakIdx.findIndex((v,i)=>v===5&&v!==f.clean[i]),red=d.bakIdx.findIndex((v,i)=>v===15&&v!==f.clean[i]);
  if(wrong.startsWith('extra')){const q=10;d.bakIdx[q]=Number(wrong.slice(5));d.bak.set([d.bakIdx[q]===15?204:0,0,0,255],q*4);}
  if(wrong==='wrong5_RGBA')d.bak[p*4]=1;if(wrong==='wrong15_RGBA')d.bak[red*4]=203;if(wrong==='wrong5_alpha')d.bak[p*4+3]=254;
  if(wrong==='wrong5_palette')f.pal[(Math.floor(p/320)*32+5)*4]=1;if(wrong==='wrong15_palette')f.pal[(Math.floor(red/320)*32+15)*4]=203;
  if(wrong==='wrong_dimensions')d.bakIdx=d.bakIdx.slice(1);
  check(wrong+'_rejected',f.draw(d)===d);
 }
 const f=setup();await settle(f);const d=f.baked();check('positive_before_revision',f.draw(d).hash===0xe8ac7fc2);f.revisit();check('revision_clears_baked_history',f.draw(d)===d);
 const fresh=setup(),unknown=fresh.baked();check('missing_clean_anchor_rejected',fresh.draw(unknown)===unknown);
 const report={schema:1,status:'passed',checks,scenes_sha256:sha(scene),render_sha256:sha(fs.readFileSync(root+'/web/src/render.js')),graphics_decoder_sha256:sha(gfx),runtime_script_sha256:sha(fs.readFileSync(__filename)),source_contracts_sha256:sha(fs.readFileSync(art+'/source-contracts.json')),scope:'Faktisk SceneHd og Spillgrafikk fra frontend, eksakte originale ZIP-banker og64000Wa2-indekser. Ingen GPU-, kamp- eller naturlig reisepaastand. Originalbakingene er spor-fixturer; eget faktisk kampbevis kreves.'};
 const out=process.env.MOONSTONE_HD_TEST_OUTPUT||art+'/verification/baked-background-fixtures-v1';assert(!fs.existsSync(out),'Bevar tidligere proof');fs.mkdirSync(out,{recursive:true});fs.writeFileSync(out+'/test.json',JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({status:report.status,checks:checks.length}));
})().catch(e=>{console.error(e);process.exitCode=1;});
