#!/usr/bin/env python3
"""Bevar urort generatorbilde og prompt. Godkjenning skjer separat."""
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / 'art/hd-remaining-icons-2026-10-11'

data = json.load(sys.stdin)
key = data['key']
assert re.fullmatch(r'[A-Za-z0-9_.-]+/\d{3}', key), key
source = data['source']
assert (ART / source).is_file(), source
path = re.search(r' as (/[^\n]+\.png) by default', data['output_hint']).group(1)
raw = 'raw/' + key + '.png'
prompt = 'prompts/' + key + '.json'
for rel in [raw, prompt]:
    (ART / rel).parent.mkdir(parents=True, exist_ok=True)
assert not (ART / raw).exists(), 'Bevar gammel revisjon foer ny lagring'
shutil.copy2(path, ART / raw)
(ART / prompt).write_text(json.dumps(data['args'], ensure_ascii=False, indent=2) + '\n')
record = dict(id=key, key=key, name=data['name'], raw=raw, source=source,
              prompt=prompt, placement='source_bounds', review_status='pending_visual_review')
out = ART / ('asset-' + key.replace('/', '-').replace('.', '_') + '.json')
out.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
print(out.relative_to(ROOT))
