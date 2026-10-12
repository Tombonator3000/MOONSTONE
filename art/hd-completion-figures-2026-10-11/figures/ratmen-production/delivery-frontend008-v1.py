"""Eksplisitt liten frontend-/bevisleveranse uten HTML, snapshot eller aktive HD-kopier."""
from pathlib import Path
import hashlib
import json

ART = Path(__file__).resolve().parent
ROOT = ART.parents[3]
BASE = ART / 'verification/frontend008-candidate-v1'
PRODUCTION = ROOT / 'art/hd-completion-figures-2026-10-11/production'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
rel = lambda p: str(p.relative_to(ROOT))
report_path = BASE / 'combined-regression-v1.json'
report = json.loads(report_path.read_text())
assert report['status'] == 'passed' and report['checks'] == 1418
for name, digest in report['production_code_sha256'].items():
    assert sha(ROOT / name) == digest
files = {ROOT / 'web/src/scenes.js', Path(__file__), report_path,
         ART / 'freeze-frontend008-v1.py', ART / 'run-frontend008-text-v1.py',
         ART / 'runtime-standard-public-v4.cjs', ART / 'runtime-standard-public-v5.cjs',
         ART / 'test-baked-background-v1.cjs', ART / 'test-original-combat-background-v1.cjs',
         ART / 'runtime-proof.cjs', ART / 'runtime-host.cjs',
         ART / 'verification/background-diagnostic-v1/source-delta-composition.json',
         ART / 'verification/frontend008-candidate-v1/ratmen/test.json',
         ART / '../dragon-production/retention/combat-background-source-contract.json',
         ART / '../dragon-production/retention/combat-background-fixture-input.json.gz',
         ART / 'source-contracts.json', ART / 'identity/source-color-contract.json',
         PRODUCTION / 'runtime-balok-025-frontend008-v1.cjs',
         PRODUCTION / 'runtime-balok-standard-frontend008-v1.cjs',
         PRODUCTION / 'runtime-tekst-eierskap-font-v1.cjs',
         PRODUCTION / 'runtime-tekst-eierskap-fixtures-v1.cjs',
         PRODUCTION / 'runtime-tekst-eierskap-host-v1.cjs'}
for row in report['proofs']:
    path = ROOT / row['path']
    assert sha(path) == row['sha256']
    files.add(path)
for row in report['representative_images']:
    path = ROOT / row['path']
    assert sha(path) == row['sha256']
    files.add(path)
for mode in ['hd', 'original']:
    for scene in ['title', 'world-map', 'inventory']:
        files.add(BASE / 'font' / f'{scene}-{mode}.png')
assert all(p.exists() for p in files)
files = {p.resolve() for p in files}
delivery = ART / 'delivery-frontend008-v1.json'
data = dict(schema=1, status='frozen_frontend_candidate', checks=1418,
            production_code_sha256=report['production_code_sha256'], html_sha256=report['html_sha256'],
            manifest_sha256=report['manifest_sha256'], wasm_core_sha256=report['wasm_core_sha256'],
            combined_proof=rel(report_path), combined_proof_sha256=sha(report_path),
            assets_unchanged=1747, pose_contracts=0,
            scope='Ny smal Ratmen-bro i scenes.js paa godkjent glyph-fix-render6b93. '
                  'Svart5 krever eksakt hel64000-komposisjon fra original Wa2 og SHA-validerte to bakingsruter med dokumentert caller/target/anker. '
                  'Originale5/15-deltaceller beholdes foran HD; ukjent forgrunn og andre avvik avvises. '
                  'Bevarte feilede helperbevis skyldes for streng forventning om begge bakinger foer den andre finnes. '
                  'Endelig v5 tester baade kildebevist37- og96-deltakomposisjon. '
                  'Ingen ny aktivering, ny kjerne eller spilltilstandsendring.',
            file_sha256={rel(p): sha(p) for p in sorted(files)})
text = json.dumps(data, indent=2, ensure_ascii=False) + '\n'
if delivery.exists():
    assert delivery.read_text() == text
else:
    delivery.write_text(text)
files.add(delivery)
listing = ART / 'delivery-frontend008-v1-files.txt'
text = '\n'.join(sorted(rel(p) for p in files)) + '\n'
if listing.exists():
    assert listing.read_text() == text
else:
    listing.write_text(text)
print(json.dumps(dict(status='ready', files=len(files), checks=1418, delivery_sha256=sha(delivery))))
