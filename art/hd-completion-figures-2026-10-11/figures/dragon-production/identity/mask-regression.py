"""Alle86 ikke-tomme drageruter: bare fem har levende ridderfarge."""
import contextlib
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
from PIL import Image

ART = Path(__file__).resolve().parents[1]
ROOT = ART.parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
import gfx
import moonfiles as mf
import hd_bestilling as bestilling

sha = lambda b: hashlib.sha256(b).hexdigest()
game = mf.Spill(str(ROOT / 'Moonstonecd32-AMIGA.zip'))
palette = gfx.standard_palett(game)
expected = {'dragon2.cel': {17, 18, 19}, 'dragon5.cel': {32, 35}, 'dragon1.cel': set()}
report = {'schema': 1, 'status': 'running', 'routes': [], 'empty': [], 'checks': 0,
          'mask_function_source_sha256': sha((ROOT / 'tools/hd_bestilling.py').read_bytes()),
          'source_zip_sha256': sha((ROOT / 'Moonstonecd32-AMIGA.zip').read_bytes())}
with tempfile.TemporaryDirectory(prefix='moonstone-dragon-mask-') as temp:
    temp = Path(temp)
    for bank in ('DRAGON1.CEL', 'DRAGON2.CEL', 'DRAGON5.CEL'):
        raw = game.les('data/' + bank)
        frames = mf.cel_les(raw)[0]
        for nr, frame in enumerate(frames):
            live = {6, 7, 8} if nr in expected[bank.lower()] else set()
            assert bestilling.maskefarger(bank, nr) == live
            assert bestilling.maskefarger(bank.swapcase(), nr) == live
            report['checks'] += 2
            if frame['plan'] == 0:
                report['empty'].append(f'{bank}/{nr:03d}.png')
                continue
            packed = mf.plan_til_indeks(frame['data'], frame['plan'], frame['bredde'], frame['hoyde'])
            indices = bestilling.utvid_indekser(packed, frame['maske'])
            assert bool(set(indices) & {6, 7, 8}) == bool(live)
            source = temp / bank / f'{nr:03d}.png'
            source.parent.mkdir(exist_ok=True)
            gfx.lagre_png(str(source), packed, frame['bredde'], frame['hoyde'], palette)
            maskpath = source.with_name(f'{nr:03d}.mask.png')
            with contextlib.redirect_stdout(io.StringIO()):
                bestilling.lag_maske(str(source), str(maskpath), spill_sti=str(ROOT / 'Moonstonecd32-AMIGA.zip'))
            actual = Image.open(maskpath).convert('RGBA')
            want = Image.new('RGBA', (frame['bredde'], frame['hoyde']))
            want.putdata([(i + 1, 128, 255, 255) if i in live else (0, 0, 0, 255) for i in indices])
            want = want.resize(actual.size, Image.Resampling.NEAREST)
            assert actual.tobytes() == want.tobytes(), (bank, nr)
            assert not any(r for r, g, b, a in actual.get_flattened_data() if r not in (7, 8, 9))
            report['checks'] += 4
            report['routes'].append({'key': f'{bank}/{nr:03d}.png', 'source_bank_sha256': sha(raw),
                'source_indices_sha256': sha(indices), 'live_indices': sorted(live),
                'live_source_pixels': sum(i in live for i in indices), 'full_4x_mask_rgba_sha256': sha(actual.tobytes())})
    # Negativ port: samme fargeindekser i en annen bank maa ikke faa dragemaske.
    for bank in ('DRAGON3.CEL', 'DRAGON4.CEL', 'DRAGON6.CEL'):
        for nr in range(50):
            assert bestilling.maskefarger(bank, nr) == set()
            report['checks'] += 1
assert len(report['routes']) == 86 and len(report['empty']) == 8
assert [r['key'] for r in report['routes'] if r['live_indices']] == [
    'DRAGON2.CEL/017.png', 'DRAGON2.CEL/018.png', 'DRAGON2.CEL/019.png',
    'DRAGON5.CEL/032.png', 'DRAGON5.CEL/035.png']
report['checks'] += 2
report['status'] = 'passed'
report['runtime_script_sha256'] = sha(Path(__file__).read_bytes())
(ART / 'identity/mask-regression.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({'status': report['status'], 'routes': len(report['routes']), 'live_routes': 5, 'checks': report['checks']}))
