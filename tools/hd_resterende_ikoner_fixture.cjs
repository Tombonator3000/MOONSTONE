/* Delte originale frontend-fixturer. Ingen skriving til emulert spillminne. */
'use strict';
async function render(p){return p.evaluate(()=>{const K=moonDebug.Kjerne,V=moonDebug.Visning;V.tegn(K.rammebuffer(),K.vindu(),K.lag());return V.bildeTilPng();});}
async function stable(p){let old=await render(p);for(let i=0;i<40;i++){const png=await render(p);if(i>=7&&png===old)return png;old=png;}return old;}
async function fixture(p,contract,mirror=false,colors=null){await p.evaluate(({c,colors,mirror})=>{
 const K=moonDebug.Kjerne,V=moonDebug.Visning,diw=[70,19,710,219],x=148,y=Math.min(90,200-c.height);
 const idx=new Uint8Array(720*288),fb=new Uint8Array(720*288*4),pal=new Uint8Array(288*32*4),bak=new Uint8Array(256000),foran=new Uint8Array(256000),forIdx=new Uint8Array(64000);forIdx.fill(255);
 for(let i=3;i<bak.length;i+=4)bak[i]=255;
 for(let i=3;i<fb.length;i+=4)fb[i]=255;
 for(let row=0;row<288;row++)for(let col=0;col<32;col++)pal.set([...colors[col].slice(0,3),255],(row*32+col)*4);
 for(let j=0;j<c.height;j++)for(let i=0;i<c.width;i++){
  const color=c.indices[j*c.width+(mirror?c.width-1-i:i)];if(!color)continue;
  const n=(y+j)*320+x+i,screen=(diw[1]+y+j)*720+diw[0]+(x+i)*2;
  forIdx[n]=color;foran.set([...colors[color].slice(0,3),255],n*4);
  idx[screen]=idx[screen+1]=color;fb.set([...colors[color].slice(0,3),255],screen*4);fb.set([...colors[color].slice(0,3),255],(screen+1)*4);
 }
 const lag={bak,for:foran,forIdx,hash:0xd1000000+c.source.frame,lys:1,lysMaks:1};
 K.skanout=()=>({gyldig:true,idx,pal});K.rammebuffer=()=>fb;K.vindu=()=>diw;K.lag=()=>lag;
 const d={fil:c.source.file,bilde:c.source.frame,x,y,w:c.width,h:c.height,xoff:0,speilet:mirror};
 window.remainingIconFixture={idx,fb,pal,lag,d,c,colors};
 // Utsnittet har25-bilders stabilisering i faktisk renderer. Kjoer dette
 // bare foerste gang, uten gjentatte dyre PNG-readbacks.
 if(!window.remainingFixtureCropReady){for(let n=0;n<26;n++)V.tegn(fb,diw,lag);window.remainingFixtureCropReady=true;}
 V.nullstillScene();V.nyttBilde([d]);V.nyttBilde([]);V.nyttBilde([]);V.nyttBilde([]);
},{contract, c:contract,colors,mirror});}
module.exports={render,stable,fixture};
