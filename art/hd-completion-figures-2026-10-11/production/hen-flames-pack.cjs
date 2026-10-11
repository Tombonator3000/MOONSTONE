/* Bevar hvert nytegnet flammes indre materiale og bind ytterformen til originalen. */
'use strict';
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const {chromium}=require('playwright');
const art=path.resolve(__dirname),sha=b=>crypto.createHash('sha256').update(b).digest('hex');
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:'/usr/bin/google-chrome',args:['--no-sandbox']});
 const report={schema:1,status:'packed_candidates_not_activated',assets:[]};
 try{
  const page=await browser.newPage();
  for(const row of JSON.parse(fs.readFileSync(art+'/hen-flames-geometries.json'))){
   const rawPath=art+'/raw/hen1-'+row.n+'-v1.png';if(!fs.existsSync(rawPath))continue;
   const raw=fs.readFileSync(rawPath);
   const result=await page.evaluate(async({row,raw})=>{
    const im=new Image();im.src='data:image/png;base64,'+raw;await im.decode();
    const tmp=document.createElement('canvas');tmp.width=im.width;tmp.height=im.height;
    const t=tmp.getContext('2d');t.drawImage(im,0,0);const pixels=t.getImageData(0,0,im.width,im.height).data;
    let x0=im.width,y0=im.height,x1=-1,y1=-1;
    for(let y=0;y<im.height;y++)for(let x=0;x<im.width;x++)if(pixels[(y*im.width+x)*4+3]>=128){x0=Math.min(x0,x);y0=Math.min(y0,y);x1=Math.max(x1,x);y1=Math.max(y1,y);}
    if(x1<x0)throw Error('Tom generering');
    const c=document.createElement('canvas');c.width=row.width*4;c.height=row.height*4;const ctx=c.getContext('2d');
    ctx.imageSmoothingQuality='high';ctx.drawImage(im,x0,y0,x1-x0+1,y1-y0+1,0,0,c.width,c.height);
    const a=ctx.getImageData(0,0,c.width,c.height).data,n=c.width*c.height,nearest=new Int32Array(n);nearest.fill(-1);
    const q=new Int32Array(n);let head=0,tail=0;
    for(let i=0;i<n;i++)if(a[i*4+3]>=128){nearest[i]=i;q[tail++]=i;}
    if(!tail)throw Error('Ingen dekkende flammemateriale');
    while(head<tail){const i=q[head++],x=i%c.width,y=(i/c.width)|0;
     for(const j of [x?i-1:-1,x<c.width-1?i+1:-1,y?i-c.width:-1,y<c.height-1?i+c.width:-1])
      if(j>=0&&nearest[j]<0){nearest[j]=nearest[i];q[tail++]=j;}
    }
    const fill=new Uint8ClampedArray(a.length);
    for(let i=0;i<n;i++){const j=nearest[i]*4;fill.set([a[j],a[j+1],a[j+2],255],i*4);}
    ctx.putImageData(new ImageData(fill,c.width,c.height),0,0);
    // De moerke kildefeltene under flammen skal ikke bli ny gul ild.
    // Bevar de opprinnelige palettflatene og geometrien uttrykkelig.
    ctx.save();ctx.scale(4,4);
    for(const region of row.preserved_dark_base){ctx.fillStyle='rgb('+region.rgb.join(',')+')';ctx.fill(new Path2D(region.clip),'evenodd');}
    ctx.restore();
    // En ett-piksel glod skal beholde arealet sitt, ikke bli en liten diamant.
    // Myk bare HD-randen0.4px; originalens binare silhuett blir uendret.
    const mask=document.createElement('canvas');mask.width=c.width;mask.height=c.height;const mc=mask.getContext('2d');mc.fillStyle='#fff';
    for(let y=0;y<row.height;y++)for(let x=0;x<row.width;x++)if(row.alpha[y*row.width+x])mc.fillRect(x*4,y*4,4,4);
    ctx.globalCompositeOperation='destination-in';ctx.filter='blur(0.4px)';ctx.drawImage(mask,0,0);ctx.filter='none';
    const output=ctx.getImageData(0,0,c.width,c.height).data;let opaque=0,empty=0;
    for(let y=0;y<row.height;y++)for(let x=0;x<row.width;x++){
     const expected=row.alpha[y*row.width+x]>0,actual=output[((y*4+2)*c.width+x*4+2)*4+3]>=128;
     if(expected!==actual)throw Error('Endret originalt alfa-midtpunkt');if(expected)opaque++;else empty++;
    }
    return{png:c.toDataURL('image/png').split(',')[1],raw_rect:[x0,y0,x1-x0+1,y1-y0+1],opaque,empty,width:c.width,height:c.height};
   },{row,raw:raw.toString('base64')});
   const png=Buffer.from(result.png,'base64');delete result.png;const rel=row.key;
   fs.mkdirSync(path.dirname(art+'/packed/'+rel),{recursive:true});fs.writeFileSync(art+'/packed/'+rel,png);
   report.assets.push({key:row.key,raw:'raw/hen1-'+row.n+'-v1.png',prompt:'prompts/hen1-'+row.n+'-v1.txt',
    raw_sha256:sha(raw),candidate_sha256:sha(png),source_indices_sha256:row.indices_sha256,...result,
    method:'individual_builtin_redraw_with_exact_source_alpha_soft_HD_edges_generated_edge_fill_and_preserved_dark_base'});
  }
 }finally{await browser.close();}
 fs.writeFileSync(art+'/verification/hen-flames-packing.json',JSON.stringify(report,null,2)+'\n');
 console.log(JSON.stringify(report.assets.map(r=>({key:r.key,size:[r.width,r.height],opaque:r.opaque,empty:r.empty}))));
})().catch(e=>{console.error(e);process.exitCode=1;});
