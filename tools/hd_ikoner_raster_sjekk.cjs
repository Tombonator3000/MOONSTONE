/* Verifiser selve rendererfunksjonene med aktive rasterbilder og originalpaletter. */
'use strict';
const fs=require('fs'),path=require('path'),assert=require('assert/strict'),{chromium}=require('playwright');
const root=path.resolve(__dirname,'..'),out=process.env.MOONSTONE_VERIFY_OUT||root+'/art/faithful-hd-icons-2026-10-11/verification';
const source=fs.readFileSync(root+'/web/src/render.js','utf8');
const code=source.slice(source.indexOf('    function ikonPalett('),source.indexOf('    /* po.cel blir brukt'));
(async()=>{
 const b=await chromium.launch({headless:true,executablePath:process.env.CHROME||'/usr/bin/google-chrome',args:['--no-sandbox']});
 const report={scope:'Originale rendererfunksjoner i nettleser, bildefilbevaring, 16 fadingnivaaer, vannsyklus, feil farge og ulik linjepalett. Ingen kunstnerisk godkjenning.',assets:[]};
 try{
  const p=await b.newPage();
  for(const m of JSON.parse(fs.readFileSync(root+'/web/hd/icons.json')).entries.filter(m=>m.render_mode==='raster')){
   const png=fs.readFileSync(root+'/web/hd/'+m.key+'.png').toString('base64');
   const result=await p.evaluate(async({m,png,code})=>{
    const checks=[];const check=(name,ok)=>{if(!ok)throw Error(m.key+': '+name);checks.push(name);};
    const im=new Image();im.src='data:image/png;base64,'+png;await im.decode();
    const canvas=document.createElement('canvas');canvas.width=im.width;canvas.height=im.height;canvas.getContext('2d').drawImage(im,0,0);
    const t={canvas,width:im.width,height:im.height,tex:{}},original=canvas.toDataURL();
    const pal=new Uint8Array(288*32*4),Kjerne={skanout:()=>({gyldig:true,pal})};
    const api=new Function('Kjerne','diwNaa',code+';return {fargeleggIkon,rasterIkonLys};')(Kjerne,[0,0,320,200]);
    const set=(level,shift=0)=>{pal.fill(0);for(let y=0;y<288;y++)for(const[c,rgb]of Object.entries(m.reference_palette)){
     const cycle=(m.reference_palette_cycles||[]).find(g=>g.includes(+c));
     const ref=cycle ? m.reference_palette[cycle[(cycle.indexOf(+c)+shift)%cycle.length]] : rgb;
     pal.set(ref.map(v=>Math.round(v/17*level/15)*17),(y*32+(+c)+(m.palette_offset||0))*4);
    }};
    const r=m.draw_rect,w=r ? r[2]-r[0] : m.width,h=r ? r[3]-r[1] : m.height;
    check('avtalte_bildemaal',im.width===w*m.scale&&im.height===h*m.scale);
    if(m.dynamic&&/^map-icons\/\d{3}$/.test(m.key)&&+m.key.slice(-3)<23){
     const ctx=canvas.getContext('2d'),pix=ctx.getImageData(0,0,im.width,im.height).data;
     let x0=im.width,y0=im.height,x1=0,y1=0;
     for(let y=0;y<im.height;y++)for(let x=0;x<im.width;x++)if(pix[(y*im.width+x)*4+3]>=16){x0=Math.min(x0,x);x1=Math.max(x1,x+1);y0=Math.min(y0,y);y1=Math.max(y1,y+1);}
     const alpha=(x,y)=>ctx.getImageData(Math.floor(x0+(x1-x0)*x),Math.floor(y0+(y1-y0)*y),1,1).data[3];
     check('originalt_visningsfelt',!m.draw_rect&&m.width===9&&m.height===5&&im.height===40);
     check('aapen_passasje',alpha(.5,.65)===0);
     check('to_steinstoetter',alpha(.17,.65)>128&&alpha(.83,.65)>128);
     check('overligger',alpha(.5,.15)>128);
    }
    let previous=-1;
    for(let n=0;n<=15;n++){
     set(n);check('fade_'+n,api.fargeleggIkon(m,t,0)&&t.ikonLys>=previous&&Math.abs(t.ikonLys-n/15)<.06);
     previous=t.ikonLys;check('bildefil_bevart_'+n,canvas.toDataURL()===original);
    }
    for(const cycle of m.reference_palette_cycles||[])for(let shift=0;shift<cycle.length;shift++){
     set(15,shift);check('vannsyklus_'+shift,api.fargeleggIkon(m,t,0)&&Math.abs(t.ikonLys-1)<.001);
    }
    set(15);const c=[m.base_index,...m.paths.map(p=>p.index)].find(c=>!m.preserve_indices?.includes(c))+(m.palette_offset||0);
    // Endre fargetone. Lavere roedstyrke alene er en gyldig fade for Hawk.
    for(let y=0;y<288;y++)pal.set([255,0,255],(y*32+c)*4);
    check('annen_farge_avvist',!api.fargeleggIkon(m,t,0));
    set(15);pal[(32+c)*4]^=16;check('ulik_linjepalett_avvist',!api.fargeleggIkon(m,t,0));
    set(15);canvas.getContext('2d').clearRect(0,0,canvas.width,canvas.height);t.ikonPalett=null;
    check('masken_gjenopprettes',api.fargeleggIkon(m,t,0)&&canvas.toDataURL()===original);
    return{key:m.key,checks};
   },{m,png,code});
   report.assets.push(result);
  }
  assert(report.assets.length>0);report.status='passed';
 }catch(e){report.status='failed';report.failure=String(e);process.exitCode=1;}
 finally{await b.close();report.created_at=new Date().toISOString();fs.mkdirSync(out,{recursive:true});fs.writeFileSync(out+'/raster-test.json',JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({status:report.status,assets:report.assets.length,checks:report.assets.reduce((n,a)=>n+a.checks.length,0),failure:report.failure}));}
})().catch(e=>{console.error(e);process.exitCode=1});
