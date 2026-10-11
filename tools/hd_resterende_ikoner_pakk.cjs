/* Pakk gjennomgaatte rastermastere uten aa skrive til standardpakken.
 * Raaresultatene beholdes urort. Kun transparente kanter og skalering endres. */
'use strict';
const fs=require('fs'),path=require('path'),crypto=require('crypto'),assert=require('assert/strict'),{chromium}=require('playwright');
const root=path.resolve(__dirname,'..'),art=root+'/art/hd-remaining-icons-2026-10-11';
const pakkCanvas=require('./hd_resterende_ikoner_canvas.cjs');
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const within=rel=>{assert.equal(typeof rel,'string');const p=path.resolve(art,rel);assert(p.startsWith(art+'/'),'Sti utenfor kunstmappen');return p;};
(async()=>{
 const activeBytes=fs.readFileSync(root+'/web/hd/icons.json'),active=JSON.parse(activeBytes),candidate=structuredClone(active);
 const baselineBytes=fs.readFileSync(art+'/research/runtime/source-baseline-icons.json'),baseline=JSON.parse(baselineBytes);
 const oldRaster=baseline.entries.filter(m=>m.render_mode==='raster');assert.equal(oldRaster.length,26,'Den uforanderlige kildepakken skal ha 26 eldre rasterruter');
 for(const m of oldRaster)assert.deepEqual(active.entries.find(a=>a.key===m.key),m,'Aktiv eldre rasterkontrakt endret: '+m.key);
 const records=fs.readdirSync(art).filter(n=>/^asset-.*\.json$/.test(n)).sort().map(n=>({...JSON.parse(fs.readFileSync(art+'/'+n)),record:n})).filter(a=>a.review_status==='reviewed_for_runtime');
 assert(records.length,'Ingen gjennomgaatte rastermastere');assert.equal(new Set(records.map(a=>a.key)).size,records.length,'Duplikatnokkel');
 const inventory=JSON.parse(fs.readFileSync(root+'/art/hd-icons-2026-10-11/source/inventory-palette.json')).palette;
 const map=JSON.parse(fs.readFileSync(root+'/art/hd-icons-2026-10-11/source/map-frame2000.json')).palette;
 const piv=JSON.parse(fs.readFileSync(art+'/research/runtime/piv-palettes.json'));
 const original=JSON.parse(fs.readFileSync(art+'/research/runtime/source-contracts.json'));
 const statiskeMi=new Set([...Array(19).keys(),20,31,33,42,43,44,45,46].map(n=>'mi.c/'+String(n).padStart(3,'0')));
 const bevarFor=key=>{
  const c=original.entries.find(c=>c.key===key),n=c?.source.frame;
  if(key==='ki.cel/037')return[30];
  if(['map-icons/023','map-icons/024','map-icons/025'].includes(key))return[19];
  if(statiskeMi.has(key)&&n<=9)return n<5?[19]:[19,31];
  if(key==='mi.c/033')return[19];if(key==='mi.c/042')return[19,31];
  return statiskeMi.has(key)&&c.source_colors.includes(31)?[31]:null;
 };
 const report={schema:1,baseline_icons_sha256:sha(activeBytes),baseline_entry_count:active.entries.length,source_baseline_icons_sha256:sha(baselineBytes),source_baseline_commit:'4365315',assets:[],preserved_raster_keys:oldRaster.map(m=>m.key),scope:'Pakking og kildekontrakter. review_status maa bygge paa separat visuell motivkontroll.'};
 const browser=await chromium.launch({headless:true,executablePath:process.env.CHROME||'/usr/bin/google-chrome',args:['--no-sandbox']});
 try{
  const p=await browser.newPage();
  for(const a of records){
   let m=structuredClone(baseline.entries.find(m=>m.key===a.key));
   if(!m&&statiskeMi.has(a.key)){
    const c=original.entries.find(c=>c.key===a.key);assert(c?.source_nontransparent_pixels,'Mangler original MI-kilde');
    const path=col=>c.indices.map((v,i)=>v===col?'M'+i%c.width+' '+Math.floor(i/c.width)+'h1v1h-1Z':'').join('');
    m={key:c.key,width:c.width,height:c.height,scale:8,source:c.source,indices_sha256:c.indices_sha256,plane_mask:c.plane_mask,
     base_index:c.source_colors.includes(19)?19:c.source_colors[0],clip:c.source_colors.map(path).join(''),paths:c.source_colors.map(index=>({index,d:path(index)}))};
    if(bevarFor(a.key))assert.deepEqual(a.preserve_indices,bevarFor(a.key),'MI-kant og valgtpuls maa bevares');
   }
   assert(m,'Mangler aktiv kildekontrakt: '+a.key);assert(m.render_mode!=='raster','Eksisterende rasterrute skal bevares: '+a.key);
   const existing=candidate.entries.findIndex(m=>m.key===a.key);if(existing<0)candidate.entries.push(m);else candidate.entries[existing]=m;
   assert(a.placement==='source_bounds'||a.placement==='contain'&&['mi.c/020','mi.c/031'].includes(a.key),'Bare kildebounds, eller godkjent proporsjonal portplassering, er tillatt');
   const raw=fs.readFileSync(within(a.raw)),source=fs.readFileSync(within(a.source));assert(fs.existsSync(within(a.prompt)),'Mangler prompt');
   let composite=null;
   if(a.composite){
    const c=a.composite,rect=c.rect;assert.equal(c.width,59,'Skattekistens originalbredde er 59');assert.equal(c.height,53,'Skattekistens originalhoeyde er 53');
    const rects={'ki.cel/031':[0,13,18,14],'ki.cel/032':[18,0,41,27],'ki.cel/033':[0,27,46,26]};
    assert.deepEqual(rect,rects[a.key],'Komposittrect maa vaere originalens skattekisterute');assert.equal(rect[2],m.width);assert.equal(rect[3],m.height);
    const csource=fs.readFileSync(within(c.source));composite={...c,source_sha256:sha(csource)};
   }

   let pal=inventory;
   if(m.hardware_sprite)pal=inventory.map((_,c)=>inventory[(c+(m.palette_offset||0))%32]);
   else if(m.scene)pal=m.dynamic?map:piv[m.source.file.toLowerCase()][m.source.frame];
   else if(a.key.startsWith('mi.c/'))pal=map;
   else if(a.key.startsWith('sel.cel/'))pal=piv['ch.piv'][0];
   assert(pal,'Mangler kildepalett: '+a.key);

   assert(a.source_clip===undefined||typeof a.source_clip==='boolean','Ugyldig kildeklipp');
   if(a.ink_indices){
    assert(a.source_clip===true,'Originalblekk krever kildeklipp');assert(a.ink_indices.length>0&&a.ink_indices.every(c=>Number.isInteger(c)&&c>=1&&c<=31&&pal[c]),'Ugyldige blekkindekser');
    assert(Array.isArray(a.ink_rect)&&a.ink_rect.length===4&&a.ink_rect.every(Number.isInteger),'Ugyldig blekkrekt');
    const [x,y,w,h]=a.ink_rect;assert(x>=0&&y>=0&&w>0&&h>0&&x+w<=m.width&&y+h<=m.height,'Blekk utenfor originalruten');
   }
   const result=await p.evaluate(pakkCanvas,{raw:raw.toString('base64'),source:source.toString('base64'),w:m.width*m.scale,h:m.height*m.scale,composite,scale:m.scale,placement:a.placement,
    source_clip:a.source_clip,clip:m.clip,ink_indices:a.ink_indices,ink_rect:a.ink_rect,paths:m.paths,palette:pal});
   if(a.preserve_indices!==undefined){assert.deepEqual(a.preserve_indices,bevarFor(a.key)||[],'Bare dokumenterte kildeindekser kan vernes');if(a.preserve_indices.length)m.preserve_indices=a.preserve_indices;}
   m.render_mode='raster';m.reference_palette=Object.fromEntries([...new Set([m.base_index,...m.paths.map(p=>p.index)])].map(c=>[c,pal[c].slice(0,3)]));
   if(a.reference_palette_cycles!==undefined){
    assert(['map-landmarks/004','map-landmarks/005'].includes(a.key),'Bare dokumenterte nye vannlandemerker kan angi palettsyklus');
    assert.deepEqual(a.reference_palette_cycles,[[21,22,23]],'Originalkartet roterer bare21..23');m.reference_palette_cycles=a.reference_palette_cycles;
    for(const c of a.reference_palette_cycles.flat())m.reference_palette[c]=pal[c].slice(0,3);
   }
   const variants=[];
   if(a.palette_variants){
    const side={'ki.cel/017':[28,29],'ki.cel/018':[30,31],'ki.cel/019':[28,29],'ki.cel/020':[30,31]}[a.key];
    const pairs={blue:[[0,51,255],[0,34,136]],orange:[[255,187,0],[187,102,0]],green:[[68,204,51],[17,102,0]],red:[[255,0,0],[136,0,0]],purple:[[0,34,119],[0,0,51]]};
    assert(side,'Palettvarianter er bare kildeverifisert for livsymbolene');assert.equal(a.palette_variants.length,5);assert.equal(new Set(a.palette_variants.map(v=>v.id)).size,5);
    assert.equal(a.palette_variants.find(v=>v.id==='blue')?.raw,a.raw,'Blaa base skal vaere normal raw');m.palette_variants=[];
    for(const v of a.palette_variants){
     assert.deepEqual(v.indices,side);assert.deepEqual(v.colors,pairs[v.id]);
     const key=v.id==='blue'?a.key:'ki-palettes/'+a.key.slice(-3)+'-'+v.id;
     m.palette_variants.push({id:v.id,key,indices:side,colors:v.colors});
     if(v.id==='blue'){side.forEach((c,i)=>m.reference_palette[c]=v.colors[i]);continue;}
     const bytes=fs.readFileSync(within(v.raw));
     const r=await p.evaluate(pakkCanvas,{raw:bytes.toString('base64'),source:source.toString('base64'),w:m.width*m.scale,h:m.height*m.scale,scale:m.scale});
     const png=Buffer.from(r.png,'base64');delete r.png;const target=within('packed/'+key+'.png');fs.mkdirSync(path.dirname(target),{recursive:true});fs.writeFileSync(target,png);
     variants.push({...v,key,...r,raw_sha256:sha(bytes),packed_sha256:sha(png),packed_bytes:png.length});
    }
   }
   const png=Buffer.from(result.png,'base64');delete result.png;
   const packed=within('packed/'+a.key+'.png');fs.mkdirSync(path.dirname(packed),{recursive:true});fs.writeFileSync(packed,png);
   report.assets.push({...a,...result,...(variants.length?{variants}:{}),record_sha256:sha(fs.readFileSync(art+'/'+a.record)),prompt_sha256:sha(fs.readFileSync(within(a.prompt))),...(composite?{composite}:{}),raw_sha256:sha(raw),source_sha256:sha(source),packed_sha256:sha(png),packed_bytes:png.length,
    warning:'Silhuettmaal er diagnostikk. Motiv og proporsjoner maa vaere kontrollert visuelt.'});
  }
  for(const key of report.preserved_raster_keys)assert.deepEqual(candidate.entries.find(m=>m.key===key),active.entries.find(m=>m.key===key),'Eldre rastermetadata endret');
  candidate.method='source-bound-contours-and-raster-redraws';
  const bytes=Buffer.from(JSON.stringify(candidate)+'\n');report.candidate_icons_sha256=sha(bytes);report.created_at=new Date().toISOString();
  fs.writeFileSync(art+'/candidate-icons.json',bytes);fs.writeFileSync(art+'/packing-report.json',JSON.stringify(report,null,2)+'\n');
  console.log(JSON.stringify({assets:report.assets.length,preserved_raster:report.preserved_raster_keys.length,entries:candidate.entries.length,files:report.assets.map(a=>({key:a.key,iou:+a.silhouette_iou.toFixed(3),bytes:a.packed_bytes}))}));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
