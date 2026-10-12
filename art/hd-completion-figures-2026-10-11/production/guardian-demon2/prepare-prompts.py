"""Separate originalbundne bestillinger, aldri nye motivdetaljer."""
from pathlib import Path
import json
HERE=Path(__file__).resolve().parent
for c in json.loads((HERE/'source-contracts.json').read_text()):
 n=c['frame']
 if n<14:subject='only the pictured pale ice-blue Guardian vortex fragment, with its particular curved vapor bands, slate shadows and dark openings. Preserve the exact cropped fragment and original arrangement of loops'
 elif n in[26,27,29,33,36,41,42,45,48,53]:subject='only the pictured cyan Guardian energy fragment with the original partial head/profile where it is visible. Preserve the depicted face angle, eye, nose, mouth and curved energy strands exactly; do not complete anatomy or introduce a second face'
 elif n==60:subject='only this original blue knight fragment: exact visible helmet, steel armor, gauntlets, sword, blue cloth and grey outer cloak in precisely the original pose. Preserve every contact point, sword direction and original gaps; do not add a whole standing knight'
 elif n>=61:subject='only this specific original cyan-white luminous energy discharge fragment. Preserve the particular branching arcs, tapered streaks, rectangular crop and original dark gaps; do not invent hands, creatures, lightning branches or new shapes'
 else:subject='only the pictured vivid cyan Guardian energy fragment, preserving its precise bends, branches, curves and internal dark openings. These are energy bands, not human limbs, ice crystals or antlers'
 prompt=f'''Use case: sketch-to-render
Asset type: one faithful photographic HD fragment of original MOONSTONE Guardian, Demon2.CEL/{n:03}.png.
Input image: exact original fragment, enlarged nearest-neighbor on white. White is only the reference backdrop.
Primary request: redraw {subject}. The reference is the sole identity and geometry authority.
Style/medium: restrained photographic practical-effects vapor, fine natural grain, layered luminous cyan wisps and soft physical light scattering. If original metal/cloth is visible, use photographed worn steel and tightly woven fabric in exactly those source fields. Avoid glossy fantasy illustration.
Composition/framing: one isolated fragment, exact {c['width']}:{c['height']} aspect ratio, original orientation, contours, holes and edge positions. Partial anatomy stays partial. Preserve original dither holes; do not fill them with new material.
Color palette: source cyan, pale blue-white and slate shadows, with opaque black where present. Only preserve original blue cloth, grey steel or tiny red details where visible. No new purple or warm colors.
Constraints: truly transparent background, no scene, ground, text, added armor, extra faces, objects, limbs, horns, crown or glow outside the original fragment. One independently rendered frame, no sprite sheet.
'''
 target=HERE/f'prompts/{n:03}-v1.txt';target.parent.mkdir(exist_ok=True)
 if target.exists():assert target.read_text()==prompt
 else:target.write_text(prompt)
print('99 separate original-reference prompts; frame060 is embedded knight, not energy')
