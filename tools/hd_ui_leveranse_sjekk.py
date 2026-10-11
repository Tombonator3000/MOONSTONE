#!/usr/bin/env python3
"""Ny leveranseintegritet mot main før UI-/bakgrunnsoppfølgingen.

Kontrollerer faktiske filer og metadata, uten å gjenbruke eldre testkvitteringer.
Dette er filintegritet, ikke en erstatning for visuell kontroll eller runtimeprøver.
"""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import subprocess

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def fil_sha(sti):
    h = hashlib.sha256()
    with sti.open('rb') as f:
        for del_ in iter(lambda: f.read(1024 * 1024), b''):
            h.update(del_)
    return h.hexdigest()


def git_bytes(ref, sti):
    return subprocess.check_output(['git', 'show', '%s:%s' % (ref, sti)], cwd=ROOT)


def git_sha(ref, sti):
    p = subprocess.Popen(['git', 'show', '%s:%s' % (ref, sti)], cwd=ROOT,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    h = hashlib.sha256()
    for del_ in iter(lambda: p.stdout.read(1024 * 1024), b''):
        h.update(del_)
    p.stdout.close()
    feil = p.stderr.read().decode()
    p.stderr.close()
    assert p.wait() == 0, feil
    return h.hexdigest()


def serialisert(data):
    # Samme serialisering på begge sider; bevarer også feltrekkefølgen.
    return json.dumps(data, ensure_ascii=False, separators=(',', ':')).encode()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--baseline', default='04f0c8e', help='Frosset main før denne leveransen.')
    ap.add_argument('--output', default='art/hd-ui-followup-2026-10-11/verification/leveranse-integritet.json')
    args = ap.parse_args()
    baseline = subprocess.check_output(['git', 'rev-parse', args.baseline+'^{commit}'],
                                       cwd=ROOT, text=True).strip()
    hd = ROOT / 'web/hd'
    manifest_sti = hd / 'manifest.json'
    manifest_bytes = manifest_sti.read_bytes()
    manifest = json.loads(manifest_bytes)
    gammel_manifest = json.loads(git_bytes(baseline, 'web/hd/manifest.json'))
    gammel_ikon = json.loads(git_bytes(baseline, 'web/hd/icons.json'))
    ikon_bytes = (hd / 'icons.json').read_bytes()
    ikoner = json.loads(ikon_bytes)
    nye_filer = {f['path']: f for f in manifest['files']}
    gamle_filer = {f['path']: f for f in gammel_manifest['files']}
    assert len(nye_filer) == len(manifest['files']), 'Duplisert filsti i manifestet'
    assert manifest['images'] == sum(f['path'].endswith('.png') for f in manifest['files'])
    manifest_kontroller = []
    for r in manifest['files']:
        rel = Path(r['path'])
        assert not rel.is_absolute() and '..' not in rel.parts, 'Ugyldig pakkesti'
        sti = hd / rel
        assert sti.is_file(), 'Mangler %s' % rel
        faktisk = fil_sha(sti)
        assert faktisk == r['sha256'], 'Manifesthash avviker: %s' % rel
        assert sti.stat().st_size == r['bytes'], 'Manifeststørrelse avviker: %s' % rel
        rad = dict(path=r['path'], sha256=faktisk, bytes=r['bytes'])
        if rel.suffix == '.png':
            with Image.open(sti) as im:
                rad['width'], rad['height'] = im.size
                im.verify()
        manifest_kontroller.append(rad)

    gamle_bg = [r for r in gammel_manifest['files'] if r.get('kind') == 'background']
    assert len(gamle_bg) == 75, 'Baseline er ikke den avtalte 75-bakgrunnspakken'
    for r in gamle_bg:
        assert nye_filer.get(r['path']) == r, 'Eldre bakgrunnsmetadata er endret: %s' % r['path']
        # Alle SHA-er er allerede målt fra dagens filer i løkken over.
    gamle_scener = {s['id']: s for s in gammel_manifest['scenes']}
    nye_scener = {s['id']: s for s in manifest['scenes']}
    for ident, s in gamle_scener.items():
        assert nye_scener.get(ident) == s, 'Eldre scenekontrakt er endret: %s' % ident

    gamle_raster = {e['key']: e for e in gammel_ikon['entries'] if e.get('render_mode') == 'raster'}
    nye_ikoner = {e['key']: e for e in ikoner['entries']}
    assert len(gamle_raster) == 102, 'Baseline er ikke den avtalte 102-rasterpakken'
    assert len(nye_ikoner) == len(ikoner['entries']), 'Duplisert ikonkontrakt'
    bevarte_raster = []
    bevarte_png = set()
    for key, e in sorted(gamle_raster.items()):
        assert key in nye_ikoner, 'Eldre rasterikon mangler: %s' % key
        original = serialisert(e)
        assert serialisert(nye_ikoner[key]) == original, 'Eldre rastermetadata er endret: %s' % key
        keys = {key} | {v['key'] for v in e.get('palette_variants', [])}
        for png_key in keys:
            rel = png_key+'.png'
            assert rel in gamle_filer and nye_filer.get(rel) == gamle_filer[rel], 'Eldre raster-PNG er endret: %s' % rel
            bevarte_png.add(rel)
        bevarte_raster.append(dict(key=key, metadata_sha256=sha(original), png=sorted(k+'.png' for k in keys)))
    for bank, h in gammel_ikon['banks'].items():
        assert ikoner['banks'].get(bank) == h, 'Eldre originalbank er endret: %s' % bank

    # Hele den inncheckede porten, ikke bare noen utvalgte emulatorkildefiler.
    port_filer = subprocess.check_output(['git', 'ls-tree', '-r', '-z', '--name-only', baseline,
                                          '--', 'port'], cwd=ROOT).decode().rstrip('\0').split('\0')
    assert port_filer and all(s.startswith('port/') for s in port_filer)
    beskyttede = []
    for rel in ['Moonstonecd32-AMIGA.zip', 'tools/moonfiles.py', 'tools/gfx.py'] + port_filer:
        sti = ROOT / rel
        assert sti.is_file(), 'Beskyttet original-/kjernefil mangler: %s' % rel
        h = fil_sha(sti)
        assert h == git_sha(baseline, rel), 'Beskyttet original-/kjernefil er endret: %s' % rel
        beskyttede.append(dict(path=rel, sha256=h))
    nye_portfiler = subprocess.check_output(['git', 'ls-files', '-z', '--', 'port'], cwd=ROOT).decode().rstrip('\0').split('\0')
    assert set(nye_portfiler) == set(port_filer), 'Portens inncheckede filutvalg er endret'

    # Kvitteringen binder kontrollen til nåværende manifest, metadata og renderer.
    kode = {str(p.relative_to(ROOT)): fil_sha(p) for p in sorted((ROOT / 'web/src').glob('*.js'))}
    assert manifest_sti.read_bytes() == manifest_bytes, 'Manifestet ble endret under prøven'
    assert (hd / 'icons.json').read_bytes() == ikon_bytes, 'Ikonmetadata ble endret under prøven'
    rapport = dict(
        status='passed', checked_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        baseline_commit=baseline, head_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        scope='Fersk filintegritet. Visuell QA og runtime dokumenteres i egne prøver.',
        manifest_sha256=sha(manifest_bytes), icons_sha256=sha(ikon_bytes), renderer_sha256=kode,
        counts=dict(manifest_files=len(manifest_kontroller), png=manifest['images'],
                    active_backgrounds=sum(r.get('kind') == 'background' for r in manifest['files']),
                    preserved_backgrounds=len(gamle_bg), preserved_scene_contracts=len(gamle_scener),
                    preserved_raster_contracts=len(bevarte_raster), preserved_raster_png=len(bevarte_png),
                    protected_original_and_core_files=len(beskyttede)),
        manifest_files=manifest_kontroller, preserved_backgrounds=[r['path'] for r in gamle_bg],
        preserved_raster=bevarte_raster, protected_original_and_core_files=beskyttede)
    output = Path(args.output)
    if not output.is_absolute():
        output = ROOT / output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(rapport, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(dict(status=rapport['status'], counts=rapport['counts'], proof=str(output)), ensure_ascii=False))


if __name__ == '__main__':
    main()
