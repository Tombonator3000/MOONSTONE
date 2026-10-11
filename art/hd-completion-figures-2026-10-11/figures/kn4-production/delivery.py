"""Lag en hashbundet kandidatindeks etter bestaatte pakke- og runtimeporter."""
import hashlib
import json
from pathlib import Path
ART=Path(__file__).resolve().parent
ROOT=ART.parents[3]
sha=lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text())
contracts=read(ART/'source-contracts.json')
packing=read(ART/'verification/packing-test.json')
proofs={name:read(ART/f'verification/{name}/test.json') for name in ('all-routes','first-route','contact-001')}
assert packing['status']=='passed'
production={p:sha(ROOT/p) for p in ('web/src/core.js','web/src/render.js','web/src/scenes.js')}
host=ROOT/'art/hd-completion-icons-2026-10-11/runtime-host'
for name,proof in proofs.items():
    assert proof['status']=='passed',(name,proof.get('failure'))
    assert proof['source_contracts_sha256']==sha(ART/'source-contracts.json'),name
    assert proof['production_code_sha256']==production,name
    assert proof['wasm_core_sha256']==sha(host/'moonstone-core-used.js'),name
    assert proof['html_sha256']==sha(host/'moonstone.html'),name
allproof=proofs['all-routes']
for key,digest in allproof['packed_png_sha256'].items():
    assert sha(ART/'packed'/key)==digest,key
records={a['key']:a for a in read(ART/'generation-records.json')['assets']}
assert len(records)==26
bykey={a['key']:a for a in packing['assets']}
entries=[]
for c in contracts['entries']:
    key=c['key'];r=records[key];p=ART/'packed'/key
    assert sha(ART/'raw'/key)==r['raw_sha256']
    entries.append(dict(key=key,source_bank=c['source_bank'],frame=c['frame'],source_size=[c['width'],c['height']],target_size=[c['target_width'],c['target_height']],original=c['original'],indices_sha256=c['indices_sha256'],plane_mask=c['plane_mask'],candidate_png=str(p.relative_to(ROOT)),png_sha256=sha(p),raw_png=str((ART/'raw'/key).relative_to(ROOT)),raw_sha256=r['raw_sha256'],prompt_file=str((ART/'prompts'/('KN4-'+str(c['frame']).zfill(3)+'.txt')).relative_to(ROOT)),generation_tool=r['tool'],generation_receipt='generation-records.json',mask_png=str(p.with_name(p.stem+'.mask.png').relative_to(ROOT)) if c['needs_mask'] else None,mask_sha256=sha(p.with_name(p.stem+'.mask.png')) if c['needs_mask'] else None,packing=bykey[key],quality_status='source_silhouette_bound_new_photographic_material',visual_review='Sammenlignet mot originalen paa comparison.png. Motivet, retningen, utsnittet og alle transparente kildepikselmidtpunkter bevares. Staal/laer og bevegelsesspor er nye fotomaterialer fra separat builtin-generering.'))
report=dict(schema=1,status='ready_for_sequential_integration',scope='26 nye separate KN4-vaapen-/bevegelsesruter, 7 eksakte aliaser og 1 palettmaske. Ingen aktive metadata er endret.',source_contracts_sha256=sha(ART/'source-contracts.json'),queue_subset_sha256=sha(ART/'queue-subset.json'),generation_records_sha256=sha(ART/'generation-records.json'),packing_test_sha256=sha(ART/'verification/packing-test.json'),production_code_sha256=production,wasm_core_sha256=allproof['wasm_core_sha256'],html_sha256=allproof['html_sha256'],runtime={k:dict(path=f'verification/{k}/test.json',sha256=sha(ART/f'verification/{k}/test.json'),checks=len(v['checks'])) for k,v in proofs.items()},entries=entries,aliases=packing['aliases'],limitations=['Samlet kontroll er en kildebasert frontend-fixtur; den paastaar ikke at alle26 er naturlig utloest i gameplay.','Reell original kamp med kropp/haandkontakt er visuelt kontrollert for000 og speilet001.','KN3/001 i kroppskontrollen er blodsprut/draktfragment, ikke en separat arm.','025 bruker originalens levende ridderfarger6/7 gjennom masken. Den generiske eldre forhåndspalettens roede felt er ikke blod.'])
(ART/'delivery.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
print(json.dumps(dict(status=report['status'],masters=len(entries),aliases=len(report['aliases']),runtime_checks=sum(len(p['checks']) for p in proofs.values()))))
