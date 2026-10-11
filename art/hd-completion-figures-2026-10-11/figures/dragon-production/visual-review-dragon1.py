"""Frys original/HD-kontroll for de16 separate DRAGON1-masterne."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ART = Path(__file__).resolve().parent
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_text())
contracts = [c for c in read(ART / 'source-contracts.json')['entries'] if c['bank'].lower() == 'dragon1.cel']
actual = read(ART / 'verification/dragon1-actual-final/test.json')
assert actual['status'] == 'passed' and not actual['errors']
assert len(actual['captures']) == 2
contact_names = ['dragon1-006-017', 'dragon1-018-021']
report = dict(schema=1, status='reviewed_against_original_and_actual_runtime',
              created_at=datetime.now(timezone.utc).isoformat(),
              masters=16, visible_photo_material_masters=16,
              preserved_original_black_shadow_masters=0,
              contact_sheets=[dict(path=f'verification/comparison-{n}.png',
                                  sha256=sha(ART / f'verification/comparison-{n}.png'))
                              for n in contact_names],
              actual_dragon_proof_sha256=sha(ART / 'verification/dragon1-actual-final/test.json'),
              actual_captures=[dict(emulator_frame=c['frame'], route=c['body']['bilde'],
                                   original_png_sha256=c['original_sha256'],
                                   hd_png_sha256=c['hd_sha256'])
                               for c in actual['captures']],
              source_color_contract_sha256=sha(ART / 'identity/source-color-contract.json'),
              packed_png_sha256={c['key']: sha(ART / 'packed' / c['key']) for c in contracts},
              notes=[
                  'Alle16 originalruter og ferdige4x-par er visuelt kontrollert. Egen builtin-generering per rute, ingen aliaser eller svarte skyggemastere.',
                  'Silhuetter, horn, kjever, membraner, hull, utsnitt og naturtro materialfarger er sammenlignet. Rot har gjennomgaatt begge kontaktark og godkjent alle16.',
                  '009v1 ble avvist fordi skyggehornet ble roedt.009v2 bevarer midthornet som skyggefullt bein og er gjennomgaatt separat.',
                  'Faktisk original CPU-kamp viser007 og008 sammen ved1252 med korrekt innbyrdes anslutning, normal retning og originalt tegneutsnitt.',
                  'Resten av dragens hode/kropp og bakgrunnen er fortsatt originaler i denne avgrensede scenekontrollen. Spilleren bruker eksisterende standard-HD.',
                  'Alle16ruter normal/speilet bestaar237 frontendkontroller; faktisk kamp bestaar39 med eksakt Original/HD-retur og uendret emulatortilstand.',
              ])
(ART / 'verification/visual-review-dragon1.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(dict(status=report['status'], masters=16, actual_captures=2,
                     sha256=sha(ART / 'verification/visual-review-dragon1.json'))))
