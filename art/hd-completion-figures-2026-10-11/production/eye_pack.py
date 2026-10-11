#!/usr/bin/env python3
"""Pakk generert øyefotodetalj i originalens eksakte øyekontur."""
import argparse, hashlib, json, os, subprocess
from collections import deque
from pathlib import Path
from PIL import Image, ImageDraw
from contours import source_contours

ART=Path(__file__).resolve().parent
FIGURES=ART.parent
ROOT=FIGURES.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('record',type=Path);p.add_argument('--skin-patch-raw',type=Path);p.add_argument('--skin-patch-prompt',type=Path);a=p.parse_args();a.record=a.record.resolve()
 old=json.loads(a.record.read_text());key=old['key']
 source_eyes={'TROLL1.CEL/006.png':[(27,1)],'TROLL1.CEL/009.png':[(10,2),(11,2)],'TROLL1.CEL/013.png':[(28,1),(27,2)],'TROLL1.CEL/016.png':[(11,1)],'TROLL1.CEL/022.png':[(7,1)],'TROLL1.CEL/028.png':[(10,4)],'TROLL1.CEL/032.png':[(9,1)],'TROLL1.CEL/037.png':[(23,8)],'TROLL2.CEL/001.png':[(70,7)],'TROLL2.CEL/003.png':[(2,6)],'TROLL2.CEL/007.png':[(17,7)],'TROLL2.CEL/012.png':[(43,2),(42,3)],'TROLL2.CEL/015.png':[(19,4)]}
 assert key in source_eyes
 base=a.record.parent/'candidate.png';assert sha(base)==old['candidate_sha256']
 im=Image.open(base).convert('RGBA');original=im.copy()
 q=json.loads((FIGURES/'queue.json').read_text());r=next(r for r in q['entries'] if r['key']==key)
 packed=Image.open(FIGURES/r['packed_original']['path']);bits=[1<<n for n in range(5) if r['plane_mask']&(1<<n)]
 ix=[sum(bit for n,bit in enumerate(bits) if v&(1<<n)) for v in packed.getdata()]
 eye_index=2 if key=='TROLL1.CEL/013.png' else 1;brightness=80 if eye_index==2 else 140
 source_eye=[(x,y) for y in range(12 if key in {'TROLL1.CEL/037.png','TROLL2.CEL/001.png','TROLL2.CEL/003.png','TROLL2.CEL/007.png','TROLL2.CEL/015.png'} else 5) for x in range(r['width']) if ix[y*r['width']+x]==eye_index]
 assert source_eye==source_eyes[key],source_eye
 eye_min_x=min(x for x,y in source_eye);eye_min_y=min(y for x,y in source_eye)
 eye_width=(max(x for x,y in source_eye)-eye_min_x+1)*4;eye_height=(max(y for x,y in source_eye)-eye_min_y+1)*4
 eye_scan_height=52 if key in {'TROLL1.CEL/037.png','TROLL2.CEL/001.png','TROLL2.CEL/003.png','TROLL2.CEL/007.png','TROLL2.CEL/015.png'} else 32 if key=='TROLL1.CEL/028.png' else 20
 # Bare det høytsittende øyet velges, aldri tannen eller munnen.
 bright=[(x,y) for y in range(eye_scan_height) for x in range(im.width) if (lambda rr,g,b,aa:rr>brightness and g>brightness and b<g+20 and aa>128)(*im.getpixel((x,y)))]
 assert (3 if key=='TROLL1.CEL/028.png' else 4)<=len(bright)<=64
 bbox=(min(x for x,y in bright),min(y for x,y in bright),max(x for x,y in bright)+1,max(y for x,y in bright)+1)
 eye_material=im.crop(bbox).resize((eye_width,eye_height),Image.Resampling.LANCZOS)
 box=(max(0,bbox[0]-6),max(0,bbox[1]-6),min(im.width,bbox[2]+6),min(im.height,bbox[3]+6))
 # Den feilplasserte øyedetaljen fjernes med nærmeste genererte blå hud.
 # Ingen kildefarge eller oppskalert originaltekstur brukes.
 nearest={};pending=deque()
 for y in range(im.height):
  for x in range(im.width):
   rr,g,b,aa=im.getpixel((x,y))
   if not(box[0]<=x<box[2] and box[1]<=y<box[3]) and aa>=128 and b>rr*1.08 and b>g*1.08:
    nearest[(x,y)]=(x,y);pending.append((x,y))
 while pending:
  x,y=pending.popleft()
  for xx,yy in [(x-1,y),(x+1,y),(x,y-1),(x,y+1)]:
   if 0<=xx<im.width and 0<=yy<im.height and (xx,yy) not in nearest:
    nearest[(xx,yy)]=nearest[(x,y)];pending.append((xx,yy))
 fill=[];skin_proof=None
 if a.skin_patch_raw:
  assert a.skin_patch_prompt
  a.skin_patch_raw=a.skin_patch_raw.resolve();a.skin_patch_prompt=a.skin_patch_prompt.resolve()
  skin=Image.open(a.skin_patch_raw).convert('RGBA').resize(im.size,Image.Resampling.LANCZOS);aff=old['global_affine'];sx,sy,dx,dy=[aff[k] for k in ['scale_x','scale_y','translate_x_px','translate_y_px']]
  skin=skin.transform(im.size,Image.Transform.AFFINE,(1/sx,0,-dx/sx,0,1/sy,-dy/sy),Image.Resampling.BICUBIC)
  skin_proof=dict(raw=str(a.skin_patch_raw.relative_to(ROOT)),raw_sha256=sha(a.skin_patch_raw),prompt=str(a.skin_patch_prompt.relative_to(ROOT)),prompt_sha256=sha(a.skin_patch_prompt),used_region=list(box),method='Only the generated eyeless photo skin patch is packed; all other RGB and all alpha retain the original candidate. Two HD pixels feather the patch boundary.')
 for y in range(box[1],box[3]):
  for x in range(box[0],box[2]):
   u,v=nearest[(x,y)]
   if a.skin_patch_raw:
    weight=min(1,min(x-box[0]+1,box[2]-x,y-box[1]+1,box[3]-y)/2);before=original.getpixel((x,y));photo=skin.getpixel((x,y));im.putpixel((x,y),tuple(round(photo[k]*weight+before[k]*(1-weight)) for k in range(3))+(before[3],))
   else:im.putpixel((x,y),original.getpixel((u,v))[:3]+(im.getpixel((x,y))[3],));fill.append([x,y,u,v])
 versions={'TROLL1.CEL/006.png':'source-eye-v10-photo-skin','TROLL1.CEL/009.png':'source-eye-v11-photo-skin','TROLL1.CEL/013.png':'source-eye-v14-gray-photo-skin','TROLL1.CEL/016.png':'source-eye-v15-photo-skin','TROLL1.CEL/022.png':'source-eye-v16-photo-skin','TROLL1.CEL/028.png':'source-eye-v17-photo-skin','TROLL1.CEL/032.png':'source-eye-v19-photo-skin','TROLL1.CEL/037.png':'source-eye-v22-photo-skin','TROLL2.CEL/001.png':'source-eye-troll2-v1-photo-skin','TROLL2.CEL/003.png':'source-eye-troll2-v1-photo-skin','TROLL2.CEL/007.png':'source-eye-troll2-v1-photo-skin','TROLL2.CEL/012.png':'source-eye-troll2-v1-photo-skin','TROLL2.CEL/015.png':'source-eye-troll2-v1-photo-skin'}
 out=a.record.parent/(versions[key] if a.skin_patch_raw else 'source-eye-v9');out.mkdir(parents=True,exist_ok=True)
 eye_bits=[255 if (x,y) in source_eye else 0 for y in range(r['height']) for x in range(r['width'])]
 shape=source_contours(eye_bits,r['width'],r['height'],lambda n:n>0)
 svg=out/'eye.svg';svg.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{im.width}" height="{im.height}" viewBox="0 0 {r["width"]} {r["height"]}"><path d="{shape}" fill="white"/></svg>\n')
 node=os.environ.get('NODE','/home/tombonator3000t/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node');env=os.environ.copy();env.setdefault('NODE_PATH','/home/tombonator3000t/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules')
 subprocess.run([node,str(ART/'mask.cjs'),str(svg),str(out/'eye-mask.png'),str(im.width),str(im.height)],check=True,env=env)
 mask=Image.open(out/'eye-mask.png').getchannel('A');eye_map=[]
 for x,y in source_eye:
  for dy in range(4):
   for dx in range(4):
    xx,yy=x*4+dx,y*4+dy;alpha=mask.getpixel((xx,yy))/255
    if alpha:
     u=(x-eye_min_x)*4+dx;v=(y-eye_min_y)*4+dy;material=eye_material.getpixel((u,v))[:3];skin=im.getpixel((xx,yy));im.putpixel((xx,yy),tuple(round(material[i]*alpha+skin[i]*(1-alpha)) for i in range(3))+(skin[3],));eye_map.append([xx,yy,u,v])
 assert im.getchannel('A').tobytes()==original.getchannel('A').tobytes()
 outside=[(x,y) for y in range(eye_scan_height) for x in range(im.width) if (lambda rr,g,b,aa:rr>brightness and g>brightness and b<g+20 and aa>128)(*im.getpixel((x,y))) and mask.getpixel((x,y))==0]
 assert not outside,outside
 target=out/'candidate.png';im.save(target,optimize=True)
 record=dict(old);record['candidate_sha256']=sha(target);record['packing']+=f' Generated eye photo material repacked inside exact original index{eye_index} eye contour. Old misplaced eye/socket uses a separately generated eyeless blue photo-skin patch when supplied; nearest blue diagnostic otherwise. Original alpha unchanged; no original RGB introduced.'
 record['eye_source_binding']=dict(source_indices=[eye_index],source_pixels=source_eye,source_center=[sum(x+.5 for x,y in source_eye)/len(source_eye),sum(y+.5 for x,y in source_eye)/len(source_eye)],generated_material_from_candidate_sha256=sha(base),generated_eye_crop=list(bbox),old_eye_skin_fill_box=list(box),nearest_generated_skin_map=fill,source_contour_mask_sha256=sha(out/'eye-mask.png'),eye_material_map=eye_map,bright_eye_pixels_outside_source_contour=outside,alpha_unchanged=True,generated_eyeless_skin_patch=skin_proof)
 if not a.skin_patch_raw:record['geometry_gate_passed']=False;record['status']='unapproved_blocky_skin_fill_diagnostic'
 record['visual_checks']['source_colors']=f'exact_original_index{eye_index}_eye_contour_bound_pending_runtime';record['visual_checks']['runtime_overlap']='pending_new_eye_candidate_runtime';record['visual_checks']['original_hd_return']='pending_new_eye_candidate_runtime'
 (out/'art-record.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
 sheet=Image.new('RGB',(720,350),'#222222');d=ImageDraw.Draw(sheet)
 for xx,label,img in [(10,'Før kildeplassering',original),(370,'Eksakt original øyeplassering',im)]:
  crop=img.crop((max(0,eye_min_x*4-20),0,min(img.width,eye_min_x*4+52),60)).resize((324,270),Image.Resampling.NEAREST);d.text((xx,8),label,fill='white');sheet.paste(crop,(xx,32),crop)
 sheet.save(out/'eye-comparison.png');print(json.dumps(dict(path=str(out.relative_to(ROOT)),sha256=sha(target),source_eye=source_eye)))

if __name__=='__main__':main()
