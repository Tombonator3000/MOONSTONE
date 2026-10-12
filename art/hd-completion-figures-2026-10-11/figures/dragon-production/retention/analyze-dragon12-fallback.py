"""Bind tidlig hodefallback til en faktisk tegnet, for tidlig fjernet D2/005."""
import hashlib
import json
import re
import sys
from pathlib import Path
ART = Path(__file__).resolve().parents[1]
ROOT = ART.parents[3]
sys.path.insert(0, str(ROOT / 'tools'))
import moonfiles as mf
from hd_bestilling import utvid_indekser
sha = lambda b: hashlib.sha256(b).hexdigest()
probe = ART / 'verification/dragon12-fallback-diagnose-v1/test.json'
r = json.loads(probe.read_text())
assert r['status'] == 'passed' and r['diagnostic_only']
s = next(s for s in r['samples'] if s['frame'] == 1405)
game = mf.Spill(str(ROOT / 'Moonstonecd32-AMIGA.zip'))
raw = game.les('data/Dragon2.cel')
f = mf.cel_les(raw)[0][5]
indices = utvid_indekser(mf.plan_til_indeks(f['data'], f['plan'], f['bredde'], f['hoyde']), f['maske'])
assert (f['bredde'], f['hoyde'], f['maske']) == (36, 48, 15)
assert sha(indices) == 'c6d27218bd4195f57d8f6a91f4fac5d19655204387d06479d0b01c505571a69e'
assert not any(v['fil'].lower() == 'dragon2.cel' and v['bilde'] == 5 for v in s['all_visible'])
cells = s['head17']['first_mismatches']
assert s['head17']['counts']['mismatch'] == s['body5']['counts']['mismatch'] == len(cells) == 8
assert s['body5']['first_mismatches'] == cells
for c in cells:
    pos = c['y'] * 320 + c['x']
    assert c['owner'] is None
    assert c['actual'] == s['for_indices'][pos] == 10
    assert indices[(c['y'] - 26) * 36 + c['x'] - 69] == c['actual']
trace = (ART / 'identity/dragon-left-v1/trace.txt').read_bytes()
calls = []
for n in (1386, 1392, 1400, 1407):
    assert re.search(('tegneliste bilde %d[^\\n]*\\n(?:[^\\n]*\\n)*?  Dragon2.cel bilde 5 x 69 y 26 \\(36x48, xoff 0\\) buffer 0a2cd6 fra 087bf0' % n).encode(), trace)
    calls.append(n)
output = dict(schema=1, status='source_exact_owner_loss_verified', runtime_proof_sha256=sha(probe.read_bytes()),
    production_code_sha256=r['production_code_sha256'], html_sha256=r['html_sha256'],
    source_zip_sha256=sha((ROOT / 'Moonstonecd32-AMIGA.zip').read_bytes()), bank_sha256=sha(raw),
    frame_indices_sha256=sha(indices), original_trace_sha256=sha(trace),
    original_call=dict(file='Dragon2.cel', frame=5, x=69, y=26, width=36, height=48, plane_mask=15,
                       caller='087bf0', target='0a2cd6', observed_frames=calls),
    matched_cells=cells, matched_count=8,
    retention_timeline=[dict(frame=t['frame'], body5=[v for v in t['visible'] if v['fil'].lower()=='dragon2.cel' and v['bilde']==5],
                            head17=[v for v in t['visible'] if v['fil'].lower()=='dragon1.cel' and v['bilde']==17])
                        for t in r['trace'] if 1389 <= t['frame'] <= 1408],
    scope='D2/005 fjernes etter kildeekte kall, selv om8 av dens opake kildeceller fortsatt er synlige. D1/017 avvises strengt fordi eieren mangler. Ingen ukjent forgrunn er godkjent og ingen frontendkode endret.',
    proposed_gate='Bare denne eksakte D2/005-banken/ruten/geometrien/planmasken/kalleren/maalbufferen kan proeves med kildeindeksvalidering og kort pending-retensjon. Wrongcaller/target/source/unknownFG skal fortsatt avvises.',
    analyzer_sha256=sha(Path(__file__).read_bytes()))
(ART / 'retention/dragon12-fallback-source-evidence.json').write_text(json.dumps(output, indent=2) + '\n')
print(json.dumps(dict(status=output['status'], cells=len(cells), source_calls=calls)))
