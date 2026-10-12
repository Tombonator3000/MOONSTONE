/* Pakk bildegenererte materialer med kildebestemte logo-/stjerneformer. */
'use strict';
const fs=require('fs'),path=require('path'),crypto=require('crypto'),assert=require('assert/strict');
const {chromium}=require('playwright');
const root=path.resolve(__dirname,'..'),art=root+'/art/hd-completion-backgrounds-2026-10-11';
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
(async()=>{
 const contracts=JSON.parse(fs.readFileSync(art+'/source-contracts.json'));
 const browser=await chromium.launch({headless:true,executablePath:'/usr/bin/google-chrome',args:['--no-sandbox']});
 const report={schema:1,status:'packed_requires_runtime_and_visual_review',assets:[]};
 try{
  const page=await browser.newPage();
  for(const row of contracts.entries){
   const raw=fs.readFileSync(art+'/'+row.raw);
   const result=await page.evaluate(async({row,raw})=>{
    const im=new Image();im.src='data:image/png;base64,'+raw;await im.decode();
    const c=document.createElement('canvas');c.width=row.output_width;c.height=row.output_height;
    const ctx=c.getContext('2d');ctx.fillStyle='#000';ctx.fillRect(0,0,c.width,c.height);
    ctx.imageSmoothingQuality='high';let rect=[0,0,im.width,im.height];
    if(row.mode==='scroll_stars'){
     // Generatoren har svarte sidefelt rundt det komplette 320:1200-panelet.
     const panelWidth=im.height*320/1200;rect=[(im.width-panelWidth)/2,0,panelWidth,im.height];
    }
    ctx.drawImage(im,...rect,0,0,c.width,c.height);
    let sourceChecks=0;
    if(row.mode==='source_gold'){
     const data=ctx.getImageData(0,0,c.width,c.height),a=data.data,n=c.width*c.height;
     const nearest=new Int32Array(n);nearest.fill(-1);const queue=new Int32Array(n);let head=0,tail=0;
     for(let i=0;i<n;i++){const j=i*4,r=a[j],g=a[j+1],b=a[j+2];if(r>70&&r>g*1.005&&g>b*1.08+5){nearest[i]=i;queue[tail++]=i;}}
     if(!tail)throw Error('Mangler gyldig generert gullmateriale');
     while(head<tail){const i=queue[head++],x=i%c.width,y=(i/c.width)|0;
      for(const v of [x?i-1:-1,x<c.width-1?i+1:-1,y?i-c.width:-1,y<c.height-1?i+c.width:-1])
       if(v>=0&&nearest[v]<0){nearest[v]=nearest[i];queue[tail++]=v;}
     }
     const filled=new Uint8ClampedArray(a.length);
     for(let i=0;i<n;i++){const j=nearest[i]*4;filled.set([a[j],a[j+1],a[j+2],255],i*4);}
     const material=document.createElement('canvas');material.width=c.width;material.height=c.height;
     material.getContext('2d').putImageData(new ImageData(filled,c.width,c.height),0,0);
     ctx.fillStyle='#000';ctx.fillRect(0,0,c.width,c.height);ctx.save();ctx.scale(4,4);
     ctx.clip(new Path2D(row.clip),'evenodd');ctx.setTransform(1,0,0,1,0,0);ctx.drawImage(material,0,0);ctx.restore();
     ctx.save();ctx.scale(4,4);
     ctx.fillStyle='#fff';ctx.fill(new Path2D(row.text_clip),'evenodd');
     for(const p of row.text_paths){ctx.fillStyle='rgb('+row.palette[p.index].join(',')+')';ctx.fill(new Path2D(p.d),'evenodd');}
     ctx.restore();
     const pix=ctx.getImageData(0,0,c.width,c.height).data;
     for(let y=0;y<200;y++)for(let x=0;x<320;x++){
      const j=((y*4+2)*c.width+x*4+2)*4,v=row.indices[y*320+x];
      if(v===0&&pix[j]+pix[j+1]+pix[j+2]!==0)throw Error('Logoens originale hull er endret');
      if(v>0&&v<16&&pix[j]+pix[j+1]+pix[j+2]===0)throw Error('Logoens gullflate har et nytt hull');
      sourceChecks++;
     }
    }
    if(row.star_paths){
     ctx.save();ctx.scale(4,4);
     for(const p of row.star_paths){ctx.fillStyle='rgb('+row.palette[p.index].join(',')+')';ctx.fill(new Path2D(p.d),'evenodd');}
     ctx.restore();
     const a=ctx.getImageData(0,0,c.width,c.height).data;
     for(let y=0;y<row.height;y++)for(let x=0;x<row.width;x++){
      const col=row.star_indices[y*row.width+x];if(!col)continue;
      const j=((y*4+2)*c.width+x*4+2)*4,rgb=row.palette[col];
      if(rgb.some((v,k)=>Math.abs(a[j+k]-v)>1))throw Error('Stjernens kildefarge eller plassering er endret');sourceChecks++;
     }
    }
    return{png:c.toDataURL('image/png').split(',')[1],raw_rect:rect,master_size:[im.width,im.height],texture_size:[c.width,c.height],source_checks:sourceChecks};
   },{row,raw:raw.toString('base64')});
   const bytes=Buffer.from(result.png,'base64');delete result.png;
   const target=art+'/packed/'+row.key+'.png';fs.mkdirSync(path.dirname(target),{recursive:true});fs.writeFileSync(target,bytes);
   report.assets.push({...row,indices:undefined,star_indices:undefined,star_paths:undefined,text_paths:undefined,text_clip:undefined,clip:undefined,...result,raw_sha256:sha(raw),packed_sha256:sha(bytes),bytes:bytes.length});
  }
 }finally{await browser.close();}
 fs.writeFileSync(art+'/packing-report.json',JSON.stringify(report,null,2)+'\n');
 console.log(JSON.stringify(report.assets.map(r=>({key:r.key,size:r.texture_size,checks:r.source_checks}))));
})().catch(e=>{console.error(e);process.exitCode=1;});
