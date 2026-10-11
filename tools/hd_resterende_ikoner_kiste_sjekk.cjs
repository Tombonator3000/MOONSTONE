/* Faktisk pakket skattekiste: felles master, eksakte CEL-soemmer og originalreferanse. */
'use strict';
const fs=require('fs'),path=require('path'),assert=require('assert/strict'),{chromium}=require('playwright'),pack=require('./hd_resterende_ikoner_canvas.cjs');
const root=path.resolve(__dirname,'..'),art=root+'/art/hd-remaining-icons-2026-10-11',dir=art+'/research/runtime';
(async()=>{
 const rows=JSON.parse(fs.readFileSync(art+'/packing-report.json')).assets.filter(a=>['ki.cel/031','ki.cel/032','ki.cel/033'].includes(a.key));assert.equal(rows.length,3);assert.equal(new Set(rows.map(a=>a.raw_sha256)).size,1);assert.equal(new Set(rows.map(a=>a.raw)).size,1);
 const orig=JSON.parse(fs.readFileSync(dir+'/source-contracts.json')),parts=rows.map(a=>({...a,png:fs.readFileSync(art+'/packed/'+a.key+'.png').toString('base64'),original:orig.entries.find(c=>c.key===a.key)}));
 const b=await chromium.launch({headless:true,executablePath:'/usr/bin/google-chrome',args:['--no-sandbox']});try{
  const p=await b.newPage(),full=await p.evaluate(pack,{raw:fs.readFileSync(art+'/'+rows[0].raw).toString('base64'),source:fs.readFileSync(art+'/'+rows[0].source).toString('base64'),w:472,h:424,scale:8,composite:{width:59,height:53,rect:[0,0,59,53]}});
  const result=await p.evaluate(async({parts,full,palette})=>{
   const canvas=(w,h)=>{const c=document.createElement('canvas');c.width=w;c.height=h;return c;},read=async b64=>{const im=new Image();im.src='data:image/png;base64,'+b64;await im.decode();return im;};
   const assembled=canvas(472,424),original=canvas(472,424),f=canvas(472,424);f.getContext('2d').drawImage(await read(full.png),0,0);const fp=f.getContext('2d').getImageData(0,0,472,424).data;let exact=0;
   for(const part of parts){const [x,y,w,h]=part.composite.rect,im=await read(part.png),c=canvas(im.width,im.height);c.getContext('2d').drawImage(im,0,0);assembled.getContext('2d').drawImage(im,x*8,y*8);const pix=c.getContext('2d').getImageData(0,0,c.width,c.height).data;
    for(let yy=0;yy<c.height;yy++)for(let xx=0;xx<c.width;xx++){const i=(yy*c.width+xx)*4,j=((y*8+yy)*472+x*8+xx)*4;if(![0,1,2,3].every(k=>pix[i+k]===fp[j+k]))throw Error(part.key+' har soemavvik');exact++;}
    const ctx=original.getContext('2d');for(let yy=0;yy<h;yy++)for(let xx=0;xx<w;xx++){const col=part.original.indices[yy*w+xx];if(!col)continue;ctx.fillStyle='rgb('+palette[col].slice(0,3).join(',')+')';ctx.fillRect((x+xx)*8,(y+yy)*8,8,8);}
   }
   const qa=canvas(984,464),ctx=qa.getContext('2d');ctx.fillStyle='#202020';ctx.fillRect(0,0,984,464);ctx.fillStyle='white';ctx.font='16px sans-serif';ctx.fillText('Original: tre CEL-ruter ved ekte kodekoordinater',10,22);ctx.fillText('HD: samme master, utsnitt og soemkoordinater',502,22);ctx.drawImage(original,10,32);ctx.drawImage(assembled,502,32);
   return{exact_pixels:exact,comparison_png:qa.toDataURL().split(',')[1],assembled_png:assembled.toDataURL().split(',')[1]};
  },{parts,full,palette:orig.palettes.inventory.palette});
  fs.writeFileSync(dir+'/chest-composite-comparison.png',Buffer.from(result.comparison_png,'base64'));fs.writeFileSync(dir+'/chest-packed-composite.png',Buffer.from(result.assembled_png,'base64'));
  const report={status:'passed',shared_raw:rows[0].raw,shared_raw_sha256:rows[0].raw_sha256,original_composite_size:[59,53],exact_fragment_pixels:result.exact_pixels,rects:rows.map(a=>({key:a.key,rect:a.composite.rect})),created_at:new Date().toISOString()};fs.writeFileSync(dir+'/chest-packed-test.json',JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report));
 }finally{await b.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
