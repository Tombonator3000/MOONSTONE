"""Kjor kildefixturer sekvensielt i egne nettlesere med fire ruter per prosess."""
from pathlib import Path
import hashlib,json,subprocess,os,time
ART=Path(__file__).resolve().parent
ROOT=ART.parents[3]
NODE='/home/tombonator3000t/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node'
RUNTIME='/home/tombonator3000t/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules'
keys=json.loads((ART/'selection-r1-rest40.json').read_text())['keys']
assert len(keys)==40 and len(set(keys))==40
out=ART/'verification/r1-rest40-fixtures-v2'
assert not out.exists(),'Bruk ny samlet proevesti'
out.mkdir(parents=True)
# Vaar standardproeve fullfoeres foer neste GPU-proeve begynner.
standard=ART/'verification/standard-007-v3/test.json'
while not standard.exists():time.sleep(5)
assert json.loads(standard.read_text())['status']=='passed'
results=[]
for n in range(10):
 group=keys[n*4:(n+1)*4];directory=out/f'group{n+1:02}'
 env=os.environ.copy();env.update(NODE_PATH=RUNTIME,MOONSTONE_HOST=str(ART.parent/'dragon-production/runtime-host-retention-v7'),MOONSTONE_OUT=str(directory),RATMEN_FIXTURE_KEYS=','.join(group))
 p=subprocess.run([NODE,str(ART/'runtime-ratmen-r1-rest40-fixtures-v2.cjs')],cwd=ROOT,env=env,text=True,capture_output=True)
 (out/f'group{n+1:02}.stdout.txt').write_text(p.stdout);(out/f'group{n+1:02}.stderr.txt').write_text(p.stderr)
 r=json.loads((directory/'test.json').read_text());assert p.returncode==0 and r['status']=='passed',(group,p.stderr)
 assert {a['key']for a in r['assets']}==set(group)
 results.append(dict(path=str((directory/'test.json').relative_to(ROOT)),sha256=hashlib.sha256((directory/'test.json').read_bytes()).hexdigest(),checks=len(r['checks']),keys=group))
 print(json.dumps(dict(group=n+1,status=r['status'],checks=len(r['checks']),assets=len(r['assets']))),flush=True)
report=dict(schema=1,status='passed',routes=40,proofs=results,checks=sum(r['checks']for r in results),scope='Ti sekvensielle nettlesere, fire originalruter per proess. Normal/speilet, fem strenge negative porter per retning, begge levende masker i fem originalpaletter. Ikke faktisk kampobservasjon.')
(out/'summary.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(status='passed',checks=report['checks'],routes=40)),flush=True)
