/* Eksporter de redigerbare SVG-kildene til standardpakkens PNG-filer. */
'use strict';
const fs=require('fs'),path=require('path'),crypto=require('crypto'),{chromium}=require('playwright');
const root=path.resolve(__dirname,'..'),art=root+'/art/hd-icons-2026-10-11';
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
(async()=>{
 const b=await chromium.launch({headless:true,executablePath:process.env.CHROME||'/usr/bin/google-chrome',args:['--no-sandbox']});
 try{
  const p=await b.newPage(),data=JSON.parse(fs.readFileSync(root+'/web/hd/icons.json'));
  for(const m of data.entries){
   const svg=fs.readFileSync(art+'/svg/'+m.key+'.svg','utf8');
   const result=await p.evaluate(async({svg,w,h})=>{const im=new Image();im.src='data:image/svg+xml;base64,'+btoa(svg);await im.decode();const c=document.createElement('canvas');c.width=w;c.height=h;c.getContext('2d').drawImage(im,0,0);return c.toDataURL('image/png').split(',')[1]},{svg,w:m.width*m.scale,h:m.height*m.scale});
   const target=root+'/web/hd/'+m.key+'.png';fs.mkdirSync(path.dirname(target),{recursive:true});fs.writeFileSync(target,Buffer.from(result,'base64'));
  }
  const file=root+'/web/hd/manifest.json',pkg=JSON.parse(fs.readFileSync(file));
  const paths=new Set(['icons.json',...data.entries.map(m=>m.key+'.png')]);
  pkg.files=pkg.files.filter(f=>!paths.has(f.path));
  for(const rel of [...paths].sort()){const bytes=fs.readFileSync(root+'/web/hd/'+rel);pkg.files.push({path:rel,bytes:bytes.length,sha256:sha(bytes),kind:'base'});}
  pkg.images=pkg.files.filter(f=>f.path.endsWith('.png')).length;
  fs.writeFileSync(file,JSON.stringify(pkg,null,2)+'\n');console.log(data.entries.length+' ikoner eksportert; pakken har '+pkg.images+' PNG-ruter');
 }finally{await b.close()}
})().catch(e=>{console.error(e);process.exitCode=1});
