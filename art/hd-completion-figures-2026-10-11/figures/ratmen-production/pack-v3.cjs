/* Pakk faktisk ny imagegen-grafikk til originalens uendrede tegnerektangel. */
'use strict';
const fs=require('fs'),path=require('path'),crypto=require('crypto'),{chromium}=require('playwright');
const art=__dirname,root=path.resolve(art,'../../../..'),figures=path.resolve(art,'../..');
const pack=require(root+'/tools/hd_resterende_ikoner_canvas.cjs'),sha=b=>crypto.createHash('sha256').update(b).digest('hex');
async function coverOriginal({png,c}){
 const im=new Image();im.src='data:image/png;base64,'+png;await im.decode();const out=document.createElement('canvas');out.width=c.target_width;out.height=c.target_height;const ctx=out.getContext('2d');ctx.drawImage(im,0,0);const d=ctx.getImageData(0,0,out.width,out.height),w=out.width,h=out.height,near=new Int32Array(w*h),queue=new Int32Array(w*h);near.fill(-1);let head=0,tail=0;
 // Utvid bare det nygenererte materialets kantfarge til den frosne kildeformen.
 const seedAlpha=c.indices.filter(Boolean).length<=4?16:220;
 for(let n=0;n<w*h;n++)if(d.data[n*4+3]>=seedAlpha){near[n]=n;queue[tail++]=n;}
 while(head<tail){const n=queue[head++],x=n%w,y=Math.floor(n/w);for(const nn of [x?n-1:-1,x+1<w?n+1:-1,y?n-w:-1,y+1<h?n+w:-1])if(nn>=0&&near[nn]<0){near[nn]=near[n];queue[tail++]=nn;}}
 if(!tail)throw Error('Ingen ugjennomsiktig generert kjerne '+c.key);
 for(let n=0;n<w*h;n++){if(d.data[n*4+3]<255){const q=near[n]*4;for(let k=0;k<3;k++)d.data[n*4+k]=d.data[q+k];}d.data[n*4+3]=255;}ctx.putImageData(d,0,0);
 // De14 lyse kildecellene i024 maa hente lyst materiale fra samme raafoto.
 if(c.pale_path){const nearPale=new Int32Array(w*h).fill(-1),queuePale=new Int32Array(w*h);let headPale=0,tailPale=0;for(let n=0;n<w*h;n++){const k=n*4;if(d.data[k]>=140&&d.data[k+1]>=d.data[k]*.65&&d.data[k+2]>=d.data[k]*.35){nearPale[n]=n;queuePale[tailPale++]=n;}}if(!tailPale)throw Error('Mangler lyst generert materiale '+c.key);while(headPale<tailPale){const n=queuePale[headPale++],x=n%w,y=n/w|0;for(const nn of[x?n-1:-1,x+1<w?n+1:-1,y?n-w:-1,y+1<h?n+w:-1])if(nn>=0&&nearPale[nn]<0){nearPale[nn]=nearPale[n];queuePale[tailPale++]=nn;}}const layer=document.createElement('canvas');layer.width=w;layer.height=h;const lc=layer.getContext('2d'),ld=lc.createImageData(w,h);for(let n=0;n<w*h;n++){const k=n*4,q=nearPale[n]*4;for(let j=0;j<3;j++)ld.data[k+j]=d.data[q+j];ld.data[k+3]=255;}lc.putImageData(ld,0,0);const mask=document.createElement('canvas');mask.width=w;mask.height=h;const mc=mask.getContext('2d');mc.scale(4,4);mc.fill(new Path2D(c.pale_path),'evenodd');lc.globalCompositeOperation='destination-in';lc.drawImage(mask,0,0);ctx.drawImage(layer,0,0);}
 // Originalens roede blodindeks15 henter roedt fotomateriale fra dette nye bildet.
 // Ingen syntetisk roedfarge eller nye former tilfoeyes.
 if(c.blood_path){const redNear=new Int32Array(w*h),redQueue=new Int32Array(w*h);redNear.fill(-1);let rh=0,rt=0;for(let n=0;n<w*h;n++){const k=n*4;if(d.data[k]>30&&d.data[k]>d.data[k+1]*1.5&&d.data[k]>d.data[k+2]*1.5){redNear[n]=n;redQueue[rt++]=n;}}if(!rt)throw Error('Mangler faktisk generert roedt kildemateriale '+c.key);while(rh<rt){const n=redQueue[rh++],x=n%w,y=Math.floor(n/w);for(const nn of [x?n-1:-1,x+1<w?n+1:-1,y?n-w:-1,y+1<h?n+w:-1])if(nn>=0&&redNear[nn]<0){redNear[nn]=redNear[n];redQueue[rt++]=nn;}}
 const layer=document.createElement('canvas');layer.width=w;layer.height=h;const lc=layer.getContext('2d'),ld=lc.createImageData(w,h);for(let n=0;n<w*h;n++){const k=n*4,q=redNear[n]*4;for(let j=0;j<3;j++)ld.data[k+j]=d.data[q+j];ld.data[k+3]=255;}lc.putImageData(ld,0,0);const m=document.createElement('canvas');m.width=w;m.height=h;const mc=m.getContext('2d');mc.scale(4,4);mc.fill(new Path2D(c.blood_path),'evenodd');lc.globalCompositeOperation='destination-in';lc.drawImage(m,0,0);ctx.drawImage(layer,0,0);}
 // Originalens opake svarte og moerke fragmenter maa ikke bli til ekstra soelvblad.
 for(const region of c.dark_paths||[]){const layer=document.createElement('canvas');layer.width=w;layer.height=h;const lc=layer.getContext('2d'),ld=lc.createImageData(w,h),factor=region.index===5?.035:.3;for(let i=0;i<d.data.length;i+=4){for(let k=0;k<3;k++)ld.data[i+k]=Math.round(d.data[i+k]*factor);ld.data[i+3]=255;}lc.putImageData(ld,0,0);const dm=document.createElement('canvas');dm.width=w;dm.height=h;const dc=dm.getContext('2d');dc.scale(4,4);dc.fill(new Path2D(region.d),'evenodd');lc.globalCompositeOperation='destination-in';lc.drawImage(dm,0,0);ctx.drawImage(layer,0,0);}
 const mask=document.createElement('canvas');mask.width=w;mask.height=h;const mc=mask.getContext('2d');mc.scale(4,4);mc.fill(new Path2D(c.clip),'evenodd');ctx.globalCompositeOperation='destination-in';ctx.drawImage(mask,0,0);
 const pixels=ctx.getImageData(0,0,w,h).data;let covered=0,expected=0,empty=0,emptyCorrect=0;for(let y=0;y<c.height;y++)for(let x=0;x<c.width;x++){const a=pixels[((y*4+2)*w+x*4+2)*4+3];if(c.indices[y*c.width+x]){expected++;covered+=a>=250;}else{empty++;emptyCorrect+=a===0;}}
 return{png:out.toDataURL('image/png').split(',')[1],source_pixel_centers:{covered,expected,empty,emptyCorrect},packing_method:'original_source_contour_with_generated_photo_and_nearest_edge_coverage'};
}
(async()=>{
 const sources=fs.readFileSync(art+'/source-contracts.json'),contracts=JSON.parse(sources),selected=new Set((process.env.RATMEN_PACK_KEYS||'').split(',').filter(Boolean));if(!selected.size)throw Error('Oppgi eksakte nye ruter i RATMEN_PACK_KEYS');
 const overrides=JSON.parse(fs.readFileSync(art+'/packing-material-overrides.json'));for(const o of overrides.entries){const c=contracts.entries.find(c=>c.key===o.key);if(c.indices_sha256!==o.indices_sha256||sha(fs.readFileSync(art+'/raw/'+c.key))!==o.raw_sha256)throw Error('Materialkilde endret '+c.key);Object.assign(c,o);}
 const b=await chromium.launch({headless:true,executablePath:'/usr/bin/google-chrome',args:['--no-sandbox']});
 const report={schema:1,source_contracts_sha256:sha(sources),assets:[],scope:'Kandidatpakke, ingen aktiv manifestendring. Ny rute klippes bare til originalens kildeform.'};
 try{const p=await b.newPage();for(const c of contracts.entries){
  if(!selected.has(c.key))continue;
  const rawPath=art+'/raw/'+c.key;if(!fs.existsSync(rawPath))continue;
  const raw=fs.readFileSync(rawPath),source=fs.readFileSync(figures+'/'+c.original.path);
  const r=await p.evaluate(pack,{raw:raw.toString('base64'),source:source.toString('base64'),w:c.target_width,h:c.target_height,scale:4,source_clip:true,clip:c.clip});
  // Svart kjerne kan mangle etter foerste klipp av en to-pikslers effekt.
  // Bruk da samme genererte materialflate foer klipp, aldri en ny tegnet form.
  if(!r.opaque_pixels && c.indices.filter(Boolean).length<=4){
   const seed=await p.evaluate(pack,{raw:raw.toString('base64'),source:source.toString('base64'),w:c.target_width,h:c.target_height,scale:4,source_clip:false,clip:c.clip});
   r.png=seed.png;r.tiny_material_seed_before_source_clip=true;
  }
  let filled;
  if(c.indices.every(i=>i===0||i===5)){
   filled=await p.evaluate(async({c})=>{const cv=document.createElement('canvas');cv.width=c.target_width;cv.height=c.target_height;const ct=cv.getContext('2d'),d=ct.createImageData(cv.width,cv.height);for(let y=0;y<cv.height;y++)for(let x=0;x<cv.width;x++)d.data[(y*cv.width+x)*4+3]=c.indices[Math.floor(y/4)*c.width+Math.floor(x/4)]?255:0;ct.putImageData(d,0,0);return{png:cv.toDataURL('image/png').split(',')[1],packing_method:'preserved_original_black_shadow_exact_nearest_neighbor'};},{c});
  }else filled=await p.evaluate(coverOriginal,{png:r.png,c});
  delete r.png;const png=Buffer.from(filled.png,'base64');delete filled.png;const dest=art+'/packed/'+c.key;fs.mkdirSync(path.dirname(dest),{recursive:true});if(fs.existsSync(dest)){if(sha(fs.readFileSync(dest))!==sha(png))throw Error('Annen pakket kandidat finnes '+c.key);}else fs.writeFileSync(dest,png);
  report.assets.push({key:c.key,source_bank_sha256:c.source_bank.sha256,indices_sha256:c.indices_sha256,original_sha256:sha(source),raw_sha256:sha(raw),packed_sha256:sha(png),...r,...filled});
 }}finally{await b.close();}
 report.aliases=[];for(const a of JSON.parse(fs.readFileSync(art+'/queue-subset.json')).aliases){if(!selected.has(a.key)&&!selected.has(a.master_key))continue;const source=art+'/packed/'+a.master_key,target=art+'/packed/'+a.key;if(!fs.existsSync(source))continue;fs.mkdirSync(path.dirname(target),{recursive:true});fs.copyFileSync(source,target);report.aliases.push({key:a.key,master_key:a.master_key,sha256:sha(fs.readFileSync(target))});}
 fs.writeFileSync(process.env.RATMEN_PACK_REPORT||art+'/packing-report-v3.json',JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report));
})().catch(e=>{console.error(e);process.exitCode=1;});
