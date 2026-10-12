/* Pakk nygenerert logo fra svart master. Bare matte/utsnitt/skala endres her;
 * bokstavene kommer fra innebygd bildegenerator, ikke originalens pikselmaske.
 * Kjor uten argument for art-pakken, med --activate for kontrollert aktivering.
 * Node med sharp brukes bare som eksisterende utviklingsverktoy. */
'use strict';
const fs=require('fs'),path=require('path'),crypto=require('crypto'),assert=require('assert/strict'),sharp=require('sharp');
const root=path.resolve(__dirname,'..'), art=root+'/art/hd-logo-2026-10-12';
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const read=p=>JSON.parse(fs.readFileSync(p,'utf8'));
(async()=>{
 const rawPath=art+'/raw/logo-black-master-v3.png', raw=fs.readFileSync(rawPath);
 const {data,info}=await sharp(raw).ensureAlpha().raw().toBuffer({resolveWithObject:true});
 assert.equal(info.channels,4);
 let x0=info.width,y0=info.height,x1=0,y1=0,opaque=0;
 for(let y=0;y<info.height;y++)for(let x=0;x<info.width;x++){
  const i=(y*info.width+x)*4, v=Math.max(data[i],data[i+1],data[i+2]);
  // Svart studio-matte: <=5 fjernes, >=24 er opakt, mellomomraadet beholder AA.
  // Gullflatene/innvendige skygger har vesentlig hoeyere RGB og beholdes.
  const a=Math.round(Math.max(0,Math.min(1,(v-5)/19))*255);data[i+3]=a;
  if(!a)data[i]=data[i+1]=data[i+2]=0;
  if(a>=64){x0=Math.min(x0,x);y0=Math.min(y0,y);x1=Math.max(x1,x+1);y1=Math.max(y1,y+1);opaque++;}
 }
 assert(opaque>100000 && opaque<info.width*info.height/2,'Uventet gullflate');
 const pad=4;x0=Math.max(0,x0-pad);y0=Math.max(0,y0-pad);x1=Math.min(info.width,x1+pad);y1=Math.min(info.height,y1+pad);
 const png=await sharp(data,{raw:info}).extract({left:x0,top:y0,width:x1-x0,height:y1-y0}).resize({width:2440,kernel:'lanczos3'}).png({compressionLevel:9}).toBuffer();
 const target=await sharp(png).metadata();
 fs.mkdirSync(art+'/packed/bold.f',{recursive:true});fs.writeFileSync(art+'/packed/bold.f/073.png',png);
 const source=read(root+'/art/hd-completion-backgrounds-2026-10-11/logo/contract.json');
 const proof={schema:1,method:'builtin_imagegen_new_lettering_black_matte_native_asset_pack',generator:'built-in image_gen; exact model version not exposed',raw:'raw/logo-black-master-v3.png',raw_sha256:sha(raw),original_reference:'art/hd-completion-backgrounds-2026-10-11/logo/source/nearest4x-reference.png',original_bank_sha256:source.bank_sha256,original_indices_sha256:source.indices_sha256,source_size:[305,54],raw_size:[info.width,info.height],raw_rect:[x0,y0,x1-x0,y1-y0],matte:{transparent_max:5,opaque_min:24,edge:'linear alpha; no glyph reshaping or pixel-mask snapping'},target:[target.width,target.height],candidate_sha256:sha(png),fit:'width',text:['MOONSTONE','A Hard Days Knight'],geometry_policy:'Smooth newly generated lettering. Original source frame, anchor and width retained; aspect ratio preserved and vertically centered by existing logo fit.',activation:process.argv.includes('--activate')};
 if(proof.activation){
  const texts=read(root+'/web/hd/text.json'), g=texts.glyphs.find(g=>g.path==='bold.f/073.png');assert(g && g.width===305 && g.height===54);
  g.raw_rect_px=[0,0,target.width,target.height];g.sha256=sha(png);g.fit='width';g.alpha_cutoff=0.15;g.method='generated-smooth-gold-logo';
  fs.writeFileSync(root+'/web/hd/bold.f/073.png',png);
  const textBytes=Buffer.from(JSON.stringify(texts,null,2)+'\n');fs.writeFileSync(root+'/web/hd/text.json',textBytes);
  const manifest=read(root+'/web/hd/manifest.json');
  for(const [name,bytes] of [['bold.f/073.png',png],['text.json',textBytes]]){
   const entry=manifest.files.find(f=>f.path===name);assert(entry,'Manglende manifestfil '+name);entry.bytes=bytes.length;entry.sha256=sha(bytes);
  }
  fs.writeFileSync(root+'/web/hd/manifest.json',JSON.stringify(manifest,null,2)+'\n');proof.manifest_sha256=sha(fs.readFileSync(root+'/web/hd/manifest.json'));
 }
 fs.mkdirSync(art+'/verification',{recursive:true});fs.writeFileSync(art+'/verification/packing.json',JSON.stringify(proof,null,2)+'\n');console.log(JSON.stringify(proof));
})().catch(e=>{console.error(e);process.exitCode=1});
