#!/usr/bin/env python3
"""
pakk.py - setter sammen nettleserversjonen til en HTML-fil.

    python3 web/pakk.py web/build/moonstone-core.js web/build/moonstone.html

Kjernen (WebAssembly innebygd i moonstone-core.js), bibliotekene i web/vendor
og kildene i web/src legges inn i web/src/index.html. Filen virker fra disk og
paa GitHub Pages uten noe annet.
"""
import os
import sys
import json
import hashlib
import shutil
import base64
from pathlib import Path

HER = os.path.dirname(os.path.abspath(__file__))
APP = ['sprak.js', 'core.js', 'audio.js', 'render.js', 'hd.js', 'scenes.js', 'input.js', 'store.js', 'net.js', 'rooms.js', 'grafikk.js', 'app.js']
VENDOR = ['three.min.js', 'peerjs.min.js', 'mqtt.min.js']


def les(sti):
    with open(sti, encoding='utf-8') as f:
        return f.read()


def trygg(js):
    # "</script" inne i et skript ville avsluttet taggen for tidlig
    return js.replace('</script', '<\\/script')


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    kjerne, ut = sys.argv[1], sys.argv[2]
    html = les(os.path.join(HER, 'src', 'index.html'))
    stil = les(os.path.join(HER, 'src', 'style.css'))
    stil = stil.replace('%%HD_FONT%%', base64.b64encode((Path(HER) / 'hd/fonts/UncialAntiqua-Regular.ttf').read_bytes()).decode('ascii'))
    vendor = '\n;\n'.join(trygg(les(os.path.join(HER, 'vendor', f))) for f in VENDOR)
    hd = Path(HER) / 'hd'
    manifest = json.loads((hd / 'manifest.json').read_text())
    assert manifest['schema'] == 1 and manifest['images'] == sum(f['path'].endswith('.png') for f in manifest['files'])
    assert len({f['path'] for f in manifest['files']}) == len(manifest['files'])
    for f in manifest['files']:
        path = hd / f['path']
        assert path.resolve().is_relative_to(hd.resolve()) and path.is_file()
        raw = path.read_bytes()
        assert len(raw) == f['bytes'] and hashlib.sha256(raw).hexdigest() == f['sha256'], path
    app = '\n'.join('/* ---- %s ---- */\n%s' % (f, trygg(les(os.path.join(HER, 'src', f)))) for f in APP)
    app = app.replace('%%HD_MANIFEST%%', json.dumps(manifest, ensure_ascii=False, separators=(',', ':')))
    html = html.replace('%%STIL%%', stil)
    html = html.replace('%%VENDOR%%', vendor)
    html = html.replace('%%KJERNE%%', trygg(les(kjerne)))
    html = html.replace('%%APP%%', app)
    os.makedirs(os.path.dirname(os.path.abspath(ut)), exist_ok=True)
    with open(ut, 'w', encoding='utf-8') as f:
        f.write(html)
    # Nettutgaven laster bildene ved behov. Lokale filer beholder originalgrafikk.
    target = Path(ut).resolve().parent / 'hd'
    for p in hd.rglob('*'):
        if p.is_file():
            dest = target / p.relative_to(hd)
            dest.parent.mkdir(parents=True, exist_ok=True)
            if p.resolve() != dest.resolve():
                shutil.copyfile(p, dest)
    print('%s: %d kB' % (ut, os.path.getsize(ut) // 1024))


if __name__ == '__main__':
    main()
