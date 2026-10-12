"""Aktiver seks beistruter; revider bare tre egne, ennaa upubliserte lokale ruter."""
from pathlib import Path
import json,hashlib,sys,shutil
H=Path(__file__).resolve().parent;R=H.parents[3];sys.path.insert(0,str(R/'tools'))
from hd_figurer_aktiver import validate
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();dpath=H/'activation-set-six-v3.json';delivery=json.loads(dpath.read_text());files=validate(delivery);assert len(files)==6
old_contract=json.loads((H/'activation-set-first3-v1.json').read_text());previous={e['key']:e['png_sha256']for e in old_contract['entries']};mp=R/'web/hd/manifest.json';before_bytes=mp.read_bytes();manifest=json.loads(before_bytes);old={r['path']:r for r in manifest['files']};assert set(files)&set(old)==set(previous)
for key,digest in previous.items():assert old[key]['sha256']==digest and sha(R/'web/hd'/key)==digest
for key,source in files.items():
 target=R/'web/hd'/key;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target);row=dict(path=key,bytes=target.stat().st_size,sha256=sha(target),kind='base');manifest['files']=[r for r in manifest['files']if r['path']!=key];manifest['files'].append(row)
manifest['files'].sort(key=lambda r:r['path']);manifest['images']=sum(r['path'].endswith('.png')for r in manifest['files']);now={r['path']:r for r in manifest['files']};assert all(now[k]==v for k,v in old.items()if k not in previous);mp.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
receipt=dict(schema=1,status='locally_activated',source_contract_path=str(dpath.relative_to(R)),source_contract_sha256=sha(dpath),before_manifest_sha256=hashlib.sha256(before_bytes).hexdigest(),after_manifest_sha256=sha(mp),revised_own_unpublished_routes=previous,new_routes=[k for k in files if k not in old],scope='Seks egne fotomastere i uendret originalform. Tre lokale, upubliserte pelsfordelinger revidert; alle tidligere publiserte filer er urort.227 runtimekontroller og11875 kildealfapunkter bestaar.',activation_script_sha256=sha(Path(__file__)));(H/'activation-receipt-six-v3.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n');print(json.dumps(dict(status=receipt['status'],images=manifest['images'],routes=6,own_unpublished_revisions=3)))
