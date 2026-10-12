"""Kjør alle101 standardruter i ti-ruters grupper; gjenbruk bare fullførte SHA-/scopevaliderte delrapporter."""
from pathlib import Path
import hashlib,json,os,subprocess,sys
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
node=Path('/home/tombonator3000t/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node')
script=HERE/'runtime-d2-d3-standard-public-008-v2.cjs'
out=Path(os.environ['MOONSTONE_HD_TEST_OUTPUT']);assert not (out/'test.json').exists();out.mkdir(parents=True,exist_ok=True)
rows=[]
for bank,index in [('guardian-demon2','remainder048-098-v2/activation-set-002.json'),('guardian-demon3','delivery008-v1/activation-set-001.json')]:
 rows+=json.loads((HERE.parent/bank/index).read_text())['entries']
keys=[r['key']for r in rows];assert len(keys)==101 and len(set(keys))==101
report=dict(schema=1,status='running',scope='Standard-only,101 kildeeksakte ruter i begge retninger,1010 negative porter og fire masker i fem originalpaletter/begge retninger. Ingen privatimport eller faktisk kampobservasjon.',script_sha256=sha(Path(__file__)),runtime_sha256=sha(script),keys=keys,groups=[],checks=0,fixtures=0,negative=0,knight_palette_variants=0)
try:
 for group,at in enumerate(range(0,len(keys),10)):
  subset=keys[at:at+10];env=dict(os.environ,MOONSTONE_HD_TEST_KEYS=json.dumps(subset),MOONSTONE_HD_TEST_OUTPUT=str(out/f'group-{group:02}'))
  proof=Path(env['MOONSTONE_HD_TEST_OUTPUT'])/'test.json'
  reused=proof.exists()
  if not reused:subprocess.run([str(node),str(script)],env=env,check=True)
  data=json.loads(proof.read_text())
  assert data['status']=='passed'and not data['errors']and data['test_sha256']==sha(script)
  assert data['html_sha256']==os.environ['MOONSTONE_HD_EXPECTED_HTML_SHA256']
  assert 'fixtures_CPU_unchanged'in data['checks']and 'StandardHd_stays_active'in data['checks']
  assert data['selected_keys']==subset and len(data['fixtures'])==len(subset)*2 and len(data['negative'])==len(subset)*10
  assert set((x['key'],x['mirror'])for x in data['fixtures'])=={(k,m)for k in subset for m in[False,True]}
  assert data['standard_before']['aktiv']and data['standard_after']['aktiv']and data['standard_after']['klar']
  if report['groups']:
   first=report['groups'][0]
   for field in ['html_sha256','manifest_sha256','source_freeze_sha256','production_code_sha256','assets','activation_sha256','source_contracts']:
    assert data[field]==first[field]
  report['groups'].append(dict(path=str(proof.relative_to(ROOT)),sha256=sha(proof),keys=subset,reused_completed_report=reused,runtime_sha256=data['test_sha256'],**{field:data[field]for field in['html_sha256','manifest_sha256','source_freeze_sha256','production_code_sha256','assets','activation_sha256','source_contracts']}))
  for field in['checks','fixtures','negative','knight_palette_variants']:report[field]+=len(data[field])
  print(json.dumps(dict(group=group,status='passed',fixtures=report['fixtures'],negative=report['negative'])),flush=True)
 assert report['fixtures']==202 and report['negative']==1010 and report['knight_palette_variants']==8
 first=report['groups'][0]
 pkg=Path(os.environ['MOONSTONE_GUARDIAN_PACKAGE']);source=Path(os.environ['MOONSTONE_HD_SOURCE_FREEZE'])
 assert sha(pkg/'moonstone.html')==first['html_sha256']and sha(pkg/'hd/manifest.json')==first['manifest_sha256']
 assert sha(source/'source-map.json')==first['source_freeze_sha256']
 for file,h in first['production_code_sha256'].items():assert sha(source/file)==h
 for file,h in first['assets'].items():assert sha(pkg/'hd'/file)==h
 report.update(html_sha256=first['html_sha256'],manifest_sha256=first['manifest_sha256'],production_code_sha256=first['production_code_sha256'],source_freeze_sha256=first['source_freeze_sha256'],package=str(pkg),source_freeze=str(source),standard_assets=first['assets'])
 assert sha(script)==report['runtime_sha256']and sha(Path(__file__))==report['script_sha256']
 report['status']='passed'
except Exception as error:
 report.update(status='failed',failure=str(error));raise
finally:
 (out/'test.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps({k:report[k]for k in['status','checks','fixtures','negative','knight_palette_variants']}),flush=True)
