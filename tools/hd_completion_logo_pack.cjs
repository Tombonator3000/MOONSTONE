/* Pakk og kontroller originalformbundet logo. Skriver bare til art/, aldri web/hd. */
'use strict';
const fs=require('fs'),path=require('path'),crypto=require('crypto'),assert=require('assert/strict');
const {chromium}=require('playwright');
const root=path.resolve(__dirname,'..'),art=root+'/art/hd-completion-backgrounds-2026-10-11/logo';
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const {execFileSync}=require('child_process');

(async()=>{
 const c=JSON.parse(fs.readFileSync(art+'/contract.json'));
 assert.equal(sha(fs.readFileSync(root+'/Moonstonecd32-AMIGA.zip')),c.source_zip_sha256);
 assert.equal(sha(fs.readFileSync(art+'/source/bold.f')),c.bank_sha256);
 assert.equal(sha(fs.readFileSync(art+'/source/ch.piv')),c.palette_bank_sha256);
 assert.equal(sha(fs.readFileSync(root+'/'+c.raw_material_source)),c.raw_material_sha256);
 const browser=await chromium.launch({headless:true,executablePath:process.env.CHROME||'/usr/bin/google-chrome',args:['--no-sandbox']});
 try{
  const p=await browser.newPage();
  await p.addScriptTag({content:fs.readFileSync(root+'/web/src/grafikk.js','utf8')});
  const svg=Object.fromEntries(['alpha','face','shadow','tone'].map(n=>[n,fs.readFileSync(art+'/'+n+'.svg','utf8')]));
  const r=await p.evaluate(async({c,svg,raw})=>{
   const source=Uint8Array.from(atob(raw),s=>s.charCodeAt(0)),parsed=Spillgrafikk._cel(source)[73];
   const mask=source[19+73*10],bits=[1,2,4,8,16].filter(b=>mask&b);
   const indices=Array.from(parsed.px,v=>bits.reduce((s,b,n)=>s|(v&(1<<n)?b:0),0));
   const exact=parsed.w===305&&parsed.h===54&&mask===c.plane_mask&&indices.every((v,i)=>v===c.indices[i]);
   const canvases={};
   for(const [name,sourceSvg]of Object.entries(svg)){
    const image=new Image();image.src='data:image/svg+xml;base64,'+btoa(sourceSvg);await image.decode();
    const canvas=document.createElement('canvas');canvas.width=1220;canvas.height=216;canvas.getContext('2d').drawImage(image,0,0);canvases[name]=canvas;
   }
   const pixels=n=>canvases[n].getContext('2d').getImageData(0,0,1220,216);
   const tone=pixels('tone'),face=pixels('face'),shadow=pixels('shadow');
   const out=document.createElement('canvas');out.width=1220;out.height=216;
   const ctx=out.getContext('2d'),body=ctx.createImageData(1220,216),[tw,th]=[c.material.width,c.material.height];
   for(let y=0;y<216;y++)for(let x=0;x<1220;x++){
    const at=(y*1220+x)*4,g=c.material_gain[(y%th)*tw+x%tw];
    for(let k=0;k<3;k++)body.data[at+k]=Math.round(tone.data[at+k]*g);
    body.data[at+3]=face.data[at+3];
   }
   const layer=document.createElement('canvas');layer.width=1220;layer.height=216;layer.getContext('2d').putImageData(body,0,0);
   ctx.drawImage(canvases.shadow,0,0);ctx.globalCompositeOperation='source-in';ctx.fillStyle='black';ctx.fillRect(0,0,1220,216);ctx.globalCompositeOperation='source-over';ctx.drawImage(layer,0,0);
   const final=ctx.getImageData(0,0,1220,216).data;
   let midpoint=0,faceMidpoint=0,shadowMidpoint=0;const bad=[];
   for(let y=0;y<54;y++)for(let x=0;x<305;x++){
    const v=indices[y*305+x],at=((y*4+2)*1220+x*4+2)*4;
    const ok=(v?final[at+3]===255:final[at+3]===0)&&((v===5)?final[at]+final[at+1]+final[at+2]===0:true);
    if(ok)midpoint++;else if(bad.length<8)bad.push({x,y,v,got:Array.from(final.slice(at,at+4))});
    if(v&&v!==5&&face.data[at+3]===255)faceMidpoint++;
    if(v===5&&shadow.data[at+3]===255)shadowMidpoint++;
   }
   function components(mask,w,h,eight=false){
    const seen=new Uint8Array(mask.length),steps=[[1,0],[-1,0],[0,1],[0,-1]];if(eight)steps.push([1,1],[1,-1],[-1,1],[-1,-1]);
    let total=0,internal=0;const holes=[];
    for(let start=0;start<mask.length;start++){
     if(!mask[start]||seen[start])continue;total++;let edge=false,x0=w,y0=h,x1=0,y1=0;const todo=[start];seen[start]=1;
     for(let q=0;q<todo.length;q++){
      const at=todo[q],x=at%w,y=Math.floor(at/w);if(x===0||y===0||x===w-1||y===h-1)edge=true;
      x0=Math.min(x0,x);y0=Math.min(y0,y);x1=Math.max(x1,x+1);y1=Math.max(y1,y+1);
      for(const[dx,dy]of steps){const xx=x+dx,yy=y+dy,next=yy*w+xx;if(xx>=0&&xx<w&&yy>=0&&yy<h&&mask[next]&&!seen[next]){seen[next]=1;todo.push(next);}}
     }
     if(!edge){internal++;holes.push({bounds:[x0,y0,x1,y1],area:todo.length});}
    }return{total,internal,holes};
   }
   const before=Uint8Array.from(indices,v=>v?1:0),after=Uint8Array.from({length:1220*216},(_,i)=>final[i*4+3]>=128?1:0);
   const faceBefore=Uint8Array.from(indices,v=>v&&v!==5?1:0),faceAfter=Uint8Array.from({length:1220*216},(_,i)=>face.data[i*4+3]>=128?1:0);
   const topology={source:components(before,305,54,true),packed:components(after,1220,216),source_holes:components(before.map(v=>1-v),305,54),packed_holes:components(after.map(v=>1-v),1220,216)};
   const faceTopology={source:components(faceBefore,305,54,true),packed:components(faceAfter,1220,216),source_holes:components(faceBefore.map(v=>1-v),305,54),packed_holes:components(faceAfter.map(v=>1-v),1220,216)};
   return{png:out.toDataURL('image/png').split(',')[1],exact,midpoint,faceMidpoint,shadowMidpoint,bad,topology,faceTopology,
    face_png:canvases.face.toDataURL('image/png').split(',')[1],shadow_png:canvases.shadow.toDataURL('image/png').split(',')[1]};
  },{c,svg,raw:fs.readFileSync(art+'/source/bold.f').toString('base64')});
  assert(r.exact,'Uavhengig CEL-/planmaske avviker');assert.equal(r.midpoint,305*54,JSON.stringify(r.bad));
  assert.equal(r.faceMidpoint,c.indices.filter(v=>v&&v!==5).length);assert.equal(r.shadowMidpoint,c.indices.filter(v=>v===5).length);
  for(const t of[r.topology,r.faceTopology]){assert.equal(t.source.total,t.packed.total,'Kontur brutt');assert.equal(t.source_holes.internal,t.packed_holes.internal,'Originalt hull endret');}
  const bytes=Buffer.from(r.png,'base64');fs.mkdirSync(art+'/packed/bold.f',{recursive:true});fs.writeFileSync(art+'/packed/bold.f/073.png',bytes);
  fs.mkdirSync(art+'/verification',{recursive:true});for(const n of['face','shadow'])fs.writeFileSync(art+'/verification/'+n+'.png',Buffer.from(r[n+'_png'],'base64'));
  delete r.png;delete r.face_png;delete r.shadow_png;
  const report={status:'passed_source_geometry_material_candidate_not_activated',scope:'Kildeform, alfa, skygger, hovedtittel/undertekst og hull. Visuell godkjenning og runtime gjenstaar.',contract_sha256:sha(fs.readFileSync(art+'/contract.json')),candidate_sha256:sha(bytes),bytes:bytes.length,width:1220,height:216,activation:false,...r};
  fs.writeFileSync(art+'/verification/packing.json',JSON.stringify(report,null,2)+'\n');
  execFileSync('python3',['-c',"from PIL import Image,ImageDraw\nfrom pathlib import Path\np=Path('"+art+"')\no=Image.open(p/'source/nearest4x-reference.png').convert('RGBA');n=Image.open(p/'packed/bold.f/073.png').convert('RGBA')\ns=Image.new('RGB',(1260,510),'#1a1a1a');d=ImageDraw.Draw(s);d.text((20,10),'Original - source exact',fill='white');s.paste(o,(20,30),o);d.text((20,262),'Source-bound gold material candidate',fill='white');s.paste(n,(20,282),n);s.save(p/'comparison.png')"]);
  console.log(JSON.stringify({status:report.status,sha256:report.candidate_sha256,bytes:report.bytes,midpoints:r.midpoint,face_holes:r.faceTopology.source_holes.internal,activation:false}));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
