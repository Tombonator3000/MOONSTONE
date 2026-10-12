/* Eget fotografi per originalrute, kildekontur og original kampbelysning. */
'use strict';
const fs=require('fs'),path=require('path'),crypto=require('crypto'),{chromium}=require('playwright');
const here=__dirname,sha=b=>crypto.createHash('sha256').update(b).digest('hex'),selected=process.env.MOONSTONE_BEAST_FRAMES?process.env.MOONSTONE_BEAST_FRAMES.split(',').map(Number):JSON.parse(fs.readFileSync(here+'/geometries-v2.json')).map(c=>c.frame);
const geometryBytes=fs.readFileSync(here+'/geometries-v2.json'),geometries=JSON.parse(geometryBytes),records=JSON.parse(fs.readFileSync(here+'/generation-records-v2.json'));
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:'/usr/bin/google-chrome',args:['--no-sandbox']});
 const report={schema:1,status:'packed_candidates_not_activated',scope:'Each route uses its own generated photographic master. Original source contours, transparent holes, silhouette and anchors are retained; source-bound material registration and original source material regions, photographic black mane detail and smoothed original skin/bone/eye light, with separately preserved flat black source shadows. This is not a claim of freehand redrawn geometry.',packing_script_sha256:sha(fs.readFileSync(__filename)),geometry_sha256:sha(geometryBytes),generation_records_sha256:sha(fs.readFileSync(here+'/generation-records-v2.json')),assets:[]};
 try{const page=await browser.newPage();for(const c of geometries.filter(c=>selected.includes(c.frame))){
 const rawRel='raw/'+c.number+'-v1.png',raw=fs.readFileSync(here+'/'+rawRel),promptRel='prompts/'+c.number+'-v1.txt';
 const record=records.find(r=>r.key===c.key);if(!record||record.generation_tool!=='builtin_image_gen'||record.raw!==rawRel||record.raw_sha256!==sha(raw)||record.prompt!==promptRel||record.prompt_sha256!==sha(fs.readFileSync(here+'/'+promptRel)))throw Error('Stale generation record '+c.key);
 const result=await page.evaluate(async({c,raw})=>{
  const im=new Image();im.src='data:image/png;base64,'+raw;await im.decode();const w=c.width*4,h=c.height*4,n=w*h,canvas=document.createElement('canvas');canvas.width=w;canvas.height=h;const ctx=canvas.getContext('2d');ctx.imageSmoothingQuality='high';
  const rc=document.createElement('canvas');rc.width=im.width;rc.height=im.height;const rctx=rc.getContext('2d');rctx.drawImage(im,0,0);const rp=rctx.getImageData(0,0,im.width,im.height).data;let bx=im.width,by=im.height,ex=0,ey=0;
  for(let y=0;y<im.height;y++)for(let x=0;x<im.width;x++)if(rp[(y*im.width+x)*4+3]>=128){bx=Math.min(bx,x);by=Math.min(by,y);ex=Math.max(ex,x+1);ey=Math.max(ey,y+1);}if(ex<=bx||ey<=by)throw Error('Empty raw '+c.key);
  const b=c.source_alpha_bounds;ctx.drawImage(im,bx,by,ex-bx,ey-by,b[0]*4,b[1]*4,(b[2]-b[0])*4,(b[3]-b[1])*4);const photo=ctx.getImageData(0,0,w,h).data;
  const material=i=>{
   if(photo[i*4+3]<128)return null;
   const r=photo[i*4],g=photo[i*4+1],b=photo[i*4+2],L=.2126*r+.7152*g+.0722*b;
   if(r>55&&r>g*3&&r>b*3)return 'eye';
   if(g>r*1.2&&b>r*1.2&&Math.max(g,b)>65)return 'mouth';
   if(L>145&&Math.max(r,g,b)<Math.min(r,g,b)*1.5)return 'bone';
   if(L>35&&Math.max(r,g,b)<Math.min(r,g,b)*1.6)return 'muzzle';
   if(r>g*1.25&&r>b*1.4)return 'hide';
   return 'fur';
  };
  const counts={},means={},rgb=new Float32Array(n*3),weights=new Float32Array(n);
  for(const type of Object.keys(c.materials)){
   const nearest=new Int32Array(n).fill(-1),queue=new Int32Array(n);let start=0,end=0,sum=0;
   for(let i=0;i<n;i++)if(material(i)===type){nearest[i]=i;queue[end++]=i;sum+=.2126*photo[i*4]+.7152*photo[i*4+1]+.0722*photo[i*4+2];}counts[type]=end;means[type]=sum/Math.max(1,end);if(!end)throw Error('Missing photographic '+type+' '+c.key);
   while(start<end){const i=queue[start++],x=i%w,y=i/w|0;for(const j of [x?i-1:-1,x+1<w?i+1:-1,y?i-w:-1,y+1<h?i+w:-1])if(j>=0&&nearest[j]<0){nearest[j]=nearest[i];queue[end++]=j;}}
   const mask=document.createElement('canvas');mask.width=w;mask.height=h;const mc=mask.getContext('2d');mc.scale(4,4);mc.fill(new Path2D(c.materials[type]),'evenodd');const alpha=mc.getImageData(0,0,w,h).data;
   for(let i=0;i<n;i++){const weight=alpha[i*4+3]/255,j=nearest[i]*4;weights[i]+=weight;for(let k=0;k<3;k++)rgb[i*3+k]+=photo[j+k]*weight;}
  }
  ctx.clearRect(0,0,w,h);ctx.save();ctx.scale(4,4);ctx.fill(new Path2D(c.alpha_path),'evenodd');ctx.restore();const outer=ctx.getImageData(0,0,w,h).data,data=ctx.createImageData(w,h);
  let opaque=0,empty=0,stoneCenters=0;
  for(let y=0;y<h;y++)for(let x=0;x<w;x++){
   const i=y*w+x,j=i*4;data.data[j+3]=outer[j+3];if(!outer[j+3])continue;
   let q=(y/4|0)*c.width+(x/4|0),index=c.indices[q],label=c.material_labels[q];
   if(!index){let best=Infinity;const xx=x/4|0,yy=y/4|0;for(let sy=Math.max(0,yy-1);sy<=Math.min(c.height-1,yy+1);sy++)for(let sx=Math.max(0,xx-1);sx<=Math.min(c.width-1,xx+1);sx++){const k=sy*c.width+sx,d=(sx+.5-(x+.5)/4)**2+(sy+.5-(y+.5)/4)**2;if(c.indices[k]&&d<best){q=k;index=c.indices[k];label=c.material_labels[k];best=d;}}}
   if(!index)continue;const type=({1:'fur',2:'hide',3:'bone',4:'eye',6:'mouth',7:'muzzle'})[label],sx=(x+.5)/4-.5,sy=(y+.5)/4-.5;let weight=0,ref=[0,0,0];
   for(let yy=Math.floor(sy)-1;yy<=Math.floor(sy)+2;yy++)for(let xx=Math.floor(sx)-1;xx<=Math.floor(sx)+2;xx++){
    if(xx<0||yy<0||xx>=c.width||yy>=c.height)continue;const k=yy*c.width+xx;if(c.material_labels[k]!==label)continue;const d=(xx-sx)**2+(yy-sy)**2,t=Math.exp(-d/1.25);weight+=t;for(let ch=0;ch<3;ch++)ref[ch]+=c.palette[c.indices[k]][ch]*t;
   }
   ref=ref.map(v=>v/Math.max(.001,weight));if(type==='fur'&&Math.max(...ref)<8)ref=[8,8,7];const sample=[0,1,2].map(k=>rgb[i*3+k]/Math.max(.001,weights[i])),L=.2126*sample[0]+.7152*sample[1]+.0722*sample[2],base=.2126*ref[0]+.7152*ref[1]+.0722*ref[2],relative=Math.max(.35,Math.min(1.8,L/Math.max(1,means[type]))),target=base*(.35+.65*relative);
   // Originalens materialomraader og lys beholdes. Eget foto gir overflatedetaljer.
   for(let k=0;k<3;k++)data.data[j+k]=type==='fur'?Math.min(90,sample[k]):Math.min(255,ref[k]*(.35+.65*relative));
  }
  // Noyaktige svarte originalskygger beholdes som kildedekorasjon.
  for(const q of c.flat_shadow)for(let dy=0;dy<4;dy++)for(let dx=0;dx<4;dx++){
   const i=((Math.floor(q/c.width)*4+dy)*w+(q%c.width*4+dx))*4;
   data.data[i]=data.data[i+1]=data.data[i+2]=0;data.data[i+3]=255;
  }
  ctx.putImageData(data,0,0);
  for(let y=0;y<c.height;y++)for(let x=0;x<c.width;x++){const q=y*c.width+x,i=((y*4+2)*w+x*4+2)*4;if(c.indices[q]&&data.data[i+3]<128)throw Error('Lost source center '+c.key);if(!c.indices[q]&&data.data[i+3]>=128)throw Error('Filled source hole '+c.key);if(c.indices[q])opaque++;else empty++;}
  return{png:canvas.toDataURL('image/png').split(',')[1],raw_size:[im.width,im.height],raw_alpha_bounds:[bx,by,ex,ey],target_size:[w,h],source_centers_opaque:opaque,source_centers_empty:empty,original_flat_shadow_cells:c.flat_shadow.length,source_material_pixels:counts};
 },{c,raw:raw.toString('base64')});
 const png=Buffer.from(result.png,'base64');delete result.png;const dest=here+'/packed-v2/'+c.key;fs.mkdirSync(path.dirname(dest),{recursive:true});fs.writeFileSync(dest,png);
 report.assets.push({key:c.key,raw:rawRel,raw_sha256:sha(raw),prompt:promptRel,prompt_sha256:sha(fs.readFileSync(here+'/'+promptRel)),candidate_sha256:sha(png),source_indices_sha256:c.indices_sha256,source_bank_sha256:c.source_bank_sha256,...result});
 }}finally{await browser.close();}
 if(new Set(report.assets.map(a=>a.raw_sha256)).size!==report.assets.length)throw Error('Reused generated master');fs.mkdirSync(here+'/verification',{recursive:true});const reportName='packing-v2.json';fs.writeFileSync(here+'/verification/'+reportName,JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({status:report.status,assets:report.assets.length}));
})().catch(e=>{console.error(e);process.exitCode=1;});
