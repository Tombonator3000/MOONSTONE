"""Lag originalreferanser og separate bestillinger uten aa endre frosne kilder."""
from pathlib import Path
import json
from PIL import Image
HERE=Path(__file__).resolve().parent
for c in json.loads((HERE/'source-contracts.json').read_text()):
 n=c['frame'];im=Image.open(HERE/f'references/{n:03}-original.png')
 ref=HERE/f'references/{n:03}-nearest20x.png'
 if not ref.exists():
  canvas=Image.new('RGBA',im.size,'white');canvas.alpha_composite(im)
  canvas.convert('RGB').resize((im.width*20,im.height*20),Image.Resampling.NEAREST).save(ref)
 if n<6:continue
 if n in [27,35,41]:
  subject="the pictured female Guardian energy head in its exact right-facing profile and tilt, with its original nose, lips, eye, chin and branching luminous cyan hair-like extensions. The extensions are the original energy strands, not invented antlers, horns or a crown. Preserve the small red detail exactly where it appears in the original face"
 elif n in [18,26,34,42,43]:
  subject="only the pictured vivid cyan branching energy fragment of the original Guardian, preserving every original bend, branch, length and dark gap. These are luminous energy strands, not human fingers, animal limbs, antlers or a new creature"
 elif n in [19,28,36,44]:
  subject="only the pictured original Guardian fragment, with vivid cyan energy shapes emerging from and interleaved with pale blue swirling vapor. Preserve the exact cyan-to-pale arrangement, fragment boundary and cropped pose; do not invent anatomy outside this original rectangle"
 else:
  subject="only the pictured pale ice-blue swirling energy-vortex band, with its original curved streaks, slate-blue shadows, narrow openings and any small cyan inset. This is a cropped piece of the original floating Guardian vortex, not an anatomical limb"
 prompt=f'''Use case: sketch-to-render
Asset type: one faithful photographic HD animation fragment of original MOONSTONE Guardian, Demon1.CEL/{n:03}.png.
Input image: exact original fragment, enlarged nearest-neighbor on white. White is a reference backdrop only.
Primary request: redraw {subject}. Follow this exact original reference as the identity and geometry authority.
Style/medium: restrained photographed practical atmospheric effect, fine translucent vapor grain, layered luminous wisps, natural light scattering. The original energy has a photographic surface, not glossy fantasy concept-painting detail.
Composition/framing: one isolated fragment in its exact {c['width']}:{c['height']} aspect ratio and orientation. Preserve complete contour, original holes, proportions and edge positions. Keep partial anatomy partial; do not complete a whole figure.
Color palette: exact original cool cyan, pale blue-white streaks and slate-blue shadows. Preserve local black shadow gaps and the tiny warm details only if present in this original fragment. No extra colors or glow outside the contour.
Constraints: genuinely transparent background; no scene, ground, text, armor, clothes, stone, ice crystals, added face, new limbs or objects. No extra motion trails. One independently rendered frame, not a sprite sheet.
'''
 dest=HERE/f'prompts/{n:03}-v1.txt'
 if dest.exists():assert dest.read_text()==prompt
 else:dest.write_text(prompt)
print('48 original references and separate prompts, first6 preserved')
