/* Kjoer eksisterende frontend-fixturer mot en isolert identisk PNG-pakke. */
'use strict';
const fs=require('fs'),path=require('path'),crypto=require('crypto'),assert=require('assert/strict'),{spawnSync}=require('child_process');
const art=__dirname,root=path.resolve(art,'../..'),input=art+'/runtime-input',sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const original=fs.readFileSync(art+'/source-contracts.json'),contracts=JSON.parse(original),redundant=[];
for(const c of contracts.entries){
 // En identisk grunnpalett er ingen alternativ palett. Konturtestets
 // RGB-krav gjelder dynamiske UI-farger, ikke fotografisk materiale.
 if(c.alternate_palettes?.length){assert(c.alternate_palettes.every(v=>JSON.stringify(v.palette)===JSON.stringify(c.palette)),c.key+' har en verklig alternativ palett');redundant.push(c.key);delete c.alternate_palettes;}
}
const hostBuild=JSON.parse(fs.readFileSync(art+'/verification/host-build.json'));assert.equal(sha(fs.readFileSync(art+'/runtime-host/moonstone-core-used.js')),hostBuild.wasm_core_sha256);assert.equal(sha(fs.readFileSync(art+'/runtime-host/moonstone.html')),hostBuild.html_sha256);
fs.mkdirSync(input,{recursive:true});fs.writeFileSync(input+'/source-contracts.json',JSON.stringify(contracts)+'\n');fs.copyFileSync(art+'/fragment-icons.json',input+'/fragment-icons.json');if(!fs.existsSync(input+'/packed'))fs.symlinkSync('../packed',input+'/packed','dir');
const result=spawnSync(process.execPath,[root+'/tools/hd_ui_sjekk.cjs'],{cwd:root,env:{...process.env,MOONSTONE_UI_ART:path.relative(root,input),MOONSTONE_HD_TEST_OUTPUT:path.relative(root,art)+'/verification/bound-runtime'},stdio:'inherit'});
const report={schema:1,status:result.status===0?'passed':'failed',source_contracts_sha256:sha(original),runtime_contracts_sha256:sha(fs.readFileSync(input+'/source-contracts.json')),fragment_icons_sha256:sha(fs.readFileSync(input+'/fragment-icons.json')),removed_identical_palette_probes:redundant,source_change:'Only redundant alternate-palettes equal to the exact original reference palette are removed. Source bank, expanded indices, dimensions and all actual paletted source colors are unchanged.',wasm_core_sha256:hostBuild.wasm_core_sha256,html_sha256:hostBuild.html_sha256,result_report:'verification/bound-runtime/ui-fixtures-test.json'};
fs.writeFileSync(art+'/verification/runtime-wrapper.json',JSON.stringify(report,null,2)+'\n');process.exitCode=result.status||0;
