"""Vis originalen ved siden av kildeformet fotomateriale, uten aktivering."""
from pathlib import Path
import argparse,math
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--first',type=int,default=18);p.add_argument('--last',type=int,default=47);p.add_argument('--output',default='verification/comparison-018-047-v1.png');a=p.parse_args()
frames=list(range(a.first,a.last+1));width,height=570,250
canvas=Image.new('RGB',(width*3,height*math.ceil(len(frames)/3)),(40,40,40));d=ImageDraw.Draw(canvas)
for cell,n in enumerate(frames):
 x=(cell%3)*width;y=(cell//3)*height
 d.text((x+10,y+8),f'Demon1.CEL/{n:03} Original / HD',(235,235,235))
 for column,source in enumerate([HERE/f'references/{n:03}-original.png',HERE/f'packed/Demon1.CEL/{n:03}.png']):
  im=Image.open(source).convert('RGBA');scale=min(4 if column==0 else 1,245/im.width,205/im.height)
  im=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.NEAREST if column==0 else Image.Resampling.LANCZOS)
  canvas.paste(im,(x+column*280+15+(245-im.width)//2,y+32+(205-im.height)//2),im)
output=HERE/a.output;assert not output.exists();canvas.save(output);print(output)
