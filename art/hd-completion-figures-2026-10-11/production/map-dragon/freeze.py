"""Frys visuelt kontrollerte kartdrageruter etter faktisk originalanimasjon."""
from pathlib import Path
import hashlib
import json

ART=Path(__file__).resolve().parent
ROOT=ART.parents[3]
FIGURES=ART.parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
relative=lambda p:str(p.relative_to(ROOT))
proof=ART/'verification/runtime-v5/test.json'
report=json.loads(proof.read_text())
assert report['status']=='passed' and len(report['checks'])==123 and not report['errors']
html=proof.parent/'loaded.html'
assert sha(html)==report['html_sha256']
delivery=dict(schema=1,visual_status='reviewed_original_and_runtime',
 source_zip_sha256=sha(ROOT/'Moonstonecd32-AMIGA.zip'),
 production_code_sha256=report['production_code_sha256'],wasm_core_sha256=report['wasm_core_sha256'],
 scope='Aatte separate genererte fotomaterialmastere. Originalens materiale-, skygge- og silhuettkonturer styrer pakking. Ingen fri fotogeometri eller full naturlig gjennomspilling paastaas.',
 proofs=[dict(path=relative(proof),sha256=sha(proof),html_path=relative(html),html_sha256=sha(html))],entries=[])
packing=json.loads((ART/'verification/packing.json').read_text())
(ART/'records').mkdir(exist_ok=True)
for number in range(34,42):
 key=f'mi.c/{number:03}.png';route=json.loads((FIGURES/'routes'/key.replace('.png','.json')).read_text())
 png=ART/'packed'/key;raw=ART/f'raw/{number:03}-v1.png';prompt=ART/f'prompts/{number:03}-v1.txt'
 assert sha(png)==report['assets'][key]
 record=ART/f'records/{number:03}-v5.json'
 method='Eget innebygd generert fotografisk materiale per rute. Originalens tre materialomraader bestemmer konturene; .4 kildepiksels avrundede kanter bevarer alle midtpunkter. Originalpalettens skyggefordeling er glattet kun innen samme materiale.70 prosent skalert fotomateriale og30 prosent original palettone. Ankre og4x-maal uendret.'
 j=dict(key=key,candidate_sha256=sha(png),raw=relative(raw),raw_sha256=sha(raw),prompt=relative(prompt),prompt_sha256=sha(prompt),generation_tool='builtin_image_gen',exact_model_version='not_exposed',source_indices_sha256=route['indices_sha256'],method=method,packing=next(a for a in packing['assets'] if a['key']==key),visual_review='Alle aatte original-/HD-kartutsnitt kontrollert; bildeform og vingestillinger foelger kilden',actual_runtime_frame=report['runtime']['seen'][str(number)]['frame'])
 record.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n')
 delivery['entries'].append(dict(key=key,bank='mi.c',frame=number,source_bank_sha256=route['source_bank']['sha256'],indices_sha256=route['indices_sha256'],png=relative(png),png_sha256=sha(png),raw=relative(raw),raw_sha256=sha(raw),prompt=relative(prompt),prompt_sha256=sha(prompt),generation_tool='builtin_image_gen',art_record=relative(record),art_record_sha256=sha(record),runtime_proof=relative(proof),runtime_asset_sha256=sha(png)))
(ART/'activation-set-001.json').write_text(json.dumps(delivery,ensure_ascii=False,indent=2)+'\n')
print('Frosset8 fotomaterialruter med123 runtimekontroller.')
