/* Sammenlign eksporterte HD-bilder med uavhengig pixelriktig SVG-kilde. */
'use strict';
const fs=require('fs'),path=require('path'),assert=require('assert/strict'),{chromium}=require('playwright');
const root=path.resolve(__dirname,'..'),art=root+'/art/hd-icons-2026-10-11';
(async()=>{
 const b=await chromium.launch({headless:true,executablePath:process.env.CHROME||'/usr/bin/google-chrome',args:['--no-sandbox']});
 const report={assets:[],errors:[],scope:'Pikselmidtpunkter i original og faktisk eksportert PNG. Dette er kilde-/eksportkontroll, ikke naturlig spillreise.'};
 try{
  const p=await b.newPage(),data=JSON.parse(fs.readFileSync(root+'/web/hd/icons.json'));
  for(const m of data.entries){
   const original=fs.readFileSync(art+'/source/'+m.key+'.svg').toString('base64'),hd=fs.readFileSync(root+'/web/hd/'+m.key+'.png').toString('base64');
   const result=await p.evaluate(async({original,hd,w,h,s})=>{
    const load=async(src)=>{const im=new Image();im.src=src;await im.decode();const c=document.createElement('canvas');c.width=w*s;c.height=h*s;c.getContext('2d').drawImage(im,0,0);return c.getContext('2d').getImageData(0,0,c.width,c.height).data;};
    const a=await load('data:image/svg+xml;base64,'+original),b=await load('data:image/png;base64,'+hd);let count=0;const failures=[];
    for(let y=0;y<h;y++)for(let x=0;x<w;x++){const i=((y*s+s/2)*w*s+x*s+s/2)*4;count++;if(a[i+3]!==b[i+3]||(a[i+3]&&[0,1,2].some(k=>a[i+k]!==b[i+k])))failures.push([x,y,Array.from(a.slice(i,i+4)),Array.from(b.slice(i,i+4))]);}
    return{samples:count,failures};
   },{original,hd,w:m.width,h:m.height,s:m.scale});
   report.assets.push({key:m.key,samples:result.samples,failed:result.failures.length});
   if(result.failures.length)report.errors.push({key:m.key,failures:result.failures.slice(0,10)});
  }
  assert.equal(report.errors.length,0,JSON.stringify(report.errors));report.status='passed';
 }catch(e){report.status='failed';report.failure=String(e);process.exitCode=1;}
 finally{report.created_at=new Date().toISOString();fs.writeFileSync(art+'/verification/source-test.json',JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({status:report.status,assets:report.assets.length,samples:report.assets.reduce((n,a)=>n+a.samples,0),errors:report.errors}));await b.close();}
})().catch(e=>{console.error(e);process.exitCode=1});
