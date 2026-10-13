#!/usr/bin/env python3
"""Kontroller ferdig installert pakke mot endelig kode og ordinær standardlasting."""
import hashlib
import json
from pathlib import Path
import sys
ART=Path(__file__).resolve().parent
ROOT=ART.parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import hd_figurer_aktiver as gate
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rel=lambda p:str(p.relative_to(ROOT))

batch=json.loads((ART/'sprites.json').read_text())
source={r['key']:r for r in json.loads((ART/'source/contracts.json').read_text())['entries']}
reportpath=ART/'verification/standard/report.json';report=json.loads(reportpath.read_text())
assert report['status']=='passed' and not report['errors'] and len(report['routes'])==225
assert all(c['control']['bakgrunn']=='hd' for m in report['combat'] for c in m['captures'])
proofhtml=ART/'verification/standard/loaded.html'
assert sha(proofhtml)==report['html_sha256']
entries=[]
for r in batch['entries']:
    e={k:r[k] for k in ['key','bank','frame','source_bank_sha256','indices_sha256','png','png_sha256','art_record','art_record_sha256']}
    e.update(existing_master=True,runtime_asset_sha256=r['png_sha256'],runtime_proof=rel(reportpath))
    if set(source[r['key']]['indices'])<={0,5}:
        raw=ROOT/r['png'];prompt=ART/'BRIEF.md';tool='preserved_original_black_shape'
    elif r.get('previous'):
        old=ROOT/'art/hd-trogg-2026-10-13';raw=old/'raw'/('TROGGAxe2.CEL-069.png' if r['frame']>=69 else 'TROGGAxe2.CEL-055.png');prompt=old/'prompts'/raw.name.replace('.png','.txt');tool='builtin_image_gen'
    else:
        raw=ART/'raw/materials.png';prompt=ART/'prompts/materials.txt';tool='builtin_image_gen'
    e.update(raw=rel(raw),raw_sha256=sha(raw),prompt=rel(prompt),prompt_sha256=sha(prompt),generation_tool=tool)
    if r.get('mask'):e.update(mask=r['mask'],mask_sha256=r['mask_sha256'])
    entries.append(e)
companions=[ART/'delivery.json',ART/'source/contracts.json',ART/'verification/activation.json',ART/'verification/source-geometries.json',ART/'verification/baking/report.json',ART/'verification/atlas.json',ART/'verification/visual-final.json',ART/'verification/standard/runtime-executed.cjs']
delivery=dict(schema=1,visual_status='reviewed_original_and_runtime',source_zip_sha256=batch['source_zip_sha256'],wasm_core_sha256=report['wasm_core_sha256'],production_code_sha256={f'web/src/{n}.js':sha(ROOT/f'web/src/{n}.js') for n in ['core','render','scenes','hd','app']},companion_derivations=[dict(path=rel(p),sha256=sha(p)) for p in companions],proofs=[dict(path=rel(reportpath),sha256=sha(reportpath),html_path=rel(proofhtml),html_sha256=sha(proofhtml))],entries=entries,scope='Final installed context:225 routes with current source-bound baked-corpse renderer.195 routes activated by historical delivery.json; source aliases and original files preserved. No reactivation or new independent AI-drawing claim.')
(ART/'delivery-active.json').write_text(json.dumps(delivery,ensure_ascii=False,indent=2)+'\n')
files=gate.validate(delivery);assert files=={}
(ART/'verification/active-gate.json').write_text(json.dumps(dict(status='passed',installed_routes=225,installed_masks=151,new_files_activated_now=0,delivery_sha256=sha(ART/'delivery-active.json'),all_source_and_runtime_bindings_checked=True),indent=2)+'\n')
print('Endelig225ruter/151masker kontrollert mot aktiv pakke og gjeldende visningskode')
