/* Kontroller hele galleriet paa to nettleserbredder, uten fysisk enhetspaastand. */
'use strict';
const fs=require('fs'),path=require('path'),assert=require('assert/strict'),{chromium}=require('playwright');
const out=path.join(__dirname,'verification/gallery');
(async()=>{fs.mkdirSync(out,{recursive:true});const browser=await chromium.launch({executablePath:'/usr/bin/google-chrome',args:['--no-sandbox']});const results=[];
try{for(const [name,width,height]of [['desktop',1440,1000],['mobile',390,844]]){
const p=await browser.newPage({viewport:{width,height}}),errors=[];p.on('pageerror',e=>errors.push(e.message));await p.goto('http://127.0.0.1:8799/');await p.evaluate(()=>document.querySelectorAll('img').forEach(i=>i.loading='eager'));await p.waitForFunction(()=>[...document.images].every(i=>i.complete&&i.naturalWidth>0));assert.equal(await p.locator('article').count(),225);assert.equal(await p.locator('img').count(),450);assert(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));await p.screenshot({path:out+'/'+name+'.png'});
for(const[bank,count]of [['TROGGAxe1.CEL',37],['TROGGAxe2.CEL',80],['TROGGSpear1.CEL',41],['TROGGSpear2.CEL',67]]){await p.locator('select').selectOption(bank);assert.equal(await p.locator('article:visible').count(),count);}assert.deepEqual(errors,[]);results.push({name,width,height,cards:225,images:450,all_images_loaded:true,no_overflow:true,filters_passed:4,errors});await p.close();}
fs.writeFileSync(out+'/report.json',JSON.stringify({status:'passed',results},null,2)+'\n');console.log('Galleri225/450 og fire filtre paa desktop/mobilbredde bestaar');}finally{await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1;});
