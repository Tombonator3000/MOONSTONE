"""Bind dragebankene til originalkode og de frosne originale CPU-palettene."""
import hashlib
import json
import struct
import sys
from pathlib import Path
ART = Path(__file__).resolve().parents[1]
ROOT = ART.parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
import moonfiles as mf
from hd_bestilling import maskefarger, utvid_indekser
sha = lambda b: hashlib.sha256(b).hexdigest()
c = json.loads((ART / 'identity/source-color-contract.json').read_text())
refpath = ROOT / c['original_palette_contract_path']
assert sha(refpath.read_bytes()) == c['original_palette_contract_sha256']
ref = json.loads(refpath.read_text())
for k in ['source_zip_sha256', 'source_mog_sha256', 'source_palette_code_sha256', 'live_palette_indices', 'fixed_red_indices', 'fixed_fire_indices', 'cases']:
    assert c[k] == ref[k], k
assert sha((ROOT / 'Moonstonecd32-AMIGA.zip').read_bytes()) == c['source_zip_sha256']
game = mf.Spill(str(ROOT / 'Moonstonecd32-AMIGA.zip'))
mog = game.les('mog');memory, _, _ = mf.legg_ut(mog)
assert sha(mog) == c['source_mog_sha256']
assert sha(memory[0x8c16:0x8d16]) == c['source_palette_code_sha256']
assert memory[0x8c16:0x8c32] == bytes.fromhex('30fc0c0030fc097630fc070030fc050030fc075430fc0c3030fc0a00')
assert memory[0x8c3e:0x8c4a] == bytes.fromhex('30fc0fc030fc0f8030bc0c50')
assert b'Dragon1.cel' in memory and b'Dragon2.cel' in memory and b'Dragon5.cel' in memory
cases = []
for case in c['cases']:
    folder = refpath.parent / case['case']
    trace = (folder / 'trace.txt').read_bytes()
    assert sha(trace) == case['trace_sha256']
    for sample in case['samples']:
        data = (refpath.parent / sample['path']).read_bytes()
        assert sha(data) == sample['sha256']
        words = list(struct.unpack_from('>32H', data, 0x961a0))
        assert words == sample['palette_words']
        assert [words[i] for i in (9, 11, 15, 29, 30, 31)] == [0xc00, 0x700, 0xa00, 0xfc0, 0xf80, 0xc50]
        assert struct.unpack_from('>L', data, 0x88dca)[0] == 0x14
    assert all(bank.encode() in trace for bank in ['Dragon1.cel', 'Dragon2.cel'])
    cases.append(case['case'])
left = ART / 'identity/dragon-left-v1'
left_observation = json.loads((left / 'source-observation.json').read_text())
assert sha((left / 'trace.txt').read_bytes()) == left_observation['trace_sha256']
assert b'Dragon5.cel' in (left / 'trace.txt').read_bytes()
left_chip = (left / 'chip1400.bin').read_bytes()
assert sha(left_chip) == left_observation['chip_sha256']
assert list(struct.unpack_from('>32H', left_chip, 0x961a0)) == c['cases'][0]['samples'][0]['palette_words']
queue = json.loads((ART / 'queue-subset.json').read_text())
rows = []
for q in queue['entries'] + queue['aliases']:
    raw = game.les(q['source_bank']['path'])
    assert sha(raw) == q['source_bank']['sha256']
    f = mf.cel_les(raw)[0][q['frame']]
    indices = utvid_indekser(mf.plan_til_indeks(f['data'], f['plan'], f['bredde'], f['hoyde']), f['maske'])
    assert sha(indices) == q['indices_sha256']
    assert bool(set(indices) & maskefarger(q['bank'], q['frame'])) == q['needs_mask']
    rows.append({'key': q['key'], 'indices_sha256': sha(indices), 'source_bank_sha256': sha(raw), 'needs_mask': q['needs_mask']})
assert len(rows) == 86 and sum(r['needs_mask'] for r in rows) == 5
report = dict(schema=1, status='passed', routes=rows, original_cpu_cases=cases,
    historical_native_binary_sha256=ref['headless_sha256'],
    original_palette_contract_sha256=c['original_palette_contract_sha256'],
    source_color_contract_sha256=sha((ART / 'identity/source-color-contract.json').read_bytes()),
    mask_regression_sha256=sha((ART / 'identity/mask-regression.json').read_bytes()),
    verifier_sha256=sha(Path(__file__).read_bytes()),
    scope='Originalkode, alle86 kilderuter og de to tidligere frosne CPU-kampenes paletter gjenkontrollert. Ingen paastand om faktisk CPU-visning av alle enkeltfragmenter.')
(ART / 'identity/source-validation.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({'status': report['status'], 'routes': len(rows), 'cpu_palettes': len(cases), 'masks': 5}))
