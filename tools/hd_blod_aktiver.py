#!/usr/bin/env python3
"""Aktiver 41 blodruter bare fra kilde-, bilde- og runtimebundet kontroll."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import moonfiles as mf

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / 'art/hd-blood-wounds-2026-10-12'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    proof_path = ART / 'verification/candidate/report.json'
    proof = json.loads(proof_path.read_bytes())
    visual_path = ART / 'verification/visual.json'
    visual = json.loads(visual_path.read_bytes())
    assert proof['status'] == 'passed' and proof['candidate'] and not proof['partial']
    assert len(proof['routes']) == 41 and not proof['errors']
    assert visual['status'] == 'passed' and visual['candidate_report_sha256'] == sha(proof_path)
    for p, digest in visual['inspected_files'].items():
        assert sha(ART / p) == digest, p
    for k, digest in proof['code_sha256'].items():
        assert sha(ROOT / f'web/src/{k}.js') == digest, k
    bank = mf.Spill(str(ROOT / 'Moonstonecd32-AMIGA.zip')).les('data/blo.cel')
    assert hashlib.sha256(bank).hexdigest() == proof['source_bank_sha256']
    manifest_path = ROOT / 'web/hd/manifest.json'
    manifest = json.loads(manifest_path.read_bytes())
    previous = {e['path']: e for e in manifest['files']}
    # Gjentatt aktivering er lov bare med samme allerede kontrollerte filer.
    receipt_path = ART / 'activation.json'
    original_manifest_sha = proof['manifest_sha256']
    if sha(manifest_path) != original_manifest_sha:
        old_receipt = json.loads(receipt_path.read_bytes())
        assert old_receipt['new_manifest_sha256'] == sha(manifest_path)
        assert old_receipt['candidate_report_sha256'] == sha(proof_path)
    for key, entry in previous.items():
        assert sha(ROOT / 'web/hd' / key) == entry['sha256'], key
        assert (ROOT / 'web/hd' / key).stat().st_size == entry['bytes'], key
    raw_hashes = set()
    additions = []
    for n in range(41):
        key = f'blo.cel/{n:03}.png'
        record = json.loads((ART / f'packing/{n:03}/record.json').read_bytes())
        source = ART / 'packed' / key
        assert sha(source) == record['candidate_sha256'] == proof['packed_sha256'][key]
        assert sha(ROOT / record['raw_file']) == record['raw_sha256']
        assert sha(ROOT / record['prompt']) == record['prompt_sha256']
        assert record['raw_sha256'] not in raw_hashes
        raw_hashes.add(record['raw_sha256'])
        assert record['source_bank_sha256'] == proof['source_bank_sha256']
        assert not record['source_midpoint_errors'] and record['silhouette_iou'] >= .90
        entry = dict(path=key, bytes=source.stat().st_size, sha256=sha(source), kind='base')
        if key in previous:
            assert previous[key] == entry
        additions.append((source, entry))
    # Ingen kopiering skjer foer hele leveransen er kontrollert.
    for source, entry in additions:
        target = ROOT / 'web/hd' / entry['path']
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
        previous[entry['path']] = entry
    manifest['files'] = sorted(previous.values(), key=lambda e: e['path'])
    manifest['images'] = sum(e['path'].endswith('.png') for e in manifest['files'])
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    receipt = dict(status='activated', checked_utc=datetime.now(timezone.utc).isoformat(),
                   candidate_report_sha256=sha(proof_path), visual_sha256=sha(visual_path),
                   previous_manifest_sha256=original_manifest_sha,
                   new_manifest_sha256=sha(manifest_path), source_bank_sha256=proof['source_bank_sha256'],
                   files={e['path']: e['sha256'] for _, e in additions},
                   independent_generated_materials=len(raw_hashes), images=manifest['images'],
                   manifest_files=len(manifest['files']))
    receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(receipt, ensure_ascii=False))


if __name__ == '__main__':
    main()
