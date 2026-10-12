"""Bind005s tidligere ukjente svarte piksler til originalens tegnede027-skygge."""
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
probe = ART / 'verification/dragon5-diagnose-five-v1/test.json'
report = json.loads(probe.read_text())
s = next(s for s in report['samples'] if s['frame'] == 1405)
game = mf.Spill(str(ROOT / 'Moonstonecd32-AMIGA.zip'))
raw = game.les('data/Dragon2.cel')
assert sha(raw) == '662891094e0a79b5831fb0c09471852cdb1af340c2bfa6293b6b9d0e5e401599'
f = mf.cel_les(raw)[0][27]
indices = utvid_indekser(mf.plan_til_indeks(f['data'], f['plan'], f['bredde'], f['hoyde']), f['maske'])
assert (f['bredde'], f['hoyde'], f['maske']) == (156, 15, 5)
assert sha(indices) == 'ef1051ae397cc0dc88d07750695af067c339c0d09c82a8fd7e31ace1fcd4e60c'
trace = (ART / 'identity/dragon-left-v1/trace.txt').read_bytes()
assert re.search(rb'tegneliste bilde 1399[^\n]*\n  Dragon2.cel bilde 27 x 2 y 173 \(156x15, xoff 0\) buffer 0a2cd6 fra 087bf0', trace)
sources = {k.lower(): v for k, v in report['decoded_sources'].items()}
cells = []
for y in range(150, 191):
    for x in range(128, 184):
        p = y * 320 + x
        actual = s['for_indices'][p]
        if actual == 255 or actual == s['background_indices'][p]:
            continue
        owner = None
        for d in s['all_visible']:
            g = sources[d['fil'].lower()][d['bilde']]
            if not (g['w'] == d['w'] and g['h'] == d['h'] and d['x'] <= x < d['x'] + d['w'] and d['y'] <= y < d['y'] + d['h']):
                continue
            i = x - d['x']
            c = g['px'][(y - d['y']) * d['w'] + (d['w'] - 1 - i if d['speilet'] else i)]
            if c:
                owner = c
        if owner == actual:
            continue
        assert owner is None and actual == 5
        assert 2 <= x < 158 and 173 <= y < 188
        assert indices[(y - 173) * 156 + x - 2] == actual
        cells.append([x, y])
assert len(cells) == 31
output = dict(schema=1, status='source_exact_shadow_owner_verified', frame=1405,
              source_probe_sha256=sha(probe.read_bytes()), original_trace_sha256=sha(trace),
              bank_sha256=sha(raw), frame_indices_sha256=sha(indices),
              source_call=dict(file='Dragon2.cel', frame=27, x=2, y=173, width=156, height=15,
                               target='0a2cd6', caller='087bf0'),
              cells=cells, cells_matched=31, analyzer_sha256=sha(Path(__file__).read_bytes()),
              scope='Ingen piksler tillates uten kilde. Alle31 er eksakt svarte original027-piksler fra faktisk CPU-kall1399.')
(ART / 'retention/original-shadow-005-evidence.json').write_text(json.dumps(output, indent=2) + '\n')
print(json.dumps({'status': output['status'], 'cells': len(cells)}))
