#!/usr/bin/env python3
"""Kontroller og aktiver gjennomgaatt TAV-spiller, ren bakgrunn og17 DICE-ruter samlet."""
import argparse
from collections import Counter, deque
import copy
import json
import math
import os
from pathlib import Path
import tempfile

from PIL import Image
import hd_figurer_aktiver as figures
import hd_bestilling as bestilling
import moonfiles as mf

ROOT = figures.ROOT
sha = figures.sha
RECT = [90, 65, 225, 188]
SOURCE_SHA = '466c92eac2ddb68f0eb98689db6ad36017683b29b23638c7b5c84fef4f6f3b42'
ZIP_SHA = '35b7d4c67b9fae6019e257780050d0f421d6ec4c250cdde48a8f296086d67a02'
PALETTES = [[0x05d, 0x03b, 0x028, 0x016, 0x003],
            [0xfa0, 0xc60, 0xb40, 0x930, 0x710],
            [0x0c5, 0x0a3, 0x082, 0x061, 0x040],
            [0xe00, 0xb00, 0x900, 0x600, 0x300]]
CODE_PATHS = {'web/src/core.js', 'web/src/render.js', 'web/src/scenes.js', 'web/src/hd.js'}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def checked(path, digest):
    source = (ROOT / path).resolve()
    require(source.is_relative_to(ROOT), 'Fil utenfor prosjektet: ' + str(path))
    require(sha(source.read_bytes()) == digest, 'Endret fil: ' + str(path))
    return source


def ref(item):
    return checked(item['path'], item['sha256'])


def read_ref(item):
    return json.loads(ref(item).read_text())


def image(path, size, mode='RGBA'):
    with Image.open(path) as im:
        require(im.format == 'PNG' and im.mode == mode and im.size == size,
                'Feil PNG-format/modus/stoerrelse: ' + str(path))
        im.load()
        return im.copy()


def source_mask(full):
    """Velg figuren fra originalmaterialer, lukkede nullskygger og dokumentert albue."""
    x0, y0, x1, y1 = RECT
    w, h = x1 - x0, y1 - y0
    indices, selected = [], []
    steel = (1, 3, 4, 5, 17)
    for y in range(y0, y1):
        for x in range(x0, x1):
            c = full[y * 320 + x]
            indices.append(c)
            selected.append(int(
                (131 <= x < 223 and 67 <= y < 174 and 6 <= c <= 11) or
                (157 <= x < 209 and 78 <= y < 135 and c in steel) or
                (92 <= x < 160 and 121 <= y < 178 and c in steel) or
                (111 <= x < 160 and 168 <= y < 186 and c in steel) or
                (103 <= x < 124 and 119 <= y < 129 and c in (1, 12, 13, 27, 28))))
    outside, queue = set(), deque()
    for y in range(h):
        for x in range(w):
            n = y * w + x
            if (x in (0, w - 1) or y in (0, h - 1)) and not selected[n]:
                outside.add(n)
                queue.append(n)
    while queue:
        n = queue.popleft()
        x, y = n % w, n // w
        for v in (n - 1 if x else -1, n + 1 if x + 1 < w else -1,
                  n - w if y else -1, n + w if y + 1 < h else -1):
            if v >= 0 and not selected[v] and v not in outside:
                outside.add(v)
                queue.append(v)
    enclosed = [n for n, c in enumerate(indices) if c == 0 and not selected[n] and n not in outside]
    for n in enclosed:
        selected[n] = 1
    dither = []
    for y in range(168, 183):
        anchors = [x for x in range(111, 160) if full[y * 320 + x] in steel]
        if anchors:
            for x in range(min(anchors), max(anchors) + 1):
                n = (y - y0) * w + x - x0
                if indices[n] == 0 and not selected[n]:
                    selected[n] = 1
                    dither.append(n)
    return bytes(indices), bytes(selected), enclosed, dither


def validate_pixels(photo, mask, indices, selected, palette):
    w, h = 135, 123
    px, mp = photo.load(), mask.load()
    for y in range(h):
        for x in range(w):
            require((px[x * 4 + 2, y * 4 + 2][3] >= 128) == bool(selected[y * w + x]),
                    'Feil originalt alfasenter i TAV-platen')
    for y in range(h * 4):
        for x in range(w * 4):
            i = y // 4 * w + x // 4
            c = indices[i]
            live = bool(selected[i]) and 6 <= c <= 10
            r, g, b, a = mp[x, y]
            require(r == (c + 1 if live else 0) and b == (255 if live else 0) and a == 255,
                    'Feil NN-indeks R/B/alfa i TAV-masken')
            pr, pg, pb, pa = px[x, y]
            if live:
                luminance = .299 * pr + .587 * pg + .114 * pb
                cr, cg, cb = palette[c][:3]
                reference = .299 * cr + .587 * cg + .114 * cb
                expected = min(255, max(0, math.floor(128 * luminance / reference + .5)))
                require(g == expected, 'Feil fotografisk luminans i TAV-masken')
            if pa and not 6 <= c <= 10:
                require(not (pb > pr * 1.35 + 1 and pb > pg * 1.1 + 1),
                        'Feil fast blaatt fotomateriale utenfor original spillerpalett')
            if pa and c == 11:
                require(pr <= 64 and pg == pb == 0, 'Fast indeks11 skal vaere original moerkeroed skygge')


def validate_tav(delivery, dice):
    require(delivery['schema'] == 1 and delivery['status'] == 'reviewed_original_and_runtime',
            'TAV-leveransen mangler visuell godkjenning')
    require(set(delivery['production_code_sha256']) == CODE_PATHS, 'Ufullstendig frontendbinding')
    require(delivery['production_code_sha256'] == dice['production_code_sha256'] and
            delivery['wasm_core_sha256'] == dice['wasm_core_sha256'], 'TAV/DICE har ulik kodebinding')
    for path, digest in delivery['production_code_sha256'].items():
        checked(path, digest)
    checked('web/build/moonstone-core.js', delivery['wasm_core_sha256'])
    require(delivery['source_zip_sha256'] == ZIP_SHA == dice['source_zip_sha256'], 'Annet originalarkiv')
    checked('Moonstonecd32-AMIGA.zip', ZIP_SHA)
    contract = read_ref(delivery['source_contract'])
    require(contract['schema'] == 1 and contract['kind'] == 'embedded-tavern-player' and
            contract['rect'] == RECT and contract['source_zip_sha256'] == ZIP_SHA, 'Annen TAV-kildekontrakt')
    require(delivery['source_file'].lower() == 'data/tav.piv' and
            delivery['source_file_sha256'] == contract['source_file_sha256'] == SOURCE_SHA, 'Annen TAV.PIV')
    game = mf.Spill(ROOT / 'Moonstonecd32-AMIGA.zip')
    original = game.les(delivery['source_file'])
    require(sha(original) == SOURCE_SHA, 'Original TAV.PIV er endret')
    planes, original_palette, data = mf.piv_alle(original)[0][0]
    full = mf.plan_til_indeks(data, planes)
    require(planes == 5 and len(full) == 320 * 200, 'Annen PIV-geometri')
    indices, selected, enclosed, dither = source_mask(full)
    require(ref(delivery['source_indices']).read_bytes() == indices, 'Annet TAV-kildeutsnitt')
    require(ref(delivery['source_mask']).read_bytes() == selected, 'Annen TAV-kildemaske')
    require(contract['enclosed_original_black_positions'] == enclosed and
            contract['original_elbow_dither_shadow']['local_positions'] == dither and len(dither) == 14,
            'Andre originale nullskygger')
    require(sum(selected) == contract['selected_pixels'] == 7431 and
            Counter(c for i, c in enumerate(indices) if selected[i]) ==
            Counter({int(k): v for k, v in contract['selected_indices'].items()}), 'Feil TAV-figurvalg')
    live = sum(bool(selected[i]) and 6 <= c <= 10 for i, c in enumerate(indices))
    excluded = sum(6 <= c <= 10 for c in full[:65 * 320])
    require(live == contract['source_live_pixels'] == 3682 and
            excluded == contract['excluded_bar_maid_live_pixels'] == 16 and
            sum(6 <= c <= 10 for c in full) == live + excluded, 'Spiller/barmaid-eierskap avviker')
    row = contract['routes'][0]
    require(len(contract['routes']) == 1 and row['indices_sha256'] == sha(indices) and
            row['alpha_indices_sha256'] == sha(selected), 'Annen TAV-rutebinding')
    palette = [[*mf.amiga_rgb(c), 255] for c in original_palette]
    palette[6:11] = [[*mf.amiga_rgb(c), 255] for c in PALETTES[0]]
    require(contract['palettes']['tavern']['rgba'] == palette, 'Annen original TAV-referansepalett')
    require(len(delivery['embedded_entries']) == 1, 'Forventet en TAV-plate')
    entry = delivery['embedded_entries'][0]
    overlay = dict(key='embedded/tav-player', rect=RECT, uv_rect=[0, 0, 1, 1],
                   foreground=False, palette_mask=True)
    require(entry['key'] == 'embedded/tav-player.png' and entry['scene_id'] == 'tavern' and
            entry['original_rect'] == RECT and entry['overlay'] == overlay and
            entry['original_selected_pixels'] == 7431 and entry['original_live_pixels'] == 3682 and
            entry['excluded_other_live_pixels'] == 16, 'Annen TAV-plateplassering/eierskap')
    photo = image(ref(entry['png']), (540, 492))
    mask = image(ref(entry['mask']), (540, 492))
    validate_pixels(photo, mask, indices, selected, palette)
    packing = read_ref(delivery['packing_proof'])
    require(packing['status'] == 'passed' and packing['photo'] == entry['png'] and
            packing['mask'] == entry['mask'] and
            packing['source_contract_sha256'] == delivery['source_contract']['sha256'], 'Annet pakkebevis')
    record = read_ref(delivery['packing_record'])
    require(record['output_sha256'] == entry['png']['sha256'] and
            record['mask_sha256'] == entry['mask']['sha256'] and
            record['source_indices_sha256'] == sha(indices), 'Annen pakkepost')
    audit = read_ref(delivery['source_audit'])
    require(audit['source_file_sha256'] == SOURCE_SHA and
            audit['source_indices_sha256'] == sha(full), 'Annen kildekartlegging')
    raw, prompt = ref(delivery['raw']), ref(delivery['prompt'])
    generation_path = ref(delivery['generation_record'])
    generation = json.loads(generation_path.read_text())
    art = generation_path.parent
    require(generation['generation_tool'] == 'builtin_image_gen' and
            checked(str((art / generation['output']).relative_to(ROOT)), generation['output_sha256']) == raw and
            checked(str((art / generation['prompt']).relative_to(ROOT)), generation['prompt_sha256']) == prompt,
            'Annen fotografisk master/prompt')
    for reference in generation['references']:
        checked(str((art / reference['path']).relative_to(ROOT)), reference['sha256'])
    derivations = {ref(d).name: ref(d) for d in delivery['material_derivations']}
    require(len(derivations) == 6 and set(derivations) == {
        'register-player-v3.cjs', 'player-v3-registered.json', 'player-v3-registered.png',
        'tav-player.png', 'normalize-fixed-material-v2.cjs', 'fixed-material-v2.json'},
        'Ufullstendig materialderivasjon')
    registration = json.loads(derivations['player-v3-registered.json'].read_text())
    fixed = json.loads(derivations['fixed-material-v2.json'].read_text())
    require(registration['input_sha256'] == delivery['raw']['sha256'] and
            registration['output_sha256'] == sha(derivations['player-v3-registered.png'].read_bytes()) ==
            record['raw_sha256'] and registration['original_plate_rect'] == RECT,
            'Annen materialregistrering')
    require(fixed['input_sha256'] == sha(derivations['tav-player.png'].read_bytes()) and
            fixed['output_sha256'] == entry['png']['sha256'] and
            fixed['source_indices_sha256'] == sha(indices) and
            fixed['live_RGB_changed'] == fixed['source_alpha_changed'] == 0, 'Annen materialnormalisering')
    before = image(derivations['tav-player.png'], (540, 492))
    old, new = before.load(), photo.load()
    for y in range(492):
        for x in range(540):
            require(old[x, y][3] == new[x, y][3], 'Materialnormalisering endrer alfa')
            if 6 <= indices[y // 4 * 135 + x // 4] <= 10:
                require(old[x, y] == new[x, y], 'Materialnormalisering endrer levende fotofelt')
    background = delivery['background']
    require(background['key'] == 'bg/44898895.png', 'Annen bakgrunnsnoekkel')
    bg = ref(background['png'])
    ref(background['prompt'])
    with Image.open(bg) as im:
        require(im.format == 'PNG' and im.mode in ('RGB', 'RGBA') and im.size == (1419, 1108),
                'Annen ren tavernabakgrunn')
    return entry, photo, mask, original, game, audit


def validate_proofs(delivery, dice, assets):
    html = ref(delivery['runtime_html']).read_bytes()
    require(sha(html) == delivery['html_sha256'], 'Annen runtime-HTML')
    ledger = read_ref(delivery['package_ledger'])
    frozen = read_ref(delivery['package_manifest'])
    require(ledger['status'] == 'frozen' and ledger['html_sha256'] == delivery['html_sha256'],
            'Annen frosset runtimepakke')
    expected_sources = {**delivery['production_code_sha256'],
        'web/build/moonstone-core.js': delivery['wasm_core_sha256'],
        'Moonstonecd32-AMIGA.zip': ZIP_SHA}
    require(ledger['source_files'] == expected_sources, 'Pakkelogg har annen kilde')
    require(ledger['files'] == [{k: r[k] for k in ('path', 'sha256', 'bytes')} for r in frozen['files']],
            'Pakkelogg og frosset manifest avviker')
    test = ref(delivery['runtime_test'])
    require(len(delivery['proofs']) == len(dice['proofs']) == 4 and
            {(p['path'], p['sha256']) for p in delivery['proofs']} ==
            {(p['path'], p['sha256']) for p in dice['proofs']}, 'TAV/DICE har ulike runtimebevis')
    colors = set()
    for proof in delivery['proofs']:
        report = read_ref(proof)
        color = report['controlled_color']
        require(type(color) is int and 0 <= color < 4 and color not in colors, 'Ugyldig/dobbel runtimefarge')
        colors.add(color)
        require(report['status'] == 'passed' and not report['errors'] and report['assets'] == assets,
                'Runtimebevis gjelder andre bilder eller feil')
        require(report['production_code_sha256'] == delivery['production_code_sha256'] and
                report['wasm_core_sha256'] == delivery['wasm_core_sha256'] and
                report['html_sha256'] == delivery['html_sha256'] and
                report['source_zip_sha256'] == ZIP_SHA and
                report['player_contract_sha256'] == delivery['source_contract']['sha256'] and
                report['package_ledger_sha256'] == delivery['package_ledger']['sha256'] and
                report['test_sha256'] == sha(test.read_bytes()), 'Stale runtime-/kode-/kildeforbindelse')
        runtime = report['runtime']
        require(runtime['imports']['bg/44898895.png'] == assets['bg/44898895.png'] and
                runtime['palette'][6:11] == PALETTES[color] and runtime['loading']['loaded'] is True and
                runtime['loading']['original'] == runtime['loading']['pendingOriginal'],
                'Bakgrunn/palett/maskefallback avviker')
        expected_checks = ['last_imported_background_is_clean_candidate', 'missing_mask_preserves_original',
            'missing_mask_exact_HD_return', 'loaded_mask_Original_unchanged',
            'loaded_mask_exact_HD_return', 'loading_state_unchanged']
        expected_checks += [f'{i}_{suffix}' for i in range(6, 23)
                            for suffix in ('HD_changes', 'exact_return', 'state_unchanged')]
        require(report['checks'] == expected_checks and set(runtime['seen']) == {str(i) for i in range(6, 23)},
                'Ufullstendig tavernaprøve')
        for number, sample in runtime['seen'].items():
            require(sample['hd'] == sample['restored'] and sample['hd'] != sample['original'] and
                    sample['state'] == sample['state_after'] and sample['figure']['hd'] is True and
                    sample['figure']['bilde'] == int(number) and sample['control']['bakgrunn'] == 'hd',
                    'Feil Original/HD-retur eller rute')
            expected_rgba = [v for c in PALETTES[color] for v in (*mf.amiga_rgb(c), 255)]
            require(sample['palette'][24:44] == expected_rgba, 'Rute har annen spillerpalett')
            for mode in ('hd', 'original', 'restored'):
                checked(str((ROOT / proof['path']).parent.relative_to(ROOT) / f'{number}-{mode}.png'), sample[mode])
    return frozen


def validate(delivery, dice):
    """Les og valider alt foer det opprettes eller erstattes noen aktiv fil."""
    manifest_path = ROOT / 'web/hd/manifest.json'
    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes)
    entry, photo, mask, original, game, audit = validate_tav(delivery, dice)
    require(len(dice['entries']) == 17 and {e['key'] for e in dice['entries']} ==
            {f'dice.cel/{i:03d}.png' for i in range(6, 23)}, 'Forventet alle17 DICE-ruter006..022')
    require(all(not e.get('existing_master') and not e.get('master_key') for e in dice['entries']),
            'DICE skal ha17 egne nye mastere')
    require(len({e['raw_sha256'] for e in dice['entries']}) == 17 and
            len({e['raw'] for e in dice['entries']}) == 17, 'DICE skal ha17 separate fotografiske mastere')
    companions = {ref(d).name: ref(d) for d in delivery['companion_derivations']}
    require(len(companions) == 5 and set(companions) == {
        'pack.cjs', 'join-cloth.py', 'freeze-packing.py', 'freeze-delivery.py', 'dice-source-cloth.json'},
        'Ufullstendig DICE-materialderivasjon')
    dice_files = figures.validate(dice)
    require(set(dice_files) == {f'dice.cel/{i:03d}.png' for i in range(6, 23)} |
            {'dice.cel/006.mask.png', 'dice.cel/007.mask.png'}, 'Forventet17 DICE-bilder og2 masker')
    files = {key: path.read_bytes() for key, path in dice_files.items()}
    files[entry['key']] = ref(entry['png']).read_bytes()
    files['embedded/tav-player.mask.png'] = ref(entry['mask']).read_bytes()
    files['bg/44898895.png'] = ref(delivery['background']['png']).read_bytes()
    assets = {key: sha(data) for key, data in files.items()}
    require(assets == delivery['runtime_assets'], 'Samlet leveranse avviker fra faktisk runtime')
    frozen = validate_proofs(delivery, dice, assets)
    bank = mf.cel_les(game.les('data/dice.cel'))[0]
    tav_indices = ref(delivery['source_indices']).read_bytes()
    for e in dice['entries']:
        source = bank[e['frame']]
        w, h = source['bredde'], source['hoyde']
        indices = bestilling.utvid_indekser(mf.plan_til_indeks(source['data'], source['plan'], w, h), source['maske'])
        im = image(ROOT / e['png'], (w * 4, h * 4))
        px = im.load()
        for y in range(h):
            for x in range(w):
                require((px[x * 4 + 2, y * 4 + 2][3] >= 128) == bool(indices[y * w + x]),
                        'Feil originalt DICE-alfasenter: ' + e['key'])
        record = json.loads(checked(e['art_record'], e['art_record_sha256']).read_text())
        packing_script = Path(e['raw']).parent.parent / 'pack.cjs'
        require(checked(str(packing_script), record['packing_script_sha256']) == companions['pack.cjs'],
                'DICE-artpost har annen pakkekode')
        require(record['background_sha256'] == assets['bg/44898895.png'] and
                record['raw_sha256'] == e['raw_sha256'] and record['prompt_sha256'] == e['prompt_sha256'],
                'DICE-materialpost har annen bakgrunn/master/prompt')
        if e['frame'] in (6, 7):
            join = record['stationary_cloth_join']
            checked(join['source_audit'], join['source_audit_sha256'])
            require(join['plate_sha256'] == assets['embedded/tav-player.png'] and
                    join['mask_sha256'] == assets['embedded/tav-player.mask.png'] and
                    join['source_pixels'] == 210, 'DICE-kappematerialet kommer fra annen TAV-plate')
            dmask = image(ROOT / e['mask'], (w * 4, h * 4)).load()
            pp, pm = photo.load(), mask.load()
            count = 0
            for y in range(h):
                for x in range(w):
                    c = indices[y * w + x]
                    if not 6 <= c <= 10:
                        continue
                    count += 1
                    tx, ty = x + 119 - RECT[0], y + 102 - RECT[1]
                    require(c == tav_indices[ty * 135 + tx],
                            'DICE og TAV har ulik originalindeks paa samme sted')
                    for dy in range(4):
                        for dx in range(4):
                            require(px[x * 4 + dx, y * 4 + dy][:3] == pp[tx * 4 + dx, ty * 4 + dy][:3] and
                                    dmask[x * 4 + dx, y * 4 + dy] == pm[tx * 4 + dx, ty * 4 + dy],
                                    'DICE/TAV-kappeskjøten er ikke byteidentisk')
            require(count == 210, 'Annet antall delte DICE-kappefelt')
    scenes = [s for s in manifest['scenes'] if s['id'] == 'tavern']
    old_scenes = [s for s in frozen['scenes'] if s['id'] == 'tavern']
    require(len(scenes) == len(old_scenes) == 1 and scenes[0] == old_scenes[0] == audit['scene_contract'],
            'Aktiv tavernascene avviker fra den testede')
    active = {r['path']: r for r in manifest['files']}
    require(len(active) == len(manifest['files']) and len({k.lower() for k in active}) == len(active),
            'Duplikater i aktivt manifest')
    bg_key = 'bg/44898895.png'
    old_bg = next(r for r in frozen['files'] if r['path'] == bg_key)
    require(active.get(bg_key) == old_bg, 'Aktiv tavernabakgrunn er endret siden prøven')
    checked('web/hd/' + bg_key, old_bg['sha256'])
    for key in files:
        if key != bg_key:
            require(key.lower() not in {k.lower() for k in active} and not (ROOT / 'web/hd' / key).exists(),
                    'Figur er allerede aktiv eller maalet finnes: ' + key)
    result = copy.deepcopy(manifest)
    result['files'] = [r for r in result['files'] if r['path'] != bg_key]
    result['files'] += [dict(path=k, bytes=len(v), sha256=sha(v), kind='background' if k == bg_key else 'base')
                        for k, v in files.items()]
    result['files'].sort(key=lambda r: r['path'])
    result['images'] = sum(r['path'].endswith('.png') for r in result['files'])
    next(s for s in result['scenes'] if s['id'] == 'tavern')['overlays'].append(entry['overlay'])
    require(manifest_path.read_bytes() == manifest_bytes, 'Manifestet ble endret under kontrollen; kjoer paa nytt')
    return dict(files=files, old_manifest=manifest_bytes,
                new_manifest=(json.dumps(result, ensure_ascii=False, indent=2) + '\n').encode(),
                old_background=(ROOT / 'web/hd' / bg_key).read_bytes(),
                source_sha256={**delivery['production_code_sha256'],
                    'web/build/moonstone-core.js': delivery['wasm_core_sha256'],
                    'Moonstonecd32-AMIGA.zip': ZIP_SHA})


def activate(plan):
    """Publiser lokale bildefiler foerst, og bytt manifestet atomisk til slutt."""
    hd = ROOT / 'web/hd'
    manifest = hd / 'manifest.json'
    bg = hd / 'bg/44898895.png'
    for path, digest in plan['source_sha256'].items():
        checked(path, digest)
    require(manifest.read_bytes() == plan['old_manifest'] and bg.read_bytes() == plan['old_background'],
            'Aktiv pakke endret siden kontrollen; ingen skriving utfoert')
    targets = [hd / key for key in plan['files']]
    for target in targets:
        require(target.resolve().is_relative_to(hd.resolve()), 'Maal utenfor HD-pakken')
        if target != bg:
            require(not target.exists(), 'Maal oppsto etter kontrollen; ingen skriving utfoert')
    installed = []
    with tempfile.TemporaryDirectory(prefix='.tavern-stage-', dir=hd) as folder:
        stage = Path(folder)
        for key, data in plan['files'].items():
            file = stage / key
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_bytes(data)
        staged_manifest = stage / 'manifest.json'
        staged_manifest.write_bytes(plan['new_manifest'])
        require(manifest.read_bytes() == plan['old_manifest'] and bg.read_bytes() == plan['old_background'],
                'Aktiv pakke endret under klargjoeringen; ingen bildefiler skrevet')
        try:
            for key in plan['files']:
                target = hd / key
                target.parent.mkdir(parents=True, exist_ok=True)
                if target == bg:
                    os.replace(stage / key, target)
                else:
                    # Lenken opprettes bare hvis maalet fremdeles ikke finnes.
                    os.link(stage / key, target)
                installed.append(target)
            require(manifest.read_bytes() == plan['old_manifest'], 'Samtidig manifestendring; ruller tilbake egne bilder')
            os.replace(staged_manifest, manifest)
        except Exception:
            for target in reversed(installed):
                if target == bg:
                    restore = stage / 'background-restore.png'
                    restore.write_bytes(plan['old_background'])
                    os.replace(restore, bg)
                else:
                    target.unlink()
            raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('delivery', type=Path)
    parser.add_argument('--dice-delivery', required=True, type=Path)
    parser.add_argument('--activate', action='store_true')
    args = parser.parse_args()
    delivery, dice = json.loads(args.delivery.read_text()), json.loads(args.dice_delivery.read_text())
    plan = validate(delivery, dice)
    if args.activate:
        activate(plan)
    print(json.dumps(dict(status='activated' if args.activate else 'checked_not_activated',
        dice_masters=17, dice_masks=2, embedded_masters=1, embedded_masks=1,
        background_revisions=1, png_files=len(plan['files']),
        manifest_sha256=sha(plan['new_manifest']))))


if __name__ == '__main__':
    main()
