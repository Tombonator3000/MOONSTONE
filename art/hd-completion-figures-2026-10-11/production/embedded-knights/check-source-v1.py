"""Bind107 faktiske monsterkilderuter til originalens fem ridderpaletter."""
from pathlib import Path
import hashlib,json,sys
H=Path(__file__).resolve().parent;R=H.parents[3];sys.path.insert(0,str(R/'tools'))
import moonfiles as mf
from hd_bestilling import KAMP_RIDDER_RUTER,utvid_indekser,maskefarger
sha=lambda b:hashlib.sha256(b).hexdigest();game=mf.Spill(R/'Moonstonecd32-AMIGA.zip');mog=mf.legg_ut(game.les('mog'))[0]
ops={'088c54':'41f9000961a0','088c5a':'d1fc0000000c','088c74':'6100002a','088ca0':'0ca9000000000036','088caa':'30fc000a30fc000730bc0004','088cc2':'30fc0f8030fc0c5030bc0a30','088cda':'30fc0f2230fc0b2230fc0700','088cf2':'30fc08c630fc059330bc0251','088d08':'30fc020630fc010330bc0001'}
for address,expected in ops.items():
 start=int(address,16)-0x80000;assert mog[start:start+len(expected)//2]==bytes.fromhex(expected),(address,expected)
manifest=json.loads((R/'web/hd/manifest.json').read_text());active={r['path'].lower():r for r in manifest['files']};rows=[]
for bank,expected in KAMP_RIDDER_RUTER.items():
 data=game.les(bank);found=set()
 for n,c in enumerate(mf.cel_les(data)[0]):
  ind=utvid_indekser(mf.plan_til_indeks(c['data'],c['plan'],c['bredde'],c['hoyde']),c['maske']);live=set(ind)&{6,7,8}
  if not live:continue
  found.add(n);key=f'{bank}/{n:03}.png';mask_key=key.replace('.png','.mask.png');assert maskefarger(bank,n)=={6,7,8};is_active=key.lower()in active
  if is_active:assert mask_key.lower()in active,'Aktiv ridderbit mangler maske: '+key
  rows.append(dict(key=key,source_bank_sha256=sha(data),indices_sha256=sha(ind),live_indices=sorted(live),live_source_pixels=sum(i in live for i in ind),currently_active=is_active,active_mask_sha256=active[mask_key.lower()]['sha256']if is_active else None))
 assert found==expected,bank
assert len(rows)==107
out=dict(schema=1,status='source_color_verified',script_sha256=sha(Path(__file__).read_bytes()),source_zip_sha256=sha((R/'Moonstonecd32-AMIGA.zip').read_bytes()),unpacked_mog_sha256=sha(mog),source_opcode_bytes=ops,source_palette_slots=[6,7,8],source_knight_words={'blue':[10,7,4],'yellow':[0xf80,0xc50,0xa30],'red':[0xf22,0xb22,0x700],'green':[0x8c6,0x593,0x251],'violet':[0x206,0x103,1]},routes=rows,scope='Kildeinventar og original maskinkode. Dette dokumenterer fargeplassene, ikke at alle107 ruter er nytegnet eller synlige i en naturlig gjennomspilling. Alle allerede aktive ruter i dette settet har maske.')
(H/'source-color-inventory-v1.json').write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n');print(json.dumps(dict(status=out['status'],routes=107,currently_active=sum(r['currently_active']for r in rows))))
