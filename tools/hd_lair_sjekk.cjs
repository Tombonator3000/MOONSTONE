/* Faktisk WebGL-visning av lair-regelen. Kontrollerte original-CPU-kamper fra
 * lag_lair_fixture.py; laster bare kildeverifiserte kartbilder fra standardpakken.
 * MOONSTONE_BUILD kan peke til en fryst mappe med moonstone.html og hd/.
 * MOONSTONE_LAIR_FIXTURES velger generatorens mappe. Ingen spillkode patch'es.
 */
'use strict';
const fs=require('fs'),path=require('path'),crypto=require('crypto'),assert=require('assert/strict'),cp=require('child_process');
const{chromium}=require('playwright');
const root=path.resolve(__dirname,'..'),out=process.env.MOONSTONE_VERIFY_OUT||'/tmp/moonstone-lair-browser';
const fixtureDir=process.env.MOONSTONE_LAIR_FIXTURES||out+'/fixtures';
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const report={scope:'Faktisk original WASM + scenes.js + WebGL. Delvis import av ekte standardkart, ikke full lastertest. Kontrollerte sluttkamper, med separat view-fixtur som holder ridderen unna porten. Originalt loot-exit testes med ekte mus.',checks:[],captures:[],errors:[]};
let browser,host;
function check(name,ok){assert(ok,name);report.checks.push(name);console.log('OK '+name);}
(async()=>{
 fs.mkdirSync(out,{recursive:true});
 if(!fs.existsSync(fixtureDir+'/fixture.json'))cp.execFileSync('python3',[root+'/tools/lag_lair_fixture.py','--out',fixtureDir],{stdio:'inherit'});
 const fixture=JSON.parse(fs.readFileSync(fixtureDir+'/fixture.json'));
 const manifest=JSON.parse(fs.readFileSync(root+'/web/hd/manifest.json')),icons=JSON.parse(fs.readFileSync(root+'/web/hd/icons.json'));
 const assetPaths=['icons.json','bg/2c1e0fa5.png',...icons.entries.filter(m=>m.scene==='world-map').map(m=>m.key+'.png')];
 const assets=assetPaths.map(name=>{const b=fs.readFileSync(root+'/web/hd/'+name),m=manifest.files.find(f=>f.path===name);assert(m&&m.bytes===b.length&&m.sha256===sha(b),'manifest '+name);return{name,data:b.toString('base64')};});
 report.asset_paths=assetPaths;report.manifest_sha256=sha(fs.readFileSync(root+'/web/hd/manifest.json'));
 if(!process.env.MOONSTONE_URL)host=await require('../art/hd-completion-figures-2026-10-11/figures/kn3-production/runtime-host.cjs')(process.env.MOONSTONE_BUILD||root+'/web/build');
 report.url=process.env.MOONSTONE_URL||host.url;
 browser=await chromium.launch({executablePath:process.env.CHROME||'/usr/bin/google-chrome',args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 const p=await browser.newPage({viewport:{width:960,height:720}});p.on('pageerror',e=>report.errors.push(e.message));
 await p.addInitScript(()=>localStorage.setItem('moonstone.innstillinger',JSON.stringify({hd:'original',hdValgt:true,sprak:'no'})));
 const response=await p.goto(report.url);report.html_sha256=sha(await response.body());
 await p.waitForFunction(()=>window.moonDebug&&moonDebug.modus()==='alene'&&moonDebug.Kjerne.bildeNr()>0,null,{timeout:60000});
 await p.keyboard.press('Pause');
 await p.evaluate(async assets=>{const{Kjerne:K,Visning:V}=moonDebug;const files=assets.map(a=>{const f=new File([Uint8Array.from(atob(a.data),c=>c.charCodeAt(0))],a.name);Object.defineProperty(f,'webkitRelativePath',{value:a.name});return f;});await V.lastHdPakke(files);V.settTvungetLag(true);K.lagPaa(true);V.settHd(true);},assets);
 const load=async file=>p.evaluate(data=>{const{Kjerne:K,Visning:V,SceneHd:S}=moonDebug;if(!K.lastTilstand(Uint8Array.from(atob(data),c=>c.charCodeAt(0))))throw new Error(K.tilstandFeil());V.nullstillScene();S.nullstill();for(let i=0;i<25;i++){K.inndata(0,0);K.bilde();V.nyttBilde(K.tegneliste());}},fs.readFileSync(file).toString('base64'));
 async function capture(name,hd){
  const d=await p.evaluate(async({hd})=>{const{Kjerne:K,Visning:V,SceneHd:S}=moonDebug;V.settHd(hd);for(let n=0;n<35;n++){V.tegn(K.rammebuffer(),K.vindu(),S.korriger(K.rammebuffer(),K.vindu(),K.lag()));await new Promise(r=>setTimeout(r,15));}const l=S.korriger(K.rammebuffer(),K.vindu(),K.lag()),canvas=document.querySelector('#lerret');V.settHd(hd);V.tegn(K.rammebuffer(),K.vindu(),l);return{png:V.bildeTilPng(),frame:K.bildeNr(),state:K.sjekksum(),scene:S.info(),control:V.hdKontroll(),overlays:(l?.overlays||[]).map(o=>o.key),geometry:{vindu:Array.from(K.vindu()),utsnitt:V.utsnitt(),width:canvas.width,height:canvas.height}};},{hd});
  assert(d.geometry.utsnitt.every((v,i)=>v===d.geometry.vindu[i]),name+': vent paa stabilt skjermutsnitt');
  const png=Buffer.from(d.png.split(',')[1],'base64');delete d.png;d.png_sha256=sha(png);d.name=name;fs.writeFileSync(out+'/'+name+'.png',png);report.captures.push(d);return d;
 }
 await load(fixture.seed_sav);const before=await capture('map-before-win',true);
 check('before_win_HD_port_visible',before.overlays.includes('map-icons/003')&&before.control.bakgrunn==='hd');
 for(const n of [20,18]){
  const c=fixture.cases.find(c=>c.location===n),key=n===20?'map-icons/003':'map-icons/026';await load(c.view_sav);
  const hd=await capture('lair'+n+'-cleared-hd',true),original=await capture('lair'+n+'-cleared-original',false),restored=await capture('lair'+n+'-cleared-hd-return',true);
  check('lair'+n+'_HD_hides_exact_port',!hd.overlays.includes(key)&&hd.scene.cleared_lairs.some(q=>q[0]===c.position[0]&&q[1]===c.position[1])&&hd.control.bakgrunn==='hd');
  check('lair'+n+'_Original_and_HD_return',original.png_sha256!==hd.png_sha256&&restored.png_sha256===hd.png_sha256);
  check('lair'+n+'_rendering_preserves_CPU',hd.state===original.state&&hd.state===restored.state);
  const loot=await p.evaluate(c=>{const K=moonDebug.Kjerne,ptr=K.les16(c.address)*65536+K.les16(c.address+2);return K.les16(c.address+8)===c.gold&&K.les16(c.address+20)===1&&c.items.every((v,i)=>K.les8(ptr+i)===v);},c);
  check('lair'+n+'_original_loot_unchanged',loot);
 }
 const empty=fixture.cases.find(c=>c.location===19);await load(empty.view_sav);const e=await capture('lair19-empty-hd',true);
 check('empty_location_removed_by_original_CPU',!e.overlays.includes('map-icons/000')&&await p.evaluate(a=>moonDebug.Kjerne.les16(a+10)===65535&&moonDebug.Kjerne.les16(a+12)===65535,empty.address));
 check('other_port_and_town_remain',e.overlays.includes('map-icons/026')&&['map-icons/023','map-icons/024','map-icons/025'].some(k=>e.overlays.includes(k)));
 // Last ekte loot og la appens inputkoe behandle et vanlig PC-museklikk.
 const c=fixture.cases.find(c=>c.location===20);await load(c.loot_sav);
 check('original_loot_screen_is_active',await p.evaluate(()=>moonDebug.Kjerne.pekerAktiv()&&moonDebug.Kjerne.les16(0x8e8ca+2)===2));
 await capture('lair20-loot-before-mouse',true);
 await p.keyboard.press('Pause');
 const q=await p.evaluate(()=>{const r=document.querySelector('#lerret').getBoundingClientRect(),v=moonDebug.Kjerne.vindu(),c=moonDebug.Visning.utsnitt(),x=r.left+(v[0]+2*155.5-c[0])/(c[2]-c[0])*r.width,y=r.top+(v[1]+150.5-c[1])/(c[3]-c[1])*r.height;return{x,y,target:document.elementFromPoint(x,y)?.id,frame:moonDebug.Kjerne.bildeNr(),intro:moonDebug.Kjerne.iIntro(),menu:moonDebug.Kjerne.iMeny(),status:document.querySelector('#status').textContent};});
 report.mouse_exit_before=q;
 await p.mouse.click(q.x,q.y);
 // kartAktiv() betyr en styrbar mennesketur. Etter en kamp kan originalen
 // allerede styre AI-ridderen. Vent paa kildebekreftet kart, ikke inputeierskap.
 try{await p.waitForFunction(()=>!moonDebug.Kjerne.pekerAktiv()&&moonDebug.SceneHd.info()?.id==='world-map'&&moonDebug.Visning.hdKontroll().hdLys>=.99,null,{timeout:30000});}catch(e){report.mouse_exit_after=await p.evaluate(()=>({frame:moonDebug.Kjerne.bildeNr(),intro:moonDebug.Kjerne.iIntro(),menu:moonDebug.Kjerne.iMeny(),pointer:moonDebug.Kjerne.pekerAktiv(),mode:moonDebug.Kjerne.les16(0x8e8cc),status:document.querySelector('#status').textContent}));await p.screenshot({path:out+'/mouse-exit-failure.png'});throw e;}
 await p.keyboard.press('Pause');
 check('real_mouse_exits_original_loot_to_map',await p.evaluate(c=>moonDebug.Kjerne.les16(c.address+20)===1&&moonDebug.Kjerne.les16(c.address+8)===c.gold,c));
 await capture('lair20-real-mouse-exit',true);
 check('no_browser_errors',report.errors.length===0);report.status='passed';
})().catch(e=>{report.status='failed';report.failure=String(e.stack||e);console.error(e);process.exitCode=1;}).finally(async()=>{if(browser)await browser.close();if(host)await host.close();fs.mkdirSync(out,{recursive:true});fs.writeFileSync(out+'/report.json',JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({status:report.status,checks:report.checks.length,out}));});
