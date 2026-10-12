/* Privat HTTP-vert og separat kontrollprosess; avslutter bare egen vert. */
'use strict';
const path=require('path'),{spawn}=require('child_process');
(async()=>{const s=await require('../figures/kn3-production/runtime-host.cjs')(process.env.MOONSTONE_FONT_PACKAGE);try{const c=spawn(process.execPath,[path.join(__dirname,process.env.MOONSTONE_TEXT_SCRIPT||'runtime-tekst-eierskap-font-v1.cjs')],{stdio:'inherit',env:{...process.env,MOONSTONE_URL:s.url}});const n=await new Promise((resolve,reject)=>{c.once('error',reject);c.once('exit',resolve);});process.exitCode=n||0;}finally{await s.close();}})().catch(e=>{console.error(e);process.exitCode=1;});
