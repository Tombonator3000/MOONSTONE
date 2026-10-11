#!/usr/bin/env python3
"""Bind seks gjennomgaatte ruter til uendret runtime og dens frosne inndata."""
import hashlib
import json
from pathlib import Path

ART = Path(__file__).resolve().parent
ROOT = ART.parents[2]
sha = lambda data: hashlib.sha256(data).hexdigest()
load = lambda path: json.loads(path.read_text())


def checked(path, digest):
    path = ROOT / path
    assert sha(path.read_bytes()) == digest, str(path)
    return path


def main():
    delivery_path = ART / 'delivery.json'
    delivery = load(delivery_path)
    assert sha(delivery_path.read_bytes()) == '277c3eb3827fbff843824c2a93717224ce3962a7c2ad41c6f5a452780b79ceeb'
    frozen = ART / 'verification/runtime-ea1f2e42181417b3-4d3a2a03'
    report_path = frozen / 'test.json'
    assert sha(report_path.read_bytes()) == '8451aef6f7b183630fc44049969d41308155da5228ec233ef489c7513bb82abd'
    report = load(report_path)
    assert report['status'] == 'passed' and not report['errors']
    input_path = frozen / 'input-index.json'
    assert sha(input_path.read_bytes()) == report['index_sha256']
    index = load(input_path)
    html = checked(str((frozen / 'loaded.html').relative_to(ROOT)), report['html_sha256'])
    binding = dict(schema=1, status='passed', errors=[],
                   scope='Hashbinding av allerede frosset runtimeprøve og dens eksakte inndata, ingen ny kampkjøring.',
                   html_sha256=report['html_sha256'], checks=[],
                   frozen_runtime=dict(path=str(report_path.relative_to(ROOT)), sha256=sha(report_path.read_bytes())),
                   frozen_input=dict(path=str(input_path.relative_to(ROOT)), sha256=sha(input_path.read_bytes())), assets=[])
    for entry in delivery['entries']:
        original = next(r for r in index['entries'] if r['key'] == entry['key'])
        assert original['candidate'] == entry['candidate']
        assert original['candidate_sha256'] == entry['candidate_sha256']
        checked(entry['candidate'], entry['candidate_sha256'])
        sample_key = entry['key'].lower().removesuffix('.png')
        assert sample_key in report['runtime']['samples']
        assert sample_key + '_emulated_state_unchanged' in report['checks']
        binding['assets'].append(dict(key=entry['key'], png=entry['candidate'], png_sha256=entry['candidate_sha256']))
        binding['checks'].append(entry['key'] + '_frozen_runtime_input_and_current_bytes_exact')
    binding_path = frozen / 'asset-bindings.json'
    binding_bytes = (json.dumps(binding, ensure_ascii=False, indent=2) + '\n').encode()
    if binding_path.exists():
        assert binding_path.read_bytes() == binding_bytes
    else:
        binding_path.write_bytes(binding_bytes)
    activation_path = ART / 'activation-set-troll-001.json'
    activation = load(activation_path)
    original_proof = activation['proofs'][0]
    proof = dict(path=str(binding_path.relative_to(ROOT)), sha256=sha(binding_bytes),
                 html_path=str(html.relative_to(ROOT)), html_sha256=report['html_sha256'])
    activation['proofs'] = [original_proof, proof]
    for entry in activation['entries']:
        entry['runtime_proof'] = proof['path']
        entry['frozen_runtime_proof'] = original_proof['path']
        for name in ('png', 'raw', 'prompt', 'art_record'):
            checked(entry[name], entry[name + '_sha256'])
        patch = entry.get('additional_generated_material')
        if patch:
            for name in ('raw', 'prompt'):
                checked(patch[name], patch[name + '_sha256'])
    activation_path.write_text(json.dumps(activation, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(dict(path=str(activation_path.relative_to(ROOT)), sha256=sha(activation_path.read_bytes()), routes=len(activation['entries']))))


if __name__ == '__main__':
    main()
