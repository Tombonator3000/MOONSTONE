"""Les originale Guardian-tabeller. Ingen runtime-, grafikk- eller manifestendring."""
from pathlib import Path
import hashlib,json,struct,sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
sys.path.insert(0,str(ROOT/'tools'))
import moonfiles as mf
sha=lambda b:hashlib.sha256(b).hexdigest()
zip_path=ROOT/'Moonstonecd32-AMIGA.zip';game=mf.Spill(zip_path);mog=game.les('data/mog');mem,_,_=mf.legg_ut(mog)
read=lambda start,end:bytes(mem[start-0x80000:end-0x80000])
# Instruksjonene kontrolleres mot relokert original, aldri mot endrede runtime-data.
expected={0x829cc:'21490000',0x829fa:'21490008',0x84a42:'237c000952b60016',0x84a4a:'237c000954d2001a',0xacb56:'b27c0082',0xacb6a:'23fc000956940008d8d2',0xaceda:'48e7fffe',0xacef4:'0469000a0050',0xacf6a:'4a690050',0xacf6e:'6e4c',0x87a50:'0200001f',0x87a58:'102e0001',0x87bf2:'06a9000000060002'}
for pc,value in expected.items():assert read(pc,pc+len(value)//2).hex()==value,(hex(pc),read(pc,pc+len(value)//2).hex())
start,end=0x95694,0x95908;at=start;draws=[];controls=[]
while at<end:
 op=read(at,at+1)[0]
 if op==0:
  d=read(at,at+6);draws.append(dict(pc=f'{at:06x}',frame=d[1],bank_table_byte_offset=d[0]&31,y=struct.unpack('b',d[2:3])[0],flags=d[3],x=struct.unpack('>h',d[4:6])[0],bytes=d.hex()));at+=6
 elif op in[0xff,0xa4,0x94]:controls.append(dict(pc=f'{at:06x}',bytes=read(at,at+2).hex()));at+=2
 elif op in[0xb0,0x84]:controls.append(dict(pc=f'{at:06x}',bytes=read(at,at+6).hex(),pointer=f'{int.from_bytes(read(at+2,at+6),"big"):06x}'));at+=6
 else:raise AssertionError((hex(at),hex(op)))
assert at==end
refs={str(n):[d for d in draws if d['frame']==n]for n in range(48,99)};assert all(refs.values())
groups=[]
for first,last,lo,hi,name in[(48,54,0x95694,0x956fe,'avstandsvalgt angrepsstart'),(55,60,0x956fe,0x95756,'fortsettelse med innebygd ridder060'),(61,70,0x95756,0x957c4,'fortsettelse trinn2'),(71,79,0x957c4,0x9582c,'fortsettelse trinn3'),(80,91,0x9582c,0x958a6,'fortsettelse trinn4'),(92,98,0x958a6,0x95908,'etter callback0acf04')]:
 rows=[d for d in draws if lo<=int(d['pc'],16)<hi and first<=d['frame']<=last];assert sorted(set(d['frame']for d in rows))==list(range(first,last+1));groups.append(dict(name=name,range=[first,last],table_range=[f'{lo:06x}',f'{hi:06x}'],table_sha256=sha(read(lo,hi)),source_draws=rows))
observed=json.loads((HERE/'verification/original-survey-fire-6000-v2/receipt.json').read_text())
report=dict(schema=1,status='source_group_usage_verified_not_runtime_observed',script_sha256=sha(Path(__file__).read_bytes()),source_zip_sha256=sha(zip_path.read_bytes()),source_mog_sha256=sha(mog),source_bank_sha256=sha(game.les('data/Demon2.CEL')),original_instruction_bytes={f'{pc:06x}':v for pc,v in expected.items()},bank_resolution={'00':'Demon2.CEL via original0829cc loading0829d6','08':'Demon3.CEL via0829fa','0c':'Demon4.CEL via08297e','10':'Demon1.CEL via0829ac'},groups=groups,table_controls=controls,selection_evidence=[dict(pc='0acb22..0acb6a',facts='Etter cooldown velger d1<=100 tabell09558a; 100<d1<=130 velger095694, som inneholder048..054. d1 settes til absolutt horisontal avstand fra086fa6 ved0aca8e..0aca94. Andre AI-baner kan levere d1; dette er ikke en global inputgaranti.'),dict(pc='0acef4',facts='Callback fra0956fa trekker10 fra originalridderens HIT.'),dict(pc='0acf6a..0acfbc',facts='Callback fra0958a8 leser ridderens HIT. VedHIT<=0 nulles seks palettord fra indeks2 og ridderens originale dødsliste090778 velges. Disse palettendringene tilhører CPU-koden, ikke grafikkverktøyet.')],observed_original_case={'receipt_sha256':sha((HERE/'verification/original-survey-fire-6000-v2/receipt.json').read_bytes()),'Demon2_frames':sorted(map(int,observed['drawn_banks']['Demon2.cel'])),'unobserved_frames':list(range(48,99))},runtime_scope='048..098 er kildebevist referert i angrepssekvensen, men ikke observert i de dokumenterte originale replays. Normal/speilet frontendfixture og faktisk originalpalett er separate visningsbevis. Ingen påstand om naturlig kampgjennomføring eller ubrukte ruter.',next_input_candidate='Kortere tilnærming med venstre og deretter slipp, slik at horisontal avstand ligger100..130 mens originalridderen lever. Dette er et kildebegrunnet forslag, ikke utført test eller garanti.')
out=HERE/'verification/source-usage-remainder-v1.json';assert not out.exists();out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(status=report['status'],groups=len(groups),frames=len(refs),sha256=sha(out.read_bytes()))))
