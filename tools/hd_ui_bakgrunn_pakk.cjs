/* Pakk nye originalbundne UI-materialer og fire bakgrunner. Raaresultater bevares. */
'use strict';
const fs=require('fs'),path=require('path'),crypto=require('crypto'),assert=require('assert/strict'),{chromium}=require('playwright');
const root=path.resolve(__dirname,'..'),art=root+'/art/hd-ui-backgrounds-2026-10-11';
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const canvasPack=require('./hd_resterende_ikoner_canvas.cjs');
(async()=>{
 const records=JSON.parse(fs.readFileSync(art+'/generation-records.json'));
 const ui=JSON.parse(fs.readFileSync(root+'/art/hd-ui-followup-2026-10-11/fragment-icons.json'));
 const sources=JSON.parse(fs.readFileSync(root+'/art/hd-ui-followup-2026-10-11/source-contracts.json'));
 const browser=await chromium.launch({headless:true,executablePath:'/usr/bin/google-chrome',args:['--no-sandbox']});
 const report={schema:1,assets:[],scope:'Originalgeometri med fotografiske materialer. Visuell kontroll kreves foer aktivering.'};
 const entries=[];
 try{
  const page=await browser.newPage();
  for(const a of records.assets){
   const raw=fs.readFileSync(art+'/'+a.raw),source=fs.readFileSync(art+'/'+a.reference);
   let result;
   if(a.key.startsWith('bg/')){
    result=await page.evaluate(async raw=>{
     const im=new Image();im.src='data:image/png;base64,'+raw;await im.decode();
     const c=document.createElement('canvas');c.width=1280;c.height=800;
     const ctx=c.getContext('2d');ctx.fillStyle='#000';ctx.fillRect(0,0,1280,800);ctx.imageSmoothingQuality='high';ctx.drawImage(im,0,0,1280,800);
     return{png:c.toDataURL('image/png').split(',')[1],master_size:[im.width,im.height],texture_size:[1280,800],placement:'full_frame_no_crop'};
    },raw.toString('base64'));
   }else{
    const m=structuredClone(ui.entries.find(m=>m.key===a.key)),s=sources.entries.find(s=>s.key===a.key);
    assert(m&&s,'Mangler kildekontrakt');
    result=await page.evaluate(canvasPack,{raw:raw.toString('base64'),source:source.toString('base64'),w:m.width*8,h:m.height*8,scale:8,placement:'source_bounds',source_clip:true,clip:m.clip});
    m.render_mode='raster';m.reference_palette=Object.fromEntries(s.source_colors.map(c=>[c,s.palette[c].slice(0,3)]));entries.push(m);
   }
   const png=Buffer.from(result.png,'base64');delete result.png;
   const dest=art+'/packed/'+a.key+'.png';fs.mkdirSync(path.dirname(dest),{recursive:true});fs.writeFileSync(dest,png);
   report.assets.push({...a,...result,raw_sha256:sha(raw),source_sha256:sha(source),packed_sha256:sha(png),bytes:png.length});
  }
 }finally{await browser.close();}
 fs.writeFileSync(art+'/fragment-icons.json',JSON.stringify({schema:ui.schema,banks:ui.banks,entries})+'\n');
 report.fragment_icons_sha256=sha(fs.readFileSync(art+'/fragment-icons.json'));
 fs.writeFileSync(art+'/packing-report.json',JSON.stringify(report,null,2)+'\n');
 console.log(JSON.stringify(report.assets.map(a=>({key:a.key,iou:a.silhouette_iou,size:a.texture_size,bytes:a.bytes}))));
})().catch(e=>{console.error(e);process.exitCode=1;});
