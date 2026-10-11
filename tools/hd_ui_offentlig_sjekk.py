#!/usr/bin/env python3
"""Kontroller den publiserte UI-/bakgrunnspakken mot lokale filer og frosset main.

Kjøres etter Pages-deploy. Lagrer offentlig HTML og byte-/hashbevis;
runtime og visuell kontroll utføres separat.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
from urllib.parse import quote
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
BASELINE = '04f0c8ead75a1c423841d07c3e30ff1cebafb881'
OUTPUT = 'art/hd-ui-backgrounds-2026-10-11/verification/public/public-assets.json'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def filkart(manifest):
    rows = manifest['files']
    result = {r['path']: r for r in rows}
    assert len(result) == len(rows), 'Duplisert filsti i manifestet'
    for path in result:
        rel = PurePosixPath(path)
        assert path and not rel.is_absolute() and '..' not in rel.parts, 'Ugyldig pakkesti: '+path
    return result


def html_modul(page, name):
    marker = ('/* ---- '+name+' ---- */\n').encode()
    assert page.count(marker) == 1, 'HTML mangler entydig modul: '+name
    start = page.index(marker)+len(marker)
    end = page.index(b'\n/* ---- ', start)
    return page[start:end]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--url', default='https://tombonator3000.github.io/MOONSTONE/')
    ap.add_argument('--output', default=OUTPUT)
    args = ap.parse_args()
    base = args.url.rstrip('/')+'/'
    output = Path(args.output)
    if not output.is_absolute():
        output = ROOT/output
    output.parent.mkdir(parents=True, exist_ok=True)
    report = dict(status='running', url=base, baseline_commit=BASELINE,
                  checked_at_utc=datetime.now(timezone.utc).isoformat(),
                  scope='Offentlige byte-/hashbevis og innebygd kode. Runtime og visuell QA kontrolleres separat.')
    try:
        hd = ROOT/'web/hd'
        local_manifest = (hd/'manifest.json').read_bytes()
        manifest = json.loads(local_manifest)
        old_bytes = subprocess.check_output(['git', 'show', BASELINE+':web/hd/manifest.json'], cwd=ROOT)
        previous, current = filkart(json.loads(old_bytes)), filkart(manifest)
        added = sorted(set(current)-set(previous))
        changed = sorted(p for p in current.keys() & previous.keys() if current[p] != previous[p])
        removed = sorted(set(previous)-set(current))
        paths = sorted(set(added+changed) | {'icons.json', 'text.json'})
        report['manifest_diff'] = dict(added=added, changed=changed, removed=removed)
        snapshot = {'web/hd/manifest.json': local_manifest}
        for path in paths:
            data = (hd/path).read_bytes()
            expected = current[path]
            assert len(data) == expected['bytes'] and sha(data) == expected['sha256'], 'Lokalt manifest avviker: '+path
            snapshot['web/hd/'+path] = data
        code = {}
        for name in ('render.js', 'hd.js', 'scenes.js'):
            rel = 'web/src/'+name
            code[name] = (ROOT/rel).read_bytes()
            snapshot[rel] = code[name]

        # En egen forespørselsnøkkel unngår å gjenbruke eldre Pages-svar.
        request_key = quote(report['checked_at_utc'], safe='')

        def fetch(path):
            request = Request(base+quote(path, safe='/')+'?hd_check='+request_key,
                              headers={'Cache-Control': 'no-cache', 'Pragma': 'no-cache'})
            with urlopen(request, timeout=30) as response:
                return response.read()

        public_manifest = fetch('hd/manifest.json')
        assert public_manifest == local_manifest, 'Offentlig manifest er ikke siste lokale pakke'
        page = fetch('index.html')
        frozen_html = output.parent/'index.html'
        frozen_html.write_bytes(page)
        report['html'] = dict(path=str(frozen_html.relative_to(ROOT)) if frozen_html.is_relative_to(ROOT) else str(frozen_html),
                              bytes=len(page), sha256=sha(page))
        compact_manifest = json.dumps(manifest, ensure_ascii=False, separators=(',', ':')).encode()
        report['embedded_modules'] = {}
        for name, source in code.items():
            expected = source.replace(b'%%HD_MANIFEST%%', compact_manifest).replace(b'</script', b'<\\/script')
            embedded = html_modul(page, name)
            assert embedded == expected, 'Offentlig HTML har eldre kode eller manifest: '+name
            report['embedded_modules'][name] = dict(source_sha256=sha(source), embedded_sha256=sha(embedded))
        report['manifest_sha256'] = sha(public_manifest)
        report['embedded_manifest_sha256'] = sha(compact_manifest)

        def check(path):
            data = fetch('hd/'+path)
            expected = current[path]
            digest = sha(data)
            assert len(data) == expected['bytes'] and digest == expected['sha256'], 'Offentlig fil avviker: '+path
            return dict(path=path, bytes=len(data), sha256=digest,
                        change='added' if path in added else 'changed' if path in changed else 'required',
                        baseline_sha256=previous.get(path, {}).get('sha256'))

        with ThreadPoolExecutor(max_workers=4) as pool:
            report['files'] = list(pool.map(check, paths))
        for rel, original in snapshot.items():
            assert (ROOT/rel).read_bytes() == original, 'Lokal fil ble endret under prøven: '+rel
        report['counts'] = dict(manifest_files=len(current), manifest_png=manifest['images'],
                                checked_files=len(paths)+1,
                                checked_png=sum(p.endswith('.png') for p in paths),
                                added_files=len(added), changed_files=len(changed), removed_files=len(removed))
        report['status'] = 'passed'
    except Exception as error:
        report['status'] = 'failed'
        report['error'] = str(error)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k not in ('files', 'manifest_diff', 'embedded_modules')}, ensure_ascii=False))
    return 0 if report['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
