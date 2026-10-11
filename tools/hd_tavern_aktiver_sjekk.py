#!/usr/bin/env python3
"""Proev negative TAV/DICE-porter og samlet installasjon i isolert testmappe."""
import argparse
import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from PIL import Image
import hd_tavern_aktiver as tav

ROOT = tav.ROOT
ART = ROOT / 'art/hd-embedded-tavern-2026-10-11'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--delivery', type=Path, default=ART / 'activation-set-001.json')
    parser.add_argument('--dice-delivery', type=Path,
        default=ROOT / 'art/hd-completion-figures-2026-10-11/production/dice/activation-set-dice-001.json')
    args = parser.parse_args()
    delivery = json.loads(args.delivery.read_text())
    dice = json.loads(args.dice_delivery.read_text())
    output = ART / 'verification/activation-gate'
    output.mkdir(parents=True, exist_ok=True)
    checks = []
    plan = tav.validate(delivery, dice)
    original_manifest = (ROOT / 'web/hd/manifest.json').read_bytes()
    original_bg = (ROOT / 'web/hd/bg/44898895.png').read_bytes()
    new_keys = set(plan['files']) - {'bg/44898895.png'}

    def no_active_change():
        assert (ROOT / 'web/hd/manifest.json').read_bytes() == original_manifest
        assert (ROOT / 'web/hd/bg/44898895.png').read_bytes() == original_bg
        assert not any((ROOT / 'web/hd' / key).exists() for key in new_keys)

    def rejected(name, mutate, expected):
        d, b = copy.deepcopy(delivery), copy.deepcopy(dice)
        mutate(d, b)
        try:
            tav.validate(d, b)
        except (ValueError, AssertionError) as error:
            assert expected in str(error), (name, str(error))
            checks.append(dict(name=name, status='rejected', reason=str(error)))
        else:
            raise AssertionError('Feil kandidat ble godtatt: ' + name)
        no_active_change()

    rejected('missing_visual_review', lambda d, b: d.update(status='candidate_requires_visual_review'), 'visuell')
    rejected('stale_frontend', lambda d, b: d['production_code_sha256'].update({'web/src/hd.js': '0' * 64}), 'kodebinding')
    rejected('stale_current_frontend', lambda d, b: (
        d['production_code_sha256'].update({'web/src/hd.js': '0' * 64}),
        b['production_code_sha256'].update({'web/src/hd.js': '0' * 64})), 'Endret fil')
    rejected('stale_wasm', lambda d, b: d.update(wasm_core_sha256='0' * 64), 'kodebinding')
    rejected('different_original_zip', lambda d, b: d.update(source_zip_sha256='0' * 64), 'originalarkiv')
    rejected('source_mask_hash', lambda d, b: d['source_mask'].update(sha256='0' * 64), 'Endret fil')

    contract = json.loads((ROOT / delivery['source_contract']['path']).read_text())
    contract['selected_pixels'] -= 1
    bad_contract = output / 'bad-contract.json'
    bad_contract.write_text(json.dumps(contract))
    rejected('source_mask_count', lambda d, b: d.update(source_contract={
        'path': str(bad_contract.relative_to(ROOT)), 'sha256': tav.sha(bad_contract.read_bytes())}), 'figurvalg')
    selected = (ROOT / delivery['source_mask']['path']).read_bytes()
    indices = (ROOT / delivery['source_indices']['path']).read_bytes()
    n = next(i for i, c in enumerate(indices) if selected[i] and 6 <= c <= 10)
    x, y = n % 135 * 4 + 2, n // 135 * 4 + 2
    for channel, expected in ((0, 'NN-indeks'), (2, 'NN-indeks'), (1, 'luminans')):
        im = Image.open(ROOT / delivery['embedded_entries'][0]['mask']['path']).copy()
        rgba = list(im.getpixel((x, y)))
        rgba[channel] = (rgba[channel] + 1) % 256
        im.putpixel((x, y), tuple(rgba))
        path = output / f'bad-mask-channel-{channel}.png'
        im.save(path)
        def change_mask(d, b, path=path):
            d['embedded_entries'][0]['mask'] = dict(path=str(path.relative_to(ROOT)), sha256=tav.sha(path.read_bytes()))
        rejected(f'wrong_mask_channel_{channel}_with_updated_hash', change_mask, expected)
    im = Image.open(ROOT / delivery['embedded_entries'][0]['png']['path']).copy()
    im.putpixel((x, y), (*im.getpixel((x, y))[:3], 0))
    bad_photo = output / 'bad-alpha-center.png'
    im.save(bad_photo)
    rejected('wrong_plate_alpha_with_updated_hash', lambda d, b: d['embedded_entries'][0].update(png={
        'path': str(bad_photo.relative_to(ROOT)), 'sha256': tav.sha(bad_photo.read_bytes())}), 'alfasenter')
    bad_size = output / 'bad-plate-size.png'
    im.crop((0, 0, 539, 492)).save(bad_size)
    rejected('wrong_plate_dimensions', lambda d, b: d['embedded_entries'][0].update(png={
        'path': str(bad_size.relative_to(ROOT)), 'sha256': tav.sha(bad_size.read_bytes())}), 'stoerrelse')
    rejected('stale_runtime_asset', lambda d, b: d['runtime_assets'].update({'embedded/tav-player.png': '0' * 64}), 'runtime')
    rejected('missing_dice_route', lambda d, b: b['entries'].pop(), 'alle17')
    rejected('dice_alias_instead_of_own_master', lambda d, b: b['entries'][0].update(master_key='dice.cel/007.png'), 'egne nye mastere')
    rejected('dice_reused_photo_instead_of_own_master', lambda d, b: b['entries'][1].update(
        raw=b['entries'][0]['raw'], raw_sha256=b['entries'][0]['raw_sha256']), 'separate fotografiske mastere')
    bad_record = output / 'bad-dice-donor.json'
    record = json.loads((ROOT / dice['entries'][0]['art_record']).read_text())
    record['stationary_cloth_join']['plate_sha256'] = '0' * 64
    bad_record.write_text(json.dumps(record))
    rejected('stale_dice_cloth_donor', lambda d, b: b['entries'][0].update(
        art_record=str(bad_record.relative_to(ROOT)), art_record_sha256=tav.sha(bad_record.read_bytes())), 'annen TAV-plate')

    # --activate med feil kilde maa stoppe uten aa opprette aktive bilder.
    bad_cli = output / 'bad-cli-delivery.json'
    changed = copy.deepcopy(delivery)
    changed['source_mask']['sha256'] = '0' * 64
    bad_cli.write_text(json.dumps(changed))
    cli = subprocess.run([sys.executable, str(ROOT / 'tools/hd_tavern_aktiver.py'), str(bad_cli),
        '--dice-delivery', str(args.dice_delivery), '--activate'], capture_output=True, text=True)
    assert cli.returncode != 0 and 'Endret fil' in cli.stderr
    no_active_change()
    checks.append(dict(name='activate_cli_validation_failure_writes_nothing', status='passed'))

    # En full installasjon og et avbrudd etter bakgrunnsbyttet proeves utenfor aktiv mappe.
    for fail in (False, True):
        with tempfile.TemporaryDirectory(prefix='moonstone-tavern-activation-') as folder:
            fixture = Path(folder)
            hd = fixture / 'web/hd'
            (hd / 'bg').mkdir(parents=True)
            (hd / 'manifest.json').write_bytes(original_manifest)
            (hd / 'bg/44898895.png').write_bytes(original_bg)
            (hd / 'unrelated.txt').write_text('bevar denne')
            for path in plan['source_sha256']:
                destination = fixture / path
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / path, destination)
            previous_root, original_replace = tav.ROOT, tav.os.replace
            tav.ROOT = fixture
            def fail_manifest(source, target):
                if Path(target) == hd / 'manifest.json':
                    raise OSError('Kontrollert feil ved siste manifestbytte')
                return original_replace(source, target)
            try:
                if fail:
                    tav.os.replace = fail_manifest
                    try:
                        tav.activate(plan)
                    except OSError as error:
                        assert 'Kontrollert feil' in str(error)
                    else:
                        raise AssertionError('Forventet manifestbyttefeil')
                    assert (hd / 'manifest.json').read_bytes() == original_manifest
                    assert (hd / 'bg/44898895.png').read_bytes() == original_bg
                    assert not any((hd / key).exists() for key in new_keys)
                    checks.append(dict(name='isolated_last_step_failure_rolls_back_all_images', status='passed'))
                else:
                    tav.activate(plan)
                    assert (hd / 'manifest.json').read_bytes() == plan['new_manifest']
                    for key, data in plan['files'].items():
                        assert (hd / key).read_bytes() == data
                    before, after = json.loads(original_manifest), json.loads(plan['new_manifest'])
                    old = {r['path']: r for r in before['files'] if r['path'] != 'bg/44898895.png'}
                    now = {r['path']: r for r in after['files']}
                    assert all(now[k] == r for k, r in old.items())
                    assert len(after['files']) == len(before['files']) + 21
                    old_tav = next(s for s in before['scenes'] if s['id'] == 'tavern')
                    new_tav = next(s for s in after['scenes'] if s['id'] == 'tavern')
                    assert new_tav['overlays'][:-1] == old_tav['overlays']
                    assert new_tav['overlays'][-1] == delivery['embedded_entries'][0]['overlay']
                    assert [s for s in before['scenes'] if s['id'] != 'tavern'] == [s for s in after['scenes'] if s['id'] != 'tavern']
                    checks.append(dict(name='isolated_all22_files_and_one_overlay_installed_together', status='passed'))
                assert (hd / 'unrelated.txt').read_text() == 'bevar denne'
            finally:
                tav.ROOT, tav.os.replace = previous_root, original_replace
    no_active_change()
    report = dict(schema=1, status='passed', checks=checks, active_package_changed=False,
        delivery=dict(path=str(args.delivery.relative_to(ROOT)), sha256=tav.sha(args.delivery.read_bytes())),
        dice_delivery=dict(path=str(args.dice_delivery.relative_to(ROOT)), sha256=tav.sha(args.dice_delivery.read_bytes())),
        validator_sha256=tav.sha((ROOT / 'tools/hd_tavern_aktiver.py').read_bytes()),
        generic_validator_sha256=tav.sha((ROOT / 'tools/hd_figurer_aktiver.py').read_bytes()),
        test_sha256=tav.sha(Path(__file__).read_bytes()), active_manifest_sha256=tav.sha(original_manifest),
        planned_manifest_sha256=tav.sha(plan['new_manifest']), assets={k: tav.sha(v) for k, v in plan['files'].items()})
    (output / 'test.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(dict(status='passed', checks=len(checks), active_package_changed=False,
        report=str((output / 'test.json').relative_to(ROOT)))))


if __name__ == '__main__':
    main()
