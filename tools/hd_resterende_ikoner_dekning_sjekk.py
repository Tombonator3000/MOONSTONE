#!/usr/bin/env python3
"""Bind bestaatte CEL-fixturer til sluttpakken uten aa gjenta uendrede ruter."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/'art/hd-remaining-icons-2026-10-11'
OUT=ART/'research/runtime'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    return json.loads(path.read_text())


def contract_sha(meta):
    return sha(json.dumps(meta,sort_keys=True,separators=(',',':')).encode())


def proof(row):
    keys=('key','raw_sha256','source_sha256','record_sha256','prompt_sha256','packed_sha256')
    return {**{k:row[k] for k in keys},'variants':[{k:v[k] for k in ('id','key','raw_sha256','packed_sha256')} for v in row.get('variants',[])]}


def main():
    candidate=read(ART/'candidate-icons.json')
    final={m['key']:m for m in candidate['entries']}
    final_rows={r['key']:r for r in read(ART/'packing-report.json')['assets']}
    report={'scope':'Alle nye statiske KI-/MI-CEL-ruter. Originalkildene brukes som eksplisitte frontendfixturer; dette er ikke naturlig kjoep/bruk av hver gjenstand.',
            'candidate_icons_sha256':sha((ART/'candidate-icons.json').read_bytes()),'contracts':len(final),'assets':[],'checks':0,'source_reports':[]}
    old_icons=OUT/'tested-snapshots/98-icons.json'
    old_rows={r['key']:r for r in read(OUT/'tested-snapshots/98-packing-report.json')['assets']}
    old_meta={m['key']:m for m in read(old_icons)['entries']}
    runtime=read(OUT/'tested-snapshots/98-runtime-contract.json')
    current={name:sha((ROOT/name).read_bytes()) for name in ('web/src/render.js','web/src/scenes.js')}
    assert current['web/src/scenes.js']==runtime['web/src/scenes.js'],'SceneHd endret etter opprinnelig test'
    transition=read(OUT/'variant-import-verification/variant-import-test.json')
    assert transition['status']=='passed' and not transition['errors']
    assert transition['source_before_render_sha256']==runtime['web/src/render.js']
    assert transition['source_after_render_sha256']==current['web/src/render.js']
    text=(ROOT/'web/src/render.js').read_text()
    before=text.replace('if (t.ikonPalett!==key || t.ikonVariantBilde!==bilde) {','if (t.ikonPalett!==key) {').replace('t.ikonLys=lys;t.ikonPalett=key;t.ikonVariantBilde=bilde;return true;','t.ikonLys=lys;t.ikonPalett=key;return true;')
    assert sha(before.encode())==runtime['web/src/render.js'],'Runtimeendringen er stoerre enn de to avgrensede cachelinjene'
    report['production_code_sha256']=current
    report['tested_before_cache_fix_sha256']={name:runtime[name] for name in current}
    report['limited_runtime_transition']={'report':'art/hd-remaining-icons-2026-10-11/research/runtime/variant-import-verification/variant-import-test.json','checks':len(transition['checks']),'change':'Samme kildepalett repainter baseteksturen hvis valgt variantteksturobjekt endres. De to linjene endrer ingen kilde-, indeks-, geometri- eller palettgodkjenning. Alle 62 CEL-fixturer gjenbrukes med dette konkrete importovergangsbeviset.'}
    aggregate=read(OUT/'final-cel-verification/cel-fixtures-batches-test.json')
    assert aggregate['status']=='passed' and aggregate['candidate_icons_sha256']==sha(old_icons.read_bytes())
    inputs=[(ROOT/b['report'],old_meta,old_rows,sha(old_icons.read_bytes())) for b in aggregate['batches']]
    delta=OUT/'additional-toads-verification/inventory-fixtures-test.json'
    delta_icons=OUT/'tested-snapshots/102-pre-water-icons.json'
    delta_meta={m['key']:m for m in read(delta_icons)['entries']}
    delta_rows={r['key']:r for r in read(OUT/'tested-snapshots/102-pre-water-packing-report.json')['assets']}
    inputs.append((delta,delta_meta,delta_rows,sha(delta_icons.read_bytes())))
    done=set()
    for file,metas,rows,snapshot_sha in inputs:
        result=read(file)
        assert result['status']=='passed' and not result['errors'] and result['candidate_icons_sha256']==snapshot_sha,file
        report['source_reports'].append(str(file.relative_to(ROOT)))
        report['checks']+=len(result['checks'])
        for tested in result['assets']:
            key=tested['key'];assert key not in done,key+' duplikattest';done.add(key)
            assert metas[key]==final[key],key+' metadata endret etter testen'
            row=rows[key];assert proof(row)==proof(final_rows[key]),key+' bilde-/kildedata endret etter testen'
            for field in ('raw','source','record','prompt'):
                assert sha((ART/row[field]).read_bytes())==row[field+'_sha256'],key+' '+field
            assert sha((ART/'packed'/f'{key}.png').read_bytes())==row['packed_sha256'],key
            for v in row.get('variants',[]):
                assert sha((ART/v['raw']).read_bytes())==v['raw_sha256'],v['key']
                assert sha((ART/'packed'/f"{v['key']}.png").read_bytes())==v['packed_sha256'],v['key']
            assert len(tested['samples'])==2 and {s['mirror'] for s in tested['samples']}=={False,True}
            for sample in tested['samples']:
                name=key.replace('/','-')+('-mirrored' if sample['mirror'] else '')
                for mode in ('original','hd'):
                    assert sha((file.parent/f'{name}-{mode}.png').read_bytes())==sample[mode+'_sha256'],key+' '+mode
                assert sample['original_sha256']!=sample['hd_sha256'],key+' uendret HD'
            report['assets'].append({**proof(row),'source_contract_sha256':contract_sha(final[key]),'test_report':str(file.relative_to(ROOT)),'sample_count':len(tested['samples']),'generated_palette_samples':len(tested.get('palette_samples',[]))})
    expected={key for key in final_rows if key.startswith(('ki.cel/','mi.c/'))}
    assert done==expected,{'missing':sorted(expected-done),'unexpected':sorted(done-expected)}
    assert len(done)==62 and len(final)==102,(len(done),len(final))
    report['status']='passed';report['tested_CEL_routes']=len(done)
    target=OUT/'combined-cel-coverage-test.json';target.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'status':report['status'],'contracts':len(final),'tested_CEL_routes':len(done),'checks':report['checks'],'report':str(target.relative_to(ROOT))}))


if __name__=='__main__':
    main()
