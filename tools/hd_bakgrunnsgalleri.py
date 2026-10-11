#!/usr/bin/env python3
"""Lag sporbar oversikt og original/HD-galleri over aktive bakgrunner."""
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / 'art/hd-all-locations-2026-10-11'


def main():
    manifest = json.loads((ROOT/'web/hd/manifest.json').read_text())
    plan = json.loads((ROOT/'art/photoreal/production-plan-2026-10-03.json').read_text())
    new = json.loads((ART/'assets.json').read_text())['assets']
    rows = []
    for f in manifest['files']:
        if f['kind'] != 'background':
            continue
        route = f['path']
        candidates = [a for a in plan['assets'] if route in
                      (a.get('routing', {}).get('hash_path'), a.get('routing', {}).get('hash_candidate'))]
        if not candidates:
            registered = next(r for r in new if r['route'] == route)
            candidates = [a for a in plan['assets'] if a['source'].get('archive_file') == 'data/'+registered['source']]
        assert candidates, route
        a = candidates[0]
        source = a['source']['archive_file']
        frame = a['source'].get('frame', 0)
        ref = ROOT/a['source']['png_path']
        if a['kind'] == 'runtime_background':
            ref = ROOT/'art/photoreal/references/runtime_background'/(Path(source).name+'.png')
        assert ref.is_file(), str(ref)
        target = ART/'references'/('gallery-'+Path(route).name)
        shutil.copyfile(ref, target)
        generated = next((r for r in new if r['route'] == route), None)
        scenes = [s['id'] for s in manifest['scenes'] if s['hash'] == Path(route).stem]
        assert hashlib.sha256((ROOT/'web/hd'/route).read_bytes()).hexdigest() == f['sha256']
        rows.append(dict(source=source, frame=frame, kind=a['kind'], route=route,
                         scenes=scenes, reference='references/'+target.name,
                         hd='../../web/hd/'+route, sha256=f['sha256'],
                         new_in_delivery=generated is not None,
                         prompt=generated['prompt'] if generated else None))
    assert len(rows) == 75
    assert sum(r['kind'] == 'runtime_background' for r in rows) == 56
    rows.sort(key=lambda r: (r['kind'] == 'runtime_background', r['source']))
    coverage = dict(schema=1, active_backgrounds=75, combat_backgrounds=56,
                    new_images=35, new_source_connections=36, rows=rows,
                    scope='Stedsskjermer og alle 56 sammensatte kampvarianter. Ikke full konvertering av flisbanker, rulleanimasjoner, rullende sluttsekvenser eller figurruter.')
    (ART/'coverage.json').write_text(json.dumps(coverage, ensure_ascii=False, indent=2)+'\n')
    html = '''<!doctype html><html lang="nb"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Moonstone bakgrunner: Original / HD</title>
<style>body{background:#171b1a;color:#eee;font:16px system-ui;margin:24px auto;max-width:1200px;padding:0 16px}a{color:#a9dbbd}article{margin:24px 0;padding:16px;background:#252c28}h2{font-size:18px}.pair{display:grid;grid-template-columns:1fr 1fr;gap:8px}img{width:100%;aspect-ratio:8/5;object-fit:contain;background:#000}.original{image-rendering:pixelated}figure{margin:0}button,input,select{font:inherit;padding:8px;margin:4px}small{overflow-wrap:anywhere}@media(max-width:600px){.pair{grid-template-columns:1fr}}</style>
<h1>Moonstone: aktive HD-bakgrunner</h1><p>75 bakgrunner, inkludert alle 56 kampvarianter. 35 bilder er lagt til i denne leveransen. Originalen står til venstre. HD-materialene følger originalens motiv og oppsett; små runetegn er ikke garantert pikselidentiske. Bevegelige figurer og dialog tegnes separat i spillet.</p>
<p>Maths HD-råbakgrunn inneholder bare arkitekturen. Originalfiguren og animasjonen tegnes foran den i spillet. <a href="verification/math/math-animated-hd.png">Faktisk Math-besøk</a>. <a href="verification/combat/combat-test.json">Kampkontroll</a> | <a href="verification/places/places-test.json">Stedskontroll</a> | <a href="coverage.json">Kildeoversikt</a></p>
<input id="search" aria-label="Søk" placeholder="Søk sted eller fil"><select id="filter" aria-label="Utvalg"><option value="all">Alle</option><option value="new">Nye bilder</option><option value="combat">Kamp</option><option value="place">Stedsskjermer</option></select><p id="count"></p><main></main>
<script>const rows=__DATA__;function draw(){const q=document.querySelector('#search').value.toLowerCase(),f=document.querySelector('#filter').value,main=document.querySelector('main');main.replaceChildren();const selected=rows.filter(r=>(r.source+' '+r.scenes.join(' ')).toLowerCase().includes(q)&&(f==='all'||f==='new'&&r.new_in_delivery||f==='combat'&&r.kind==='runtime_background'||f==='place'&&r.kind!=='runtime_background'));document.querySelector('#count').textContent=selected.length+' bakgrunner';for(const r of selected){const a=document.createElement('article'),h=document.createElement('h2');h.textContent=r.scenes.join(' / ')||r.source;a.append(h);const small=document.createElement('small');small.textContent=r.source+' | '+r.route+(r.new_in_delivery?' | Ny i denne leveransen':' | Tidligere aktiv');a.append(small);const pair=document.createElement('div');pair.className='pair';for(const [src,label]of[[r.reference,'Original'],[r.hd,'HD']]){const fig=document.createElement('figure'),im=document.createElement('img'),cap=document.createElement('figcaption');im.src=src;im.alt=label+' '+r.source;im.loading='lazy';if(label==='Original')im.className='original';cap.textContent=label;fig.append(im,cap);pair.append(fig)}a.append(pair);if(r.prompt){const link=document.createElement('a');link.href=r.prompt;link.textContent='Prompt';a.append(link)}main.append(a)}}document.querySelector('#search').oninput=draw;document.querySelector('#filter').onchange=draw;draw();</script></html>'''
    (ART/'index.html').write_text(html.replace('__DATA__', json.dumps(rows, ensure_ascii=False)))
    print('75 aktive bakgrunner katalogisert, 56 kampvarianter og 19 øvrige bilder.')


if __name__ == '__main__':
    main()
