"""Egen bestilling for hver original Demon3-rute, ingen aktivering."""
from pathlib import Path
import json
HERE=Path(__file__).resolve().parent
for c in json.loads((HERE/'source-contracts.json').read_text()):
 n=c['frame']
 if n==15:subject='only this very small rectangular embedded knight-and-cyan-light fragment. A narrow vertical deep blue cloth strip is in the center, cropped gray steel plates at the upper left and upper right, and a broad cyan energy band crosses horizontally through the middle. Only these pictured pieces are visible. Do not add a head, helmet, face, sword, full body or complete limbs; retain the exact cropped source arrangement'
 elif n==20:subject='only the pictured cropped side-profile blue knight helmet and upper shoulder facing left. Preserve the narrow black visor opening, gray segmented helmet and neck, pale highlight beside the neck, the long narrow blue plume across the upper right and blue shoulder/cloth in the lower part. Do not add a visible human face, sword, hands, lower body or extra helmet crest; reproduce only this cropped source composition'
 elif n==21:subject='only the pictured partial blue knight fragment: cropped gray armored pieces across the upper left and descending along the left half, dark blue cloth down the center/right and diagonally toward the lower right, with a cyan energy band around the left-middle gray piece. Preserve the separate lower projections and every gap exactly. Do not add a head, face, helmet, sword, unseen body or complete limbs; reproduce only these cropped source pieces'
 elif n==19:subject='only the pictured narrow vertical pale steel sword-blade fragment, exact straight length, width and highlight. Do not add a hilt, hand, energy bolt or complete weapon'
 elif n in[22,24,26,30]:subject='only the visible cyan Guardian energy hand or branching fragment. Follow its exact number of projections, cropped orientation and dark gaps. Do not add fingers, a whole arm, a second hand or a creature'
 elif n in[38,39,43]:subject='only the exact cyan Guardian dissolution fragment with the tiny red detail and partial profile where visible in the source. Preserve every original checker-pattern gap and cropped feature. Do not invent a complete face, skull, eye or extra anatomy'
 elif n>=47:subject='only the exact thin pale cream rectangular outline shown in the original. It is an original display outline, not an anatomical part. Preserve the exact straight line width, rectangular aspect and empty transparent center. Restrained photographed pale surface grain within the line only, no frame bevel, ornaments, scenery or new shapes'
 else:subject='only the pictured original pale-cyan Guardian light streak, vapor band or branching discharge fragment. Preserve the exact curvature, thickness, disconnected parts, taper and dark gaps. It is a cropped light fragment, not an invented creature or limb'
 prompt=f'''Use case: sketch-to-render
Asset type: one faithful photographic HD fragment of original MOONSTONE Guardian, Demon3.CEL/{n:03}.png.
Input image: original fragment enlarged nearest-neighbor against white. White is only the reference backdrop; source opaque black fields stay opaque black.
Primary request: render {subject}. This exact original reference is the sole geometry and identity authority.
Style/medium: restrained photographic practical-effects cyan vapor and natural fine grain, layered soft light scattering. Original steel uses worn photographed metal; original blue clothing uses tightly woven cloth. No glossy fantasy illustration or invented effects.
Composition: exactly one isolated fragment, original {c['width']}:{c['height']} aspect ratio, orientation, contour, crop, gaps and placements. Every partial feature remains partial. No sprite sheet.
Color: original pale-cyan light, white/cream highlights, slate shadows, source black and only the original tiny red details. Preserve blue cloth and grey steel only where the source shows them.
Constraints: transparent background, no scene, floor, text, new objects, faces, horns, crown, extra branches, armor or glow outside the original source contour.
'''
 p=HERE/f'prompts/{n:03}-v1.txt';p.parent.mkdir(exist_ok=True)
 if p.exists():assert p.read_text()==prompt
 else:p.write_text(prompt)
print('50 separate original-reference prompts, fixture-only until actual observation')
