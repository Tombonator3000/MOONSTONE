#!/usr/bin/env python3
"""Avvis gamle bevis, feil kilde, maskefeil og bilder uten egen nytegning."""
import copy
import hashlib
import json
import tempfile
from pathlib import Path
from unittest.mock import patch
from PIL import Image
import hd_figurer_aktiver as gate

ROOT = gate.ROOT
path = ROOT / 'art/hd-completion-figures-2026-10-11/activation-set-001.json'
delivery = json.loads(path.read_text())
checks = []
files = gate.validate(delivery)
assert len(files) == 70
checks.append('69 ruter og levende maske har gyldige kilder og runtimebevis')


def rejected(name, edit, expected):
    candidate = copy.deepcopy(delivery)
    edit(candidate)
    try:
        gate.validate(candidate)
    except (AssertionError, KeyError) as error:
        assert expected in str(error), (name, str(error))
        checks.append(name)
    else:
        raise AssertionError('Feil leveranse ble godkjent: ' + name)


rejected('Ugodkjent visuell sammenligning avvises',
         lambda d: d.update(visual_status='candidate'), '')
rejected('Endret produksjonskode avvises',
         lambda d: d['production_code_sha256'].update({'web/src/scenes.js': '0' * 64}), 'Endret fil')
rejected('Bevis fra annen HTML avvises',
         lambda d: d['proofs'][0].update(html_sha256='0' * 64), 'Annen runtime-HTML')
rejected('Annen originalbank avvises',
         lambda d: d['entries'][0].update(source_bank_sha256='0' * 64), 'Annen originalbank')
rejected('Annet bilde enn runtimebildet avvises',
         lambda d: d['entries'][0].update(runtime_asset_sha256='0' * 64), 'Runtimebevis gjelder annet bilde')
rejected('Manglende separat raabilde avvises',
         lambda d: d['entries'][0].update(raw_sha256='0' * 64), 'Endret fil')
rejected('Ekstern bildegenerator avvises',
         lambda d: d['entries'][0].update(generation_tool='other'), '')
rejected('Feil alias avvises',
         lambda d: next(e for e in d['entries'] if e.get('master_key')).update(master_key='KN4.ob/999.png'), '')

masked = next(e for e in delivery['entries'] if e.get('mask'))
checked = gate.checked
with tempfile.TemporaryDirectory(prefix='moonstone-mask-') as tmp:
    mask = Image.open(ROOT / masked['mask']).convert('RGBA')
    mask.putpixel((0, 0), (255, 128, 255, 255))
    bad = Path(tmp) / 'mask.png'
    mask.save(bad)
    def changed_mask(p, digest):
        return bad if p == masked['mask'] else checked(p, digest)
    with patch.object(gate, 'checked', changed_mask):
        rejected('Maske som skifter feil originalindeks avvises', lambda d: None, 'Feil levende indeks')

manifest = json.loads((ROOT / 'web/hd/manifest.json').read_text())
active = {e['path']: e for e in manifest['files']}
for key, source in files.items():
    assert active[key]['sha256'] == hashlib.sha256(source.read_bytes()).hexdigest()
checks.append('Alle aktiverte filer er eksakt de beviste bildene')
report = dict(status='passed', checks=checks, count=len(checks), delivery_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
out = ROOT / 'art/hd-completion-figures-2026-10-11/verification/activation-gates.json'
out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(str(len(checks)) + ' aktiveringsporter bestaar.')
