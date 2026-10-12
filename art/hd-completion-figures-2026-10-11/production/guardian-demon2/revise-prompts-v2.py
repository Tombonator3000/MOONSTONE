"""Rett tre ennå ikke genererte utsnitt etter separat inspeksjon av originalen."""
from pathlib import Path
import hashlib,json
HERE=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
old="only the pictured cyan Guardian energy fragment with the original partial head/profile where it is visible. Preserve the depicted face angle, eye, nose, mouth and curved energy strands exactly; do not complete anatomy or introduce a second face"
new={41:"only this original upright cyan energy fragment with long branching strands and the exact checker-pattern dissolution holes. There is no visible face in this crop; do not invent a face, eye, mouth or hand",42:"only this original curved cyan energy band with its precise dark curve, short internal projections and checker-pattern holes. Do not add a face, eye, mouth, limb or creature",45:"only this exact narrow cropped cyan energy fragment, including its small dark sideward wedge and checker-pattern edge. Preserve the crop; do not extend it to reveal an eye, mouth or a complete head"}
rows=[]
for n,subject in new.items():
 p=HERE/f'prompts/{n:03}-v1.txt';assert not (HERE/f'raw/{n:03}-v1.png').exists()
 text=p.read_text();before=sha(p)
 if old in text:p.write_text(text.replace(old,subject))
 else:assert subject in text
 rows.append(dict(frame=n,prompt=str(p.relative_to(HERE)),prompt_sha256=sha(p),source_reference=f'references/{n:03}-nearest20x.png',source_reference_sha256=sha(HERE/f'references/{n:03}-nearest20x.png'),reason='Separate visual inspection: no visible face in this crop; reference and source geometry unchanged'))
output=HERE/'verification/prompt-corrections-v2.json';value=dict(schema=1,script_sha256=sha(Path(__file__)),changes=rows)
if output.exists():assert json.loads(output.read_text())==value
else:output.write_text(json.dumps(value,indent=2)+'\n')
print('3 ungenerated prompts corrected, frozen first15 untouched')
