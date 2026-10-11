"""Bind KN5s levende/faste farger til originalkode og to faktiske CPU-kamper."""
import hashlib
import json
import re
import struct
import sys
from pathlib import Path

ART = Path(__file__).resolve().parent
ROOT = ART.parents[4]
sys.path.insert(0, str(ROOT / 'tools'))
import moonfiles as mf
from hd_bestilling import maskefarger, utvid_indekser

sha = lambda b: hashlib.sha256(b).hexdigest()
game = mf.Spill(str(ROOT / 'Moonstonecd32-AMIGA.zip'))
mog = game.les('mog')
memory, _, _ = mf.legg_ut(mog)
bank = game.les('data/KN5.ob')
frames, _ = mf.cel_les(bank)
assert len(frames) == 65
# Originalgrenens faste roedfarger9..15 og ild29..31.
assert memory[0x8c16:0x8c32] == bytes.fromhex('30fc0c0030fc097630fc070030fc050030fc075430fc0c3030fc0a00')
assert memory[0x8c3e:0x8c4a] == bytes.fromhex('30fc0fc030fc0f8030bc0c50')
assert memory[0x8c54:0x8c60] == bytes.fromhex('41f9000961a0d1fc0000000c')
assert memory[0x8c74:0x8c78] == bytes.fromhex('6100002a')
assert memory[0x8caa:0x8cb6] == bytes.fromhex('30fc000a30fc000730bc0004')
assert memory[0x8cda:0x8ce6] == bytes.fromhex('30fc0f2230fc0b2230fc0700')
assert memory[0x45c6:0x45ce] == bytes.fromhex('217c00090dcc0008')
cases = []
for name, live in [('dragon-idle-v1', [0x00a, 0x007, 0x004]), ('dragon-red-v1', [0xf22, 0xb22, 0x700])]:
    folder = ART / name
    observed = json.loads((folder / 'source-observation.json').read_text())
    assert observed['exit_code'] == 0
    trace = (folder / 'trace.txt').read_text()
    assert sha(trace.encode()) == observed['trace_sha256']
    calls = []
    frame_number = None
    for line in trace.splitlines():
        match = re.match(r'tegneliste bilde (\d+)', line)
        if match:
            frame_number = int(match[1])
        match = re.match(r'  Kn5.ob bilde (\d+) x (-?\d+) y (-?\d+) \((\d+)x(\d+), xoff (\d+)(, speilet)?\) buffer ([0-9a-f]+) fra ([0-9a-f]+)', line)
        if match:
            nr, x, y, w, h, xoff = map(int, match.groups()[:6])
            assert (w, h) == (frames[nr]['bredde'], frames[nr]['hoyde'])
            calls.append(dict(emulator_frame=frame_number, route=nr, x=x, y=y, width=w, height=h,
                              xoff=xoff, mirrored=bool(match[7]), buffer=match[8], caller=match[9]))
    assert set(c['route'] for c in calls) == set(range(58, 65))
    samples = []
    for dump in sorted(folder.glob('chip*.bin')):
        data = dump.read_bytes()
        palette = list(struct.unpack_from('>32H', data, 0x961a0))
        assert palette[6:9] == live
        assert [palette[i] for i in (9, 11, 15, 29, 30, 31)] == [0xc00, 0x700, 0xa00, 0xfc0, 0xf80, 0xc50]
        assert struct.unpack_from('>L', data, 0x88dca)[0] == 0x14
        samples.append(dict(path=str(dump.relative_to(ART)), sha256=sha(data), palette_words=palette))
    cases.append(dict(case=name, command=observed['command'], trace_sha256=observed['trace_sha256'],
                      test_scope='Original CPU med scenestartskrivinger, pluss original ridderfarge-ID i roed kontroll. Ingen palett- eller tegnelisteskriving.',
                      first_call_per_route=[next(c for c in calls if c['route'] == nr) for nr in range(58, 65)], samples=samples))
indices = []
for nr, f in enumerate(frames):
    packed = mf.plan_til_indeks(f['data'], f['plan'], f['bredde'], f['hoyde'])
    expanded = utvid_indekser(packed, f['maske'])
    indices.append(dict(frame=nr, width=f['bredde'], height=f['hoyde'], plane_mask=f['maske'],
                        bitplane_sha256=sha(f['data']), indices_sha256=sha(expanded), source_indices=sorted(set(expanded)),
                        needs_mask=bool(set(expanded) & maskefarger('KN5.ob', nr))))
assert [f['frame'] for f in indices if f['needs_mask']] == [0, 1, 4, 5, 6, 20, 22, 23]
result = dict(schema=1, status='source_and_two_original_cpu_colors_verified',
              source_zip_sha256=sha((ROOT / 'Moonstonecd32-AMIGA.zip').read_bytes()),
              source_mog_sha256=sha(mog), source_bank_sha256=sha(bank),
              headless_sha256=sha((ROOT / 'port/moonstone-headless').read_bytes()),
              source_palette_code_sha256=sha(memory[0x8c16:0x8d16]),
              source_dragon_death_table_sha256=sha(memory[0x10dcc:0x10e4a]),
              live_palette_indices=[6, 7, 8], fixed_red_indices=[9, 11, 15], fixed_fire_indices=[29, 30, 31],
              identity='058..064: brennende ridder som faller i original dragekamp; 000..057: separate blod-/saardeler, ingen ubekreftet handling per rute.',
              preview_limit='Den eldre combat-preview bruker feil cyan/rosa for058..064 og er bare formreferanse.',
              cases=cases, frames=indices,
              mask_function_sha256=sha((ROOT / 'tools/hd_bestilling.py').read_bytes()))
target = ART / 'source-color-contract.json'
if target.exists():
    assert json.loads(target.read_text()) == result, 'Frosset kildekontrakt avviker'
else:
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(dict(frames=65, original_cpu_cases=2, observed_routes=list(range(58,65)), masks=8, contract_sha256=sha(target.read_bytes()))))
