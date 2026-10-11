/* Kontraktprøver for ekte canvas-kjerne: komposittsøm, hull og kildeblekk. */
'use strict';
const fs=require('fs'),path=require('path'),assert=require('assert/strict'),{chromium}=require('playwright');
const pack=require('./hd_resterende_ikoner_canvas.cjs'),root=path.resolve(__dirname,'..');
(async()=>{
 const b=await chromium.launch({headless:true,executablePath:'/usr/bin/google-chrome',args:['--no-sandbox']});
 try{
  const p=await b.newPage(),checks=[];
  const data=await p.evaluate(()=>{
   const make=(w,h,draw)=>{const c=document.createElement('canvas');c.width=w;c.height=h;draw(c.getContext('2d'));return c.toDataURL().split(',')[1];};
   return{raw:make(118,106,c=>{for(let y=0;y<53;y++)for(let x=0;x<59;x++){c.fillStyle=`rgb(${x*4},${y*4},${(x+y)*2})`;c.fillRect(x*2,y*2,2,2);}}),source:make(59,53,c=>{c.fillStyle='white';c.fillRect(0,0,59,53);}),tall:make(2,8,c=>{c.fillStyle='white';c.fillRect(0,0,2,8);}),solid:make(4,4,c=>{c.fillStyle='rgb(110,80,40)';c.fillRect(0,0,4,4);})};
  });
  const full=await p.evaluate(pack,{raw:data.raw,source:data.source,w:472,h:424,scale:8});
  const pieces=[];for(const rect of [[0,13,18,14],[18,0,41,27],[0,27,46,26]])pieces.push({...await p.evaluate(pack,{raw:data.raw,source:data.source,w:rect[2]*8,h:rect[3]*8,scale:8,composite:{width:59,height:53,rect}}),rect});
  const seam=await p.evaluate(async({full,pieces})=>{
   const read=async png=>{const i=new Image();i.src='data:image/png;base64,'+png;await i.decode();const c=document.createElement('canvas');c.width=i.width;c.height=i.height;c.getContext('2d').drawImage(i,0,0);return c;};
   const f=await read(full.png),r=f.getContext('2d').getImageData(0,0,f.width,f.height).data;let pixels=0;
   for(const part of pieces){const c=await read(part.png),a=c.getContext('2d').getImageData(0,0,c.width,c.height).data,[x,y]=part.rect;for(let yy=0;yy<c.height;yy++)for(let xx=0;xx<c.width;xx++){const i=(yy*c.width+xx)*4,j=((y*8+yy)*f.width+x*8+xx)*4;for(let k=0;k<4;k++)if(a[i+k]!==r[j+k])return{okay:false,pixels};pixels++;}}
   return{okay:true,pixels};
  },{full,pieces});assert(seam.okay,'Fragmentene må ha identiske fullmasterpiksler');checks.push({name:'three_chest_fragments_share_exact_pixels',...seam});
  const rune=await p.evaluate(pack,{raw:data.solid,source:data.solid,w:32,h:32,scale:8,source_clip:true,clip:'M0 0h4v4h-4Z M1 1h1v1h-1Z',ink_indices:[7,8],ink_rect:[0,0,3,3],paths:[{index:7,d:'M0 0h4v1h-4Z'},{index:8,d:'M2 2h2v2h-2Z'}],palette:{7:[221,0,0],8:[85,34,17]}});
  const samples=await p.evaluate(async png=>{const i=new Image();i.src='data:image/png;base64,'+png;await i.decode();const c=document.createElement('canvas');c.width=i.width;c.height=i.height;c.getContext('2d').drawImage(i,0,0);return[[4,4],[12,12],[20,20],[28,4],[28,28]].map(([x,y])=>[...c.getContext('2d').getImageData(x,y,1,1).data]);},rune.png);
  assert.deepEqual(samples,[[221,0,0,255],[0,0,0,0],[85,34,17,255],[110,80,40,255],[110,80,40,255]]);checks.push({name:'original_ink_and_transparent_hole_exact_and_bounded',samples});
  const port=await p.evaluate(pack,{raw:data.tall,source:data.solid,w:72,h:40,scale:8,placement:'contain'});assert.deepEqual(port.target_ink_bounds,[31,0,10,40]);checks.push({name:'approved_gate_preserves_aspect_and_bottom_anchor',bounds:port.target_ink_bounds});
  const report={status:'passed',created_at:new Date().toISOString(),checks};fs.writeFileSync(root+'/art/hd-remaining-icons-2026-10-11/research/runtime/canvas-contract-test.json',JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report));
 }finally{await b.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
