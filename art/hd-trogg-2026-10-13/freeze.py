#!/usr/bin/env python3
"""Frys bare kontrollerte vaapenruter til prosjektets eksisterende aktiveringsport."""
import hashlib
import json
from pathlib import Path
ART=Path(__file__).resolve().parent
ROOT=ART.parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rel=lambda p:str(p.relative_to(ROOT))


def main():
    batch=json.loads((ART/'weapons.json').read_text())
    proof=ART/'verification/candidate/report.json'
    report=json.loads(proof.read_text())
    visual=ART/'verification/visual.json'
    assert report['status']=='passed' and not report['errors']
    assert json.loads(visual.read_text())['status']=='reviewed_original_and_runtime'
    html=ART/'verification/candidate/loaded.html'
    assert sha(html)==report['html_sha256']
    entries=[]
    for r in batch['entries']:
        assert report['assets'][r['key']]==r['png_sha256']
        raw=ART/'raw'/('TROGGAxe2.CEL-069.png' if r['frame']>=69 else 'TROGGAxe2.CEL-055.png')
        prompt=ART/'prompts'/raw.name.replace('.png','.txt')
        record=ART/f'weapons-packing/{r["frame"]:03}/record.json'
        e={k:r[k] for k in ['key','bank','frame','source_bank_sha256','indices_sha256','png','png_sha256']}
        e.update(raw=rel(raw),raw_sha256=sha(raw),prompt=rel(prompt),prompt_sha256=sha(prompt),generation_tool='builtin_image_gen',art_record=rel(record),art_record_sha256=sha(record),runtime_asset_sha256=r['png_sha256'],runtime_proof=rel(proof),additional_generated_materials=[dict(raw=rel(ART/m['raw']),raw_sha256=m['raw_sha256'],prompt=rel(ART/m['prompt']),prompt_sha256=m['prompt_sha256']) for m in r['materials'].values()])
        if r.get('mask'):e.update(mask=r['mask'],mask_sha256=r['mask_sha256'])
        entries.append(e)
    companions=[ART/'weapons.py',ART/'verification/candidate/runtime-executed.cjs',ART/'source/contracts.json',ART/'generation.json',visual]
    delivery=dict(schema=1,visual_status='reviewed_original_and_runtime',source_zip_sha256=batch['source_zip_sha256'],wasm_core_sha256=report['wasm_core_sha256'],production_code_sha256={f'web/src/{n}.js':sha(ROOT/f'web/src/{n}.js') for n in ['core','render','scenes','hd','app']},companion_derivations=[dict(path=rel(p),sha256=sha(p)) for p in companions],proofs=[dict(path=rel(proof),sha256=sha(proof),html_path=rel(html),html_sha256=report['html_sha256'])],entries=entries,scope='30 source-constrained weapon/material sprites from three generated masters, not a completed Trogg body',limits=['Four routes need terrain color masks','Only subset observed in original CPU encounters; all30 have source/frontend checks','No complete natural campaign or physical mobile test'])
    (ART/'delivery.json').write_text(json.dumps(delivery,ensure_ascii=False,indent=2)+'\n')
    print('Fryst',len(entries),'vaapenruter')


if __name__=='__main__':main()
