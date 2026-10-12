"""Samme fotografiske kappe i kildeidentiske, ubevegelige DICE/TAV-felt."""
from pathlib import Path
import hashlib,json
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
TAV=ROOT/'art/hd-embedded-tavern-2026-10-11';audit_path=TAV/'verification/dice-source-cloth.json'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
audit=json.loads(audit_path.read_text());plate=TAV/'packed/embedded/tav-player.png';mask=TAV/'packed/embedded/tav-player.mask.png'
source=Image.open(plate).convert('RGBA');sp=source.load();report_path=HERE/'verification/packing.json';report=json.loads(report_path.read_text())
for row in report['assets']:
 n=Path(row['key']).stem
 if int(n)>=8:continue
 c=next(g for g in json.loads((HERE/'geometries.json').read_text()) if g['n']==n);authority=next(r for r in audit['rows'] if r['frame']==n)
 positions=authority['source_identical_cloth_positions'];assert positions==[i for i,v in enumerate(c['indices']) if v in range(6,11)];assert len(positions)==210 and authority['xy']==c['background_xy']==[119,102]
 png=HERE/'packed'/row['key'];im=Image.open(png).convert('RGBA');ip=im.load()
 for q in positions:
  sx,sy=q%c['width'],q//c['width']
  for yy in range(4):
   for xx in range(4):
    x,y=sx*4+xx,sy*4+yy;ip[x,y]=sp[(119-90)*4+x,(102-65)*4+y][:3]+(ip[x,y][3],)
 im.save(png);row['candidate_sha256']=sha(png);row['stationary_cloth_join']=dict(source_audit=str(audit_path.relative_to(ROOT)),source_audit_sha256=sha(audit_path),plate=str(plate.relative_to(ROOT)),plate_sha256=sha(plate),mask=str(mask.relative_to(ROOT)),mask_sha256=sha(mask),source_pixels=210,method='Samme originalindeks paa samme TAV-koordinat. Bare RGB i210stasjonare kappepiksler deler fotografisk materiale med den innbygde figuren. Egen hanskefoto/pose og all alfa bevares.')
report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print('Delt ubevegelig kappe i006/007; hver hanskemaster beholdt')
