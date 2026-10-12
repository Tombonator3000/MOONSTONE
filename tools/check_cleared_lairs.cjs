/* Faktisk original WASM og scenes.js. Visningsadapteren erstatter bare GPU/HTTP,
 * ikke CPU, scanout, minne, PIV-dekoding eller den produserte scenekoden. */
'use strict';
const fs=require('fs'),path=require('path'),vm=require('vm'),crypto=require('crypto'),assert=require('assert/strict'),cp=require('child_process');
const root=path.resolve(__dirname,'..'),args=process.argv.slice(2);
const out=path.resolve(args.includes('--out')?args[args.indexOf('--out')+1]:'/tmp/moonstone-cleared-lairs-check');
const fixtures=path.resolve(args.includes('--fixtures')?args[args.indexOf('--fixtures')+1]:out+'/fixtures');
fs.mkdirSync(out,{recursive:true});
if(!fs.existsSync(fixtures+'/fixture.json'))cp.execFileSync('python3',[root+'/tools/lag_lair_fixture.py','--root',root,'--out',fixtures],{stdio:'inherit'});
const fixture=JSON.parse(fs.readFileSync(fixtures+'/fixture.json'));
const manifest=JSON.parse(fs.readFileSync(root+'/web/hd/manifest.json'));
const icons=JSON.parse(fs.readFileSync(root+'/web/hd/icons.json')).entries;
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const report={scope:'Kontrollerte originalkamper fra lag_lair_fixture.py. Faktisk WASM+scanout+scenes.js, uten GPU. Visningsfixtur flytter ridderen16piksler foer original redraw; natural-sav bevarer posisjonen. Ingen nye spillregler eller autoloot.',checks:[],cases:[],fixture:fixtures+'/fixture.json'};
const check=(name,value)=>{assert(value,name);report.checks.push(name);console.log('OK '+name);};
global.MoonCore=require(root+'/web/build/moonstone-core.js');
vm.runInThisContext(fs.readFileSync(root+'/web/src/core.js','utf8')+'\nglobal.K=Kjerne;');
vm.runInThisContext(fs.readFileSync(root+'/web/src/grafikk.js','utf8')+'\nglobal.G=Spillgrafikk;');
let hd=true,background=true;
global.StandardHd={info:()=>({aktiv:true}),scener:()=>manifest.scenes};
global.Visning={hdAntall:()=>1,hdPaa:()=>hd,harHdBilde:()=>background,sceneOverleggKlar:()=>true,
 sceneIkoner:id=>icons.filter(i=>i.scene===id&&i.dynamic),sceneIkonKlar:()=>true};
vm.runInThisContext(fs.readFileSync(root+'/web/src/scenes.js','utf8')+'\nglobal.S=SceneHd;');
const keys=l=>l.overlays.map(o=>o.key).sort();
const region=(array,x,y)=>Array.from({length:45},(_,i)=>array[(y+Math.floor(i/9))*320+x+i%9]);
const state=()=>({hash:K.sjekksum(),sha:sha(K.lagreTilstand())});
async function draw(){let l;for(let i=0;i<14;i++){l=S.korriger(K.rammebuffer(),K.vindu(),K.lag());await new Promise(r=>setTimeout(r,10));}return l;}
async function load(file){assert(K.lastTilstand(fs.readFileSync(file)),K.tilstandFeil());S.nullstill();hd=true;background=true;for(let i=0;i<25;i++){K.inndata(0,0);K.bilde();}return draw();}
function originalPort(x,y){const scan=K.skanout(),v=K.vindu(),g=G._cel(K.hentFil('data/mi.c'))[20];return g.px.every((c,i)=>!c||scan.idx[(v[1]+y+Math.floor(i/9))*720+v[0]+(x+i%9)*2]===c);}
(async()=>{
 await K.last();K.aapneInnebygd();K.start(false);K.menyPaa(true);K.lagPaa(true);
 let l=await load(fixture.seed_sav);
 check('foer seier er port136,40 synlig i HD',keys(l).includes('map-icons/003')&&originalPort(136,40));
 const seedState=state();await draw();check('sourcekontroll og tegning endrer ikke CPU eller lagring',JSON.stringify(state())===JSON.stringify(seedState));
 for(const idx of [20,18]){
  const c=fixture.cases.find(c=>c.location===idx),[x,y]=c.position,key=idx===20?'map-icons/003':'map-icons/026';
  l=await load(c.view_sav);const before=state(),raw=K.skanout().idx.slice();
  check(`lair${idx}: original seiersflag er1`,K.les16(c.address+20)===1);
  check(`lair${idx}: gull/loot er fortsatt urort`,K.les16(c.address+8)===c.gold&&c.items.every((v,i)=>K.les8(K.les16(c.address)*65536+K.les16(c.address+2)+i)===v));
  check(`lair${idx}: original CPU beholder porten`,originalPort(x,y));
  check(`lair${idx}: HD skjuler port og kildepiksler`,!keys(l).includes(key)&&region(l.forIdx,x,y).every(v=>v===255)&&S.info().cleared_lairs.some(p=>p[0]===x&&p[1]===y));
  const hidden=l.forIdx.slice(),hiddenKeys=keys(l),read=K.les16;
  K.les16=a=>a===c.address+20?0:read(a);
  const undefeated=await draw();K.les16=read;
  check(`lair${idx}: foer seiersflag vises den samme porten`,keys(undefeated).includes(key));
  check(`lair${idx}: andre markorer og byer beholdes`,JSON.stringify(keys(undefeated).filter(k=>k!==key))===JSON.stringify(hiddenKeys));
  check(`lair${idx}: bare akkurat9x5-feltet frigis`,hidden.every((v,p)=>p%320>=x&&p%320<x+9&&Math.floor(p/320)>=y&&Math.floor(p/320)<y+5||v===undefeated.forIdx[p]));
  hd=false;const original=await draw();
  check(`lair${idx}: Original beholder den opprinnelige porten`,region(original.forIdx,x,y).some(v=>v===19)&&!S.info().cleared_lairs);
  hd=true;l=await draw();check(`lair${idx}: HD-retur skjuler igjen`,region(l.forIdx,x,y).every(v=>v===255)&&!keys(l).includes(key));
  check(`lair${idx}: Original/HD endrer aldri scanout eller state`,raw.every((v,i)=>v===K.skanout().idx[i])&&JSON.stringify(state())===JSON.stringify(before));
  report.cases.push({location:idx,frame:K.bildeNr(),original_port:true,hd_port:false,gold:c.gold,items:c.items,core:before});
 }
 const empty=fixture.cases.find(c=>c.location===19);l=await load(empty.view_sav);
 check('helt tom lair fjernes av originalen medFFFF,FFFF',K.les16(empty.address+10)===65535&&K.les16(empty.address+12)===65535&&!originalPort(96,16));
 check('helt tom lair har ingen HD-port',!keys(l).includes('map-icons/000')&&region(l.forIdx,96,16).every(v=>v===255));
 check('ubeseiret24,24 bruker ny026-kontrakt',keys(l).includes('map-icons/026'));
 const gold=fixture.cases.find(c=>c.location===20);await load(gold.view_sav);
 for(const filename of ['mog','mi.c']){
  const original=K.hentFil('data/'+filename),changed=original.slice();changed[100]^=1;
  K.leggInnFil('data/'+filename,changed);l=await draw();
  check(`endret ${filename} avviser minnekartregel`,keys(l).includes('map-icons/003')&&originalPort(136,40)&&!S.info().cleared_lairs);
  K.leggInnFil('data/'+filename,original);l=await draw();
  check(`original ${filename} gjenoppretter regel etter filrevisjon`,!keys(l).includes('map-icons/003')&&region(l.forIdx,136,40).every(v=>v===255));
 }
 const read=K.les16;
 for(const [label,override] of [['ukjent seiersflag',a=>a===gold.address+20?2:read(a)],['ugyldig tabell',a=>a===0x8cdb2?65535:read(a)],['endret opcode',a=>a===0x080d1c?0:read(a)]]){
  K.les16=override;l=await draw();K.les16=read;
  check(label+' beholder originalport',keys(l).includes('map-icons/003')&&originalPort(136,40)&&!S.info().cleared_lairs);
 }
 const originalScan=K.skanout,scan=originalScan(),idx=scan.idx.slice(),v=K.vindu();idx[(v[1]+41)*720+v[0]+138*2]=31;
 K.skanout=()=>({...scan,idx});l=await draw();K.skanout=originalScan;
 check('overlapp/ny markerstatus beholder pikselvern',!S.info().cleared_lairs&&l.forIdx[41*320+138]===31);
 background=false;l=await draw();background=true;
 check('manglende HD-terreng beholder originalport',region(l.forIdx,136,40).some(v=>v===19)&&!S.info().cleared_lairs);
 report.status='passed';
})().catch(e=>{report.status='failed';report.failure=String(e);console.error(e);process.exitCode=1;}).finally(()=>{
 report.source_sha256=Object.fromEntries(['web/src/scenes.js','tools/lag_lair_fixture.py','web/hd/icons.json','web/build/moonstone-core.js'].map(f=>[f,sha(fs.readFileSync(root+'/'+f))]));
 fs.writeFileSync(out+'/report.json',JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({status:report.status,checks:report.checks.length,failure:report.failure}));
});
