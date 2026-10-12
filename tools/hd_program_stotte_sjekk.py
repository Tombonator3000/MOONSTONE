#!/usr/bin/env python3
"""Kildebundet intro-/sluttspor og originaldeterminisme, uten ny grafikk."""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import re
import shutil
import struct
import subprocess
import tempfile

from PIL import Image
from moonfiles import Spill, cel_les, piv_les, plan_til_indeks, amiga_rgb

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / 'art/hd-program-support-2026-10-11'
sha = lambda b: hashlib.sha256(b).hexdigest()


def rolling_sources(spill, out):
    banks = [spill.les(n) for n in ['bg1a.PIV', 'bg1c.PIV', 'bg1b.PIV']]
    decoded = [piv_les(b) for b in banks]
    indices = [plan_til_indeks(b[2], b[0]) for b in decoded]
    raw = spill.les('intro.stile')
    tiles = struct.unpack('>480H', raw)
    pixels = bytearray(320 * 1200)
    for n, code in enumerate(tiles):
        bank, tile = divmod(code, 80)
        assert bank < 3
        sx, sy = (tile % 10) * 32, (tile // 10) * 25
        dx, dy = (n % 10) * 32, (n // 10) * 25
        for y in range(25):
            pixels[(dy+y)*320+dx:(dy+y)*320+dx+32] = indices[bank][(sy+y)*320+sx:(sy+y)*320+sx+32]
    palette = [amiga_rgb(c) for c in decoded[0][1]]
    image = Image.new('RGB', (320, 1200))
    image.putdata([palette[c] for c in pixels])
    image.save(out / 'intro-scroll-original.png')
    (out / 'intro-scroll-indices.bin').write_bytes(pixels)
    credit = struct.unpack('>480H', spill.les('co.stile'))
    end_piv = piv_les(spill.les('bg7.piv'))
    end_px = plan_til_indeks(end_piv[2], end_piv[0])
    end = bytearray(320*1200)
    for n, code in enumerate(credit):
        assert code < 80
        sx, sy = (code % 10)*32, (code // 10)*25
        dx, dy = (n % 10)*32, (n // 10)*25
        for y in range(25):
            end[(dy+y)*320+dx:(dy+y)*320+dx+32] = end_px[(sy+y)*320+sx:(sy+y)*320+sx+32]
    end_im = Image.new('RGB', (320,1200))
    end_im.putdata([amiga_rgb(end_piv[1][c]) for c in end])
    end_im.save(out/'ending-scroll-original.png')
    (out/'ending-scroll-indices.bin').write_bytes(end)
    refs = ROOT/'art/hd-completion-runtime-2026-10-11/references'
    refs.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(out/'intro-scroll-original.png', refs/'intro-scroll.png')
    shutil.copyfile(out/'ending-scroll-original.png', refs/'ending-scroll.png')
    def fnv(data):
        h=2166136261
        for b in data: h=((h^b)*16777619)&0xffffffff
        return f'{h:08x}'
    return {'tile_size': [32, 25], 'atlas_grid': [10, 8], 'map_grid': [10, 48],
            'composite_size': [320, 1200], 'scroll_range': [0, 1000],
            'intro_bank_order': ['bg1a.PIV', 'bg1c.PIV', 'bg1b.PIV'],
            'intro_unique_tiles': len(set(tiles)),
            'intro_bank_tiles': {str(i): sorted({t % 80 for t in tiles if t // 80 == i}) for i in range(3)},
            'intro_indices_sha256': sha(pixels),
            'ending_unique_tiles': len(set(credit)),
            'intro_route': 'bg/'+fnv(pixels)+'.png',
            'ending_route': 'bg/'+fnv(end)+'.png',
            'ending_indices_sha256': sha(end),
            'ending_bank': 'bg7.piv, lastet i bank0 ved $085792 etter toemming ved $08577a. Stjerner/vannvirvel, ingen bokstavrulle.',
            'assembly_evidence': ['$08530e-$08539c: bankrekkefolge', '$09980a-$0998be: 10 kolonner og 25 linjer per rad',
                                  '$099866-$09988e: indeks/80 velger bank', '$099b50-$099b92: indeks%80 til 32x25',
                                  '$08577a-$0857ce: toem bank0, last bg7 i bank0 og bg8 i bank1', '$080d2e: sluttens stjerne-/vannrulling']}


def trace_rows(text, spill):
    frame = 0
    rows = []
    sizes = {}
    for line in text.splitlines():
        m = re.match(r'tegneliste bilde (\d+)', line)
        if m:
            frame = int(m[1])
        m = re.match(r'  (.*?) bilde (-?\d+) x (-?\d+) y (-?\d+) \((\d+)x(\d+), xoff (\d+)(, speilet)?\) buffer ([0-9a-f]+) fra ([0-9a-f]+)', line)
        if not m:
            continue
        name, index, x, y, w, h, xoff, flip, target, caller = m.groups()
        assert name, (frame, line)
        if name.lower() not in sizes:
            sizes[name.lower()] = cel_les(spill.les(name))[0]
        index, w, h = int(index), int(w), int(h)
        source = sizes[name.lower()][index]
        assert (w, h) == (source['bredde'], source['hoyde']), (frame, name, index)
        rows.append({'frame': frame, 'fil': name, 'bilde': index, 'x': int(x), 'y': int(y), 'w': w, 'h': h,
                     'xoff': int(xoff), 'speilet': bool(flip), 'target': int(target, 16), 'caller': int(caller, 16)})
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--baseline', type=Path, required=True, help='Frosset headless-binær fra før observatorendringen')
    ap.add_argument('--frames', type=int, default=6500)
    ap.add_argument('--sources-only', action='store_true')
    args = ap.parse_args()
    out = ART / 'verification'; out.mkdir(parents=True, exist_ok=True)
    spill = Spill(str(ROOT / 'Moonstonecd32-AMIGA.zip'))
    core = ROOT / 'port/moonstone-headless'
    report = {'scope': 'Naturlig intro. Sluttgren bruker eksplisitt testflagg ved oppstart, ikke en paastand om full gjennomspilling.',
              'zip_sha256': sha((ROOT / 'Moonstonecd32-AMIGA.zip').read_bytes()),
              'sources': {n: sha(spill.les(n)) for n in ['program', 'intro.stile', 'co.stile', 'bg1a.PIV', 'bg1b.PIV', 'bg1c.PIV', 'bg7.piv']},
              'source_files': {str(p.relative_to(ROOT)): sha(p.read_bytes()) for p in [ROOT/'port/src/game.c', ROOT/'port/src/hooks.c', ROOT/'port/src/lag.c', ROOT/'port/src/amiga.h']},
              'rolling': rolling_sources(spill, out), 'checks': [], 'runs': []}
    if not args.sources_only:
        report['binaries'] = {'baseline': sha(args.baseline.read_bytes()), 'current': sha(core.read_bytes())}
        for mode in ['intro', 'ending']:
            with tempfile.TemporaryDirectory(prefix='moon-program-') as temp:
                temp = Path(temp)
                matches = []
                trace = ''
                for variant, binary in [('baseline', args.baseline), ('current', core)]:
                    work = temp / variant; work.mkdir()
                    cmd = [str(binary), '--headless', '--frames', str(args.frames), '--log', '0',
                           '--shot-every', '500', '--shot-dir', str(work), '--save-state', f'{args.frames}:{work}/final.sav']
                    for f in range(500, args.frames+1, 500):
                        cmd += ['--dump', f'{f}:{work}/ram_{f:05d}.bin']
                    if mode == 'ending':
                        # CLI-en har 64 eksplisitte oppsettskrivinger. Verdien
                        # leses med base0; 0x80 er seiersbit7, desimal80 er feil.
                        for f in range(64):
                            cmd += ['--skriv', f'{f}:3e0:0x80:2']
                    if variant == 'current':
                        cmd += ['--tegneliste', f'1:{args.frames}', '--lag-dump', str(work/'layers')]
                        (work/'layers').mkdir()
                    result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=True)
                    if variant == 'current':
                        trace = result.stdout
                    matches.append({p.name: sha(p.read_bytes()) for p in work.iterdir() if p.is_file()})
                assert matches[0] == matches[1], {k for k in matches[0] if matches[0][k] != matches[1].get(k)}
                flag = int.from_bytes((temp/'current'/'ram_00500.bin').read_bytes()[0x80190:0x80192], 'big')
                assert bool(flag & 0x80) == (mode == 'ending'), (mode, flag)
                rows = trace_rows(trace, spill)
                assert rows, mode
                (out / f'{mode}-draws.json').write_text(json.dumps(rows, indent=2)+'\n')
                (out / f'{mode}-draws.txt').write_text(trace)
                visible = [r for r in rows if r['x'] < 320 and r['x']+r['w'] > 0 and r['y'] < 200 and r['y']+r['h'] > 0]
                summary = {'mode': mode, 'program_flag_080190': flag, 'frames': args.frames, 'original_identical_files': matches[1], 'draw_calls': len(rows),
                           'geometries_checked': len(rows),
                           'source_frames_scope': 'Tegnekall med geometri som skjærer320x200. Ikke full pikselbevist synlighet; target/caller skiller bakgrunn/dobbelbuffer.',
                           'source_frames': {n: sorted({r['bilde'] for r in visible if r['fil'] == n}) for n in sorted({r['fil'] for r in visible})}}
                report['runs'].append(summary); report['checks'] += [mode+'_chip_png_state_identical', mode+'_draw_source_geometry_valid',mode+'_program_branch_verified']
                for p in (temp/'current').glob('shot_*.png'):
                    shutil.copyfile(p, out/(mode+'-'+p.name))
                print(mode, 'original-identisk', len(matches[1]), 'filer; tegnekall', len(rows), flush=True)
    report['status'] = 'passed'
    (out / ('program-sources.json' if args.sources_only else 'program-support-test.json')).write_text(json.dumps(report, indent=2)+'\n')


if __name__ == '__main__':
    main()
