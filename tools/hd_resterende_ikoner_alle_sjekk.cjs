/* Sekvensielle avgrensede GPU-nettlesere for alle nye KI/MI-kontrakter. */
'use strict';
const fs=require('fs'),path=require('path'),crypto=require('crypto'),assert=require('assert/strict'),{spawnSync}=require('child_process');
const root=path.resolve(__dirname,'..'),art=root+'/art/hd-remaining-icons-2026-10-11',out=path.resolve(root,process.env.MOONSTONE_HD_TEST_OUTPUT||'art/hd-remaining-icons-2026-10-11/research/runtime/all-cel-verification');
const sha=b=>crypto.createHash('sha256').update(b).digest('hex'),hash=sha(fs.readFileSync(art+'/candidate-icons.json'));
const assets=JSON.parse(fs.readFileSync(art+'/packing-report.json')).assets.filter(a=>['ki.cel','mi.c'].includes(a.key.split('/')[0])),size=8,report={candidate_icons_sha256:hash,batches:[],keys:[],checks:0};
fs.mkdirSync(out,{recursive:true});
try{
 const runtime=Object.fromEntries(['web/src/render.js','web/src/scenes.js'].map(f=>[f,sha(fs.readFileSync(root+'/'+f))]));
 report.production_code_sha256=runtime;
 if(process.env.MOONSTONE_FIXTURE_RESUME==='1'){
  const previous=JSON.parse(fs.readFileSync(art+'/research/runtime/tested-snapshots/98-runtime-contract.json'));
  for(const file of Object.keys(runtime))assert.equal(runtime[file],previous[file],'Produksjonskode endret etter tidligere batch');
 }
 for(let i=0;i<assets.length;i+=size){
  assert.equal(sha(fs.readFileSync(art+'/candidate-icons.json')),hash,'Kandidaten ble endret under testing');
  const keys=assets.slice(i,i+size).map(a=>a.key),dir=out+'/batch-'+String(i/size+1).padStart(2,'0');
  const file=dir+'/inventory-fixtures-test.json',prior=fs.existsSync(file)?JSON.parse(fs.readFileSync(file)):null;
  let child={status:0},result=prior;
  const reused=process.env.MOONSTONE_FIXTURE_RESUME==='1'&&prior?.status==='passed'&&prior.candidate_icons_sha256===hash&&JSON.stringify(prior.assets.map(a=>a.key))===JSON.stringify(keys);
  if(reused)console.log(JSON.stringify({status:'reused_passed',assets:keys.length,checks:prior.checks.length}));
  else{
   child=spawnSync(process.execPath,[root+'/tools/hd_resterende_ikoner_sjekk.cjs'],{cwd:root,encoding:'utf8',env:{...process.env,MOONSTONE_ICON_KEYS:keys.join(','),MOONSTONE_HD_TEST_OUTPUT:dir},timeout:300000});
   if(child.stdout)process.stdout.write(child.stdout);if(child.stderr)process.stderr.write(child.stderr);
   result=fs.existsSync(file)?JSON.parse(fs.readFileSync(file)):null;
  }
  report.batches.push({keys,report:path.relative(root,file),status:result?.status||'failed',reused,failure:result?.failure||String(child.error||'')});
  assert.equal(child.status,0,'GPU-batch feilet');assert.equal(result.status,'passed');assert.equal(result.candidate_icons_sha256,hash);assert.deepEqual(result.assets.map(a=>a.key),keys);
  report.keys.push(...keys);report.checks+=result.checks.length;
 }
 assert.equal(sha(fs.readFileSync(art+'/candidate-icons.json')),hash);assert.equal(new Set(report.keys).size,assets.length);report.status='passed';
}catch(e){report.status='failed';report.failure=String(e);process.exitCode=1;}
report.created_at=new Date().toISOString();fs.writeFileSync(out+'/cel-fixtures-batches-test.json',JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({status:report.status,assets:report.keys.length,batches:report.batches.length,checks:report.checks,failure:report.failure}));
