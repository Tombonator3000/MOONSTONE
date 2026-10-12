"""Bevar kildeformer og skill kun originalens dokumenterte fargefelt."""
from pathlib import Path
import hashlib,json
HERE=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rows=json.loads((HERE/'source-contracts.json').read_text())
for c in rows:
 # Samme fotografi leverer materiallys. Fargefelt blandes bare med samme
 # originalgruppe, saa sortindeks5, roed detalj15 og kremhvitt1/2 beholdes.
 c['material_labels']=[0 if i==0 else 5 if i==5 else 3 if 9<=i<=12 else 4 if i==15 else 6 if i in [1,2] else 1 for i in c['indices']]
assert len(rows)==48
assert rows[:3]==json.loads((HERE/'first3-v1/geometries.json').read_text())
(HERE/'geometries.json').write_text(json.dumps(rows,separators=(',',':'))+'\n')
(HERE/'verification/geometry-build-v1.json').write_text(json.dumps(dict(schema=1,status='source_shapes_preserved',frames=48,source_contracts_sha256=sha(HERE/'source-contracts.json'),geometry_sha256=sha(HERE/'geometries.json'),script_sha256=sha(Path(__file__)),scope='Original source contours and all indices/anchors remain unchanged. Only original material groups are separated for source-color interpolation; each generated photograph still supplies its own light detail. First3 geometry records are unchanged.'),indent=2)+'\n')
print('48 source geometries; first3 byte-equivalent records')
