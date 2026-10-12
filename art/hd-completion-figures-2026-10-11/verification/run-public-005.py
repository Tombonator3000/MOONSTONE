"""Kjoer tre faktiske offentlige scener mot femte pakkes frosne kildekode."""
from pathlib import Path
import os,json,subprocess
R=Path(__file__).resolve().parents[3];F=R/'art/hd-completion-figures-2026-10-11';base=F/'verification/integration-005-final/package';out=F/'verification/public-005';assert json.loads((out/'assets.json').read_text())['status']=='passed';env=os.environ.copy();env.update(NODE_PATH='/home/tombonator3000t/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules',MOONSTONE_HD_PUBLIC_URL='https://tombonator3000.github.io/MOONSTONE/',MOONSTONE_HD_PUBLIC_HTML_SHA256='bfeebb4274c260e1bf484b098bf08caad016c5eda360de088758e77649dbb272',MOONSTONE_HD_SOURCE_FREEZE=str(F/'verification/source-freezes-005'))
node='/home/tombonator3000t/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node'
for name,script,var in [('guardian','production/guardian/runtime-standard-public-v5.cjs','MOONSTONE_GUARDIAN_PACKAGE'),('beast','production/beast/runtime-standard-actual-frozen-v1.cjs','MOONSTONE_BEAST_PACKAGE'),('ending','production/runtime-integration-ending-frozen-v1.cjs','MOONSTONE_HD_PACKAGE')]:
 dest=out/name;assert not(dest/'test.json').exists(),name;env[var]=str(base);env['MOONSTONE_HD_TEST_OUTPUT']=str(dest);subprocess.run([node,str(F/script)],cwd=R,env=env,check=True);d=json.loads((dest/'test.json').read_text());assert d['status']=='passed'and not d['errors']
print('Tre offentlige scenekontroller bestaar.')
