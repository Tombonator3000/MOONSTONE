"""Eksporter bare original test005 med faktisk kildebekreftet Guardian-palett."""
from pathlib import Path
import hashlib,json,sys
from PIL import Image
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];sys.path.insert(0,str(ROOT/'tools'));import moonfiles as mf
sha=lambda b:hashlib.sha256(b).hexdigest()
case_bytes=(HERE/'../../palettes/cases/guardian.json').read_bytes();case=json.loads(case_bytes);zipfile=ROOT/'Moonstonecd32-AMIGA.zip';assert sha(zipfile.read_bytes())==case['source_zip_sha256']
game=mf.Spill(zipfile);blob=game.les('data/test');planes,pal,raw=mf.piv_alle(blob)[0][5];assert planes==5
h=2166136261
for v in raw:h=((h^v)*16777619)&0xffffffff
assert h==0xcbc31cbf and sha(raw)=='92f8624a8eedac5b5c0c88e804021bcf32276a01536198509bfd045d33c446fc'
indices=bytes(mf.plan_til_indeks(raw,5));rgba=bytes(v for i in indices for v in case['colors'][i]+[255]);im=Image.frombytes('RGBA',(320,200),rgba)
folder=HERE/'references/background';folder.mkdir(exist_ok=True);native=folder/'cbc31cbf-original.png';enlarged=folder/'cbc31cbf-nearest4x.png';im.save(native);im.resize((1280,800),Image.Resampling.NEAREST).save(enlarged)
(folder/'cbc31cbf-indices.bin').write_bytes(indices);(folder/'cbc31cbf-bitplanes.bin').write_bytes(raw)
record=dict(schema=1,status='source_export_verified',scope='Original source test005. Guardian palette comes from original combat initializer, no palette writes. Runtime clean-background byte confirmation is separate; do not draw combat figures into the HD background.',source_file='data/test',source_frame=5,source_file_sha256=sha(blob),source_zip_sha256=case['source_zip_sha256'],source_palette_contract=str((HERE/'../../palettes/cases/guardian.json').resolve().relative_to(ROOT)),source_palette_contract_sha256=sha(case_bytes),palette_rgb=case['colors'],source_piv_palette_words=pal,planes_sha256=sha(raw),indices_sha256=sha(indices),rgba_sha256=sha(rgba),fnv1a='cbc31cbf',native_size=[320,200],native_png=str(native.relative_to(ROOT)),native_png_sha256=sha(native.read_bytes()),nearest_png=str(enlarged.relative_to(ROOT)),nearest_png_sha256=sha(enlarged.read_bytes()),export_script_sha256=sha(Path(__file__).read_bytes()))
(folder/'cbc31cbf-source.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record))
