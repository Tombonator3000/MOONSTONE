"""Frys vokterens originalformer og observerte kampfarger, uten aktivering."""
import hashlib,json,sys
from pathlib import Path
from PIL import Image
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
FIGURES=HERE.parents[1]
sys.path.insert(0,str(ROOT/'tools'))
sys.path.insert(0,str(HERE.parent))
import moonfiles as mf
from hd_bestilling import utvid_indekser
from contours import source_contours
sha=lambda b:hashlib.sha256(b).hexdigest()
case=FIGURES/'palettes/cases/guardian.json'
source=json.loads(case.read_text())
assert source['status']=='original_palette_branch_and_controlled_runtime_verified'
game=mf.Spill(ROOT/'Moonstonecd32-AMIGA.zip')
bank=game.les('data/Demon1.CEL')
assert sha(bank)=='248da7eff5f029694e53d0013d7a023e18cc4c5bd940fe8133f88ce6228dc704'
queue=json.loads((FIGURES/'queue.json').read_text())
rows=[]
for n,c in enumerate(mf.cel_les(bank)[0]):
 key=f'Demon1.CEL/{n:03}.png'
 q=next(q for q in queue['entries'] if q['key']==key)
 w,h=c['bredde'],c['hoyde']
 indices=utvid_indekser(mf.plan_til_indeks(c['data'],c['plan'],w,h),c['maske'])
 assert sha(indices)==q['indices_sha256']
 palette=[rgb+[255] for rgb in source['colors']]
 im=Image.new('RGBA',(w,h));im.putdata([tuple(palette[i][:3])+((255 if i else 0),) for i in indices])
 directory=HERE/'references';directory.mkdir(parents=True,exist_ok=True)
 native=directory/f'{n:03}-original.png';im.save(native)
 if n<6:
  canvas=Image.new('RGBA',im.size,'white');canvas.alpha_composite(im)
  canvas.convert('RGB').resize((w*20,h*20),Image.Resampling.NEAREST).save(directory/f'{n:03}-nearest20x.png')
  text=f'''Use case: sketch-to-render
Asset type: faithful photographic HD remake of one original MOONSTONE Guardian animation fragment, Demon1.CEL/{n:03}.png.
Input image: the exact original fragment, enlarged nearest-neighbor on white. White is only a reference backdrop.
Primary request: redraw only the pictured pale ice-blue swirling energy-vortex fragment as photographic practical-effects mist and layered luminous wisps. Preserve this particular fragment's exact silhouette, orientation, internal dark openings, proportions and original arrangement of pale cyan bands. This is a piece of the floating Guardian's vortex, not stone, armor, clothing, ice crystal or a new creature.
Style/medium: restrained photographed practical atmospheric effect with very fine translucent vapor grain and softly illuminated pale blue-white spiral streaks. Realistic material detail inside the original form, no glossy fantasy concept painting.
Composition/framing: isolate precisely this fragment; preserve its {w}:{h} aspect ratio and pose. Keep the complete original contour visible without any crop or added motion trails outside it.
Color palette: preserve original pale cyan and slate-blue shadows, no purple or warm colors.
Constraints: transparent background, no scene, no ground, no text, no new objects, no added face or limbs, no changes to the depicted shape. One independently rendered frame, not a sprite sheet.
'''
  prompt=HERE/'prompts'/f'{n:03}-v1.txt';prompt.parent.mkdir(parents=True,exist_ok=True);prompt.write_text(text)
 shape=source_contours(list(indices),w,h,bool)
 rows.append(dict(key=key,frame=n,number=f'{n:03}',width=w,height=h,indices=list(indices),indices_sha256=sha(indices),source_bank_sha256=sha(bank),source_palette_contract=str(case.relative_to(ROOT)),source_palette_contract_sha256=sha(case.read_bytes()),palette=palette,source_alpha_bounds=im.getbbox(),material_labels=[1 if i else 0 for i in indices],alpha_path=shape,materials={'light':shape},moonstone_source_pixels=0,moonstone_highlight_pixels=0,identity='original Guardian energy fragment; no undocumented per-frame action label'))
(HERE/'source-contracts.json').write_text(json.dumps(rows,separators=(',',':'))+'\n')
print(len(rows),'original contracts; first6 prompts; no HD activation')
