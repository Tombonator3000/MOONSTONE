#!/usr/bin/env python3
"""Eksporter kildebundet figurkø, kontroller den og pakk én nytegnet kandidat.

Alle utdata forblir i denne artmappen. Originaler, referanseforstørrelser og
maskemaler er forberedelser, aldri ferdige HD-nytegninger.
"""
import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import html
import io
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

from PIL import Image, ImageDraw

ART = Path(__file__).resolve().parent
ROOT = ART.parents[1]
sys.path.insert(0, str(ROOT/'tools'))
if (ART/'source/tools').exists():
    sys.path.insert(0, str(ART/'source/tools'))
import gfx
import hd_bestilling as order
import moonfiles as mf

GROUPS = {'Monstre', 'Riddere', 'Stedsfigurer', 'Blod og sår',
          'Drageanimasjon', 'Kroanimasjoner', 'Intro og slutt'}
QA = ['samme_pose_og_motiv', 'samme_utsnitt_og_anker', 'samme_vapen_og_utstyr',
      'originalfarger_bekreftet', 'troverdig_materiale_uten_nye_detaljer',
      'transparent_bakgrunn_uten_kantglod', 'sammenheng_med_naboruter',
      'speiling_og_overlapping_i_runtime', 'original_hd_retur', 'palett_og_toning_i_runtime']


def sha(data):
    return hashlib.sha256(data).hexdigest()


def digest(path):
    return sha(path.read_bytes())


def relative(path):
    return str(path.relative_to(ART))


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


def freeze(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        assert path.read_bytes() == data, 'Frosset kilde er endret: '+str(path)
    else:
        path.write_bytes(data)


def save_png(path, image):
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, optimize=True)
    return dict(path=relative(path), sha256=digest(path), width=image.width, height=image.height)


def key_parts(key):
    bank, filename = key.split('/')
    assert re.fullmatch(r'[A-Za-z0-9_.-]+', bank) and re.fullmatch(r'\d{3}\.png', filename)
    return bank, int(filename[:-4])


def aliases(row):
    result = [(row['hd_fil'], 'redraw')]
    exact = re.search(r'Samme bilde brukes også som (.+?)\. Legg samme tegning der\.', row['merknad'])
    if exact:
        result += [(p, 'exact_copy') for p in re.findall(r'[A-Za-z0-9_.-]+/\d+\.png', exact.group(1))]
    result += [(p, 'he_mask_copy') for p in re.findall(
        r'Samme tegning skal også ligge som ([A-Za-z0-9_.-]+/\d+\.png)', row['merknad'])]
    return result


def package(group):
    if group == 'Monstre':
        return '01-monstre'
    if group == 'Riddere':
        return '02-riddere'
    return '03-steder-effekter-intro'


def identity(bank, frame):
    if bank in order.INTRO_HVOR:
        return order.INTRO_HVOR[bank]
    if bank in order.PALETT:
        return 'Ridderens separate kropp-, våpen- eller blodfragment fra '+bank
    if bank.lower() == 'hen1.c':
        return 'Tempelet/Stonehenge: originalbank hen1.c, delt indeksgeometri med Klift1.CEL'
    if bank.lower() == 'wi1.c':
        return 'Trollmannen Math, separat originalfigur eller animasjonsfragment'
    if bank.lower() == 'mys.cel':
        return 'Healeren: begge øyne lukket' if frame == 6 else 'Mystikeren: ett øye lukket'
    if bank.lower() == 'dice.cel':
        if 10 <= frame <= 22:
            return ('Tavernaen: tre kastede Dragon Dice over bordet; bruk tav.piv-paletten. '
                    'Bevar hver ternings plassering, rotasjon og størrelse fra originalruten')
        return ('Tavernaen: ridderens stålhanske/arm over bordet; bruk tav.piv-paletten, ikke dice.piv. '
                'Eksakt håndstilling og handling må leses fra originalruten') if 6 <= frame <= 9 else 'Terningspillets separate originalrute'
    if bank.lower() == 'mi.c':
        return 'Kartets flygende drage, animasjonsrute '+str(frame-34)
    if bank.lower() == 'blo.cel':
        return 'Blodsprut over figurer i kamp'
    for prefix, name in order.MONSTRE.items():
        if bank.lower().startswith(prefix.lower()):
            return name+', separat originalfragment fra '+bank
    raise AssertionError('Ukjent bankidentitet: '+bank)


def raw_frames(game):
    result, banks, empty = {}, {}, []
    for path in game.data_filer():
        name = path.split('/')[-1]
        data = game.les(path)
        if not (name.lower().endswith(order.FIGURER) and mf.er_cel(data)):
            continue
        frames = mf.cel_les(data)[0]
        banks[name] = dict(path=path, sha256=sha(data), bytes=len(data), frames=len(frames))
        for nr, f in enumerate(frames):
            key = f'{name}/{nr:03}.png'
            if not f['plan']:
                empty.append(key)
                continue
            packed = mf.plan_til_indeks(f['data'], f['plan'], f['bredde'], f['hoyde'])
            result[key] = dict(frame=f, packed=bytes(packed), indices=order.utvid_indekser(packed, f['maske']))
    return result, banks, empty


def export_palettes(game):
    palettes = {}
    raw = gfx.standard_palett(game)
    palettes['combat-preview'] = dict(source='data/test', source_frame=4,
        source_sha256=sha(game.les('test')), colors=[mf.amiga_rgb(c) for c in raw],
        status='preview_only_not_a_monster_or_player_color_approval')
    for name in ('WI1.P', 'WI2.P', 'hen1.p', 'bg5.piv', 'hea.piv', 'mys.piv', 'dice.piv', 'tav.piv'):
        raw = mf.piv_alle(game.les(name))[0][0][1]
        palettes[name.lower()] = dict(source=game.finn(name), source_frame=0,
            source_sha256=sha(game.les(name)), colors=[mf.amiga_rgb(c) for c in raw],
            status='original_scene_palette; verify_the_route_in_this_scene')
    path = ROOT/'art/hd-icons-2026-10-11/source/map-frame2000.json'
    snapshot = json.loads(path.read_text())
    freeze(ART/'source/map-frame2000.json', path.read_bytes())
    palettes['map-runtime'] = dict(source=str(path.relative_to(ROOT)), source_sha256=digest(path),
        source_frame=snapshot['frame'], state=snapshot['state'],
        colors=[c[:3] for c in snapshot['palette']], status='captured_world_map_palette')
    math_path=ART/'source/runtime-palette-contracts/math.json'
    if not math_path.exists():
        freeze(math_path,(ROOT/'art/hd-math-figures-2026-10-11/source-contract.json').read_bytes())
    math=json.loads(math_path.read_text())
    assert math['source_zip_sha256']==digest(ROOT/'Moonstonecd32-AMIGA.zip')
    assert math['bank_sha256']==sha(game.les('Wi1.C'))
    for name,record in math['palettes'].items():
        palettes[name]=dict(source=relative(math_path),source_sha256=digest(math_path),
            source_frame=record['frame'],state=record['state'],colors=[c[:3] for c in record['rgba']],
            status='captured_original_Math_palette; tower015..020_live_indices6..10')
    tavern_path=ART/'source/runtime-palette-contracts/tavern.json'
    tavern=json.loads(tavern_path.read_text())
    assert tavern['source_zip_sha256']==digest(ROOT/'Moonstonecd32-AMIGA.zip')
    assert tavern['source_banks']['dice.cel']==sha(game.les('dice.cel'))
    palettes['tavern-blue']=dict(source=relative(tavern_path),source_sha256=digest(tavern_path),
        source_frame=1500,colors=[c[:3] for c in tavern['variants']['blue']['rgba']],
        status='captured_original_tavern_palette; dice006/007_live_indices6..10')
    for name, record in palettes.items():
        write_json(ART/'source/palettes'/f'{name}.json', record)
        if record['source'].startswith('data/'):
            freeze(ART/'source/palette-banks'/record['source'][5:], game.les(record['source']))
    return palettes


def palette_for(bank, frame):
    if bank.lower()=='wi1.c':return 'math-tower' if frame>=15 else 'math-balcony'
    if bank.lower()=='dice.cel' and 6<=frame<=22:return 'tavern-blue'
    return {'wi1.c': 'wi1.p', 'hen1.c': 'hen1.p', 'klift1.cel': 'hen1.p',
            'dice.cel': 'dice.piv', 'mi.c': 'map-runtime',
            'mys.cel': 'hea.piv' if frame == 6 else 'mys.piv'}.get(bank.lower(), 'combat-preview')


def mask_colors(bank,frame):
    if bank.lower()=='wi1.c' and 15<=frame<=20:return set(range(6,11))
    if bank.lower()=='dice.cel' and frame in (6,7):return set(range(6,11))
    return order.RIDDERFARGER if bank in order.PALETT else set()


def neutral_mask(indices, size, live_indices=None):
    live_indices=order.RIDDERFARGER if live_indices is None else set(live_indices)
    image = Image.new('RGBA', size, (0, 0, 0, 255))
    image.putdata([(i+1, 128, 255, 255) if i in live_indices else (0, 0, 0, 255) for i in indices])
    return image.resize((size[0]*4, size[1]*4), Image.Resampling.NEAREST)


def prompt(record):
    return (f"Nytegn bare originalruten {record['key']}, separat. Målet er en trofast, naturtro HD-oppdatering.\n"
            f"Kilde: {record['original']['path']} (SHA256 {record['original']['sha256']}).\n"
            f"Kildegeometri: {record['width']} x {record['height']}; lever RGBA PNG i {record['target_width']} x {record['target_height']}.\n"
            f"Bankidentitet: {record['identity']}. Denne ruten er ikke en ny hel figur eller en ny scene.\n"
            "Bevar samme motiv, pose, proporsjoner, våpenretning, fragmentkanter, åpninger og plassering i hele kilderektangelet.\n"
            "Ikke beskjær, sentrer på nytt, flytt fotpunktet, speil, legg til utstyr eller fyll inn kroppsdeler som ikke finnes i originalen.\n"
            "Bakgrunnen skal være transparent. Naturtro overflater, rolig lys og konkrete materialer; ingen ny fantasydekor eller lysglød.\n"
            f"Palettreferanse: {record['palette_id']}; status: {record['palette_status']}.\n"
            "Forhåndsvisningspalett er ikke en godkjent fargefasit. Monstre må sammenlignes med faktisk originalscene før endelig fargegodkjenning.\n"
            + ("Ridderfargene styres av egen indeksmaske. Grå rustning med nøytralverdi 128 må pakkes med --gray-reference 128.\n" if record['needs_mask'] else '')
            + "Sammenlign den nye ruten direkte mot kilden og bevar kilde-/prompt-/kandidatbevis. Automatisk oppskalering er ikke nytegning.\n")


def rolling_sources(game):
    records = []
    for name in ('bg1a.PIV', 'bg1b.PIV', 'bg1c.PIV'):
        data = game.les(name)
        freeze(ART/'source/rolling-banks'/name, data)
        plan, raw_palette, raw_bits = mf.piv_alle(data)[0][0]
        indices = mf.plan_til_indeks(raw_bits, plan)
        original = Image.frombytes('P', (320, 200), indices)
        original.putpalette(gfx.palett_liste(raw_palette))
        atlas = save_png(ART/'references/rolling'/name/'atlas.png', original)
        tiles = []
        # Dokumentert inspeksjonsrutenett fra de bevarte 32x25-referansene.
        # Rutenettet er ikke en påstand om dekodet .stile eller runtime-ruting.
        for n in range(80):
            x, y = n % 10 * 32, n // 10 * 25
            png = save_png(ART/'references/rolling'/name/f'{n:03}.png', original.crop((x, y, x+32, y+25)))
            tiles.append(dict(cell=n, rect=[x, y, 32, 25], original=png))
        records.append(dict(bank=name, source_sha256=sha(data), original_atlas=atlas,
                            inspection_grid=[10, 8], inspection_cell_size=[32, 25], cells=tiles,
                            status='source_grid_only_no_runtime_contract_or_redraw_claim'))
    compositions = []
    for name in ('intro.stile', 'co.stile'):
        data = game.les(name)
        freeze(ART/'source/rolling-banks'/name, data)
        compositions.append(dict(bank=name, bytes=len(data), sha256=sha(data), status='composition_not_decoded_here'))
    return dict(piv_banks=records, composition_banks=compositions, inspection_cells=240,
                note='Separat fra CEL-køen og de fem bakgrunnsrevisjonene. Hele rulleforløpet er fortsatt uverifisert.')


def export():
    game_path = ROOT/'Moonstonecd32-AMIGA.zip'
    game = mf.Spill(str(game_path))
    parser_hashes = {}
    for path in ('tools/moonfiles.py', 'tools/gfx.py', 'tools/hd_bestilling.py'):
        frozen = ART/'source'/path
        if not frozen.exists():
            freeze(frozen, (ROOT/path).read_bytes())
        parser_hashes[path] = digest(frozen)
    provenance_path = ART/'source/provenance.json'
    if not provenance_path.exists():
        write_json(provenance_path, dict(commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()))
    provenance = json.loads(provenance_path.read_text())
    source_csv = ART/'source/order.csv'
    if not source_csv.exists():
        freeze(source_csv, (ROOT/'docs/hd-bestilling-liste.csv').read_bytes())
    rows = list(csv.DictReader(io.StringIO(source_csv.read_text()), delimiter=';'))
    assert len(rows) == 1796, 'Denne køen fryser bestillingen med 1796 rader'
    selected = [r for r in rows if r['gruppe'] in GROUPS]
    selected_keys = {key for r in selected for key, _ in aliases(r)}
    frames, all_banks, empty = raw_frames(game)
    palettes = export_palettes(game)
    preview_palette = gfx.palett_liste(gfx.standard_palett(game))
    program, mog = game.les('program').lower(), game.les('mog').lower()
    for name in ('program', 'mog'):
        freeze(ART/'source/programs'/name, game.les(name))
    manifest_source = ART/'source/manifest-at-preparation.json'
    if not manifest_source.exists():
        freeze(manifest_source, (ROOT/'web/hd/manifest.json').read_bytes())
    active_manifest = json.loads(manifest_source.read_text())
    active = {r['path'].lower() for r in active_manifest['files']}
    records, seen = [], set()
    for row in selected:
        master = row['hd_fil']
        master_frame = frames[master]
        for key, role in aliases(row):
            assert key not in seen, 'Duplisert målrute: '+key
            seen.add(key)
            bank, frame = key_parts(key)
            raw = frames[key]
            f, indices = raw['frame'], raw['indices']
            w, h = f['bredde'], f['hoyde']
            assert (w, h) == (int(row['kilde_bredde']), int(row['kilde_hoyde']))
            assert int(row['hd_bredde']) == w*4 and int(row['hd_hoyde']) == h*4
            remap = {}
            for a, b in zip(master_frame['indices'], indices):
                assert remap.setdefault(a, b) == b, 'Uentydig indekskopi: '+key
            if role in ('redraw', 'exact_copy'):
                assert raw['indices'] == master_frame['indices'], 'Kopien avviker: '+key
            else:
                assert all(a == b or order.HE_BYTTE.get(a) == b for a, b in remap.items()), key
            assert key.lower() not in active, 'Ruten har allerede direkte aktiv PNG: '+key
            live_indices=mask_colors(bank,frame)
            needs_mask=bool(set(indices)&live_indices)
            math_override=bank.lower()=='wi1.c' and 15<=frame<=20
            tavern_override=bank.lower()=='dice.cel' and frame in (6,7)
            if role == 'redraw' and not (math_override or tavern_override):
                assert needs_mask == (row['trenger_maske'] == 'ja'), key
            source = all_banks[bank]
            freeze(ART/'source/banks'/bank, game.les(source['path']))
            pal_id = palette_for(bank, frame)
            pal = palettes[pal_id]
            packed = Image.frombytes('P', (w, h), raw['packed'])
            packed.putpalette(preview_palette)
            packed.info['transparency'] = 0
            packed_png = save_png(ART/'source/packed'/key, packed)
            original = Image.new('RGBA', (w, h))
            original.putdata([tuple(pal['colors'][i])+(255 if i else 0,) for i in indices])
            original_png = save_png(ART/'references/original'/key, original)
            enlarged = save_png(ART/'references/nearest4x'/key, original.resize((w*4, h*4), Image.Resampling.NEAREST))
            alpha = Image.frombytes('L', (w, h), bytes(255 if i else 0 for i in indices))
            silhouette = save_png(ART/'source/alpha'/key, alpha)
            mask = save_png(ART/'mask-templates'/key.replace('.png', '.mask.png'), neutral_mask(indices, (w, h),live_indices)) if needs_mask else None
            intro_only = bank.lower().encode() in program and bank.lower().encode() not in mog
            record = dict(key=key, master_key=master, role=role, package=package(row['gruppe']),
                order_group=row['gruppe'], order_priority='4' if row['gruppe']=='Intro og slutt' else row['prioritet'],
                identity=identity(bank, frame), master_usage=row['hvor_i_spillet'],
                identity_limit='Kildebank og brukssted. Ingen udokumentert handlingsetikett per rute.',
                bank=bank, frame=frame, width=w, height=h, target_width=w*4, target_height=h*4,
                source_bank=source, bitplane_sha256=sha(f['data']), packed_indices_sha256=sha(raw['packed']),
                indices_sha256=sha(indices), plane_mask=f['maske'], packed_planes=f['plan'], source_flag=f['flagg'],
                source_indices=sorted(set(indices)), index_remap={str(a): b for a, b in sorted(remap.items())},
                source_neighbors=[f'{bank}/{n:03}.png' for n in range(max(0, frame-2), frame+3)
                                  if n != frame and f'{bank}/{n:03}.png' in selected_keys],
                neighbor_limit='Nærliggende kilde-ID-er, ikke en bekreftet animasjonsrekkefølge',
                alpha_bounds=alpha.getbbox(), origin=[0, 0], placement='Originalens tegnerektangel; ingen ny sentrering eller justering av fotpunkt',
                palette_id=pal_id, palette_status=pal['status'], palette_source_sha256=pal['source_sha256'],
                palette_file_sha256=digest(ART/'source/palettes'/f'{pal_id}.json'),
                original=original_png, nearest4x_reference=enlarged, packed_original=packed_png, silhouette=silhouette,
                needs_mask=needs_mask, neutral_mask_template=mask,
                live_palette_indices=sorted(live_indices),
                source_order_mask_override=dict(reason='Original08a9b6 recolors6..10 in '+('Math tower' if math_override else 'tavern'),
                    contract='source/runtime-palette-contracts/'+('math' if math_override else 'tavern')+'.json',
                    sha256=digest(ART/'source/runtime-palette-contracts'/('math.json' if math_override else 'tavern.json'))) if math_override or tavern_override else None,
                mask_warning='KN5-indeks 9/11 trenger faktisk kamp-/fargemåling' if bank == 'KN5.ob' and set(indices) & {9, 11} else None,
                intro_only=intro_only, runtime_gate='program_art_palette_and_animation_runtime_pending' if intro_only else 'new_art_requires_route_runtime_check',
                art_status='pending_individual_redraw' if role == 'redraw' else 'pending_master_redraw',
                target_png='hd/'+key, target_mask='hd/'+key.replace('.png', '.mask.png') if needs_mask else None,
                source_order_note=row['merknad'])
            records.append(record)
            write_json(ART/'routes'/key.replace('.png', '.json'), record)
            if role == 'redraw':
                prompt_path = ART/'prompts'/key.replace('.png', '.txt')
                prompt_path.parent.mkdir(parents=True, exist_ok=True)
                prompt_path.write_text(prompt(record), encoding='utf-8')
                review = ART/'reviews'/key.replace('.png', '.json')
                if not review.exists():
                    write_json(review, dict(key=key, source_indices_sha256=record['indices_sha256'],
                        original_sha256=original_png['sha256'], candidate_sha256=None,
                        authoring_method=None, prompt=None, generator=None,
                        visual_checks={k: 'pending' for k in QA}, status='pending'))
    # Alle ikke-tomme, uaktiverte CEL-ruter skal dekkes av figurer eller de
    # elleve separate ikonsakene. Logoen er en uttrykkelig aktiv revisjon.
    icon_keys = {r['hd_fil'] for r in rows if r['gruppe'] in ('Inventar-UI', 'Kro- og byikoner')}
    remaining = {key for key in frames if key.lower() not in active}
    assert remaining == seen | icon_keys, 'Udekkede eller ekstra ruter: '+str(remaining ^ (seen | icon_keys))
    assert len(records) == 2040 and len(selected) == 1779
    banks = {name: all_banks[name] for name in sorted({r['bank'] for r in records}, key=str.lower)}
    rolling = rolling_sources(game)
    outside = [r for r in rows if r['gruppe'] not in GROUPS]
    write_json(ART/'outside-scope.json', dict(order_rows=outside, counts=dict(icons=11, backgrounds=5, logo=1),
                                            rolling=rolling, empty_cel_routes=empty))
    counts = dict(order_rows=len(rows), independent_redraws=len(selected), concrete_routes=len(records),
                  exact_copies=sum(r['role'] == 'exact_copy' for r in records),
                  he_mask_copies=sum(r['role'] == 'he_mask_copy' for r in records),
                  mask_templates=sum(r['needs_mask'] for r in records),
                  independent_masks=sum(r['needs_mask'] and r['role'] == 'redraw' for r in records),
                  banks=len(banks), intro_routes=sum(r['intro_only'] for r in records),
                  intro_independent=sum(r['intro_only'] and r['role'] == 'redraw' for r in records),
                  by_group=dict(Counter(r['gruppe'] for r in selected)),
                  by_package={p: dict(independent=sum(r['role'] == 'redraw' for r in records if r['package'] == p),
                                      routes=sum(r['package'] == p for r in records)) for p in sorted({r['package'] for r in records})})
    embedded_work=[dict(key='WI1.P/embedded-Math-figure',source_bank=game.finn('WI1.P'),
        source_bank_sha256=sha(game.les('WI1.P')),authoring_scope='Maths ansikt, kropp og hender bakt inn i WI1.P',
        status='additional_non_CEL_figure_redraw_pending',
        count_scope='Ikke inkludert i 1779 CEL-mastere eller 2040 CEL-målruter; regionkontrakt og egen runtimekontroll kreves',
        preparation_owner='art/hd-math-figures-2026-10-11')]
    write_json(ART/'additional-non-cel-work.json',embedded_work)
    queue = dict(schema=1, status='source_preparation_only_no_finished_hd_art', counts=counts, banks=banks,
                 additional_non_cel_work=embedded_work,
                 source_zip_sha256=digest(game_path), source_order_sha256=digest(source_csv),
                 source_manifest_sha256=digest(manifest_source),
                 source_program_sha256=sha(game.les('program')), source_mog_sha256=sha(game.les('mog')),
                 parser_sha256=parser_hashes, source_commit=provenance['commit'], entries=records)
    write_json(ART/'queue.json', queue)
    columns = ['package', 'order_group', 'key', 'master_key', 'role', 'bank', 'frame', 'width', 'height',
               'target_width', 'target_height', 'needs_mask', 'intro_only', 'runtime_gate', 'palette_id',
               'palette_status', 'indices_sha256', 'bitplane_sha256', 'target_png', 'target_mask']
    with (ART/'queue.csv').open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, columns, delimiter=';', extrasaction='ignore')
        writer.writeheader()
        writer.writerows(records)
    galleries(records)
    print(json.dumps(counts, ensure_ascii=False))


def galleries(records):
    by_bank = defaultdict(list)
    for r in records:
        by_bank[r['bank']].append(r)
    links = []
    for bank, entries in sorted(by_bank.items(), key=lambda p: p[0].lower()):
        entries.sort(key=lambda r: r['frame'])
        sheet = Image.new('RGB', (1200, 36+((len(entries)+7)//8)*180), '#242424')
        draw = ImageDraw.Draw(sheet)
        draw.text((8, 8), bank+' / originalreferanser / '+entries[0]['palette_status'], fill='white')
        for n, r in enumerate(entries):
            x, y = n % 8 * 150, 36+n//8*180
            im = Image.open(ART/r['original']['path']).convert('RGBA')
            factor = min(4, 136/im.width, 140/im.height)
            im = im.resize((max(1, round(im.width*factor)), max(1, round(im.height*factor))), Image.Resampling.NEAREST)
            sheet.paste(im, (x+(150-im.width)//2, y), im)
            draw.text((x+5, y+143), f"{r['frame']:03} {r['role']}", fill='white')
            draw.text((x+5, y+157), f"{r['width']}x{r['height']} -> {r['target_width']}x{r['target_height']}", fill='#cccccc')
        path = ART/'contact-sheets'/f'{bank}.png'
        save_png(path, sheet)
        links.append(f'<li><a href="{html.escape(relative(path))}">{html.escape(bank)}</a>: {len(entries)} ruter</li>')
    (ART/'index.html').write_text('<!doctype html><html lang="no"><meta charset="utf-8"><title>Moonstone figurkø</title>'
        '<style>body{background:#202020;color:#eee;font:16px sans-serif;max-width:1100px;margin:30px auto}a{color:#9cd}li{margin:7px}</style>'
        '<h1>Originalreferanser til figurproduksjon</h1><p>2040 ruter, 1779 selvstendige nytegninger. Dette er kildeeksport, ikke HD-kunst.</p>'
        '<p>Combat-preview er en arbeidsvisning. Den bekrefter ikke monsterfarger. Trollet skal være blått i faktisk originalscene.</p>'
        '<p><a href="queue.csv">Produksjonskø CSV</a> | <a href="queue.json">Kildekontrakter JSON</a> | <a href="README.md">Arbeidsmåte</a></p><ul>'
        + ''.join(links)+'</ul></html>', encoding='utf-8')


def check():
    queue = json.loads((ART/'queue.json').read_text())
    game = mf.Spill(str(ROOT/'Moonstonecd32-AMIGA.zip'))
    assert digest(ROOT/'Moonstonecd32-AMIGA.zip') == queue['source_zip_sha256']
    assert digest(ART/'source/order.csv') == queue['source_order_sha256']
    assert digest(ART/'source/manifest-at-preparation.json') == queue['source_manifest_sha256']
    for path, expected in queue['parser_sha256'].items():
        assert digest(ART/'source'/path) == expected, 'Frosset parser endret: '+path
    frames, _, _ = raw_frames(game)
    tested = []
    for r in queue['entries']:
        original = frames[r['key']]
        assert r['indices_sha256'] == sha(original['indices'])
        assert r['bitplane_sha256'] == sha(original['frame']['data'])
        assert digest(ART/'source/banks'/r['bank']) == r['source_bank']['sha256']
        with Image.open(ART/r['packed_original']['path']) as im:
            assert im.mode == 'P' and im.tobytes() == original['packed']
        palette_path = ART/'source/palettes'/f"{r['palette_id']}.json"
        assert digest(palette_path) == r['palette_file_sha256']
        palette = json.loads(palette_path.read_text())
        if palette['source'].startswith('data/'):
            assert sha(game.les(palette['source'])) == r['palette_source_sha256']
        elif r['palette_id']=='map-runtime':
            assert digest(ART/'source/map-frame2000.json') == r['palette_source_sha256']
        else:
            assert digest(ART/palette['source'])==r['palette_source_sha256']
        expected_pixels = bytes(v for i in original['indices'] for v in tuple(palette['colors'][i])+(255 if i else 0,))
        with Image.open(ART/r['original']['path']) as im:
            assert im.mode == 'RGBA' and im.tobytes() == expected_pixels, r['key']
        for field in ('original', 'nearest4x_reference', 'packed_original', 'silhouette', 'neutral_mask_template'):
            record = r[field]
            if record:
                assert digest(ART/record['path']) == record['sha256'], record['path']
        if r['needs_mask']:
            with Image.open(ART/r['neutral_mask_template']['path']) as im:
                assert im.tobytes() == neutral_mask(original['indices'], (r['width'], r['height']),r['live_palette_indices']).tobytes(), r['key']
        tested.append(dict(key=r['key'], indices_sha256=r['indices_sha256'], role=r['role']))
    assert len(tested) == 2040 and len({r['key'] for r in tested}) == 2040
    report = dict(status='passed', scope='Faktiske originalbanker, pakkede/utvidede indekser, eksportfiler og levende maskemaler. Ingen nytegning eller runtimegodkjenning.',
                  queue_sha256=digest(ART/'queue.json'), source_zip_sha256=queue['source_zip_sha256'],
                  routes=len(tested), masks=queue['counts']['mask_templates'], entries=tested)
    write_json(ART/'verification/source-check.json', report)
    print(json.dumps({k: v for k, v in report.items() if k != 'entries'}, ensure_ascii=False))


def observe():
    queue = json.loads((ART/'queue.json').read_text())
    directory = ROOT/'art/hd-program-support-2026-10-11/verification'
    names = ('intro-draws.json', 'ending-draws.json', 'program-support-test.json')
    snapshots = {name: (directory/name).read_bytes() for name in names}
    evidence = json.loads(snapshots['program-support-test.json'])
    assert evidence['status'] == 'passed' and evidence['zip_sha256'] == queue['source_zip_sha256']
    assert evidence['sources']['program'] == queue['source_program_sha256']
    revision = sha(b''.join(snapshots.values()))[:16]
    for name, data in snapshots.items():
        freeze(ART/'source/program-observations'/revision/name, data)
    lookup = {r['key'].lower(): r for r in queue['entries']}
    hits = defaultdict(list)
    for name in names[:2]:
        for draw in json.loads(snapshots[name]):
            key = f"{draw['fil'].lower()}/{draw['bilde']:03}.png"
            if key not in lookup:
                continue
            r = lookup[key]
            assert (draw['w'], draw['h']) == (r['width'], r['height']), r['key']
            hits[r['key']].append(dict(journey=name[:-11], **draw))
    entries = [dict(key=r['key'], observed=r['key'] in hits, draws=hits.get(r['key'], []))
               for r in queue['entries']]
    report = dict(status='source_observations_only_not_art_or_complete_journey_approval',
                  queue_sha256=digest(ART/'queue.json'), evidence_revision=revision,
                  evidence_sha256={name: sha(data) for name, data in snapshots.items()},
                  scope=evidence['scope'], observed_concrete_routes=len(hits),
                  observed_intro_routes=sum(r['intro_only'] and r['key'] in hits for r in queue['entries']),
                  total_intro_routes=queue['counts']['intro_routes'], entries=entries)
    write_json(ART/'runtime-observations.json', report)
    print(json.dumps({k: v for k, v in report.items() if k != 'entries'}, ensure_ascii=False))


def pack(key, candidate, art_record, gray_reference):
    queue = json.loads((ART/'queue.json').read_text())
    master = next(r for r in queue['entries'] if r['key'].lower() == key.lower())
    assert master['role'] == 'redraw', 'Pakk den selvstendige masterruten: '+master['master_key']
    data = candidate.read_bytes()
    provenance = json.loads(art_record.read_text())
    assert provenance['key'] == master['key'] and provenance['candidate_sha256'] == sha(data)
    assert provenance['source_indices_sha256'] == master['indices_sha256']
    assert provenance['authoring_method'] == 'individual_redraw', 'Oppskalering er ikke separat nytegning'
    assert provenance.get('geometry_gate_passed') is not False, 'Avvist geometridiagnose er ikke en leveranse'
    with Image.open(candidate) as image:
        assert image.mode == 'RGBA' and image.size == (master['target_width'], master['target_height']), 'Lever ubeskåret RGBA i eksakt 4x-mål'
        image.load()
        original = Image.open(ART/master['nearest4x_reference']['path']).convert('RGBA')
        assert image.tobytes() != original.tobytes(), 'Kandidaten er bare originalens nærmeste-nabo-forstørrelse'
        px = image.load()
        assert any(len({px[x+dx,y+dy] for dx in range(4) for dy in range(4)})>1
                   for y in range(0,image.height,4) for x in range(0,image.width,4)), 'Kandidaten er bare 4x pikselblokker, ogsaa med endret palett'
        alpha = image.getchannel('A')
        expected_alpha = Image.open(ART/master['silhouette']['path']).resize(image.size, Image.Resampling.NEAREST)
        a, b = alpha.tobytes(), expected_alpha.tobytes()
        intersection = sum(x >= 128 and y >= 128 for x, y in zip(a, b))
        union = sum(x >= 128 or y >= 128 for x, y in zip(a, b))
        assert union and intersection/union >= .90, 'Silhuetten avviker for mye; rett kandidaten før pakking'
        silhouette_iou = intersection/union
    pack_dir = ART/'packs'/master['key'].replace('.png', '')/sha(data)[:16]
    freeze(pack_dir/'art-record.json', art_record.read_bytes())
    outputs = []
    master_mask = None
    if master['needs_mask']:
        mask_path = pack_dir/'master.mask.png'
        # Normaliser farget kunst mot rutens faktisk valgte scenepalett, ikke
        # den frosne indekseksportens generiske preview-farger.
        mask_source=Image.open(ART/master['packed_original']['path']).copy()
        palette=json.loads((ART/'source/palettes'/f"{master['palette_id']}.json").read_text())
        colors=[v for rgb in palette['colors'] for v in rgb]
        mask_source.putpalette(colors+[0]*(768-len(colors)))
        source_path=pack_dir/'mask-source'/master['key']
        source_path.parent.mkdir(parents=True,exist_ok=True);mask_source.save(source_path,optimize=True)
        order.lag_maske(str(source_path), str(mask_path), str(candidate),
                        str(ROOT/'Moonstonecd32-AMIGA.zip'), gray_reference)
        master_mask = Image.open(mask_path).convert('RGBA')
        live=set(master['live_palette_indices'])
        master_mask.putdata([pixel if pixel[0]-1 in live else (0,0,0,255) for pixel in master_mask.getdata()])
    for r in queue['entries']:
        if r['master_key'] != master['key']:
            continue
        target = pack_dir/'hd'/r['key']
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(candidate, target)
        outputs.append(dict(path='hd/'+r['key'], sha256=digest(target), bytes=target.stat().st_size))
        if r['needs_mask']:
            assert master_mask is not None
            mask = master_mask.copy()
            mapping = {int(a)+1: b+1 for a, b in r['index_remap'].items()}
            mask.putdata([(mapping.get(red, red), green, blue, alpha) if red else (red, green, blue, alpha)
                          for red, green, blue, alpha in mask.getdata()])
            target_mask = target.with_suffix('.mask.png')
            mask.save(target_mask, optimize=True)
            outputs.append(dict(path='hd/'+r['key'].replace('.png', '.mask.png'), sha256=digest(target_mask), bytes=target_mask.stat().st_size))
    report = dict(status='packed_candidate_not_activated', key=master['key'], candidate_sha256=sha(data),
                  source_indices_sha256=master['indices_sha256'], queue_sha256=digest(ART/'queue.json'),
                  silhouette_iou=silhouette_iou, authoring_evidence='supplied_record_not_automatic_visual_approval',
                  visual_checks=provenance.get('visual_checks', {}), runtime_gate=master['runtime_gate'], files=outputs)
    write_json(pack_dir/'packing.json', report)
    print(json.dumps({k: v for k, v in report.items() if k != 'files'}, ensure_ascii=False))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    commands = ap.add_subparsers(dest='command', required=True)
    commands.add_parser('export')
    commands.add_parser('check')
    commands.add_parser('observe')
    p = commands.add_parser('pack')
    p.add_argument('--key', required=True)
    p.add_argument('--candidate', required=True, type=Path)
    p.add_argument('--art-record', required=True, type=Path)
    p.add_argument('--gray-reference', type=int)
    args = ap.parse_args()
    if args.command == 'export':
        export()
    elif args.command == 'check':
        check()
    elif args.command == 'observe':
        observe()
    else:
        pack(args.key, args.candidate, args.art_record, args.gray_reference)


if __name__ == '__main__':
    main()
