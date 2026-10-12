"""Kjoer fem offentlige scener mot sjette pakkes frosne kildekode, bevar alle forsoek."""
from pathlib import Path
import os,json,subprocess,hashlib
R=Path(__file__).resolve().parents[3];F=R/'art/hd-completion-figures-2026-10-11';base=F/'verification/integration-006-final-v2/package';out=F/'verification/public-006';assets=json.loads((out/'assets.json').read_text());assert assets['status']=='passed';env=os.environ.copy();env.update(NODE_PATH='/home/tombonator3000t/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules',MOONSTONE_HD_PUBLIC_URL='https://tombonator3000.github.io/MOONSTONE/',MOONSTONE_HD_PUBLIC_HTML_SHA256=assets['html_sha256'],MOONSTONE_HD_SOURCE_FREEZE=str(F/'verification/source-freezes-006'))
node='/home/tombonator3000t/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();selected=[]
for name,script,var in [('guardian','production/guardian/runtime-standard-public-v6.cjs','MOONSTONE_GUARDIAN_PACKAGE'),('guardian-demon2','production/guardian-demon2/runtime-standard-public-v1.cjs','MOONSTONE_GUARDIAN_PACKAGE'),('dragon','figures/dragon-production/runtime-standard-public-v1.cjs','MOONSTONE_DRAGON_PACKAGE'),('beast','production/beast/next006-011-v1/runtime-standard-public-v1.cjs','MOONSTONE_BEAST_PACKAGE'),('ending','production/runtime-integration-ending-frozen-v1.cjs','MOONSTONE_HD_PACKAGE')]:
 for attempt in range(1,4):
  dest=out/(name if attempt==1 else name+'-retry'+str(attempt-1));p=dest/'test.json'
  if p.exists():
   d=json.loads(p.read_text())
   if d['status']!='passed':continue
  else:
   env[var]=str(base);env['MOONSTONE_HD_TEST_OUTPUT']=str(dest);subprocess.run([node,str(F/script)],cwd=R,env=env,check=True);d=json.loads(p.read_text())
  assert d['status']=='passed' and not d['errors'];assert d['html_sha256']==assets['html_sha256'] and d['manifest_sha256']==assets['manifest_sha256'];assert d.get('test_sha256',d.get('runtime_script_sha256'))==sha(F/script)
  selected.append(dict(name=name,path=str(p.relative_to(R)),sha256=sha(p),checks=len(d['checks'])));break
 else:raise RuntimeError('Tre bevarte mislykkede forsoek: '+name)
(out/'runtime-selection.json').write_text(json.dumps(dict(status='passed',runtime_proofs=selected),indent=2)+'\n');print('Fem offentlige scenekontroller bestaar.')
