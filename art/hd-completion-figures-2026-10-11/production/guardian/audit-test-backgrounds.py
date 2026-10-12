"""Kildebundet Test-/terrengaudit. Eksporterer originaler, aldri HD-grafikk."""
from pathlib import Path
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import argparse,hashlib,json,re,struct,subprocess,sys
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
sys.path.insert(0,str(ROOT/'tools'));import moonfiles as mf
sha=lambda b:hashlib.sha256(b).hexdigest()
rel=lambda p:str(p.relative_to(ROOT))
def fnv(b):
 h=2166136261
 for v in b:h=((h^v)*16777619)&0xffffffff
 return f'{h:08x}'
def save(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
ap=argparse.ArgumentParser();ap.add_argument('--output',default='verification/test-background-audit-v1');ap.add_argument('--capture32',action='store_true');args=ap.parse_args()
OUT=HERE/args.output;assert not (OUT/'audit.json').exists(),'Bevar tidligere kvittering';OUT.mkdir(parents=True,exist_ok=True)
game=mf.Spill(ROOT/'Moonstonecd32-AMIGA.zip');mog=game.les('mog');memory,_,_=mf.legg_ut(mog);test=game.les('data/test');pivs,end=mf.piv_alle(test)
assert len(pivs)==9 and end==len(test)
manifest_bytes=(ROOT/'web/hd/manifest.json').read_bytes();manifest=json.loads(manifest_bytes);hd={f['path'] for f in manifest['files']};(OUT/'manifest-at-audit.json').write_bytes(manifest_bytes)
def read(address,count):return memory[address-0x80000:address-0x80000+count]
def long(address):return struct.unpack('>I',read(address,4))[0]
def text(address):return memory[address-0x80000:].split(b'\0',1)[0].decode('latin1')
assert read(0x8015a,10)==bytes.fromhex('23fc0000000c00095f12') and read(0x80170,6)==bytes.fromhex('4eb900083d6e')
assert read(0x82960,6)==bytes.fromhex('4eb9000832f2')
assert read(0x88d16,12)==bytes.fromhex('0cb90000000800088dca6700')
roles=['terrengflisbank for terrain0/4','felles flisbank og UI-dekorasjoner','terrengflisbank for terrain8','terrengflisbank for terrain12','grunnbakgrunn terrain4','grunnbakgrunn terrain12 og Guardian uten dekorasjoner','grunnbakgrunn terrain8','grunnbakgrunn terrain0','verdenskart']
offsets=[8,12,20,16,24,32,36,28,92];position=0;source=[];sheet=Image.new('RGB',(960,660),(20,20,20));pen=ImageDraw.Draw(sheet)
for n,(planes,pal,raw) in enumerate(pivs):
 length=6+(2<<planes)+struct.unpack_from('>I',test,position+2)[0];indices=bytes(mf.plan_til_indeks(raw,planes));palette=[mf.amiga_rgb(w)for w in pal];image=Image.new('RGB',(320,200));image.putdata([tuple(palette[i])for i in indices]);png=OUT/f'test{n:03}-source-palette.png';image.save(png)
 x=n%3*320;y=n//3*220;sheet.paste(image,(x,y+20));pen.text((x+3,y+3),f'Test{n:03} {fnv(raw)}',fill='white')
 source.append(dict(frame=n,role=roles[n],compressed_offset=position,compressed_length=length,source_pointer_table_offset=hex(offsets[n]),planes_sha256=sha(raw),indices_sha256=sha(indices),fnv1a=fnv(raw),native_png=rel(png),native_png_sha256=sha(png.read_bytes()),palette_words=pal,palette_role='PIV source palette only; combat overrides below',direct_hd_path=f'bg/{fnv(raw)}.png',direct_hd=f'bg/{fnv(raw)}.png'in hd))
 position+=length
assert position==len(test);sheet.save(OUT/'source-nine.png')
terrains=[dict(terrain=0,base=7,atlas=0,common=1,table=0x8fdbc,branch=0x83326,counter=0x8cfb6,counter_bytes=2,palette_table=0x95ff6),dict(terrain=4,base=4,atlas=0,common=1,table=0x8fdfc,branch=0x833a4,counter=0x8cfb8,counter_bytes=1,palette_table=0x96010),dict(terrain=8,base=6,atlas=2,common=1,table=0x8fddc,branch=0x83226,counter=0x8cfb2,counter_bytes=2,palette_table=0x96044),dict(terrain=12,base=5,atlas=3,common=1,table=0x8fd9c,branch=0x832a4,counter=0x8cfb4,counter_bytes=2,palette_table=0x9602a)]
scenes=[]
for t in terrains:
 t['terrain_palette_16_28']=list(struct.unpack('>13H',read(t['palette_table'],26)));t['files']=[]
 for n in range(8):
  name=text(long(t['table']+n*4));blob=game.les(name);unpacked=mf.lz_ut(blob[4:]);collisions=struct.unpack_from('>H',unpacked)[0];start=2+8*collisions;tiles=[];pos=start
  while pos+6<=len(unpacked):
   code,x,y=struct.unpack_from('>Hhh',unpacked,pos);pos+=6
   if code>>8==255:break
   if code>>8==254:continue
   bank=t['atlas']if code>>8==3 else 1;tile=code&255;assert tile<80
   tiles.append(dict(code=hex(code),bank=bank,tile=tile,source_rect=[tile%10*32,tile//10*25,32,25],destination=[x,y]))
  else:raise AssertionError('Mangler avslutning')
  record=dict(terrain=t['terrain'],variant=n,source_file=name,source_file_sha256=sha(blob),unpacked_sha256=sha(unpacked),collision_count=collisions,tile_start=start,tile_count=len(tiles),bank_counts=dict(Counter(v['bank']for v in tiles)),negative_y=sum(v['destination'][1]<0 for v in tiles),negative_x=sum(v['destination'][0]<0 for v in tiles),right_edge=sum(v['destination'][0]>288 for v in tiles),tiles=tiles)
  scenes.append(record);t['files'].append(name)
assert len(scenes)==32
historical=[];palette_root=HERE/'../../palettes'
for file in sorted((palette_root/'cases').glob('*.json')):
 c=json.loads(file.read_text())
 if 'terrain'not in c:continue
 chip_path=palette_root/'runtime'/c['case']/'chip1500.bin';chip=chip_path.read_bytes();assert sha(chip)==c['chip_sha256']['chip1500.bin'];assert c['mog_sha256']==sha(mog)
 actual_terrain=struct.unpack_from('>I',chip,0x95f12)[0];bg=struct.unpack_from('>I',chip,0x8cde8)[0];raw=chip[bg:bg+40000];words=list(struct.unpack_from('>32H',chip,0x961a0));assert words==c['words'];h=fnv(raw)
 historical.append(dict(case=c['case'],frame=1500,scope='Historical controlled original headless run, not fresh WASM or public proof',case_path=rel(file.resolve()),case_sha256=sha(file.read_bytes()),chip_path=rel(chip_path.resolve()),chip_sha256=sha(chip),headless_sha256=c['headless_sha256'],actual_terrain=actual_terrain,background_pointer=hex(bg),background_fnv1a=h,background_planes_sha256=sha(raw),exact_raw_Test_frames=[n for n,p in enumerate(pivs)if p[2]==raw],direct_hd=f'bg/{h}.png'in hd,palette_words=words,palette_rgb=c['colors']))
def capture(scene):
 t=next(t for t in terrains if t['terrain']==scene['terrain']);folder=OUT/'original-runtime'/f"terrain{t['terrain']:02}-variant{scene['variant']}";folder.mkdir(parents=True,exist_ok=True)
 # Den forste originale 0831da velger n-1, kampinitialisatoren velger n.
 writes=[(0x80172,0x84316,4),(0x8d9ac,0x8d5b4,4),(0x8015c,t['terrain'],4),(t['counter'],(scene['variant']-1)&7,t['counter_bytes'])]
 command=[str(ROOT/'port/moonstone-headless'),'--headless','--frames','1250','--log','2','--press','100:esc:4','--press','700:down:4','--press','760:down:4','--press','820:fire:4','--dump',f'1200:{folder}/chip1200.bin','--dump',f'1250:{folder}/chip1250.bin']
 for address,value,size in writes:command+=['--skriv',f'900:{address:x}:0x{value:x}:{size}']
 result=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,check=True);(folder/'stdout.txt').write_text(result.stdout);(folder/'stderr.txt').write_text(result.stderr)
 chips=[(folder/f'chip{f}.bin').read_bytes()for f in(1200,1250)];backgrounds=[];palettes=[]
 for chip in chips:
  assert struct.unpack_from('>I',chip,0x95f12)[0]==t['terrain'];assert struct.unpack_from('>I',chip,0x88dca)[0]==0
  counter=int.from_bytes(chip[t['counter']:t['counter']+t['counter_bytes']],'big');assert counter==(scene['variant']+1)&7,(scene['source_file'],counter)
  pointer=struct.unpack_from('>I',chip,0x8cde8)[0];backgrounds.append(chip[pointer:pointer+40000]);palettes.append(list(struct.unpack_from('>32H',chip,0x961a0)))
 assert backgrounds[0]==backgrounds[1],'Original bakgrunn ble endret mellom fangstene';assert palettes[0]==palettes[1]
 raw=backgrounds[0];indices=bytes(mf.plan_til_indeks(raw,5));colors=[mf.amiga_rgb(w)for w in palettes[0]];image=Image.new('RGB',(320,200));image.putdata([tuple(colors[i])for i in indices]);png=folder/'background.png';image.save(png);(folder/'bitplanes.bin').write_bytes(raw);(folder/'indices.bin').write_bytes(indices)
 h=fnv(raw);r=dict(source_file=scene['source_file'],variant=scene['variant'],terrain=t['terrain'],status='source_original_runtime_export_verified',scope='Original beast initializer, terrain immediate and existing round-robin counter selected in private test memory only. No palette writes, no modified blitter, not a natural visit.',initializer='0x84316',command=command,test_writes=[dict(frame=900,address=hex(a),value=hex(v),bytes=s)for a,v,s in writes],stable_frames=[1200,1250],chip_sha256={str(f):sha(b)for f,b in zip((1200,1250),chips)},background_fnv1a=h,planes_sha256=sha(raw),indices_sha256=sha(indices),palette_words=palettes[0],palette_rgb=colors,source_palette_16_28_correct=palettes[0][16:29]==t['terrain_palette_16_28'],png=rel(png),png_sha256=sha(png.read_bytes()),direct_hd=f'bg/{h}.png'in hd)
 assert r['source_palette_16_28_correct'];save(folder/'receipt.json',r);print(scene['source_file'],h,'HD'if r['direct_hd']else'Original',flush=True);return r
runtime=[]
if args.capture32:
 with ThreadPoolExecutor(max_workers=2)as pool:runtime=list(pool.map(capture,scenes))
excerpts=[('test-pointer-table',0x80262,0x802d0),('terrain-selection',0x831da,0x834fc),('tile-source-and-mask',0x99abc,0x99df8),('tile-coordinates-and-file-load',0x99df8,0x99f28),('combat-palette',0x88a4e,0x88dca),('guardian-resets-background',0x82960,0x829a0),('guardian-initializer',0x849ea,0x84ae0),('world-map-Test008',0xaac14,0xaac58),('PIV-palette-loading',0x9cc54,0x9cc96)]
proofs=[];disasm=(ROOT/'disasm/mog.s').read_text().splitlines()
for name,start,finish in excerpts:
 data=read(start,finish-start);path=OUT/f'{name}.bin';path.write_bytes(data);assembly=[line for line in disasm if re.match(r'^[0-9a-f]{6} ',line)and start<=int(line[:6],16)<finish];(OUT/f'{name}.s').write_text('\n'.join(assembly)+'\n');proofs.append(dict(name=name,start=hex(start),end_exclusive=hex(finish),bytes_sha256=sha(data),path=rel(path)))
report=dict(schema=1,status='passed',scope='Read-only audit and optional original headless reference export. No generated art, no production modification.',script_sha256=sha(Path(__file__).read_bytes()),source_zip_sha256=sha((ROOT/'Moonstonecd32-AMIGA.zip').read_bytes()),mog_sha256=sha(mog),test_file_sha256=sha(test),headless_sha256=sha((ROOT/'port/moonstone-headless').read_bytes()),manifest_at_audit_sha256=sha(manifest_bytes),source_pivs=source,terrain_contracts=terrains,tile_scenes=scenes,historical_original_cases=historical,original_composites=runtime,source_excerpts=proofs,findings=['Test000..003 are source atlases, not four missing full-screen backgrounds.','Test004/006/007 are base terrain images. Their final background hashes normally change after *.t decorations. Direct raw hash absence is not a complete coverage audit.','Test005 is used without decorations by Guardian via082960->0832f2. cbc31cbf has HD in this manifest.','Every terrain selects eight original *.t layouts, or the exact scene file stored at08fb52 when08fb4e==2.','Tile group03 selects terrain atlas; other nonFE/nonFF groups select common atlas001. Original mask blitter uses five-plane nonzero coverage.','Combat palette starts from the last PIV palette, then original monster/player/terrain functions replace indices. Guardian uses its own9..31 source words and skips terrain replacement.','World map Test008 has a source-bound scene route, so its dynamic marker hash alone is not a coverage count.','bg1a.PIV/bg1c.PIV are intro scrolling tile banks handled by the scroll scene contract, not additional full-screen static backgrounds.'],limitations=['No freehand tile composition is asserted. The original blitter clips negative Y as -y-1, clamps negative X without source advance and can write across the right edge. Optional runtime exports execute that original code.','Historical combat backgrounds can include original runtime modifications. A missing dynamic hash is an observed lookup hole, not automatically a distinct new image job.','The optional32 layout exports use the original beast palette in each terrain; monster9..15 and player6..8 can vary in other fights.','No complete world traversal, gameplay modification, public verification or new HD art is claimed.'])
save(OUT/'audit.json',report);print(json.dumps(dict(status='passed',pivs=len(source),terrain_layouts=len(scenes),runtime_layouts=len(runtime),runtime_direct_hd=sum(r['direct_hd']for r in runtime),audit=rel(OUT/'audit.json'),sha256=sha((OUT/'audit.json').read_bytes()))))
