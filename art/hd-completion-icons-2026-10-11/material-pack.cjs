/* Fotografiske materialer i frosne kildekonturer. Ingen nye motivkonturer tegnes. */
'use strict';
const fs=require('fs'),path=require('path'),crypto=require('crypto'),{chromium}=require('playwright');
const art=__dirname,root=path.resolve(art,'../..'),sha=b=>crypto.createHash('sha256').update(b).digest('hex');
async function materialPack({raw,free,native,c,m,g}){
 const read=async data=>{const im=new Image();im.src='data:image/png;base64,'+data;await im.decode();const canvas=document.createElement('canvas');canvas.width=im.width;canvas.height=im.height;canvas.getContext('2d').drawImage(im,0,0);return canvas;};
 const original=await read(raw),photo=original.getContext('2d').getImageData(0,0,original.width,original.height),w=c.width*8,h=c.height*8;
 const out=document.createElement('canvas');out.width=w;out.height=h;const ctx=out.getContext('2d');
 const group=(r,gg,b)=>c.source.file==='ki.cel'?(gg>r*1.1&&gg>b*1.05?'leaf':'bark'):(Math.abs(r-gg)<60&&gg-b>=0&&gg-b<65&&!(gg>r*1.1)?'light':'field');
 const samples={},cropReports=[];
 const materialMode=c.source.file!=='mys.cel';
 if(materialMode){
  const required=g.groups.map(x=>x.material);
  // Maksimalt helt ugjennomsiktig rektangel gir ekte, sammenhengende fotomateriale.
  for(const name of required){
   const heights=new Int32Array(original.width);let best=[0,0,0,0],area=0;
   for(let y=0;y<original.height;y++){
    for(let x=0;x<original.width;x++){const q=(y*original.width+x)*4,p=photo.data;heights[x]=p[q+3]>245&&group(p[q],p[q+1],p[q+2])===name?heights[x]+1:0;}
    const stack=[];
    for(let x=0;x<=original.width;x++){const ht=x===original.width?0:heights[x];let start=x;while(stack.length&&stack.at(-1)[1]>ht){const [s,hh]=stack.pop(),a=(x-s)*hh;if(a>area){area=a;best=[s,y-hh+1,x-s,hh];}start=s;}if(!stack.length||stack.at(-1)[1]<ht)stack.push([start,ht]);}
   }
   if(area<16)throw Error('For lite fotografisk materiale '+c.key+' '+name);
   const [x,y,cw,ch]=best,tile=document.createElement('canvas');
   // Bevar naturlig materialstruktur i et repeterende atlas, ikke AI-motivets geometri.
   const side=Math.min(cw,ch),square=[x+Math.floor((cw-side)/2),y+Math.floor((ch-side)/2),side,side];tile.width=tile.height=Math.min(192,side);tile.getContext('2d').drawImage(original,...square,0,0,tile.width,tile.height);
   const d=tile.getContext('2d').getImageData(0,0,tile.width,tile.height).data;let lum=0,mean=[0,0,0];for(let i=0;i<d.length;i+=4){lum+=.2126*d[i]+.7152*d[i+1]+.0722*d[i+2];for(let k=0;k<3;k++)mean[k]+=d[i+k];}lum/=d.length/4;mean=mean.map(v=>v/(d.length/4));
   samples[name]={tile,d,lum,mean};cropReports.push({material:name,raw_rect:square,max_opaque_rect:best,tile_size:[tile.width,tile.height],mean_luminance:lum,mean_rgb:mean,opaque_crop_area:area});
  }
  // Farge-/lysregionene kommer fra originalruten; bare mikromateriale kommer fra generatoren.
  const materialCanvas=document.createElement('canvas');materialCanvas.width=w;materialCanvas.height=h;
  const source=await read(native),lighting=document.createElement('canvas');lighting.width=w;lighting.height=h;const lightingCtx=lighting.getContext('2d');lightingCtx.imageSmoothingEnabled=true;lightingCtx.imageSmoothingQuality='high';lightingCtx.drawImage(source,0,0,w,h);const light=lightingCtx.getImageData(0,0,w,h).data;
  for(const region of g.groups){
   const name=region.material,s=samples[name],layer=materialCanvas.getContext('2d').createImageData(w,h),rgb=region.source_indices.reduce((sum,i)=>sum.map((v,k)=>v+c.palette[i][k]/region.source_indices.length),[0,0,0]);
   const lums=region.source_indices.map(i=>.2126*c.palette[i][0]+.7152*c.palette[i][1]+.0722*c.palette[i][2]),minLum=Math.min(...lums),maxLum=Math.max(...lums);
   for(let y=0;y<h;y++)for(let x=0;x<w;x++){
    const n=(y*w+x)*4,q=((y%s.tile.height)*s.tile.width+x%s.tile.width)*4;
    const base=.2126*light[n]+.7152*light[n+1]+.0722*light[n+2],bounded=Math.max(minLum,Math.min(maxLum,base)),target=c.source.file==='ki.cel'?Math.max(18,bounded):Math.max(8,bounded);
    const local=.2126*s.d[q]+.7152*s.d[q+1]+.0722*s.d[q+2],ratio=target/s.lum;
    const contrast=c.source.file==='ki.cel'?.7:.25;
    for(let k=0;k<3;k++){const natural=(s.mean[k]+(s.d[q+k]-s.mean[k])*contrast)*ratio,exact=rgb[k]*(1+contrast*(local/s.lum-1));layer.data[n+k]=Math.max(0,Math.min(255,Math.round(natural*.7+exact*.3)));}
    layer.data[n+3]=255;
   }
   materialCanvas.getContext('2d').putImageData(layer,0,0);
   // Ett separat masklager behoevs fordi disjunkta konturer ikke skal skjare hverandre.
   const mask=document.createElement('canvas');mask.width=w;mask.height=h;const mc=mask.getContext('2d');mc.scale(8,8);mc.fillStyle='#fff';mc.fill(new Path2D(region.d),'evenodd');
   const l=document.createElement('canvas');l.width=w;l.height=h;const lc=l.getContext('2d');lc.drawImage(materialCanvas,0,0);lc.globalCompositeOperation='destination-in';lc.drawImage(mask,0,0);ctx.drawImage(l,0,0);
  }
 }else{
  const f=await read(free);ctx.drawImage(f,0,0,w,h);
  const d=ctx.getImageData(0,0,w,h),queue=new Int32Array(w*h),near=new Int32Array(w*h);near.fill(-1);let head=0,tail=0;
  for(let n=0;n<w*h;n++)if(d.data[n*4+3]>220){near[n]=n;queue[tail++]=n;}
  while(head<tail){const n=queue[head++],x=n%w,y=Math.floor(n/w);for(const nn of [x?n-1:-1,x+1<w?n+1:-1,y?n-w:-1,y+1<h?n+w:-1])if(nn>=0&&near[nn]<0){near[nn]=near[n];queue[tail++]=nn;}}
  for(let n=0;n<w*h;n++)if(d.data[n*4+3]<255){const q=near[n]*4;for(let k=0;k<3;k++)d.data[n*4+k]=d.data[q+k];d.data[n*4+3]=255;}
  ctx.putImageData(d,0,0);
 }
 const mask=document.createElement('canvas');mask.width=w;mask.height=h;const mc=mask.getContext('2d');mc.scale(8,8);mc.fillStyle='#fff';mc.fill(new Path2D(m.clip),'evenodd');ctx.globalCompositeOperation='destination-in';ctx.drawImage(mask,0,0);ctx.globalCompositeOperation='source-over';
 const pixels=ctx.getImageData(0,0,w,h).data;let covered=0,expected=0,empty=0,emptyCorrect=0;
 for(let y=0;y<c.height;y++)for(let x=0;x<c.width;x++){const i=c.indices[y*c.width+x],q=((y*8+4)*w+x*8+4)*4;if(i){expected++;if(pixels[q+3]>=250)covered++;}else{empty++;if(pixels[q+3]===0)emptyCorrect++;}}
 return{png:out.toDataURL('image/png').split(',')[1],texture_size:[w,h],material_crops:cropReports,packing_method:materialMode?'photographic_material_in_source_semantic_contours':'source_clipped_photo_with_nearest_edge_coverage',source_pixel_centers:{covered,expected,empty,emptyCorrect}};
}
(async()=>{
 const fragment=JSON.parse(fs.readFileSync(art+'/fragment-icons.json')),sources=JSON.parse(fs.readFileSync(art+'/source-contracts.json')),geometries=JSON.parse(fs.readFileSync(art+'/material-geometries.json'));
 const browser=await chromium.launch({headless:true,executablePath:'/usr/bin/google-chrome',args:['--no-sandbox']});const report={schema:1,scope:'Kildebundne konturer og separat imagegen-fotomateriale. Ikke en fritegnet motivnytolkning.',assets:[]};
 try{const p=await browser.newPage();for(const m of fragment.entries){const c=sources.entries.find(c=>c.key===m.key),g=geometries.entries.find(g=>g.key===m.key),raw=fs.readFileSync(art+'/raw/'+m.key+'.png'),native=fs.readFileSync(art+'/references/'+m.key+'-native.png'),free=fs.readFileSync(art+'/free-pack/'+m.key+'.png');const r=await p.evaluate(materialPack,{raw:raw.toString('base64'),free:free.toString('base64'),native:native.toString('base64'),c,m,g});const png=Buffer.from(r.png,'base64');delete r.png;const dest=art+'/packed/'+m.key+'.png';fs.mkdirSync(path.dirname(dest),{recursive:true});fs.writeFileSync(dest,png);report.assets.push({key:m.key,source:c.source,original_size:[c.width,c.height],indices_sha256:c.indices_sha256,raw_sha256:sha(raw),packed_sha256:sha(png),...r});}}finally{await browser.close();}
 report.fragment_icons_sha256=sha(fs.readFileSync(art+'/fragment-icons.json'));report.source_contracts_sha256=sha(fs.readFileSync(art+'/source-contracts.json'));fs.writeFileSync(art+'/packing-report.json',JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report.assets.map(a=>({key:a.key,centers:a.source_pixel_centers}))));
})().catch(e=>{console.error(e);process.exitCode=1;});
