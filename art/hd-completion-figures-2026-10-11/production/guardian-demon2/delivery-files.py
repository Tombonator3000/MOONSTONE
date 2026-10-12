"""Eksplisitt filliste uten HTML, pakke-snapshot eller aktive HD-kopier."""
from pathlib import Path
import argparse,json
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
ap=argparse.ArgumentParser();ap.add_argument('index');ap.add_argument('--output',default='delivery-demon2-first15-files.txt');args=ap.parse_args();index_path=HERE/args.index;index=json.loads(index_path.read_text());files={str(index_path.relative_to(ROOT)),str(Path(__file__).relative_to(ROOT))}
for row in index['companion_derivations']:files.add(row['path'])
for row in index['proofs']:files.add(row['path'])
for entry in index['entries']:
 for field in['png','raw','prompt','art_record']:files.add(entry[field])
 record=json.loads((ROOT/entry['art_record']).read_text());files.add(str((HERE/record['source_reference']).relative_to(ROOT)));files.add(str((HERE/f"references/{entry['frame']:03}-original.png").relative_to(ROOT)))
folder=index_path.parent;files.add(str((folder/'freeze-proof.json').relative_to(ROOT)))
proof=(ROOT/index['proofs'][0]['path']).parent
for frame in[0,7,14]:
 for mode in['original','hd']:files.add(str((proof/f'combat-{frame:03}-{mode}.png').relative_to(ROOT)))
for frame in[0,7,14]:
 for suffix in['-original.png','-hd.png','-mirror-original.png','-mirror-hd.png']:files.add(str((proof/f'{frame:03}{suffix}').relative_to(ROOT)))
assert all((ROOT/f).is_file()for f in files)
assert all(not f.endswith('.html')and'/package/'not in f and not f.startswith('web/hd/')and not f.endswith('chip1200.bin')and not f.endswith('chip1250.bin')for f in files)
target=HERE/args.output;assert not target.exists();target.write_text('\n'.join(sorted(files))+'\n');print(len(files),'repo-paths',target)
