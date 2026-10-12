"""Kontroller offentlige filer mot den uforanderlige aattende pakken."""
from pathlib import Path
import concurrent.futures,hashlib,json,subprocess,urllib.request
from datetime import datetime,timezone
R=Path(__file__).resolve().parents[3];F=R/'art/hd-completion-figures-2026-10-11';P=F/'verification/integration-008-final-v1/package';O=F/'verification/public-008';O.mkdir(exist_ok=True);sha=lambda b:hashlib.sha256(b).hexdigest();base='https://tombonator3000.github.io/MOONSTONE/'
get=lambda route:urllib.request.urlopen(urllib.request.Request(base+route,headers={'Cache-Control':'no-cache'}),timeout=60).read()
index=json.loads((F/'delivery-contracts-008.json').read_text());manifest=(P/'hd/manifest.json').read_bytes();m=json.loads(manifest);old=json.loads(subprocess.check_output(['git','show',index['public_baseline_commit']+':web/hd/manifest.json'],cwd=R));before={x['path']:x for x in old['files']};rows=[x for x in m['files']if before.get(x['path'])!=x];assert len(rows)==index['public_new_png_files']
html=get('');assert sha(html)==sha((P/'moonstone.html').read_bytes());public_manifest=get('hd/manifest.json');assert public_manifest==manifest

def check(row):
 b=get('hd/'+row['path']);assert len(b)==row['bytes']and sha(b)==row['sha256'],row['path'];return row
with concurrent.futures.ThreadPoolExecutor(max_workers=8)as pool:done=list(pool.map(check,rows))
record=dict(status='passed',url=base,created_at=datetime.now(timezone.utc).isoformat(),html_sha256=sha(html),manifest_sha256=sha(public_manifest),images=m['images'],files=len(m['files']),new_png_files=len(done),assets=done,source_package=str(P.relative_to(R)),test_sha256=sha(Path(__file__).read_bytes()),limits='Filpublisering bekreftet; faktiske offentlige spillscener verifiseres separat.')
(O/'assets.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({k:v for k,v in record.items()if k not in ['assets']}))
