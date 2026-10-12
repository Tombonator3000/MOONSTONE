"""Activate only nine explicitly frozen and validated008 deliveries."""
from pathlib import Path
import sys,json,hashlib,subprocess
R=Path(__file__).resolve().parents[3];F=R/'art/hd-completion-figures-2026-10-11';sys.path.insert(0,str(R/'tools'))
from hd_figurer_aktiver import validate
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
paths=['production/activation-set-balok-025-b3-twentysix-v8.json','production/activation-set-balok-026-three-original-shadows-v8.json','figures/ratmen-production/activation-set-ratmen-r1-rest40-v2.json','production/guardian-demon2/remainder048-098-v2/activation-set-002.json','production/guardian-demon3/delivery008-v1/activation-set-001.json','production/beast/next042-055-v1/activation-set-eleven-v2.json','production/beast/shadow015-v1/activation-set-shadow015-v2.json','production/troll-remainder-v1/activation-set-remainder-008-v1.json','production/beast/next058-099-v1/activation-set-seven-008-v1.json']
baseline='19c515d';oldbytes=subprocess.check_output(['git','show',baseline+':web/hd/manifest.json'],cwd=R);old={f['path']:f for f in json.loads(oldbytes)['files']};active=json.loads((R/'web/hd/manifest.json').read_text());oldkeys={f['path']:f for f in active['files']};assert oldkeys==old,'Active package must start from exact007 checkpoint'
contracts=[];expected={};routes=[];photo=[]
for name in paths:
 p=F/name;contract=json.loads(p.read_text());files=validate(contract)
 for key,source in files.items():
  assert key not in expected and key not in old,'No overlap or prior asset overwrite';expected[key]=sha(source)
 for entry in contract['entries']:
  if not entry.get('existing_master'):
   routes.append(entry['key'])
   if entry['generation_tool']=='builtin_image_gen':photo.append(entry['raw_sha256'])
 contracts.append(dict(path=str(p.relative_to(R)),sha256=sha(p),routes=len([e for e in contract['entries']if not e.get('existing_master')]),png_files=len(files)))
assert len(routes)==len(set(routes))==202 and len(expected)==222
assert len(photo)==len(set(photo))
pre=dict(schema=1,status='explicit_preflight_passed',baseline_commit=baseline,baseline_manifest_sha256=hashlib.sha256(oldbytes).hexdigest(),previous_files=len(old),new_routes=len(routes),new_png_files=len(expected),photographic_masters=len(photo),preserved_original_routes=len(routes)-len(photo),deliveries=contracts,expected_new_files=expected,frontend_final_base='art/hd-completion-figures-2026-10-11/verification/integration-008-base/final-base-receipt-v1.json')
(F/'delivery-contracts-008-preactivation-v1.json').write_text(json.dumps(pre,ensure_ascii=False,indent=2)+'\n')
for row in contracts:subprocess.run([sys.executable,str(R/'tools/hd_figurer_aktiver.py'),row['path'],'--activate'],cwd=R,check=True)
manifest=json.loads((R/'web/hd/manifest.json').read_text());now={f['path']:f for f in manifest['files']}
assert all(now[k]==v for k,v in old.items());assert {k:v['sha256']for k,v in now.items()if k not in old}==expected
receipt=dict(**pre);receipt.update(status='locally_activated_final_runtime_pending',manifest_sha256=sha(R/'web/hd/manifest.json'),images=manifest['images'],files=len(now),backgrounds=sum(k.startswith('bg/')and k.endswith('.png')for k in now))
(F/'delivery-progress-008-activation-v1.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:receipt[k]for k in ['status','images','files','new_routes','new_png_files','photographic_masters','preserved_original_routes']}))
