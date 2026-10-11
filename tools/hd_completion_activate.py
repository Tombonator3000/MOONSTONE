#!/usr/bin/env python3
"""Kontroller og koble inn siste ikonmaterialer, bakgrunnsrevisjoner og logo."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

from PIL import Image
import moonfiles as mf

ROOT = Path(__file__).resolve().parents[1]
ICONS = ROOT / 'art/hd-completion-icons-2026-10-11'
ART = ROOT / 'art/hd-completion-backgrounds-2026-10-11'
sha = lambda data: hashlib.sha256(data).hexdigest()
read = lambda path: json.loads(path.read_text())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--activate', action='store_true')
    args = parser.parse_args()
    game = mf.Spill(str(ROOT / 'Moonstonecd32-AMIGA.zip'))
    fragment = read(ICONS / 'fragment-icons.json')
    icon_pack = read(ICONS / 'packing-report.json')
    proof = read(ICONS / 'verification/bound-runtime/ui-fixtures-test.json')
    assert proof['status'] == 'passed' and not proof['errors']
    assert proof['fragment_icons_sha256'] == sha((ICONS / 'fragment-icons.json').read_bytes())
    assert proof['source_contracts_sha256'] == sha((ICONS / 'source-contracts.json').read_bytes())
    for rel, digest in proof['production_code_sha256'].items():
        assert sha((ROOT / rel).read_bytes()) == digest, 'Utdatert runtimekode: ' + rel
    expected_icons = {'ki.cel/034', 'ki.cel/035', 'ki.cel/036', 'mys.cel/000', 'mys.cel/001'} | {
        f'dice.cel/{n:03d}' for n in range(6)}
    assert {m['key'] for m in fragment['entries']} == expected_icons
    sources = {}
    for row in icon_pack['assets']:
        key = row['key']
        file = ICONS / 'packed' / (key + '.png')
        assert sha(file.read_bytes()) == row['packed_sha256'] == proof['packed_png_sha256'][key]
        assert Image.open(file).size == tuple(row['texture_size'])
        source = row['source']
        assert sha(game.les('data/' + source['file'])) == source['bank_sha256']
        sources[key + '.png'] = file
    assert len(sources) == 11
    expected_bg = {'bg/' + key for key in ['94c7f163', 'c2501c17', 'a45a2508', '46963198',
                                            'd0f67acb', '6b258d27', '0df34a83']}
    backgrounds = read(ART / 'packing-report.json')['assets']
    assert {a['key'] for a in backgrounds} == expected_bg
    for row in backgrounds:
        key = row['key']
        file = ART / 'packed' / (key + '.png')
        assert sha(file.read_bytes()) == row['packed_sha256']
        assert sha((ART / row['raw']).read_bytes()) == row['raw_sha256']
        assert Image.open(file).size == tuple(row['texture_size'])
        assert Image.open(file).convert('RGBA').getchannel('A').getextrema() == (255, 255)
        if row.get('source_file'):
            assert sha(game.les('data/' + row['source_file'])) == row['source_sha256']
        else:
            assert sha((ART / row['reference']).read_bytes()) == row['source_sha256']
        sources[key + '.png'] = file
    logo = ART / 'logo/packed/bold.f/073.png'
    logo_proof = read(ART / 'logo/verification/packing.json')
    logo_contract = read(ART / 'logo/contract.json')
    assert sha(logo.read_bytes()) == logo_proof['candidate_sha256']
    assert sha((ART / 'logo/contract.json').read_bytes()) == logo_proof['contract_sha256']
    assert sha(game.les('data/bold.f')) == logo_contract['bank_sha256']
    assert Image.open(logo).size == (1220, 216)
    sources['bold.f/073.png'] = logo
    active = read(ROOT / 'web/hd/icons.json')
    old_icons = {m['key']: m for m in active['entries'] if m['key'] not in expected_icons}
    active['entries'] = sorted(list(old_icons.values()) + fragment['entries'], key=lambda m: m['key'])
    active['banks'].update(fragment['banks'])
    assert {m['key']: m for m in active['entries'] if m['key'] not in expected_icons} == old_icons
    texts = read(ROOT / 'web/hd/text.json')
    glyph = next(g for g in texts['glyphs'] if g['path'] == 'bold.f/073.png')
    glyph.update(width=305, height=54, raw_rect_px=[0, 0, 1220, 216], sha256=sha(logo.read_bytes()))
    manifest = read(ROOT / 'web/hd/manifest.json')
    # Tidligere feilmotivmasker trengs ikke paa de kildekontrollerte revisjonene.
    for scene in manifest['scenes']:
        if scene['id'] in ('stonehenge-knight', 'stonehenge-overhead', 'intro-stars'):
            for field in ('protected', 'protected_indices', 'preserve_regions'):
                scene.pop(field, None)
        elif scene['id'] == 'mindscape-logo':
            scene['protected_indices'] = [0]
    result = dict(status='checked_not_activated', paths=sorted(sources),
                  figure_redraws=0, scope='11 ikonmaterialer, 5 bakgrunnsrevisjoner, 2 rullestriper, logo')
    if args.activate:
        for rel, source in sources.items():
            target = ROOT / 'web/hd' / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        (ROOT / 'web/hd/icons.json').write_text(json.dumps(active, ensure_ascii=False, separators=(',', ':')) + '\n')
        (ROOT / 'web/hd/text.json').write_text(json.dumps(texts, ensure_ascii=False, indent=2) + '\n')
        files = {f['path']: f for f in manifest['files']}
        for rel in list(sources) + ['icons.json', 'text.json']:
            data = (ROOT / 'web/hd' / rel).read_bytes()
            files[rel] = dict(path=rel, sha256=sha(data), bytes=len(data),
                              kind='background' if rel.startswith('bg/') else 'base')
        manifest['files'] = sorted(files.values(), key=lambda f: f['path'])
        manifest['images'] = sum(f['path'].endswith('.png') for f in manifest['files'])
        (ROOT / 'web/hd/manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
        result.update(status='activated_for_integration_verification',
                      manifest_sha256=sha((ROOT / 'web/hd/manifest.json').read_bytes()))
        (ART / 'activation.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
