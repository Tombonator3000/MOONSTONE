#!/usr/bin/env python3
"""Lagre en original Balok-kampreferanse med eksplisitt testtilstand og inndata."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ART = Path(__file__).resolve().parent
ROOT = ART.parents[2]

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('name')
    parser.add_argument('--frame', type=int, required=True)
    parser.add_argument('--input', choices=['upper', 'lower', 'fire', 'none'], default='upper')
    parser.add_argument('--input-start', type=int, default=1350)
    args = parser.parse_args()
    out = ART / 'balok/probes' / args.name
    assert not out.exists(), 'Bevar eldre originalbevis'
    (out / 'shots').mkdir(parents=True)
    cmd = ['port/moonstone-headless', '--headless', '--frames', str(args.frame + 10), '--log', '2', '--press', '100:esc:4', '--press', '700:down:4', '--press', '760:down:4', '--press', '820:fire:4', '--press', '1200:left:120']
    if args.input in ['upper', 'lower']:
        cmd += ['--press', str(args.input_start) + ':' + ('up' if args.input == 'upper' else 'down') + ':600']
    if args.input != 'none':
        cmd += ['--press', str(args.input_start) + ':fire:600']
    cmd += ['--tegneliste', str(args.frame - 5) + ':16', '--skriv', '900:80172:0x84780:4', '--skriv', '900:8d9ac:0x8d5b4:4', '--skriv', '900:8015c:0xc:4', '--shot-every', str(args.frame), '--shot-dir', str(out / 'shots')]
    result = subprocess.run(cmd, cwd=ROOT, capture_output=True)
    (out / 'trace.txt').write_bytes(result.stdout)
    (out / 'stderr.txt').write_bytes(result.stderr)
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    proof = dict(command=cmd, exit_code=result.returncode, headless_sha256=sha(ROOT / cmd[0]), trace_sha256=sha(out / 'trace.txt'), scope='Originalkamp etter tre eksplisitte scene-init-skrivinger og faktisk tastinndata. Ingen palett- eller tegnelisteskriving; ikke naturlig kartreise.', screenshots=[dict(path=str(f.relative_to(ROOT)), sha256=sha(f)) for f in (out / 'shots').glob('*.png')])
    (out / 'source-observation.json').write_text(json.dumps(proof, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(dict(output=str(out.relative_to(ROOT)), exit_code=result.returncode, trace_sha256=proof['trace_sha256'], screenshots=len(proof['screenshots']))))

if __name__ == '__main__':
    main()
