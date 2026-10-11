/* Reproduser siste Math-kandidat; produksjonsmetadata aktiveres separat av rot. */
'use strict';const {spawnSync}=require('child_process'),path=require('path');const art=__dirname,root=path.resolve(art,'../..');
const tasks=[
[0,'material/math-static-head-joined.png',{MOONSTONE_FIGURE_CONTRACT:art+'/static-pack-contract.json'}],
[3,'raw/003-v3.png',{MOONSTONE_FIGURE_EXPRESSION:art+'/open-eye-expression-registration.json'}],
[4,'material/004-registered.png',{MOONSTONE_FIGURE_CROP:JSON.stringify([141/320,53/200,38/320,13/200]),MOONSTONE_FIGURE_EXPRESSION:art+'/eye-expression-registration.json'}],
...[5,10].map(n=>[n,'material/'+String(n).padStart(3,'0')+'-head-joined.png',{MOONSTONE_FIGURE_CROP:JSON.stringify([12/70,12/72,46/70,48/72]),MOONSTONE_FIGURE_SHARED_MATERIAL:art+'/shared-cloth.json'}]),
...[7,12].map(n=>[n,'material/'+String(n).padStart(3,'0')+'-head-joined.png',{MOONSTONE_FIGURE_CROP:JSON.stringify([12/64,12/56,40/64,32/56]),MOONSTONE_FIGURE_SHARED_MATERIAL:art+'/shared-face-cloth-007-012.json',MOONSTONE_FIGURE_SEAM:art+'/cloak-bottom-seam-007-012.json'}])];
for(const[frame,raw,env]of tasks){const p=spawnSync(process.execPath,[root+'/tools/hd_math_figurer_pakk.cjs',String(frame),art+'/'+raw],{cwd:root,env:{...process.env,MOONSTONE_FIGURE_ART:path.relative(root,art),...env},stdio:'inherit'});if(p.status)process.exit(p.status||1);}
