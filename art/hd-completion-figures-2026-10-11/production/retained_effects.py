#!/usr/bin/env python3
"""Eksporter kildeidentiske TROLL-effekter og skill observerte fra uavklarte ruter."""
import hashlib
import json
import re
from pathlib import Path
from PIL import Image

ART = Path(__file__).resolve().parent
FIG = ART.parent
ROOT = ART.parents[2]
TARGET = ART / 'retained-effects-v1'
EFFECTS = [12, 36, 41, 42, 43, 44, 45, 46, 47]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def freeze(path, value):
    data = (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()
    if path.exists():
        assert path.read_bytes() == data, path
    else:
        path.write_bytes(data)


def main():
    queue_path = FIG / 'queue.json'
    queue = json.loads(queue_path.read_text())
    palette_path = FIG / 'palettes/cases/troll.json'
    palette = json.loads(palette_path.read_text())
    observed = {}
    pattern = re.compile(r'^  Troll1\.cel bilde (\d+) x (-?\d+) y (-?\d+) \((\d+)x(\d+), xoff (\d+)(, speilet)?\) buffer ([0-9a-f]+) fra ([0-9a-f]+)$')
    for trace in sorted((ART / 'verification').glob('original-troll*/trace.txt')):
        frame = None
        for line in trace.read_text().splitlines():
            if line.startswith('tegneliste bilde '):
                frame = int(line.split()[2])
            match = pattern.match(line)
            if not match or int(match[1]) not in EFFECTS:
                continue
            number = int(match[1])
            x, y, w, h = map(int, match.group(2, 3, 4, 5))
            if number in observed or not (x < 320 and x + w > 0 and y < 200 and y + h > 0):
                continue
            observation = trace.parent / 'source-observation.json'
            assert observation.exists()
            observed[number] = dict(trace=str(trace.relative_to(ROOT)), trace_sha256=sha(trace), observation=str(observation.relative_to(ROOT)), observation_sha256=sha(observation), frame=frame, draw=dict(x=x, y=y, w=w, h=h, mirrored=bool(match[7]), target=match[8], caller=match[9]), visibility_scope='Tegnekallets rektangel skjaerer skjermen. Dette alene beviser ikke synlige piksler.')
    TARGET.mkdir(exist_ok=True)
    entries, runtime_entries = [], []
    for number in EFFECTS:
        key = f'TROLL1.CEL/{number:03}.png'
        route = next(e for e in queue['entries'] if e['key'] == key)
        ref = next(e for e in palette['references'] if e['key'] == key)
        assert route['indices_sha256'] == ref['source_indices_sha256']
        source = FIG / 'palettes' / ref['original']
        packed = Image.open(FIG / route['packed_original']['path'])
        bits = [1 << n for n in range(5) if route['plane_mask'] & (1 << n)]
        indices = [sum(bit for n, bit in enumerate(bits) if value & (1 << n)) for value in packed.getdata()]
        original = Image.open(source).convert('RGBA')
        expected = [tuple(palette['colors'][value]) + (255 if value else 0,) for value in indices]
        assert list(original.getdata()) == expected
        output = TARGET / f'{number:03}.png'
        rgba = original.resize((route['target_width'], route['target_height']), Image.Resampling.NEAREST)
        if output.exists():
            assert Image.open(output).convert('RGBA').tobytes() == rgba.tobytes()
        else:
            rgba.save(output, optimize=True)
        entry = dict(key=key, method='retained_original_effect', counts_as_individual_redraw=False, source_bank=route['source_bank'], source_indices_sha256=route['indices_sha256'], packed_original=route['packed_original'], source_png=str(source.relative_to(ROOT)), source_png_sha256=sha(source), source_indices=sorted(set(indices)), target_size=list(rgba.size), png=str(output.relative_to(ROOT)), png_sha256=sha(output), exact_nearest4x_rgba=True, source_runtime_observation=observed.get(number), status='retained_original_effect_pending_runtime_proof' if number in observed else 'source_usage_unresolved_not_completed', identity='Konstant svart skyggefelt.' if number == 12 else 'Originalt rutemoenster for klubbas bevegelsesspor. Kildeindekser, hull og farger beholdes eksakt.')
        entries.append(entry)
        if number in observed:
            runtime_entries.append(dict(key=key, candidate=entry['png'], candidate_sha256=entry['png_sha256']))
    freeze(TARGET / 'source-contract.json', dict(schema=1, scope='Ni originale skygge-/bevegelsesfelt. Eksport og pakkeforberedelse, ingen fotonytegning eller aktivering. Uobserverte ruter holdes uavklart.', queue_sha256=sha(queue_path), source_zip_sha256=palette['source_zip_sha256'], palette_contract_sha256=sha(palette_path), entries=entries))
    freeze(TARGET / 'candidates.json', dict(schema=1, scope='Bare aatte ruter med observerte originale tegnekall. Kildeidentiske originale effekter, ingen nye genererte bilder.', entries=runtime_entries))
    print(json.dumps(dict(source_effects=len(entries), observed_draw_rectangles=len(runtime_entries), source_usage_unresolved=[e['key'] for e in entries if not e['source_runtime_observation']], output=str(TARGET.relative_to(ROOT)))))


if __name__ == '__main__':
    main()
