/* Kildebundet pakking av eget fotografisk materiale for hver kartdragerute. */
'use strict';
const fs=require('fs'),path=require('path'),crypto=require('crypto'),{chromium}=require('playwright');
const art=__dirname,root=path.resolve(art,'../../../..'),sha=b=>crypto.createHash('sha256').update(b).digest('hex');
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:'/usr/bin/google-chrome',args:['--no-sandbox']});
 const report={status:'packed_candidates_not_activated',scope:'Ett separat generert fotografisk raabilde per originalrute. Originalens roede kropp, brune vinger og lyse underside styrer materialkonturene; originalankre og alfa beholdes. Ingen paastand om fri kontur-nytegning.',assets:[]};
 try{const page=await browser.newPage();for(const c of JSON.parse(fs.readFileSync(art+'/geometries.json'))){
  const rawRel='raw/'+c.number+'-v1.png',raw=fs.readFileSync(art+'/'+rawRel);
  const result=await page.evaluate(async({c,raw})=>{
   const im=new Image();im.src='data:image/png;base64,'+raw;await im.decode();
   const w=c.width*4,h=c.height*4,canvas=document.createElement('canvas');canvas.width=w;canvas.height=h;
   const ctx=canvas.getContext('2d');ctx.imageSmoothingQuality='high';ctx.drawImage(im,0,0,w,h);
   const photo=ctx.getImageData(0,0,w,h).data,n=w*h;
   const material=i=>{const r=photo[i*4],g=photo[i*4+1],b=photo[i*4+2];if(photo[i*4+3]<128)return null;if(r>g*1.65&&r>b*1.55)return'red';if(Math.max(r,g,b)>100&&r-g<70&&g>b*1.1)return'pale';return'wing';};
   ctx.clearRect(0,0,w,h);const sourceCounts={},materialMeans={},rgbSum=new Float32Array(n*3),weightSum=new Float32Array(n);
   for(const type of ['wing','red','pale']){
    const nearest=new Int32Array(n),queue=new Int32Array(n);nearest.fill(-1);let start=0,end=0;
    let sum=0;for(let i=0;i<n;i++)if(material(i)===type){nearest[i]=i;queue[end++]=i;sum+=.2126*photo[i*4]+.7152*photo[i*4+1]+.0722*photo[i*4+2];}sourceCounts[type]=end;materialMeans[type]=sum/Math.max(1,end);
    if(!end)throw Error('Mangler generert materiale '+type+' i '+c.key);
    while(start<end){const i=queue[start++],x=i%w,y=(i/w)|0;for(const j of [x?i-1:-1,x+1<w?i+1:-1,y?i-w:-1,y+1<h?i+w:-1])if(j>=0&&nearest[j]<0){nearest[j]=nearest[i];queue[end++]=j;}}
    const layer=document.createElement('canvas');layer.width=w;layer.height=h;const lc=layer.getContext('2d'),data=lc.createImageData(w,h);
    for(let i=0;i<n;i++){const j=nearest[i]*4;data.data.set([photo[j],photo[j+1],photo[j+2],255],i*4);}lc.putImageData(data,0,0);
    const mask=document.createElement('canvas');mask.width=w;mask.height=h;const mc=mask.getContext('2d');mc.scale(4,4);mc.fill(new Path2D(c.materials[type]),'evenodd');
    const alpha=mc.getImageData(0,0,w,h).data;for(let i=0;i<n;i++){const weight=alpha[i*4+3]/255;weightSum[i]+=weight;for(let k=0;k<3;k++)rgbSum[i*3+k]+=data.data[i*4+k]*weight;}
   }
   const outer=document.createElement('canvas');outer.width=w;outer.height=h;const oc=outer.getContext('2d');oc.scale(4,4);oc.fill(new Path2D(c.alpha_path),'evenodd');const a=oc.getImageData(0,0,w,h).data,data=ctx.createImageData(w,h);
   for(let i=0;i<n;i++){for(let k=0;k<3;k++)data.data[i*4+k]=rgbSum[i*3+k]/Math.max(.001,weightSum[i]);data.data[i*4+3]=a[i*4+3];}ctx.putImageData(data,0,0);
   const pixels=ctx.getImageData(0,0,w,h);let opaque=0,empty=0;
   // Originalindeksen styrer materialets lyse/morke fargeforhold. Fotoet gir
   // mikrovariasjon; ikke la lyse hudprover bli lyse omriss rundt hele dragen.
   for(let y=0;y<h;y++)for(let x=0;x<w;x++){
    let index=c.indices[(y/4|0)*c.width+(x/4|0)];const j=(y*w+x)*4;if(!pixels.data[j+3])continue;
    if(!index){let best=Infinity;for(let yy=Math.max(0,(y/4|0)-1);yy<=Math.min(c.height-1,(y/4|0)+1);yy++)for(let xx=Math.max(0,(x/4|0)-1);xx<=Math.min(c.width-1,(x/4|0)+1);xx++){const si=c.indices[yy*c.width+xx],d=(xx+.5-(x+.5)/4)**2+(yy+.5-(y+.5)/4)**2;if(si&&d<best){index=si;best=d;}}}if(!index)continue;
    const typeFor=i=>i===28?'red':i>=16?'wing':i>0?'pale':null;
    const type=typeFor(index),sourceX=(x+.5)/4-.5,sourceY=(y+.5)/4-.5;
    // Kontinuerlig original skyggefordeling innen samme materiale. Ikke glatt
    // over mellom roed kropp, brune vinger og lys underside.
    let weight=0,ref=[0,0,0];
    for(let yy=Math.floor(sourceY)-1;yy<=Math.floor(sourceY)+2;yy++)for(let xx=Math.floor(sourceX)-1;xx<=Math.floor(sourceX)+2;xx++){
     if(xx<0||yy<0||xx>=c.width||yy>=c.height)continue;const si=c.indices[yy*c.width+xx];if(typeFor(si)!==type)continue;
     const d=(xx-sourceX)**2+(yy-sourceY)**2,k=Math.exp(-d/1.25);weight+=k;for(let ch=0;ch<3;ch++)ref[ch]+=c.palette[si][ch]*k;
    }
    ref=ref.map(v=>v/weight);const base=.2126*ref[0]+.7152*ref[1]+.0722*ref[2];
    const factor=base/Math.max(1,materialMeans[type]);
    for(let k=0;k<3;k++)pixels.data[j+k]=Math.round(Math.min(255,ref[k]*.30+pixels.data[j+k]*factor*.70));
   }
   ctx.putImageData(pixels,0,0);
   for(let y=0;y<c.height;y++)for(let x=0;x<c.width;x++){const index=c.indices[y*c.width+x],j=((y*4+2)*w+x*4+2)*4;if(index&&pixels.data[j+3]<128)throw Error('Tapt kildepunkt');if(!index&&pixels.data[j+3]>=128)throw Error('Fylt kildehull');index?opaque++:empty++;}
   return{png:canvas.toDataURL('image/png').split(',')[1],source_material_pixels:sourceCounts,source_centers_opaque:opaque,source_centers_empty:empty,raw_size:[im.width,im.height],target_size:[w,h]};
  },{c,raw:raw.toString('base64')});
  const png=Buffer.from(result.png,'base64');delete result.png;const destination=art+'/packed/'+c.key;fs.mkdirSync(path.dirname(destination),{recursive:true});fs.writeFileSync(destination,png);
  report.assets.push({key:c.key,raw:rawRel,raw_sha256:sha(raw),prompt:'prompts/'+c.number+'-v1.txt',candidate_sha256:sha(png),source_indices_sha256:c.indices_sha256,...result});
 }}finally{await browser.close();}
 fs.mkdirSync(art+'/verification',{recursive:true});fs.writeFileSync(art+'/verification/packing.json',JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({status:report.status,assets:report.assets.length}));
})().catch(e=>{console.error(e);process.exitCode=1;});
