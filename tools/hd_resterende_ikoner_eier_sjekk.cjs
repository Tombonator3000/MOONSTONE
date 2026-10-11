/* Kjoer den faktiske eier-/pikselryddingen med originale CEL-kilder, uten GPU. */
'use strict';
const fs=require('fs'),path=require('path'),crypto=require('crypto'),assert=require('assert/strict');
const root=path.resolve(__dirname,'..'),art=root+'/art/hd-remaining-icons-2026-10-11';
const out=path.resolve(root,process.env.MOONSTONE_HD_TEST_OUTPUT||'art/hd-remaining-icons-2026-10-11/research/runtime/post-main-merge/ownership');
const source=fs.readFileSync(root+'/web/src/render.js','utf8'),sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const contracts=JSON.parse(fs.readFileSync(art+'/research/runtime/source-contracts.json')).entries;
const metas=new Map(JSON.parse(fs.readFileSync(root+'/web/hd/icons.json')).entries.map(m=>[m.key,m]));
const actual=source.slice(source.indexOf('    function eierskap(lest)'),source.indexOf('    function oppdaterPalett()'));
assert(actual.includes('const ikonVern = visteListe.map'));
const run=new Function('input',`
 let hdTegnbare,hdFigurLys,hdFigurMaske,hdPoseViste,hdKontroll,hdMarkor,palettKlar;
 const hdPaa=true,hdPoser=new Map(),lysUkjent=false,hdLys=1;
 const {visteListe,banks,metas,lag}=input;
 const hdIkoner=new Map(metas),hdPakke=new Map(visteListe.filter(d=>d.hd).map(d=>[d.fil+'/'+String(d.bilde).padStart(3,'0'),{}]));
 const forData=lag.for.slice(),vernData=new Uint8Array(256000),vernTex={};
 const originalCeler=new Map([...banks.keys()].map(k=>[k,{name:k}]));
 const originalCel=(name)=>banks.get(name.toLowerCase());
 const bankHash=(b)=>({hash:input.hashes[b.name]});
 const indeksHash=g=>g.hash;
 const oppdaterPalett=()=>true,forberedPoser=()=>new Set(),forberedTekst=()=>new Set(),forberedMarkor=()=>{};
 const fargeleggIkon=()=>true,erTittel=()=>false,bevarTitteltekst=()=>false;
 ${actual}
 forberedHd(lag);
 return {forData,vernData,control:hdKontroll,accepted:visteListe.map(d=>hdTegnbare.has(d))};
`);
const report={status:'running',checks:[],cases:[],production_code_sha256:{'web/src/render.js':sha(source),'web/src/scenes.js':sha(fs.readFileSync(root+'/web/src/scenes.js'))},scope:'Faktisk eierskap/forberedHd fra sammenslaatt renderer, originale KI/MI-indekser, normale/speilede ruter, kildevern og overlapp. GPU, palettvalg og bildefiler testes separat.'};
const check=(n,v)=>{assert(v,n);report.checks.push(n);};
function fixture(draws,unknown=false){
 const banks=new Map(),hashes={};
 const ds=draws.map(({key,x=100,y=80,mirror=false,hd=true})=>{
  const c=contracts.find(c=>c.key===key);assert(c,key);if(!banks.has(c.source.file))banks.set(c.source.file,[]);
  banks.get(c.source.file)[c.source.frame]={w:c.width,h:c.height,px:c.indices,planmaske:c.plane_mask,hash:c.indices_sha256};hashes[c.source.file]=c.source.bank_sha256;
  return {fil:c.source.file,bilde:c.source.frame,w:c.width,h:c.height,x,y,xoff:0,speilet:mirror,hd};
 });
 const forIdx=new Uint8Array(64000).fill(255),front=new Uint8Array(256000),owner=new Int16Array(64000).fill(-1);
 ds.forEach((d,k)=>{const g=banks.get(d.fil)[d.bilde];for(let j=0;j<d.h;j++)for(let i=0;i<d.w;i++){
  const c=g.px[j*d.w+(d.speilet?d.w-1-i:i)],p=(d.y+j)*320+d.x+i;if(!c)continue;owner[p]=k;forIdx[p]=c;front.set([c*7%256,c*11%256,c*13%256,255],p*4);
 }});
 if(unknown){const d=ds[0],g=banks.get(d.fil)[d.bilde],i=g.px.findIndex(c=>c===0);assert(i>=0);const p=(d.y+Math.floor(i/d.w))*320+d.x+i%d.w;forIdx[p]=15;front.set([1,2,3,255],p*4);}
 return {visteListe:ds,banks,hashes,metas,lag:{for:front,forIdx,hash:123},owner};
}
try{
 for(const [name,draws] of [
  ['selected_helmet',[{key:'mi.c/009'}]],['selected_helmet_mirrored',[{key:'mi.c/009',mirror:true}]],
  ['regular_helmet',[{key:'mi.c/004'}]],['grave_selected',[{key:'mi.c/042'}]],
  ['gold_two_source_pixels',[{key:'ki.cel/037'}]],
  ['two_HD_owners',[{key:'mi.c/009'},{key:'ki.cel/003',x:102,y:82}]],
  ['later_original_owner',[{key:'mi.c/009'},{key:'ki.cel/003',x:102,y:82,hd:false}]],
  ['earlier_original_owner',[{key:'ki.cel/003',x:102,y:82,hd:false},{key:'mi.c/009'}]],
 ]){
  const f=fixture(draws),r=run(f);check(name+'_intended_HD_approved',r.accepted.every((v,i)=>v===f.visteListe[i].hd));
  let protectedCount=0,removedCount=0,laterOriginalCount=0;
  for(let p=0;p<64000;p++){
   const e=f.owner[p];if(e<0)continue;const d=f.visteListe[e],m=metas.get(d.fil+'/'+String(d.bilde).padStart(3,'0'));
   if(d.hd){if(m.preserve_indices?.includes(f.lag.forIdx[p])){
    assert.equal(r.vernData[p*4+3],255,name+' preserved owner');assert.deepEqual(r.forData.slice(p*4,p*4+4),f.lag.for.slice(p*4,p*4+4));protectedCount++;
   }else{assert.equal(r.forData[p*4+3],0,name+' removed owner');removedCount++;}}
   else {assert.deepEqual(r.forData.slice(p*4,p*4+4),f.lag.for.slice(p*4,p*4+4));
    if(f.visteListe.some((o,k)=>o.hd&&k<e&&p%320>=o.x&&p%320<o.x+o.w&&Math.floor(p/320)>=o.y&&Math.floor(p/320)<o.y+o.h)){
     assert.equal(r.vernData[p*4+3],255,name+' later original owner');laterOriginalCount++;
    }
   }
  }
  check(name+'_pixel_ownership_exact',removedCount>0);report.cases.push({name,protectedCount,removedCount,laterOriginalCount});
 }
 const bad=run(fixture([{key:'mi.c/009'}],true));check('unknown_foreground_rejects_entire_icon',!bad.accepted[0]&&bad.control.piksler===1);
 report.status='passed';
}catch(e){report.status='failed';report.failure=String(e);process.exitCode=1;}
fs.mkdirSync(out,{recursive:true});fs.writeFileSync(out+'/ownership-test.json',JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report));
