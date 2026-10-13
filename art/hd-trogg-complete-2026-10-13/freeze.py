#!/usr/bin/env python3
"""Frys hele serien til samme strenge kilde-/runtimeport som tidligere leveranser."""
import hashlib
import json
from pathlib import Path
ART=Path(__file__).resolve().parent
ROOT=ART.parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rel=lambda p:str(p.relative_to(ROOT))

def main():
    batch=json.loads((ART/'sprites.json').read_text())
    proof=ART/'verification/candidate/report.json';report=json.loads(proof.read_text())
    palette=ART/'verification/palettes/report.json'
    assert report['status']=='passed' and not report['errors']
    assert json.loads(palette.read_text())['status']=='passed'
    visual=ART/'verification/visual.json'
    assert json.loads(visual.read_text())['status']=='reviewed_original_and_runtime'
    html=ART/'verification/candidate/loaded.html';assert sha(html)==report['html_sha256']
    entries=[]
    for r in batch['entries']:
        assert report['assets'][r['key']]==r['png_sha256']
        e={k:r[k] for k in ['key','bank','frame','source_bank_sha256','indices_sha256','png','png_sha256','art_record','art_record_sha256']}
        e.update(runtime_asset_sha256=r['png_sha256'],runtime_proof=rel(proof))
        if r.get('existing_master'):
            e['existing_master']=True
            old=ROOT/'art/hd-trogg-2026-10-13'
            raw=old/'raw'/('TROGGAxe2.CEL-069.png' if r['frame']>=69 else 'TROGGAxe2.CEL-055.png')
            prompt=old/'prompts'/raw.name.replace('.png','.txt')
            e.update(raw=rel(raw),raw_sha256=sha(raw),prompt=rel(prompt),prompt_sha256=sha(prompt),generation_tool='builtin_image_gen')
        elif r.get('alias_of'):
            e['master_key']=r['alias_of']
        elif r.get('pure_black_source'):
            raw=ROOT/r['art_record'];raw=raw.parent/'source.png'
            prompt=ART/'BRIEF.md'
            e.update(raw=rel(raw),raw_sha256=sha(raw),prompt=rel(prompt),prompt_sha256=sha(prompt),generation_tool='preserved_original_black_shape')
        else:
            raw=ART/'raw/materials.png';prompt=ART/'prompts/materials.txt'
            e.update(raw=rel(raw),raw_sha256=sha(raw),prompt=rel(prompt),prompt_sha256=sha(prompt),generation_tool='builtin_image_gen',additional_generated_materials=[dict(raw=rel(ART/'raw/equipment.png'),raw_sha256=sha(ART/'raw/equipment.png'),prompt=rel(ART/'prompts/equipment.txt'),prompt_sha256=sha(ART/'prompts/equipment.txt'))])
        if r.get('mask'):e.update(mask=r['mask'],mask_sha256=r['mask_sha256'])
        entries.append(e)
    companions=[ART/'pack.py',ART/'source/contracts.json',ART/'source/manifest-before.json',ART/'generation.json',ART/'verification/candidate/runtime-executed.cjs',ART/'verification/palettes/runtime-executed.cjs',palette,ART/'verification/atlas.json',visual]
    delivery=dict(schema=1,visual_status='reviewed_original_and_runtime',source_zip_sha256=batch['source_zip_sha256'],wasm_core_sha256=report['wasm_core_sha256'],production_code_sha256={f'web/src/{n}.js':sha(ROOT/f'web/src/{n}.js') for n in ['core','render','scenes','hd','app']},companion_derivations=[dict(path=rel(p),sha256=sha(p)) for p in companions],proofs=[dict(path=rel(proof),sha256=sha(proof),html_path=rel(html),html_sha256=report['html_sha256'])],entries=entries,scope='Alle225 Trogg-ruter:195 nye,30 bevarte.163 unike kildeformer;62 eksakte aliaser. To nye materialatlas og kildebundet geometri, ikke225 uavhengig nytegnede anatomiske poser.',limits=['Rene svarte skygger og skaft bevares som originalformer','Alle ruter har frontendprøve; faktisk CPU-dekning oppgis separat','Ingen full naturlig kampanje eller fysisk mobilprøve'])
    (ART/'delivery.json').write_text(json.dumps(delivery,ensure_ascii=False,indent=2)+'\n')
    print('Fryst225 ruter,195 nye,30 eksisterende')

if __name__=='__main__':main()
