"""Explicit two-mask addition to existing source-identical photographs, after exact runtime proof."""
from pathlib import Path
import hashlib,json,sys,shutil
H=Path(__file__).resolve().parent;R=H.parents[3];sys.path.insert(0,str(R/'tools'))
from hd_figurer_aktiver import code_in_html
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:str(p.relative_to(R));cpath=H/'source-contracts-v1.json';source=json.loads(cpath.read_text());proof=H/'verification/runtime-v1/test.json';report=json.loads(proof.read_text());html=proof.parent/'loaded.html'
assert source['status']=='prepared_not_activated' and report['status']=='passed' and not report['errors']
assert report['source_contracts_sha256']==sha(cpath) and report['test_sha256']==sha(H/'runtime-v1.cjs')
assert sha(html)==report['html_sha256'];content=html.read_bytes()
for p,h in report['production_code_sha256'].items():assert sha(R/p)==h and code_in_html((R/p).read_bytes().replace(b'</script',b'<\\/script'),content)
assert sha(R/'Moonstonecd32-AMIGA.zip')==source['source_zip_sha256']==report['source_zip_sha256'];assert sha(R/'web/build/moonstone-core.js')==report['wasm_core_sha256']
assert len(report['fixtures'])==20 and report['runtime']['sample']['source']['maske'];assert report['runtime']['sample']['source']['bilde']==10
manifest_path=R/'web/hd/manifest.json';before=manifest_path.read_bytes();manifest=json.loads(before);old={r['path'].lower():r for r in manifest['files']};added=[]
for c in source['rows']:
 assert sha(R/c['png'])==c['png_sha256']==old[c['key'].lower()]['sha256']==report['assets'][c['key']]
 assert sha(R/c['mask'])==c['mask_sha256']==report['assets'][c['key'].replace('.png','.mask.png')]
 key=c['key'].replace('.png','.mask.png');assert key.lower()not in old,'Mask already active; do not duplicate';target=R/'web/hd'/key;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(R/c['mask'],target);row=dict(path=key,bytes=target.stat().st_size,sha256=sha(target),kind='base');manifest['files'].append(row);added.append(row)
manifest['files'].sort(key=lambda r:r['path']);manifest['images']=sum(r['path'].endswith('.png')for r in manifest['files']);assert all(next(r for r in manifest['files']if r['path'].lower()==k)==v for k,v in old.items());manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
receipt=dict(schema=1,status='locally_activated',scope=report['scope'],visual_status='reviewed_original_and_runtime',before_manifest_sha256=hashlib.sha256(before).hexdigest(),after_manifest_sha256=sha(manifest_path),new_masks=added,existing_photographs_unchanged={c['key']:c['png_sha256']for c in source['rows']},source_contracts_path=rel(cpath),source_contracts_sha256=sha(cpath),runtime_proof_path=rel(proof),runtime_proof_sha256=sha(proof),script_sha256=sha(Path(__file__)),production_code_sha256=report['production_code_sha256'],original_source_zip_sha256=report['source_zip_sha256']);(H/'activation-receipt-v1.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(dict(status=receipt['status'],new_masks=2,images=manifest['images'],existing_photographs_unchanged=True)))
