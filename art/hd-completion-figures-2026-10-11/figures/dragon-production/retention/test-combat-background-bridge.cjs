/* Eksakte kilde-/deltaporter for kampbakgrunn. Ingen emulering eller spillminneskriving. */
'use strict';
const fs=require('fs'),path=require('path'),vm=require('vm'),crypto=require('crypto'),assert=require('assert/strict');
const art=path.resolve(__dirname,'..'),root=path.resolve(art,'../../../..');
const code=fs.readFileSync(root+'/web/src/scenes.js','utf8'),input=JSON.parse(fs.readFileSync(__dirname+'/combat-background-fixture-input.json'));
const sha=b=>crypto.createHash('sha256').update(b).digest('hex'),checks=[];
const check=(name,value)=>{assert(value,name);checks.push(name);};
function setup(row,badSource){
 const files=Object.fromEntries(Object.entries(input.files).map(([f,b])=>[f,Uint8Array.from(Buffer.from(b,'base64'))]));
 if(badSource==='unknown')delete files[row.source_file];
 else if(badSource){const f=badSource==='program'?'program':badSource==='test'?'test':badSource==='mog'?'mog':row.source_file;files[f][files[f].length-1]^=1;}
 let rev=0,hd=true;const pal=new Uint8Array(288*128);for(let y=0;y<288;y++)pal.set([204,0,0,255],(y*32+15)*4);
 const context={console,crypto:crypto.webcrypto,Uint8Array,Uint32Array,Map,Set,Math,Promise,
  StandardHd:{info:()=>({aktiv:true,klar:true}),scener:()=>[]},Visning:{hdAntall:()=>1,hdPaa:()=>hd,harHdBilde:()=>true},
  Kjerne:{hentFil:n=>files[n.slice(5)],filRevisjon:()=>rev,skanout:()=>({gyldig:true,pal}),iIntro:()=>false,iSlutt:()=>false}};
 vm.createContext(context);const S=vm.runInContext(code+'\nSceneHd;',context),clean=Uint8Array.from(Buffer.from(row.indices_base64,'base64'));
 const lag={hash:parseInt(row.hash,16),bakIdx:clean.slice(),bak:new Uint8Array(256000),forIdx:new Uint8Array(64000).fill(255),for:new Uint8Array(256000),lys:123};
 for(let p=0;p<64000;p++)lag.bak.set([20,30,40,255],p*4);
 function delta(){const d={...lag,hash:0x11112222,bakIdx:lag.bakIdx.slice(),bak:lag.bak.slice(),forIdx:lag.forIdx.slice(),for:lag.for.slice()};
  const p=clean.findIndex(c=>c!==15);d.bakIdx[p]=15;d.bak.set([204,0,0,255],p*4);return{d,p};}
 return {S,lag,clean,pal,delta,draw:l=>S.korriger(new Uint8Array(720*288*4),[0,0,640,200],l),revisit:()=>rev++,hd:v=>{hd=v;}};
}
async function settle(f){f.draw(f.lag);await new Promise(r=>setTimeout(r,12));}
(async()=>{
 for(const row of input.entries){
  check(row.hash+'_frozen_indices_SHA',sha(Buffer.from(row.indices_base64,'base64'))===row.indices_sha256);
  const f=setup(row);await settle(f);const{d,p}=f.delta(),before=sha(d.bak),out=f.draw(d);
  check(row.hash+'_clean_identity',out.hash===f.lag.hash);check(row.hash+'_one_delta',out.kampDeltaVern[p]===1&&out.kampDeltaVern.reduce((a,v)=>a+v,0)===1);
  check(row.hash+'_original_red_cell',out.forIdx[p]===15&&[204,0,0,255].every((v,k)=>out.for[p*4+k]===v));
  check(row.hash+'_background_unmodified',out.bak===d.bak&&out.bakIdx===d.bakIdx&&sha(d.bak)===before);
  check(row.hash+'_unrelated_foreground_preserved',out.for.every((v,i)=>Math.floor(i/4)===p||v===d.for[i]));
  f.hd(false);check(row.hash+'_Original_same_identity',f.draw(d).hash===out.hash);f.hd(true);check(row.hash+'_HD_same_identity',f.draw(d).hash===out.hash);
  d.forIdx[p]=7;d.for.set([0,0,119,255],p*4);const overlay=f.draw(d);check(row.hash+'_native_foreground_over_delta',overlay.forIdx[p]===7&&overlay.for[p*4+2]===119&&overlay.kampDeltaVern[p]);
  const wrong=f.delta();wrong.d.bakIdx[wrong.p]=14;check(row.hash+'_one_non15_rejected',f.draw(wrong.d)===wrong.d);
  const extra=f.delta();const q=extra.p+1;extra.d.bakIdx[q]=f.clean[q]===14?13:14;check(row.hash+'_one_non15_among_red_rejected',f.draw(extra.d)===extra.d);
  const rgba=f.delta();rgba.d.bak[rgba.p*4]=203;check(row.hash+'_wrong_delta_RGBA_rejected',f.draw(rgba.d)===rgba.d);
  const palette=f.delta();f.pal[60]=170;check(row.hash+'_wrong_palette15_rejected',f.draw(palette.d)===palette.d);f.pal[60]=204;
  f.revisit();check(row.hash+'_file_revision_clears_anchor',f.draw(d)===d);
 }
 const row=input.entries.find(r=>r.hash==='e8ac7fc2');
 for(const bad of ['unknown','source','program','test','mog']){const f=setup(row,bad);await settle(f);const{d}=f.delta();check('wrong_'+bad+'_source_rejected',f.draw(d)===d);}
 const changed=setup(row);changed.lag.bakIdx[0]^=1;await settle(changed);const b=changed.delta();check('changed_clean_indices_SHA_rejected',changed.draw(b.d)===b.d);
 const unknown=setup(row);const u=unknown.delta();check('no_observed_clean_anchor_rejected',unknown.draw(u.d)===u.d);
 const report={schema:1,status:'passed',checks,scenes_sha256:sha(code),runtime_script_sha256:sha(fs.readFileSync(__filename)),source_contract_sha256:sha(fs.readFileSync(__dirname+'/combat-background-source-contract.json')),scope:'Actual SceneHd JavaScript with frozen original files and all33 clean source buffers. Pure layer fixture, not a game or GPU runtime claim.'};
 fs.writeFileSync(__dirname+'/combat-background-fixture-proof.json',JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({status:report.status,checks:checks.length}));
})().catch(e=>{console.error(e);process.exitCode=1;});
