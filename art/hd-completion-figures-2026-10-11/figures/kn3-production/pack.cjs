/* Pakk faktisk ny imagegen-grafikk til originalens uendrede tegnerektangel. */
'use strict';
const fs=require('fs'),path=require('path'),crypto=require('crypto'),{chromium}=require('playwright');
const art=__dirname,root=path.resolve(art,'../../../..'),figures=path.resolve(art,'../..');
const pack=require(root+'/tools/hd_resterende_ikoner_canvas.cjs'),sha=b=>crypto.createHash('sha256').update(b).digest('hex');
async function coverOriginal({png,c}){
 const im=new Image();im.src='data:image/png;base64,'+png;await im.decode();const out=document.createElement('canvas');out.width=c.target_width;out.height=c.target_height;const ctx=out.getContext('2d');ctx.drawImage(im,0,0);const d=ctx.getImageData(0,0,out.width,out.height),w=out.width,h=out.height,near=new Int32Array(w*h),queue=new Int32Array(w*h);near.fill(-1);let head=0,tail=0;
 // Utvid bare det nygenererte materialets kantfarge til den frosne kildeformen.
 for(let n=0;n<w*h;n++)if(d.data[n*4+3]>=220){near[n]=n;queue[tail++]=n;}
 while(head<tail){const n=queue[head++],x=n%w,y=Math.floor(n/w);for(const nn of [x?n-1:-1,x+1<w?n+1:-1,y?n-w:-1,y+1<h?n+w:-1])if(nn>=0&&near[nn]<0){near[nn]=near[n];queue[tail++]=nn;}}
 if(!tail)throw Error('Ingen ugjennomsiktig generert kjerne '+c.key);
 for(let n=0;n<w*h;n++){if(d.data[n*4+3]<255){const q=near[n]*4;for(let k=0;k<3;k++)d.data[n*4+k]=d.data[q+k];}d.data[n*4+3]=255;}ctx.putImageData(d,0,0);
 // Originalens blodindeks15 henter bare roedt fotomateriale fra dette nye bildet.
 // Ingen syntetisk roedfarge eller nye blodformer tilfoeyes.
 if(c.blood_path){const redNear=new Int32Array(w*h),redQueue=new Int32Array(w*h);redNear.fill(-1);let rh=0,rt=0;for(let n=0;n<w*h;n++){const k=n*4;if(d.data[k]>30&&d.data[k]>d.data[k+1]*1.5&&d.data[k]>d.data[k+2]*1.5){redNear[n]=n;redQueue[rt++]=n;}}if(!rt)throw Error('Mangler faktisk generert roedt blodmateriale '+c.key);while(rh<rt){const n=redQueue[rh++],x=n%w,y=Math.floor(n/w);for(const nn of [x?n-1:-1,x+1<w?n+1:-1,y?n-w:-1,y+1<h?n+w:-1])if(nn>=0&&redNear[nn]<0){redNear[nn]=redNear[n];redQueue[rt++]=nn;}}
 const layer=document.createElement('canvas');layer.width=w;layer.height=h;const lc=layer.getContext('2d'),ld=lc.createImageData(w,h);for(let n=0;n<w*h;n++){const k=n*4,q=redNear[n]*4;for(let j=0;j<3;j++)ld.data[k+j]=d.data[q+j];ld.data[k+3]=255;}lc.putImageData(ld,0,0);const m=document.createElement('canvas');m.width=w;m.height=h;const mc=m.getContext('2d');mc.scale(4,4);mc.fill(new Path2D(c.blood_path),'evenodd');lc.globalCompositeOperation='destination-in';lc.drawImage(m,0,0);ctx.drawImage(layer,0,0);}
 // Originalens opake svarte og moerke fragmenter maa ikke bli til ekstra soelvblad.
 for(const region of c.dark_paths||[]){const layer=document.createElement('canvas');layer.width=w;layer.height=h;const lc=layer.getContext('2d'),ld=lc.createImageData(w,h),factor=region.index===5?.035:.3;for(let i=0;i<d.data.length;i+=4){for(let k=0;k<3;k++)ld.data[i+k]=Math.round(d.data[i+k]*factor);ld.data[i+3]=255;}lc.putImageData(ld,0,0);const dm=document.createElement('canvas');dm.width=w;dm.height=h;const dc=dm.getContext('2d');dc.scale(4,4);dc.fill(new Path2D(region.d),'evenodd');lc.globalCompositeOperation='destination-in';lc.drawImage(dm,0,0);ctx.drawImage(layer,0,0);}
 const mask=document.createElement('canvas');mask.width=w;mask.height=h;const mc=mask.getContext('2d');mc.scale(4,4);mc.fill(new Path2D(c.clip),'evenodd');ctx.globalCompositeOperation='destination-in';ctx.drawImage(mask,0,0);
 const pixels=ctx.getImageData(0,0,w,h).data;let covered=0,expected=0,empty=0,emptyCorrect=0;for(let y=0;y<c.height;y++)for(let x=0;x<c.width;x++){const a=pixels[((y*4+2)*w+x*4+2)*4+3];if(c.indices[y*c.width+x]){expected++;covered+=a>=250;}else{empty++;emptyCorrect+=a===0;}}
 return{png:out.toDataURL('image/png').split(',')[1],source_pixel_centers:{covered,expected,empty,emptyCorrect},packing_method:'original_source_contour_with_generated_photo_and_nearest_edge_coverage'};
}
(async()=>{
 const sources=fs.readFileSync(art+'/source-contracts.json'),contracts=JSON.parse(sources);
 const b=await chromium.launch({headless:true,executablePath:'/usr/bin/google-chrome',args:['--no-sandbox']});
 const report={schema:1,source_contracts_sha256:sha(sources),assets:[],scope:'Kandidatpakke, ingen aktiv manifestendring. Ny rute klippes bare til originalens kildeform.'};
 try{const p=await b.newPage();for(const c of contracts.entries){
  const rawPath=art+'/raw/'+c.key;if(!fs.existsSync(rawPath))continue;
  const raw=fs.readFileSync(rawPath),source=fs.readFileSync(figures+'/'+c.original.path);
  const r=await p.evaluate(pack,{raw:raw.toString('base64'),source:source.toString('base64'),w:c.target_width,h:c.target_height,scale:4,source_clip:true,clip:c.clip});
  const filled=await p.evaluate(coverOriginal,{png:r.png,c});delete r.png;const png=Buffer.from(filled.png,'base64');delete filled.png;const dest=art+'/packed/'+c.key;fs.mkdirSync(path.dirname(dest),{recursive:true});fs.writeFileSync(dest,png);
  report.assets.push({key:c.key,source_bank_sha256:c.source_bank.sha256,indices_sha256:c.indices_sha256,original_sha256:sha(source),raw_sha256:sha(raw),packed_sha256:sha(png),...r,...filled});
 }}finally{await b.close();}
 report.aliases=[];for(const a of JSON.parse(fs.readFileSync(art+'/queue-subset.json')).aliases){const source=art+'/packed/'+a.master_key,target=art+'/packed/'+a.key;if(!fs.existsSync(source))continue;fs.mkdirSync(path.dirname(target),{recursive:true});fs.copyFileSync(source,target);report.aliases.push({key:a.key,master_key:a.master_key,sha256:sha(fs.readFileSync(target))});}
 fs.writeFileSync(art+'/packing-report.json',JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report));
})().catch(e=>{console.error(e);process.exitCode=1;});
