#!/usr/bin/env python3
"""Fullfoer den24. kildeekte kartporten med eksisterende HD-materiale.

Standardkommandoen validerer. --activate legger til map-icons/026 uten aa
endre eksisterende ikonkontrakter eller bildefiler. Originalspillet endres ikke.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path

import moonfiles as mf
from hd_ikoner_bygg import map_port_expected, map_shapes

ROOT = Path(__file__).resolve().parents[1]
sha = lambda data: hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--activate', action='store_true')
    args = parser.parse_args()
    game = mf.Spill(str(ROOT/'Moonstonecd32-AMIGA.zip'))
    icons_path,manifest_path = ROOT/'web/hd/icons.json',ROOT/'web/hd/manifest.json'
    icons,manifest = json.loads(icons_path.read_text()),json.loads(manifest_path.read_text())
    previous = copy.deepcopy(icons['entries'])
    files = {e['path']:e for e in manifest['files']}
    for name,e in files.items():
        data = (ROOT/'web/hd'/name).read_bytes()
        assert len(data)==e['bytes'] and sha(data)==e['sha256'],name
    master = next(e for e in previous if e['key']=='map-icons/000')
    px,expected,source = map_port_expected(game,24,24)
    assert master['indices_sha256']==sha(bytes(px))
    assert (master['width'],master['height'],master['render_mode'])==(9,5,'raster')
    assert len([s for s in map_shapes() if s[4]=='bar'])==24
    # Uavhengig Original-WASM-fangst3925: to transparente hjørner bevarer17/20.
    assert sha(bytes(expected))=='f3b7b90d3a1a66546037c4bcdeff3c9a241b18d68b47d9a4fb1832eb4b1e356c'
    entry = copy.deepcopy(master)
    entry.update(key='map-icons/026',rect=[24,24,33,29],expected=expected,source=source)
    png = (ROOT/'web/hd/map-icons/000.png').read_bytes()
    existing = next((e for e in previous if e['key']==entry['key']),None)
    if existing:
        assert existing==entry,'Annen eksisterende026-kontrakt'
        assert (ROOT/'web/hd/map-icons/026.png').read_bytes()==png
        assert files['map-icons/026.png']['sha256']==sha(png)
    elif args.activate:
        icons['entries'].append(entry)
        icons['entries'].sort(key=lambda e:e['key'])
        assert all(e==next(m for m in icons['entries'] if m['key']==e['key']) for e in previous)
        new_icons = (json.dumps(icons,ensure_ascii=False,separators=(',',':'))+'\n').encode()
        changed={'icons.json':new_icons,'map-icons/026.png':png}
        manifest['files']=[e for e in manifest['files'] if e['path'] not in changed]
        for name,data in changed.items():
            manifest['files'].append({'path':name,'bytes':len(data),'sha256':sha(data),'kind':'base'})
        manifest['files'].sort(key=lambda e:e['path'])
        manifest['images']=sum(e['path'].endswith('.png') for e in manifest['files'])
        for name,data in changed.items():
            target=ROOT/'web/hd'/name
            temporary=target.with_suffix(target.suffix+'.tmp')
            temporary.write_bytes(data)
            temporary.replace(target)
        temporary=manifest_path.with_suffix('.json.tmp')
        temporary.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
        temporary.replace(manifest_path)
    else:
        raise SystemExit('Kildekontroll bestaar;026 mangler. Bruk --activate for avtalt aktivering.')
    current={e['path']:e for e in manifest['files']}
    assert all(current[n]==e for n,e in files.items() if n!='icons.json')
    print(json.dumps({'status':'passed','gate_routes':24,'icon_contracts':len(icons['entries']),
        'reused_png_sha256':sha(png),'manifest_sha256':sha(manifest_path.read_bytes()),
        'images':manifest['images'],'files':len(manifest['files']),
        'original_and_existing_pngs_unchanged':True,'scope':'Kilde-/filkontroll; faktisk visning proeves separat.'}))


if __name__=='__main__':
    main()
