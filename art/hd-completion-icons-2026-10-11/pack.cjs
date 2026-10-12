/* Kandidatpakking av separat genererte ikonmaterialer. Ingen aktive filer endres. */
'use strict';
const fs=require('fs'),path=require('path'),crypto=require('crypto'),{chromium}=require('playwright');
const art=__dirname,root=path.resolve(art,'../..'),sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const canvasPack=require(root+'/tools/hd_resterende_ikoner_canvas.cjs');
(async()=>{
 const fragment=JSON.parse(fs.readFileSync(art+'/fragment-icons.json')),sources=JSON.parse(fs.readFileSync(art+'/source-contracts.json'));
 const browser=await chromium.launch({headless:true,executablePath:'/usr/bin/google-chrome',args:['--no-sandbox']});
 const report={schema:1,scope:'Fritt generert materiale klippet mot originalgeometri, foreloepig sammenligning.',assets:[]};
 try{
  const p=await browser.newPage();
  for(const m of fragment.entries){
   const raw=fs.readFileSync(art+'/raw/'+m.key+'.png'),source=fs.readFileSync(art+'/references/'+m.key+'-native.png'),c=sources.entries.find(c=>c.key===m.key);
   const result=await p.evaluate(canvasPack,{raw:raw.toString('base64'),source:source.toString('base64'),w:m.width*8,h:m.height*8,scale:8,placement:'source_bounds',source_clip:true,clip:m.clip});
   const png=Buffer.from(result.png,'base64');delete result.png;const dest=art+'/free-pack/'+m.key+'.png';fs.mkdirSync(path.dirname(dest),{recursive:true});fs.writeFileSync(dest,png);
   m.render_mode='raster';m.reference_palette=Object.fromEntries(c.source_colors.map(i=>[i,c.palette[i].slice(0,3)]));
   report.assets.push({key:m.key,...result,source:c.source,width:m.width,height:m.height,indices_sha256:c.indices_sha256,raw_sha256:sha(raw),source_png_sha256:sha(source),packed_sha256:sha(png)});
  }
 }finally{await browser.close();}
 fs.writeFileSync(art+'/fragment-icons.json',JSON.stringify(fragment)+'\n');fs.writeFileSync(art+'/free-packing-report.json',JSON.stringify(report,null,2)+'\n');
 console.log(JSON.stringify(report.assets.map(a=>({key:a.key,iou:a.silhouette_iou,size:a.texture_size}))));
})().catch(e=>{console.error(e);process.exitCode=1;});
