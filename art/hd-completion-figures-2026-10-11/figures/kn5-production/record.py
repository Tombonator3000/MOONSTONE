"""Bevar ett innebygd generatorkall, eksakt prompt og ny rawfil."""
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

ART = Path(__file__).resolve().parent
payload = json.loads(sys.argv[1])
path = ART/'generation-records.json'
records = json.loads(path.read_text())
for item in payload:
    key = item['key'];bank,framepng=key.split('/');frame=framepng[:-4]
    raw = Path(re.search(r'as (\/[^\s]+\.png) by default', item['hint'])[1])
    destination = ART/'raw'/bank/f'{frame}.png'
    destination.parent.mkdir(exist_ok=True)
    if destination.exists():
        assert destination.read_bytes() == raw.read_bytes(), 'En annen kandidat finnes: '+str(destination)
    else:
        shutil.copyfile(raw, destination)
    record = dict(key=key, prompt=item['prompt'],
                  tool='builtin_image_gen', output_hint=item['hint'],
                  args=dict(transparent_background=True,
                            referenced_image_paths=item.get('references', [item.get('reference', str(ART/'references'/bank/f'{frame}.png'))])),
                  raw_sha256=hashlib.sha256(destination.read_bytes()).hexdigest())
    old = next((r for r in records['assets'] if r['key'] == record['key']), None)
    if old:
        assert old == record, 'Registrert kall er annerledes: '+record['key']
    else:
        records['assets'].append(record)
    (ART/'prompts').mkdir(exist_ok=True)
    (ART/'prompts'/f'{bank}-{frame}.txt').write_text(item['prompt']+'\n')
path.write_text(json.dumps(records, indent=2)+'\n')
print(json.dumps({'saved': len(payload), 'total': len(records['assets'])}))
