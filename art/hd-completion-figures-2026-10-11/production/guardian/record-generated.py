"""Kopier et eget builtin-bilde og bind det til originalreferanse og prompt."""
from pathlib import Path
import hashlib,json,shutil,sys
HERE=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
n=int(sys.argv[1]);source=Path(sys.argv[2]).resolve();assert 0<=n<48
assert source.is_file() and '/.codex/generated_images/' in str(source) and source.name.startswith('exec-') and source.suffix=='.png'
dest=HERE/f'raw/{n:03}-v1.png';dest.parent.mkdir(exist_ok=True)
if dest.exists():assert sha(dest)==sha(source)
else:shutil.copyfile(source,dest)
prompt=HERE/f'prompts/{n:03}-v1.txt';reference=HERE/f'references/{n:03}-nearest20x.png'
record=dict(key=f'Demon1.CEL/{n:03}.png',generation_tool='builtin_image_gen',tool_call_id=source.stem,generated_source_path=str(source),raw=str(dest.relative_to(HERE)),raw_sha256=sha(dest),prompt=str(prompt.relative_to(HERE)),prompt_sha256=sha(prompt),source_reference=str(reference.relative_to(HERE)),source_reference_sha256=sha(reference),status='generated_candidate_not_activated')
call=HERE/f'generation-calls/{n:03}-v1.json';call.parent.mkdir(exist_ok=True)
if call.exists():assert json.loads(call.read_text())==record
else:call.write_text(json.dumps(record,indent=2)+'\n')
calls=[json.loads(p.read_text())for p in sorted((HERE/'generation-calls').glob('*-v1.json'))];assert len({r['key']for r in calls})==len({r['raw_sha256']for r in calls})==len({r['tool_call_id']for r in calls})==len(calls)
(HERE/'generation-records-v1.json').write_text(json.dumps(calls,indent=2)+'\n')
print(json.dumps(dict(status='recorded',key=record['key'],sha256=record['raw_sha256'],distinct_master_count=len(calls))))
