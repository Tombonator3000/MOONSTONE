"""Frys gjennomgaatte original/HD-kontaktark og faktiske dragebilder."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ART = Path(__file__).resolve().parent
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_text())
contracts = read(ART / 'source-contracts.json')['entries']
actual = read(ART / 'verification/dragon-final/test.json')
assert actual['status'] == 'passed' and not actual['errors']
assert len(actual['captures']) == 7
contact_names = ['000-011', '012-023', '024-035', '036-047', '048-059', '060-064']
report = dict(schema=1, status='reviewed_against_original_and_actual_runtime',
              created_at=datetime.now(timezone.utc).isoformat(),
              masters=65, visible_photo_material_masters=65,
              preserved_original_black_shadow_masters=0,
              contact_sheets=[dict(path=f'verification/comparison-{n}.png',
                                  sha256=sha(ART / f'verification/comparison-{n}.png'))
                              for n in contact_names],
              actual_dragon_proof_sha256=sha(ART / 'verification/dragon-final/test.json'),
              actual_captures=[dict(emulator_frame=c['frame'], route=c['body']['bilde'],
                                   original_png_sha256=c['original_sha256'],
                                   hd_png_sha256=c['hd_sha256'])
                               for c in actual['captures']],
              source_color_contract_sha256=sha(ART / 'identity/source-color-contract.json'),
              packed_png_sha256={c['key']: sha(ART / 'packed' / c['key']) for c in contracts},
              notes=[
                  'Hver av65 originalruter og hvert ferdig4x-par er visuelt gjennomgaatt. Egen builtin-generering per rute, ingen aliaser.',
                  'Rustningsfragmenter, blodretning, transparente hull og grunne/lange utsnitt er beholdt. Foto har staal, noeytralt stoff og vaatt moerkt roedt blod.',
                  '058v1 er avvist fordi den viste en ny hel ridder;058v2 og059..064 bruker kun egen original som formreferanse.',
                  '058..064 beholder den originale brennende silhuetten, fallretningen og lave sluttformen. Original dragen og dens ildstrale er kontekst, ikke nytegnet her.',
                  'Faktisk original CPU-dragekamp viser alle7ildruter med original kildegeometri, speiling og korrekt overlapp foran/bak originalild.',
                  '020 har uavklart anatomisk delidentitet; kildeformens staal- og draktpartier er beholdt uten gjettet handlingsnavn.',
                  'Ridder6..8 omfarges;9/11/15 er fast roedt og29..31 er ild iht originalkode og to original CPU-paletter.',
              ])
(ART / 'verification/visual-review.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(dict(status=report['status'], masters=65, actual_captures=7,
                     sha256=sha(ART / 'verification/visual-review.json'))))
