/* Pakk separat fotografisk hanske/terning med originalkontur og samme HD-bord. */
'use strict';
const fs=require('fs'),path=require('path'),crypto=require('crypto'),{chromium}=require('playwright');
const art=__dirname,root=path.resolve(art,'../../../..'),sha=b=>crypto.createHash('sha256').update(b).digest('hex');
(async()=>{
 const b=await chromium.launch({headless:true,executablePath:'/usr/bin/google-chrome',args:['--no-sandbox']});
 const report={status:'packed_candidates_not_activated',scope:'Hver rute bruker sitt eget genererte bilde.006..009 er hanske/arm,010..022 er tre kastede terninger. Originalens samlede graa objekt- og draktkontur bevares, med samme fotografiske bord som HD-bakgrunnen.',assets:[]};
 try{const p=await b.newPage();for(const c of JSON.parse(fs.readFileSync(art+'/geometries.json'))){
  const version=c.n==='010'?3:c.n==='011'?2:1,rawRel='raw/dice-'+c.n+'-v'+version+'.png',rawPath=art+'/'+rawRel;if(!fs.existsSync(rawPath))continue;
  const raw=fs.readFileSync(rawPath),bg=fs.readFileSync(root+'/art/hd-embedded-tavern-2026-10-11/raw/tav-clean-v1.png');
  const r=await p.evaluate(async({c,raw,bg})=>{
   async function read(base64){const im=new Image();im.src='data:image/png;base64,'+base64;await im.decode();return im;}
   const im=await read(raw),wood=await read(bg),w=c.width*4,h=c.height*4,cn=document.createElement('canvas');cn.width=w;cn.height=h;
   const ctx=cn.getContext('2d');ctx.imageSmoothingQuality='high';ctx.drawImage(im,0,0,w,h);const photo=ctx.getImageData(0,0,w,h).data;
   const woodCanvas=document.createElement('canvas');woodCanvas.width=w;woodCanvas.height=h;const wc=woodCanvas.getContext('2d');
   if(c.background_xy)wc.drawImage(wood,c.background_xy[0]/256*wood.width,c.background_xy[1]/200*wood.height,c.width/256*wood.width,c.height/200*wood.height,0,0,w,h);else wc.drawImage(im,0,0,w,h);
   const table=wc.getImageData(0,0,w,h).data,n=w*h;
   const material=i=>{const r=photo[i*4],g=photo[i*4+1],b=photo[i*4+2],hi=Math.max(r,g,b),lo=Math.min(r,g,b);return b>r*1.5&&b>g*1.25?'cloth':hi-lo<Math.max(22,hi*.35)&&hi>15?'steel':'wood';};
   const nearest={};for(const type of ['cloth','steel']){if(type==='cloth'&&!c.has_cloth)continue;const near=new Int32Array(n),q=new Int32Array(n);near.fill(-1);let a=0,z=0;for(let i=0;i<n;i++)if(material(i)===type&&photo[i*4+3]>128){near[i]=i;q[z++]=i;}if(!z)throw Error('Mangler generert '+type+' i '+c.key);
    while(a<z){const i=q[a++],x=i%w,y=(i/w)|0;for(const j of [x?i-1:-1,x+1<w?i+1:-1,y?i-w:-1,y+1<h?i+w:-1])if(j>=0&&near[j]<0){near[j]=near[i];q[z++]=j;}}
    nearest[type]=near;
   }
   ctx.clearRect(0,0,w,h);ctx.drawImage(woodCanvas,0,0);
   for(const type of ['steel','cloth']){
    if(type==='cloth'&&!c.has_cloth)continue;
    const layer=document.createElement('canvas');layer.width=w;layer.height=h;const lc=layer.getContext('2d'),data=lc.createImageData(w,h);
    for(let i=0;i<n;i++){const j=nearest[type][i]*4;data.data.set([photo[j],photo[j+1],photo[j+2],255],i*4);}
    lc.putImageData(data,0,0);const mask=document.createElement('canvas');mask.width=w;mask.height=h;const mc=mask.getContext('2d');mc.scale(4,4);mc.fill(new Path2D(type==='steel'?c.steel_clip:c.cloth_clip),'evenodd');lc.globalCompositeOperation='destination-in';lc.drawImage(mask,0,0);ctx.drawImage(layer,0,0);
   }
   // Bevar originalens gjennomsiktige kildepunkter;008..022 har faste graa farger, ikke draktmaske.
   const alpha=ctx.getImageData(0,0,w,h);for(let y=0;y<h;y++)for(let x=0;x<w;x++)if(!c.indices[(y/4|0)*c.width+(x/4|0)])alpha.data[(y*w+x)*4+3]=0;ctx.putImageData(alpha,0,0);
   // Smaa isolerte kildepiksler skal beholde hele arealet sitt ved alfa-pakking.
   const img=ctx.getImageData(0,0,w,h);let opaque=0,empty=0;
   for(let y=0;y<c.height;y++)for(let x=0;x<c.width;x++){const expected=c.indices[y*c.width+x]!==0,j=((y*4+2)*w+x*4+2)*4;if(expected&&img.data[j+3]<128)throw Error('Tapt kildepunkt '+c.key);if(!expected&&img.data[j+3]>=128)throw Error('Fylt kildehull '+c.key);if(expected)opaque++;else empty++;}
   return{png:cn.toDataURL('image/png').split(',')[1],opaque_source_centers:opaque,empty_source_centers:empty,raw_size:[im.width,im.height],target_size:[w,h]};
  },{c,raw:raw.toString('base64'),bg:bg.toString('base64')});
  const png=Buffer.from(r.png,'base64');delete r.png;const dest=art+'/packed/'+c.key;fs.mkdirSync(path.dirname(dest),{recursive:true});fs.writeFileSync(dest,png);report.assets.push({key:c.key,raw:rawRel,prompt:'prompts/dice-'+c.n+'-v'+version+'.txt',raw_sha256:sha(raw),candidate_sha256:sha(png),source_indices_sha256:c.source_indices_sha256,background_sha256:sha(bg),background:'art/hd-embedded-tavern-2026-10-11/raw/tav-clean-v1.png',identity:Number(c.n)<10?'hanske/arm':'tre kastede terninger',...r});
 }}finally{await b.close();}
 fs.writeFileSync(art+'/verification/packing.json',JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report.assets));
})().catch(e=>{console.error(e);process.exitCode=1;});
