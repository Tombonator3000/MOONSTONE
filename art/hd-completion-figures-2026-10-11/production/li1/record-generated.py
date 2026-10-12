from pathlib import Path
import sys,json,hashlib,shutil
HERE=Path(__file__).resolve().parent
ORIGIN=Path('/home/tombonator3000t/.codex/generated_images/01a12bdd-775f-7861-a140-acf03481be58')
records=json.loads((HERE/'generation-records-v1.json').read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for pair in sys.argv[1:]:
 n,f=pair.split('=',1);q=f'{int(n):03d}';key=f'li1.cel/{q}.png'
 if any(x['key']==key for x in records):raise ValueError('Already recorded '+key)
 raw=f'raw/{q}-v1.png';prompt=f'prompts/{q}-v1.txt';ref=f'source/{q}-nearest4x.png'
 shutil.copyfile(ORIGIN/f,HERE/raw)
 records.append(dict(key=key,generation_tool='builtin_image_gen',generated_output=f,raw=raw,raw_sha256=sha(HERE/raw),prompt=prompt,prompt_sha256=sha(HERE/prompt),reference=ref,reference_sha256=sha(HERE/ref),generation_scope='One distinct builtin call using this original frame as the geometric reference; no exact model version claim.'))
(HERE/'generation-records-v1.json').write_text(json.dumps(sorted(records,key=lambda x:x['key']),indent=2)+'\n')
print(len(records),'separate generated masters saved')
