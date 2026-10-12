"""Collect only the35 newly activated Troll, Beast and original-shadow routes for standard loading proof."""
from pathlib import Path
import sys,json,hashlib
R=Path(__file__).resolve().parents[3];F=R/'art/hd-completion-figures-2026-10-11';sys.path.insert(0,str(R/'tools'))
import moonfiles as mf
from hd_bestilling import utvid_indekser
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rows=[];inputs=[]
for name in ['production/troll-remainder-v1/runtime-geometries-remainder-v1.json','production/beast/next058-099-v1/runtime-geometries-v1.json','production/beast/next042-055-v1/runtime-geometries-v1.json','production/beast/shadow015-v1/runtime-geometries-v1.json']:
 p=F/name;v=json.loads(p.read_text());inputs.append(dict(path=str(p.relative_to(R)),sha256=sha(p)))
 for row in v:
  rows.append({**row,'bank':row.get('bank','be1.c'),'preserved_original_black_shadow':set(row['indices'])<={0,5},'needs_mask':bool(row.get('needs_mask',False))})
p=F/'production/activation-set-balok-026-three-original-shadows-v8.json';inputs.append(dict(path=str(p.relative_to(R)),sha256=sha(p)));palette=json.loads((F/'palettes/cases/balok.json').read_text())['colors'];palette=[x[:3]+[255]for x in palette];game=mf.Spill(R/'Moonstonecd32-AMIGA.zip')
for entry in json.loads(p.read_text())['entries']:
 bank=game.les('data/'+entry['bank']);src=mf.cel_les(bank)[0][entry['frame']];w,h=src['bredde'],src['hoyde'];indices=utvid_indekser(mf.plan_til_indeks(src['data'],src['plan'],w,h),src['maske']);assert set(indices)=={0,5}
 rows.append(dict(key=entry['key'],bank=entry['bank'],frame=entry['frame'],number=f"{entry['frame']:03}",width=w,height=h,indices=list(indices),palette=palette,source_bank_sha256=hashlib.sha256(bank).hexdigest(),indices_sha256=hashlib.sha256(indices).hexdigest(),packed_candidate_path=entry['png'],candidate_png_sha256=entry['png_sha256'],needs_mask=False,preserved_original_black_shadow=True))
assert len(rows)==len({r['key']for r in rows})==35
out=dict(schema=1,inputs=inputs,entries=rows)
p=F/'verification/standard-mixed35-geometries-008-v1.json';p.write_text(json.dumps(out,indent=2)+'\n')
print('35 explicit standard routes prepared')
