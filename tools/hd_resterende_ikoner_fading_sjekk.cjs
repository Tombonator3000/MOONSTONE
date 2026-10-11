/* Hele firebitsfadingen for kildeverifiserte livpaletter, samme runtimefunksjon. */
'use strict';
const fs=require('fs'),assert=require('assert/strict'),path=require('path');
const root=path.resolve(__dirname,'..'),dir=root+'/art/hd-remaining-icons-2026-10-11/research/runtime';
const src=fs.readFileSync(root+'/web/src/render.js','utf8'),first=src.indexOf('    function rasterIkonVariant('),end=src.indexOf('    function fargeleggIkon(',first);
const select=new Function(src.slice(first,end)+';return rasterIkonVariant;')();
const contracts=JSON.parse(fs.readFileSync(dir+'/source-contracts.json')),pairs={blue:[[0,51,255],[0,34,136]],orange:[[255,187,0],[187,102,0]],green:[[68,204,51],[17,102,0]],red:[[255,0,0],[136,0,0]],purple:[[0,34,119],[0,0,51]]};
const report={status:'passed',scope:'Samme produksjonsfunksjon, 16 Amiga-fadingtrinn for fire livruter og fem dokumenterte fargepar. Eksakt bildefarge kan ikke bestemmes i svart/naer svart.',samples:[]};
for(const key of ['ki.cel/017','ki.cel/018','ki.cel/019','ki.cel/020']){
 const c=contracts.entries.find(c=>c.key===key),side=['017','019'].includes(key.slice(-3))?[28,29]:[30,31],m={key,render_mode:'raster',reference_palette:c.reference_palette,palette_variants:Object.entries(pairs).map(([id,colors])=>({id,key:id==='blue'?key:'ki-palettes/'+key.slice(-3)+'-'+id,indices:side,colors}))};
 for(const v of m.palette_variants)for(let level=0;level<16;level++){
  const ref=structuredClone(c.reference_palette);side.forEach((n,i)=>ref[n]=v.colors[i]);const colors=c.source_colors,rgb=colors.map(n=>ref[n].map(value=>Math.floor(value/17*level/15)*17)),got=select(m,{colors,rgb});assert(got,key+' '+v.id+' '+level+' avvist');
  if(level>=4)assert.equal(got.key,v.key,key+' '+v.id+' '+level+' feil fargebilde');report.samples.push({key,id:v.id,level,selected:got.key,brightness:got.lys});
 }
}
report.created_at=new Date().toISOString();fs.writeFileSync(dir+'/palette-fading-test.json',JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({status:'passed',samples:report.samples.length}));
