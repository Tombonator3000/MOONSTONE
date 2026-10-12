"""Frys original/HD-kontroll for de26 separate DRAGON2-masterne."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ART = Path(__file__).resolve().parent
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_text())
contracts = [c for c in read(ART / 'source-contracts.json')['entries'] if c['bank'].lower() == 'dragon2.cel']
actual = read(ART / 'verification/dragon2-actual-final/test.json')
assert actual['status'] == 'passed' and not actual['errors']
assert len(actual['captures']) == 12
contact_names = ['dragon2-1', 'dragon2-2', 'dragon2-3']
report = dict(schema=1, status='reviewed_against_original_and_actual_runtime',
              created_at=datetime.now(timezone.utc).isoformat(),
              masters=26, visible_photo_material_masters=25,
              preserved_original_black_shadow_masters=1,
              contact_sheets=[dict(path=f'verification/comparison-{n}.png',
                                  sha256=sha(ART / f'verification/comparison-{n}.png'))
                              for n in contact_names],
              actual_dragon_proof_sha256=sha(ART / 'verification/dragon2-actual-final/test.json'),
              actual_captures=[dict(emulator_frame=c['frame'], route=c['body']['bilde'],
                                   original_png_sha256=c['original_sha256'],
                                   hd_png_sha256=c['hd_sha256'])
                               for c in actual['captures']],
              source_color_contract_sha256=sha(ART / 'identity/source-color-contract.json'),
              packed_png_sha256={c['key']: sha(ART / 'packed' / c['key']) for c in contracts},
              notes=[
                  'Alle26 original/HD-par er visuelt kontrollert. Rot har gjennomgaatt alle tre kontaktark og godkjent silhuetter/materialer, innbakt ridder, ild og flat skygge.',
                  '25 separate builtin-genereringer. Rene svarte027 er eksakt original0/5-alfa medNN4x, uten fotoendring.',
                  'Faktisk CPU-kamp viser12 forskjellige bankruter. To representative original/HD-par002 og022 er visuelt gjennomgaatt for hel kropp og ildpust.',
                  'Kroppens segmenter, foetter, hode og bank1-horn/membraner kobles ved originalgeometrien. Ingen ekstra vinger, lemmer eller endret pose.',
                  'Tre6..8-masker bevarer ridderfargene, mens faste roedfarger og ild beholder materialfargen.019 anatomisk delidentitet er uavklart og ikke gjettet.',
                  'DRAGON5-effekter er foreloepig originaler. Bakgrunnen er bevisst beholdt som original i denne figurkontrollen.',
              ])
(ART / 'verification/visual-review-dragon2.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(dict(status=report['status'], masters=26, actual_captures=12,
                     sha256=sha(ART / 'verification/visual-review-dragon2.json'))))
