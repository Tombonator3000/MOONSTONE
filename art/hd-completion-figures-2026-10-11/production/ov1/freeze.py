"""Frys fire kildeavgrensede fotomaterialer etter faktisk introprove."""
from pathlib import Path
import hashlib
import json

ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent
ART=HERE.parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
relative=lambda p:str(p.relative_to(ROOT))
proof=HERE/'verification/runtime-v5/test.json'
runtime=json.loads(proof.read_text())
assert runtime['status']=='passed' and len(runtime['checks'])==15 and not runtime['errors']
records=[]
ids=['exec-22522359-db24-4832-90c5-6a413aa2ba0d.png','exec-e7d50f5f-59ae-494d-a4d0-bf600fa4d39f.png','exec-bce7edc7-f595-4729-8ca7-8f4c1b0e8540.png','exec-873314db-3eee-4839-8634-7ea80827273d.png']
packing=json.loads((HERE/'verification/packing.json').read_text())
entries=[]
for item in packing['assets']:
    number=int(Path(item['key']).stem)
    route=json.loads((ART/f'routes/ov1.cel/{number:03}.json').read_text())
    png=HERE/'packed'/item['key'];raw=HERE/item['raw'];prompt=HERE/item['prompt']
    assert sha(png)==runtime['assets'][item['key']]==item['candidate_sha256']
    record={**item,'generation_tool':'builtin_image_gen','generated_output':ids[number],
            'raw_sha256':sha(raw),'prompt_sha256':sha(prompt),'packing_script_sha256':sha(HERE/'pack.cjs'),
            'geometry_sha256':sha(HERE/'geometries.json'),
            'method':'Eget fotografisk raabilde per originalrute. Originalens glatte materialkonturer og alle kildealfamidtpunkter beholdes. Lyse bladkomponenter registreres til genererte bladteksturer. Ingen fri kontur- eller posenytegning paastaas.',
            'visual_status':'reviewed_original_and_natural_intro'}
    target=HERE/f'records/{number:03}-v2.json';target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n');records.append(record)
    entries.append(dict(key=item['key'],bank='ov1.cel',frame=number,
         source_bank_sha256=route['source_bank']['sha256'],indices_sha256=route['indices_sha256'],
         png=relative(png),png_sha256=sha(png),raw=relative(raw),raw_sha256=sha(raw),
         prompt=relative(prompt),prompt_sha256=sha(prompt),generation_tool='builtin_image_gen',
         runtime_proof=relative(proof),runtime_asset_sha256=sha(png),
         art_record=relative(target),art_record_sha256=sha(target),
         qa=dict(source_centers_opaque=item['source_centers_opaque'],source_centers_empty=item['source_centers_empty'],
                 source_midpoints_missing=0,source_transparent_midpoints_filled=0,
                 original_hd_return='exact',emulated_state='unchanged',unknown_hole_rejected=True)))
(HERE/'generation-records-v2.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
delivery=dict(schema=1,visual_status='reviewed_original_and_runtime',source_zip_sha256=sha(ROOT/'Moonstonecd32-AMIGA.zip'),
 production_code_sha256=runtime['production_code_sha256'],wasm_core_sha256=runtime['wasm_core_sha256'],
 proofs=[dict(path=relative(proof),sha256=sha(proof),html_path=relative(proof.parent/'loaded.html'),html_sha256=runtime['html_sha256'])],
 scope='Fire separate fotomaterialmastere med originalgeometri, i naturlig intro3200. Kildepalett fra skanout, ingen minne- eller palettskriving. Ingen ferdige druider eller flammer paastaas.',entries=entries)
(HERE/'activation-set-001.json').write_text(json.dumps(delivery,ensure_ascii=False,indent=2)+'\n')
print('Frosset fire OV1-materialmastere')
