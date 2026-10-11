/* Eksporter originale UI-konturer til en separat, etterproevbar kandidat. */
'use strict';
const fs=require('fs'),path=require('path'),assert=require('assert/strict'),crypto=require('crypto'),{chromium}=require('playwright');
const root=path.resolve(__dirname,'..'),art=path.resolve(root,process.env.MOONSTONE_UI_ART||'art/hd-ui-followup-2026-10-11');
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
(async()=>{
 const source=JSON.parse(fs.readFileSync(art+'/source-contracts.json')),fragment=JSON.parse(fs.readFileSync(art+'/fragment-icons.json'));
 assert.equal(source.candidate_icons_sha256,sha(fs.readFileSync(art+'/candidate-icons.json')));
 const report={scope:'Kildefast form, dimensjon og samtlige kildepikselmidtpunkter. Ingen fotografisk materialgodkjenning.',fragment_icons_sha256:sha(fs.readFileSync(art+'/fragment-icons.json')),source_contracts_sha256:sha(fs.readFileSync(art+'/source-contracts.json')),assets:[],checks:0};
 const b=await chromium.launch({headless:true,executablePath:process.env.CHROME||'/usr/bin/google-chrome',args:['--no-sandbox']});
 try{
  const p=await b.newPage();
  for(const m of fragment.entries){
   const c=source.entries.find(c=>c.key===m.key),svg=fs.readFileSync(art+'/svg/'+m.key+'.svg','utf8');
   const result=await p.evaluate(async({svg,m,c})=>{
    const im=new Image();im.src='data:image/svg+xml;base64,'+btoa(svg);await im.decode();const canvas=document.createElement('canvas');canvas.width=m.width*8;canvas.height=m.height*8;
    const ctx=canvas.getContext('2d');ctx.drawImage(im,0,0);const data=ctx.getImageData(0,0,canvas.width,canvas.height).data;
    let exact=0,transparent=0;const bad=[];
    for(let y=0;y<m.height;y++)for(let x=0;x<m.width;x++){
     const i=y*m.width+x,idx=c.indices[i],at=((y*8+4)*canvas.width+x*8+4)*4,got=Array.from(data.slice(at,at+4));
     const good=idx?got.every((v,k)=>v===(k===3?255:c.palette[idx][k])):got[3]===0;
     if(good){exact++;if(!idx)transparent++;}else if(bad.length<10)bad.push({x,y,idx,got});
    }
    // Tynne diagonaler skal vaere sammenhengende, og alle originale hull
    // skal beholdes. Bare midtpunkttreff ville godta feilaktige perlekjeder.
    const components=(mask,w,h,eight=false)=>{const seen=new Uint8Array(mask.length),offsets=eight?[[1,0],[-1,0],[0,1],[0,-1],[1,1],[1,-1],[-1,1],[-1,-1]]:[[1,0],[-1,0],[0,1],[0,-1]];let total=0,internal=0;for(let at=0;at<mask.length;at++){if(!mask[at]||seen[at])continue;total++;let edge=false;const todo=[at];seen[at]=1;for(let q=0;q<todo.length;q++){const i=todo[q],x=i%w,y=Math.floor(i/w);if(x===0||y===0||x===w-1||y===h-1)edge=true;for(const[dx,dy]of offsets){const xx=x+dx,yy=y+dy,n=yy*w+xx;if(xx>=0&&xx<w&&yy>=0&&yy<h&&mask[n]&&!seen[n]){seen[n]=1;todo.push(n);}}}if(!edge)internal++;}return{total,internal};};
    const before=Uint8Array.from(c.indices,v=>v?1:0),after=Uint8Array.from({length:canvas.width*canvas.height},(_,i)=>data[i*4+3]>=128?1:0);
    const topology={source_components:components(before,m.width,m.height,true).total,packed_components:components(after,canvas.width,canvas.height).total,source_holes:components(before.map(v=>1-v),m.width,m.height).internal,packed_holes:components(after.map(v=>1-v),canvas.width,canvas.height).internal};
    return{png:canvas.toDataURL('image/png').split(',')[1],exact,transparent,bad,topology};
   },{svg,m,c});
   assert.equal(result.exact,m.width*m.height,m.key+': kildepikselmidtpunkter avviker '+JSON.stringify(result.bad));
   assert.equal(result.topology.source_components,result.topology.packed_components,m.key+': diagonale originalstroek ble brutt');
   assert.equal(result.topology.source_holes,result.topology.packed_holes,m.key+': originale hull ble endret');
   const file=art+'/packed/'+m.key+'.png';fs.mkdirSync(path.dirname(file),{recursive:true});const bytes=Buffer.from(result.png,'base64');fs.writeFileSync(file,bytes);
   report.assets.push({key:m.key,width:m.width*8,height:m.height*8,bytes:bytes.length,sha256:sha(bytes),source_midpoints:result.exact,transparent_midpoints:result.transparent,topology:result.topology,quality_status:c.quality_status});
   report.checks+=result.exact+5;
  }
  report.status='passed';report.created_at=new Date().toISOString();fs.writeFileSync(art+'/packing-report.json',JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({status:report.status,assets:report.assets.length,checks:report.checks}));
 }finally{await b.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
