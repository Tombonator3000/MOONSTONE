#!/usr/bin/env python3
"""Aktiver gjennomgaatt pergament og fire bakgrunner, bevar eksisterende ruter."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path
import moonfiles as mf

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT/'art/hd-ui-backgrounds-2026-10-11'
sha = lambda b: hashlib.sha256(b).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--activate', action='store_true')
    args = ap.parse_args()
    report = json.loads((ART/'packing-report.json').read_text())
    fragment = json.loads((ART/'fragment-icons.json').read_text())
    assert sha((ART/'fragment-icons.json').read_bytes()) == report['fragment_icons_sha256']
    approved = {'bg/e868fda9', 'bg/94e65527', 'bg/d744b02e', 'bg/e2e904b2', 'mi.c/032'}
    rows = [a for a in report['assets'] if a['key'] in approved]
    assert len(rows) == 5
    for a in rows:
        assert sha((ART/'packed'/f"{a['key']}.png").read_bytes()) == a['packed_sha256']
    panel = next(m for m in fragment['entries'] if m['key'] == 'mi.c/032')
    assert next(a for a in rows if a['key'] == 'mi.c/032')['silhouette_iou'] > .97
    game = mf.Spill(str(ROOT/'Moonstonecd32-AMIGA.zip'))
    scenes = []
    for ident, name, key, rect in [
        ('intro-forest', 'bg1b.PIV', 'd744b02e', [0, 0, 320, 200]),
        ('intro-water', 'bg7.PIV', 'e2e904b2', [0, 153, 320, 200]),
    ]:
        bank = game.les('data/'+name)
        planes = mf.piv_alle(bank)[0][0][2]
        h = 2166136261
        for b in planes.ljust(40000, b'\0'):
            h = ((h ^ b) * 16777619) & 0xffffffff
        assert f'{h:08x}' == key
        scenes.append(dict(id=ident, file=name, frame=0, source_sha256=sha(bank),
                           hash=key, rect=rect, uv_rect=[0, 0, 320, 200],
                           minimum_match=.90, minimum_detail=.90, foreground_padding=0))
    if not args.activate:
        print(json.dumps(dict(status='checked_not_activated', assets=len(rows))))
        return
    active_path = ROOT/'web/hd/icons.json'
    active = json.loads(active_path.read_text())
    old = {m['key']: m for m in active['entries'] if m['key'] != panel['key']}
    active['entries'] = sorted(list(old.values())+[panel], key=lambda m: m['key'])
    active['banks'].update(fragment['banks'])
    assert {m['key']: m for m in active['entries'] if m['key'] != panel['key']} == old
    active_path.write_text(json.dumps(active, ensure_ascii=False, separators=(',', ':'))+'\n')
    manifest_path = ROOT/'web/hd/manifest.json'
    manifest = json.loads(manifest_path.read_text())
    files = {f['path']: f for f in manifest['files']}
    for a in rows:
        rel = f"{a['key']}.png"
        target = ROOT/'web/hd'/rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ART/'packed'/rel, target)
    for rel in ['icons.json']+[f"{a['key']}.png" for a in rows]:
        data = (ROOT/'web/hd'/rel).read_bytes()
        files[rel] = dict(path=rel, bytes=len(data), sha256=sha(data),
                          kind='background' if rel.startswith('bg/') else 'base')
    manifest['files'] = sorted(files.values(), key=lambda f: f['path'])
    manifest['images'] = sum(f['path'].endswith('.png') for f in manifest['files'])
    ids = {s['id'] for s in scenes}
    manifest['scenes'] = [s for s in manifest['scenes'] if s['id'] not in ids]+scenes
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n')
    activation = dict(status='activated_for_runtime_verification', assets=sorted(approved),
                      rejected_materials=['ki.cel/034', 'ki.cel/035', 'ki.cel/036'],
                      rejected_reason='Mister for mye av originalens silhuett; behold originalen.',
                      manifest_sha256=sha(manifest_path.read_bytes()))
    (ART/'activation.json').write_text(json.dumps(activation, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(activation))


if __name__ == '__main__':
    main()
