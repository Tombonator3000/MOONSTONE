/* Pakk urorte genererte rastermastere til originalens teksturmaal og anker.
 * Ingen motivtegning her: kun transparent marg, skalering og PNG-eksport. */
'use strict';
const fs=require('fs'),path=require('path'),crypto=require('crypto'),{chromium}=require('playwright');
const root=path.resolve(__dirname,'..'),art=root+'/art/faithful-hd-icons-2026-10-11';
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
(async()=>{
 const assets=JSON.parse(fs.readFileSync(art+'/assets.json')).assets;
 const icons=JSON.parse(fs.readFileSync(art+'/raster-icons.json'));
 const b=await chromium.launch({headless:true,executablePath:process.env.CHROME||'/usr/bin/google-chrome',args:['--no-sandbox']});
 const report=[];
 try {
  const p=await b.newPage();
  for(const a of assets.filter(a=>a.review_status==='reviewed_for_runtime')) {
   const m=icons.entries.find(m=>m.key===a.key),raw=fs.readFileSync(art+'/'+a.raw),source=fs.readFileSync(art+'/'+a.source);
   const result=await p.evaluate(async({raw,source,w,h,placement})=>{
    const read=async data=>{const im=new Image();im.src='data:image/png;base64,'+data;await im.decode();const c=document.createElement('canvas');c.width=im.width;c.height=im.height;c.getContext('2d').drawImage(im,0,0);return c;};
    const original=await read(source),master=await read(raw);
    const bounds=c=>{const pix=c.getContext('2d').getImageData(0,0,c.width,c.height).data;let x0=c.width,y0=c.height,x1=0,y1=0;
     for(let y=0;y<c.height;y++)for(let x=0;x<c.width;x++)if(pix[(y*c.width+x)*4+3]>=16){x0=Math.min(x0,x);x1=Math.max(x1,x+1);y0=Math.min(y0,y);y1=Math.max(y1,y+1);}
     if(x1<=x0||y1<=y0)throw Error('Tom rasterkilde');return[x0,y0,x1-x0,y1-y0];};
    const from=bounds(master),to=bounds(original),out=document.createElement('canvas');out.width=w;out.height=h;
    let dest;
    if(placement==='contain'){
     const scale=Math.min(w/from[2],h/from[3]);
     dest=[(w-from[2]*scale)/2,h-from[3]*scale,from[2]*scale,from[3]*scale];
    }else dest=placement==='full_rect' ? [0,0,w,h] : [to[0]*w/original.width,to[1]*h/original.height,to[2]*w/original.width,to[3]*h/original.height];
    out.getContext('2d').drawImage(master,...from,...dest);
    const ref=document.createElement('canvas');ref.width=w;ref.height=h;ref.getContext('2d').drawImage(original,0,0,w,h);
    const aa=out.getContext('2d').getImageData(0,0,w,h).data,bb=ref.getContext('2d').getImageData(0,0,w,h).data;
    let both=0,either=0,ink=0;for(let i=3;i<aa.length;i+=4){const a=aa[i]>=128,b=bb[i]>=128;both+=a&&b;either+=a||b;ink+=a;}
    return{png:out.toDataURL().split(',')[1],master_size:[master.width,master.height],raw_ink_bounds:from,target_ink_bounds:dest,
     silhouette_iou:both/either,opaque_pixels:ink,texture_size:[w,h]};
   },{raw:raw.toString('base64'),source:source.toString('base64'),
    w:(m.draw_rect ? m.draw_rect[2]-m.draw_rect[0] : m.width)*m.scale,
    h:(m.draw_rect ? m.draw_rect[3]-m.draw_rect[1] : m.height)*m.scale,placement:a.placement});
   const png=Buffer.from(result.png,'base64');delete result.png;
   const packed=art+'/packed/'+a.key+'.png';fs.mkdirSync(path.dirname(packed),{recursive:true});fs.writeFileSync(packed,png);
   report.push({...a,...result,raw_sha256:sha(raw),source_sha256:sha(source),packed_sha256:sha(png),packed_bytes:png.length,
    warning:'Silhuettmaal er en diagnose. Det godkjenner ikke motiv, proporsjoner eller materialer.'});
  }
  fs.writeFileSync(art+'/packing-report.json',JSON.stringify({schema:1,assets:report},null,2)+'\n');
  console.log(JSON.stringify(report.map(a=>({id:a.id,iou:+a.silhouette_iou.toFixed(3),bytes:a.packed_bytes})),null,2));
 } finally {await b.close()}
})().catch(e=>{console.error(e);process.exitCode=1});
