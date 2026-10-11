/* Pakk én separat bildegenerert Math-rute i originalens uendrede 4x-rektangel. */
'use strict';
const fs=require('fs'),path=require('path'),crypto=require('crypto'),assert=require('assert/strict'),{chromium}=require('playwright');
const root=path.resolve(__dirname,'..'),art=path.resolve(root,process.env.MOONSTONE_FIGURE_ART||'art/hd-math-figures-2026-10-11'),frame=Number(process.argv[2]),raw=path.resolve(process.argv[3]);
const crop=process.env.MOONSTONE_FIGURE_CROP?JSON.parse(process.env.MOONSTONE_FIGURE_CROP):null;
if(crop)assert(crop.length===4&&crop.every(v=>Number.isFinite(v)&&v>=0&&v<=1)&&crop[2]>0&&crop[3]>0&&crop[0]+crop[2]<=1&&crop[1]+crop[3]<=1,'Gyldig kildebundet kontekstutsnitt');
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
(async()=>{assert(Number.isInteger(frame));const contract=JSON.parse(fs.readFileSync(process.env.MOONSTONE_FIGURE_CONTRACT||art+'/source-contract.json')),row=contract.routes.find(r=>r.frame===frame);assert(row);
 const bytes=fs.readFileSync(raw),indices=Array.from(fs.readFileSync(row.indices_file?art+'/'+row.indices_file:art+'/source/indices/'+String(frame).padStart(3,'0')+'.bin'));
 const alphaIndices=row.alpha_indices_file?Array.from(fs.readFileSync(art+'/'+row.alpha_indices_file)):indices;
 if(row.alpha_indices_file)assert(sha(Buffer.from(alphaIndices))===row.alpha_indices_sha256&&alphaIndices.length===indices.length,'Originalbundet separat PIV-figurmaske');
 if(row.fill_missing_by_material!==undefined)assert(row.fill_missing_by_material===true&&row.alpha_indices_file,'Materialutfylling krever kildebundet PIV-figurmaske');
 let shared=null;
 if(process.env.MOONSTONE_FIGURE_SHARED_MATERIAL){
  const file=path.resolve(process.env.MOONSTONE_FIGURE_SHARED_MATERIAL),meta=JSON.parse(fs.readFileSync(file)),mask=fs.readFileSync(art+'/'+meta.mask),donor=fs.readFileSync(art+'/'+meta.donor);
  assert(meta.schema===1&&meta.frames.includes(frame)&&meta.width===row.width&&meta.height===row.height,'Delt materiale maa passe denne originalruten');
  assert(sha(mask)===meta.mask_sha256&&sha(donor)===meta.donor_sha256&&mask.length===indices.length,'Frosne materialkilder');
  const originals=meta.frames.map(n=>fs.readFileSync(art+'/source/indices/'+String(n).padStart(3,'0')+'.bin'));
  for(let n=0;n<meta.frames.length;n++)assert(sha(originals[n])===meta.source_indices[String(meta.frames[n]).padStart(3,'0')]);
  if(meta.comparison_indices_file){const compare=fs.readFileSync(art+'/'+meta.comparison_indices_file);assert(sha(compare)===meta.comparison_indices_sha256&&compare.length===indices.length,'Frossen PIV-indekssammenligning');originals.push(compare);}
  for(let i=0;i<mask.length;i++)if(mask[i])assert(meta.allowed_indices.includes(indices[i])&&originals.every(b=>b[i]===indices[i]),'Bare identisk originalmateriale deles');
  if(meta.feather_bottom_rows!==undefined)assert(Number.isFinite(meta.feather_bottom_rows)&&meta.feather_bottom_rows>0&&meta.feather_bottom_rows<=row.height,'Lokal materialsoem innen originalruten');
  if(meta.row_weights!==undefined)assert(meta.row_weights.length===row.height&&meta.row_weights.every(n=>Number.isFinite(n)&&n>=0&&n<=1),'Dokumenterte materialvekter innen originalruten');
  shared={meta,donor:donor.toString('base64'),contract_sha256:sha(fs.readFileSync(file))};
 }
 let expression=null;
 if(process.env.MOONSTONE_FIGURE_EXPRESSION){
  const file=path.resolve(process.env.MOONSTONE_FIGURE_EXPRESSION),meta=JSON.parse(fs.readFileSync(file)),donor=fs.readFileSync(art+'/'+meta.donor);
  assert(meta.schema===1&&meta.frame===frame&&meta.width===row.width&&meta.height===row.height&&sha(donor)===meta.donor_sha256,'Frossen uttrykksregistrering');
  assert(meta.ellipses.every(r=>r.length===4&&r.every(Number.isFinite)&&r[2]>0&&r[3]>0&&r[0]-r[2]>=0&&r[1]-r[3]>=0&&r[0]+r[2]<=row.width&&r[1]+r[3]<=row.height),'Oeyefelt innen originalruten');
  assert(Number.isFinite(meta.feather_fraction)&&meta.feather_fraction>0&&meta.feather_fraction<=1,'Avgrenset intern hudovergang');
  expression={meta,donor:donor.toString('base64'),contract_sha256:sha(fs.readFileSync(file))};
 }
 let seam=null;
 if(process.env.MOONSTONE_FIGURE_SEAM){
  const file=path.resolve(process.env.MOONSTONE_FIGURE_SEAM),meta=JSON.parse(fs.readFileSync(file)),donor=fs.readFileSync(art+'/'+meta.donor);
  assert(meta.schema===1&&meta.frames.includes(frame)&&meta.width===row.width&&meta.height===row.height&&sha(donor)===meta.donor_sha256,'Frossen lokal kappesoem');
  assert(sha(Buffer.from(indices))===meta.source_indices[String(frame).padStart(3,'0')],'Kappesoem bundet til originalruten');
  assert(meta.original_rect.length===4&&meta.original_rect[2]-meta.original_rect[0]===row.width&&meta.original_rect[3]-meta.original_rect[1]===row.height,'Kappesoem har originalrektangelet');
  assert(meta.row_weights.length===row.height&&meta.row_weights.every(n=>Number.isFinite(n)&&n>=0&&n<=1)&&meta.row_weights.slice(0,row.height-6).every(n=>n===0),'Bare siste seks originalrader kan materialregistreres');
  seam={meta,donor:donor.toString('base64'),contract_sha256:sha(fs.readFileSync(file))};
 }
 const b=await chromium.launch({headless:true,executablePath:'/usr/bin/google-chrome',args:['--no-sandbox']});let result;
 try{const p=await b.newPage();result=await p.evaluate(async({row,raw,indices,alphaIndices,palette,crop,shared,expression,seam})=>{const im=new Image();im.src='data:image/png;base64,'+raw;await im.decode();
  const c=document.createElement('canvas');c.width=row.target_width;c.height=row.target_height;const ctx=c.getContext('2d');ctx.imageSmoothingQuality='high';
  let registration='full_original_rectangle';
  if(crop){ctx.drawImage(im,crop[0]*im.width,crop[1]*im.height,crop[2]*im.width,crop[3]*im.height,0,0,c.width,c.height);registration='source_bound_context_crop';}
  else if(row.height<=10&&row.live_palette_mask_indices.length){
   // Svart/transparent polstring rundt ekstremt tynne mastere er ikke tekstur.
   // Registrer bare dette stoffmaterialet mot originalens blekkrektangel;
   // originalens kontur nedenfor bestemmer fortsatt alle synlige piksler.
   const native=document.createElement('canvas');native.width=im.width;native.height=im.height;const nc=native.getContext('2d');nc.drawImage(im,0,0);const rgba=nc.getImageData(0,0,im.width,im.height).data;
   let rx0=im.width,ry0=im.height,rx1=0,ry1=0,sx0=row.width,sy0=row.height,sx1=0,sy1=0;
   for(let y=0;y<im.height;y++)for(let x=0;x<im.width;x++)if(rgba[(y*im.width+x)*4+3]>=128){rx0=Math.min(rx0,x);ry0=Math.min(ry0,y);rx1=Math.max(rx1,x+1);ry1=Math.max(ry1,y+1);}
   for(let y=0;y<row.height;y++)for(let x=0;x<row.width;x++)if(indices[y*row.width+x]){sx0=Math.min(sx0,x);sy0=Math.min(sy0,y);sx1=Math.max(sx1,x+1);sy1=Math.max(sy1,y+1);}
   ctx.drawImage(im,rx0,ry0,rx1-rx0,ry1-ry0,sx0*4,sy0*4,(sx1-sx0)*4,(sy1-sy0)*4);registration='thin_cloth_ink_bounds';
  }else ctx.drawImage(im,0,0,c.width,c.height);
  if(shared){
   // Allerede generert materiale paa samme originalsted deles bare der
   // kildeindeksene er identiske. Endrede animasjonsfelt har egen master.
   const donor=new Image();donor.src='data:image/png;base64,'+shared.donor;await donor.decode();const r=shared.meta.donor_crop_normalized;
   if(shared.meta.feather_bottom_rows||shared.meta.row_weights){
    const layer=document.createElement('canvas');layer.width=c.width;layer.height=c.height;const lc=layer.getContext('2d');lc.scale(4,4);lc.clip(new Path2D(shared.meta.alpha_path),'evenodd');lc.setTransform(1,0,0,1,0,0);lc.drawImage(donor,r[0]*donor.width,r[1]*donor.height,r[2]*donor.width,r[3]*donor.height,0,0,c.width,c.height);
    const base=ctx.getImageData(0,0,c.width,c.height),fixed=lc.getImageData(0,0,c.width,c.height);
    for(let y=0;y<c.height;y++)for(let x=0;x<c.width;x++){const at=(y*c.width+x)*4,t=Math.min(1,(y/4)/(shared.meta.feather_bottom_rows||1)),weight=shared.meta.row_weights?shared.meta.row_weights[Math.min(row.height-1,Math.floor(y/4))]:(1-t)*(1-t)*(1+2*t),amount=weight*fixed.data[at+3]/255;for(let k=0;k<3;k++)base.data[at+k]=Math.round(base.data[at+k]*(1-amount)+fixed.data[at+k]*amount);}
    ctx.putImageData(base,0,0);
   }else{ctx.save();ctx.scale(4,4);ctx.clip(new Path2D(shared.meta.alpha_path),'evenodd');ctx.setTransform(1,0,0,1,0,0);ctx.drawImage(donor,r[0]*donor.width,r[1]*donor.height,r[2]*donor.width,r[3]*donor.height,0,0,c.width,c.height);ctx.restore();}
  }
  if(expression){
   // Hud og hodeform holdes fra den faste fotografiske identiteten.
   // Bare de to dokumenterte oeyelokk-/brynfeltaa bruker den nye uttrykksmasteren.
   const donor=new Image();donor.src='data:image/png;base64,'+expression.donor;await donor.decode();const r=expression.meta.donor_crop_normalized;
   const fixed=document.createElement('canvas');fixed.width=c.width;fixed.height=c.height;const fc=fixed.getContext('2d');fc.drawImage(donor,r[0]*donor.width,r[1]*donor.height,r[2]*donor.width,r[3]*donor.height,0,0,c.width,c.height);
   const base=fc.getImageData(0,0,c.width,c.height),photo=ctx.getImageData(0,0,c.width,c.height);
   for(let y=0;y<c.height;y++)for(let x=0;x<c.width;x++){
    const sx=(x+.5)/4,sy=(y+.5)/4;let amount=0;
    for(const [cx,cy,rx,ry]of expression.meta.ellipses){const distance=Math.sqrt(((sx-cx)/rx)**2+((sy-cy)/ry)**2);amount=Math.max(amount,Math.max(0,Math.min(1,(1-distance)/expression.meta.feather_fraction)));}
    const at=(y*c.width+x)*4;for(let k=0;k<4;k++)photo.data[at+k]=Math.round(base.data[at+k]*(1-amount)+photo.data[at+k]*amount);
   }
   ctx.putImageData(photo,0,0);
  }
  if(seam){
   // Siste seks kilderader ligger i kappens originale felt. Samme
   // fotografiske kappemateriale registreres mykt mot fastplaten nederst.
   // Egen munn-/skjeggmaster og alle kildeankre/alfakonturer beholdes.
   const donor=new Image();donor.src='data:image/png;base64,'+seam.donor;await donor.decode();const r=seam.meta.donor_crop_normalized;
   const fixed=document.createElement('canvas');fixed.width=c.width;fixed.height=c.height;const fc=fixed.getContext('2d');fc.drawImage(donor,r[0]*donor.width,r[1]*donor.height,r[2]*donor.width,r[3]*donor.height,0,0,c.width,c.height);
   const base=ctx.getImageData(0,0,c.width,c.height),cloth=fc.getImageData(0,0,c.width,c.height);
   for(let y=0;y<c.height;y++)for(let x=0;x<c.width;x++){const at=(y*c.width+x)*4,weight=seam.meta.row_weights[Math.floor(y/4)];for(let k=0;k<3;k++)base.data[at+k]=Math.round(base.data[at+k]*(1-weight)+cloth.data[at+k]*weight);}
   ctx.putImageData(base,0,0);
  }
  let data=ctx.getImageData(0,0,c.width,c.height),a=data.data;let rawIntersection=0,rawUnion=0;
  for(let y=0;y<c.height;y++)for(let x=0;x<c.width;x++){
   const present=a[(y*c.width+x)*4+3]>=128,expected=alphaIndices[(y/4|0)*row.width+(x/4|0)]!==0;
   if(present&&expected)rawIntersection++;if(present||expected)rawUnion++;
  }
  // Generatoren leverer materialer i samme utsnitt. Alfakonturen kommer fra
  // originalen, saa ingen rute faar nye kroppsdeler, nye hull eller nytt anker.
  const photoNearest=new Int32Array(c.width*c.height).fill(-1),photoQueue=new Int32Array(photoNearest.length);let photoHead=0,photoTail=0;
  for(let q=0;q<photoNearest.length;q++)if(a[q*4+3]>=128){photoNearest[q]=q;photoQueue[photoTail++]=q;}
  if(!photoTail)throw Error('Ingen synlige genererte materialpiksler');
  while(photoHead<photoTail){const q=photoQueue[photoHead++],x=q%c.width,y=q/c.width|0;
   for(const v of [x?q-1:-1,x<c.width-1?q+1:-1,y?q-c.width:-1,y<c.height-1?q+c.width:-1])
    if(v>=0&&photoNearest[v]<0){photoNearest[v]=photoNearest[q];photoQueue[photoTail++]=v;}
  }
  const filled=new Uint8ClampedArray(a.length);
  const materialNearest=[];
  if(row.fill_missing_by_material){
   for(const accept of [(q)=>a[q*4+2]>a[q*4]*1.35+1&&a[q*4+2]>a[q*4+1]*1.1+1,(q)=>a[q*4]*.299+a[q*4+1]*.587+a[q*4+2]*.114<40]){
    const nearest=new Int32Array(photoNearest.length).fill(-1),queue=new Int32Array(nearest.length);let head=0,tail=0;for(let q=0;q<nearest.length;q++)if(a[q*4+3]>=128&&accept(q)){nearest[q]=q;queue[tail++]=q;}
    if(!tail)throw Error('Manglende fotografisk PIV-materialklasse');while(head<tail){const q=queue[head++],x=q%c.width,y=q/c.width|0;for(const v of [x?q-1:-1,x<c.width-1?q+1:-1,y?q-c.width:-1,y<c.height-1?q+c.width:-1])if(v>=0&&nearest[v]<0){nearest[v]=nearest[q];queue[tail++]=v;}}materialNearest.push(nearest);
   }
  }
  for(let q=0;q<photoNearest.length;q++){let near=photoNearest[q];if(row.fill_missing_by_material&&a[q*4+3]<128){const x=q%c.width,y=q/c.width|0,source=indices[(y/4|0)*row.width+(x/4|0)];if(row.live_palette_mask_indices.includes(source))near=materialNearest[0][q];else if(source===0)near=materialNearest[1][q];}const j=near*4;filled.set([a[j],a[j+1],a[j+2],255],q*4);}
  const material=document.createElement('canvas');material.width=c.width;material.height=c.height;
  material.getContext('2d').putImageData(new ImageData(filled,c.width,c.height),0,0);
  ctx.clearRect(0,0,c.width,c.height);ctx.save();ctx.scale(4,4);ctx.clip(new Path2D(row.alpha_path),'evenodd');ctx.setTransform(1,0,0,1,0,0);ctx.drawImage(material,0,0);ctx.restore();
  data=ctx.getImageData(0,0,c.width,c.height);a=data.data;let intersection=0,union=0;
  const m=document.createElement('canvas');m.width=c.width;m.height=c.height;const md=m.getContext('2d').createImageData(c.width,c.height);
  // R/B er originalens NN-palettindeks, uavhengig av avrundet fotoalfa.
  // G baerer den nye fotografiske luminansen, ogsaa paa kantpiksler som
  // tidligere ikke ble klassifisert som blaatt materiale.
  let clothPixels=0;
  for(let y=0;y<c.height;y++)for(let x=0;x<c.width;x++){
   const q=y*c.width+x,j=q*4,i=indices[(y/4|0)*row.width+(x/4|0)],present=a[j+3]>=128,expected=alphaIndices[(y/4|0)*row.width+(x/4|0)]!==0;
   if(present&&expected)intersection++;if(present||expected)union++;
   md.data[j+3]=255;
   if(row.live_palette_mask_indices.includes(i)){
    const sourceIndex=i;
    const luminance=v=>v[0]*.299+v[1]*.587+v[2]*.114,reference=luminance(palette[sourceIndex]),g=reference>0?Math.max(0,Math.min(255,Math.round(128*luminance(a.subarray(j,j+3))/reference))):128;
    md.data.set([sourceIndex+1,g,255,255],j);clothPixels++;
   }
  }
  m.getContext('2d').putImageData(md,0,0);
  return{image:c.toDataURL('image/png').split(',')[1],mask:row.live_palette_mask_indices.length?m.toDataURL('image/png').split(',')[1]:null,master_size:[im.width,im.height],size:[c.width,c.height],registration,raw_silhouette_iou:rawIntersection/rawUnion,silhouette_iou:intersection/union,cloth_pixels:clothPixels};
 },{row,raw:bytes.toString('base64'),indices,alphaIndices,palette:contract.palettes[row.scene].rgba,crop,shared,expression,seam});}finally{await b.close();}
 const target=art+'/packed/'+row.target;fs.mkdirSync(path.dirname(target),{recursive:true});const img=Buffer.from(result.image,'base64');fs.writeFileSync(target,img);
 const record={status:'candidate_requires_runtime_visual_review',key:row.target,authoring_method:'individual_redraw_with_source_alpha_constraint',tool:'builtin image_gen',raw_file:path.relative(root,raw),raw_sha256:sha(bytes),raw_crop_normalized:crop,source_indices_sha256:row.indices_sha256,reference_sha256:row.reference_sha256,output_sha256:sha(img),master_size:result.master_size,size:result.size,material_registration:result.registration,raw_silhouette_iou:result.raw_silhouette_iou,silhouette_iou:result.silhouette_iou};
 if(row.fill_missing_by_material)record.missing_material_fill={source_alpha_sha256:row.alpha_indices_sha256,method:'Only missing generated alpha is filled from nearest generated blue cloth or generated dark material for original0 shadows. Existing photo pixels stay unchanged.'};
 if(shared)record.shared_unchanged_material={kind:shared.meta.kind,contract_sha256:shared.contract_sha256,donor:shared.meta.donor,donor_sha256:shared.meta.donor_sha256,mask_sha256:shared.meta.mask_sha256,mask_pixels:shared.meta.mask_pixels,original_rect:shared.meta.original_rect,method:shared.meta.scope};
 if(expression)record.expression_registration={contract_sha256:expression.contract_sha256,donor_sha256:expression.meta.donor_sha256,ellipses:expression.meta.ellipses,feather_fraction:expression.meta.feather_fraction,method:expression.meta.scope};
 if(seam)record.cloak_seam_registration={contract_sha256:seam.contract_sha256,donor_sha256:seam.meta.donor_sha256,original_rect:seam.meta.original_rect,row_weights:seam.meta.row_weights,method:seam.meta.scope};
 if(result.mask){const mask=Buffer.from(result.mask,'base64');fs.writeFileSync(target.replace('.png','.mask.png'),mask);record.mask_sha256=sha(mask);record.mask_indices=row.live_palette_mask_indices;record.cloth_pixels=result.cloth_pixels;record.mask_method='exact_original_nn_palette_index_independent_of_alpha_with_generated_photo_luminance';}
 fs.writeFileSync(target.replace('.png','.json'),JSON.stringify(record,null,2)+'\n');console.log(JSON.stringify(record));
})().catch(e=>{console.error(e);process.exitCode=1;});
