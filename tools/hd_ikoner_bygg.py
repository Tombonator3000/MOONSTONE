#!/usr/bin/env python3
"""Bygg redigerbare SVG-konturer fra originale CEL-fargeflater. Ingen bildegenerator."""
import hashlib
import json
from pathlib import Path
from collections import defaultdict
import moonfiles as mf

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / 'art/hd-icons-2026-10-11'
SCALE = 8


def sha(data):
    return hashlib.sha256(data).hexdigest()


def contours(px, w, h, accept):
    # Marching squares paa pikselmidtpunktene. Entydige diagonaler forbindes,
    # diagonale enkeltpiksler forblir to separate deler, slik originalen krever.
    segments = []
    cases = {1:[(3,0)],2:[(0,1)],3:[(3,1)],4:[(1,2)],5:[(3,0),(1,2)],
             6:[(0,2)],7:[(3,2)],8:[(2,3)],9:[(0,2)],10:[(0,1),(2,3)],
             11:[(1,2)],12:[(3,1)],13:[(0,1)],14:[(3,0)]}
    def yes(x,y):
        return 0 <= x < w and 0 <= y < h and accept(px[y*w+x])
    for y in range(-1,h):
        for x in range(-1,w):
            code=sum(1<<i for i,(dx,dy) in enumerate([(0,0),(1,0),(1,1),(0,1)]) if yes(x+dx,y+dy))
            pts=[(2*x+2,2*y+1),(2*x+3,2*y+2),(2*x+2,2*y+3),(2*x+1,2*y+2)]
            segments.extend((pts[a],pts[b]) for a,b in cases.get(code,[]))
    edges=defaultdict(list)
    for a,b in segments: edges[a].append(b);edges[b].append(a)
    loops=[]
    while edges:
        start=next(iter(edges));cur=start;loop=[]
        while True:
            loop.append(cur);nxt=edges[cur].pop()
            if not edges[cur]:del edges[cur]
            edges[nxt].remove(cur)
            if not edges[nxt]:del edges[nxt]
            cur=nxt
            if cur==start:break
        # Fjern kollineaere punkter uten aa endre form eller enkeltpikselhull.
        keep=[]
        for i,p in enumerate(loop):
            a=loop[i-1];b=loop[(i+1)%len(loop)]
            if (p[0]-a[0])*(b[1]-p[1]) != (p[1]-a[1])*(b[0]-p[0]):keep.append(p)
        if len(keep)>=3:loops.append([(x/2,y/2) for x,y in keep])
    def fmt(x):return f'{x:.4f}'.rstrip('0').rstrip('.')
    parts=[]
    for points in loops:
        # 0.12 sourcepiksel avrunding. Kurven holder seg innen kildecellen;
        # sourcepikselmidtpunkter og hullenes identitet endres ikke.
        joins=[]
        for i,b in enumerate(points):
            a=points[i-1];c=points[(i+1)%len(points)]
            def near(v):
                dx,dy=v[0]-b[0],v[1]-b[1];length=(dx*dx+dy*dy)**.5
                f=min(.12,length*.2)/length
                return (b[0]+dx*f,b[1]+dy*f)
            joins.append((near(a),b,near(c)))
        p=joins[-1][2];s=f'M{fmt(p[0])} {fmt(p[1])}'
        for a,b,c in joins:s+=f'L{fmt(a[0])} {fmt(a[1])}Q{fmt(b[0])} {fmt(b[1])} {fmt(c[0])} {fmt(c[1])}'
        parts.append(s+'Z')
    return ''.join(parts)


def make_entry(key, px, w, h, pal, source, **extras):
    colors=sorted(set(px) if extras.get('opaque') else set(px)-{0})
    clip=f'M0 0H{w}V{h}H0Z' if extras.get('opaque') else contours(px,w,h,lambda v:v!=0)
    paths=[{'index':c,'d':contours(px,w,h,lambda v:v==c)} for c in colors]
    most=max(colors,key=px.count)
    entry={'key':key,'width':w,'height':h,'scale':SCALE,'source':source,
           'indices_sha256':sha(bytes(px)),'clip':clip,'base_index':most,'paths':paths,**extras}
    svg=['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d">'%(w*SCALE,h*SCALE,w,h),
         '<defs><clipPath id="shape"><path d="%s" clip-rule="evenodd"/></clipPath></defs>'%clip,
         '<g clip-path="url(#shape)">']
    for c,path in [(most,clip)]+[(r['index'],r['d']) for r in paths]:
        rgb=pal[c][:3];svg.append('<path d="%s" fill="rgb(%d,%d,%d)" fill-rule="evenodd"/>'%(path,*rgb))
    svg+=['</g></svg>']
    original=['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" shape-rendering="crispEdges">'%(w*SCALE,h*SCALE,w,h)]
    for j in range(h):
        for i in range(w):
            c=px[j*w+i]
            if c or extras.get('opaque'):original.append('<rect x="%d" y="%d" width="1" height="1" fill="rgb(%d,%d,%d)"/>'%(i,j,*pal[c][:3]))
    original.append('</svg>')
    original_path=ART/'source'/f'{key}.svg';original_path.parent.mkdir(parents=True,exist_ok=True);original_path.write_text('\n'.join(original)+'\n')
    target=ART/'svg'/f'{key}.svg';target.parent.mkdir(parents=True,exist_ok=True);target.write_text('\n'.join(svg)+'\n')
    return entry


def main():
    game=mf.Spill(str(ROOT/'Moonstonecd32-AMIGA.zip'))
    palette=json.loads((ART/'source/inventory-palette.json').read_text())['palette']
    banks={};entries=[]
    selections={'ki.cel':list(range(34))+[37],'po.cel':[0],'sel.cel':[0]}
    for name,frames in selections.items():
        data=game.les(name);banks[name]=sha(data);images,_=mf.cel_les(data)
        for i in frames:
            g=images[i];w,h=g['bredde'],g['hoyde'];packed=mf.plan_til_indeks(g['data'],g['plan'],w,h)
            bits=[1<<b for b in range(5) if g['maske']&(1<<b)]
            expanded=[sum(bit for p,bit in enumerate(bits) if v&(1<<p)) for v in packed]
            pal=palette
            if name=='po.cel':pal=[palette[(c+16)%32] for c in range(32)]
            if name=='sel.cel':
                _,rawpal,_=mf.piv_alle(game.les('ch.piv'))[0][0];pal=[mf.amiga_rgb(c) for c in rawpal]
            key=f'{name}/{i:03}'
            entry=make_entry(key,expanded,w,h,pal,{'file':name,'frame':i,'bank_sha256':sha(data)},plane_mask=g['maske'])
            if name=='po.cel':entry['hardware_sprite']=True;entry['palette_offset']=16
            entries.append(entry)
    # Fem pengesekkvalg er en del av tav.piv, ikke fem nye objekter.
    data=game.les('tav.piv');planes,pal,bp=mf.piv_alle(data)[0][0];full=mf.plan_til_indeks(bp,planes)
    palette=[mf.amiga_rgb(c) for c in pal]
    panels=[]
    for i,rect in enumerate([[272,4,310,29]]+[[277,35+28*n,305,51+28*n] for n in range(5)]):
        x0,y0,x1,y1=rect;px=[full[y*320+x] for y in range(y0,y1) for x in range(x0,x1)]
        key=f'scene-icons/{i:03}'
        # Hele det maalte pergamentfeltet beholdes. Bare konturene gjores glatte.
        entry=make_entry(key,px,x1-x0,y1-y0,palette,{'file':'tav.piv','frame':0,'bank_sha256':sha(data),'rect':rect},scene='tavern',rect=rect,opaque=True)
        entries.append(entry);panels.append({'key':key,'rect':rect,'uv_rect':[0,0,1,1],'foreground':True})
    # Kartmarkoerene kommer fra en naturlig, dokumentert originalramme.
    # Bare eksakte kildemønstre erstattes; andre statuser forblir originale.
    sample=json.loads((ART/'source/map-frame2000.json').read_text())
    bars=[(96,16),(232,16),(296,32),(136,40),(176,48),(240,48),(32,64),(80,64),
          (216,72),(272,80),(96,88),(208,104),(24,112),(104,120),(248,120),
          (48,136),(168,136),(120,144),(24,160),(152,176),(232,176),(288,176),(80,184)]
    shapes=[(x,y,9,5,'bar') for x,y in bars]+[(160,20,8,10,'village'),(300,100,8,10,'village'),(160,180,8,10,'village')]
    source=game.les('test')
    for i,(x,y,w,h,kind) in enumerate(shapes):
        expected=[sample['indices'][(y+j)*320+x+k] for j in range(h) for k in range(w)]
        px=[c if (kind=='bar' and not (j==3 and k in (0,8))) or (kind=='village' and c in (19,24,2,3)) else 0
            for j in range(h) for k,c in enumerate(expected[j*w:(j+1)*w])]
        entry=make_entry(f'map-icons/{i:03}',px,w,h,sample['palette'],
            {'file':'test','frame':8,'bank_sha256':sha(source),'runtime_frame':2000,'runtime_state':sample['state']},
            scene='world-map',rect=[x,y,x+w,y+h],expected=expected,dynamic=True)
        entries.append(entry)
    # Landemerkene beholdes paa kildekartets faktiske posisjoner. Polygonene
    # er manuelle uttak fra originalen, ikke ny arkitektur eller nye motiver.
    planes,pal,bp=mf.piv_alle(source)[0][8];map_px=mf.plan_til_indeks(bp,planes)
    palette=[mf.amiga_rgb(c) for c in pal]
    landmarks=[
        ([84,31,111,62],[(84,48),(87,45),(87,37),(90,36),(92,31),(95,34),(95,44),(98,36),(102,39),(102,45),(106,45),(110,50),(111,61),(87,62)],None),
        ([216,14,224,33],[(219,14),(221,14),(221,16),(220,18),(220,29),(222,29),(224,32),(216,33),(216,30),(219,29),(219,18)],None),
        ([150,96,166,108],None,{1,2,3,4}),
        ([88,151,108,168],None,{1,2,3,4,5,12}),
        ([242,89,253,112],[(244,89),(248,91),(248,97),(249,103),(253,109),(251,112),(242,112),(242,108),(244,102)],None),
        ([284,146,312,175],[(284,167),(284,159),(286,157),(289,157),(289,160),(292,162),(292,153),(295,151),(295,149),(298,146),(301,149),(301,155),(304,157),(305,161),(307,157),(310,159),(312,173),(304,175),(297,172),(292,168)],None),
    ]
    def inside(x,y,poly):
        value=False
        for i,(ax,ay) in enumerate(poly):
            bx,by=poly[i-1]
            if (ay>y)!=(by>y) and x<(bx-ax)*(y-ay)/(by-ay)+ax:value=not value
        return value
    landmark_overlays=[]
    for i,(rect,poly,stone_colors) in enumerate(landmarks):
        x0,y0,x1,y1=rect;w,h=x1-x0,y1-y0
        mask=[inside(x+.5,y+.5,poly) if poly else map_px[y*320+x] in stone_colors
              for y in range(y0,y1) for x in range(x0,x1)]
        if stone_colors:
            # Bare original skygge inntil original steinflate, ikke skogflaten.
            core=mask[:]
            for j in range(h):
                for k in range(w):
                    if map_px[(y0+j)*320+x0+k] not in (19,8):continue
                    if any(core[yy*w+xx] for yy in range(max(0,j-1),min(h,j+2)) for xx in range(max(0,k-1),min(w,k+2))):mask[j*w+k]=True
        px=[map_px[(y0+j)*320+x0+k] if mask[j*w+k] else 0 for j in range(h) for k in range(w)]
        key=f'map-landmarks/{i:03}'
        entries.append(make_entry(key,px,w,h,palette,{'file':'test','frame':8,'bank_sha256':sha(source),'rect':rect,'mask_polygon':poly,'stone_colors':sorted(stone_colors) if stone_colors else None},scene='world-map',rect=rect))
        landmark_overlays.append({'key':key,'rect':rect,'uv_rect':[0,0,1,1]})
    manifest={'schema':1,'method':'source-contours','banks':banks,'entries':entries}
    (ROOT/'web/hd/icons.json').write_text(json.dumps(manifest,ensure_ascii=False,separators=(',',':'))+'\n')
    (ART/'icons.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    package=json.loads((ROOT/'web/hd/manifest.json').read_text())
    for scene in package['scenes']:
        if scene['id']=='world-map':scene['overlays']=[o for o in scene.get('overlays',[]) if not o['key'].startswith('map-landmarks/')]+landmark_overlays
        if scene['id']=='tavern':scene['overlays']=[o for o in scene.get('overlays',[]) if not o['key'].startswith('scene-icons/')]+panels
    (ROOT/'web/hd/manifest.json').write_text(json.dumps(package,ensure_ascii=False,indent=2)+'\n')
    print(len(entries),'konturikoner, kildebanker',banks)

if __name__=='__main__':main()
