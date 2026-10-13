#!/usr/bin/env python3
"""Bygg lokalt konseptgalleri og oversiktsark fra valgte bilder."""
from pathlib import Path
import json,html,math
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parent
cards={
'balok':('Enorm kjeve, oransje hud og svart ryggmanke. Ekstra ørehorn er fjernet i v2.','Kjeve og hode må ha stabile fester gjennom bitt. Offerfragmenter beholder ridderfarge.'),
'war-beast':('Lav firbeint kropp, massiv svart manke, lys snute og lange lyse munnfremspring.','Kontroller fremspringenes nøyaktige feste i sammensatte originalposer før fast modell.'),
'mudman':('Bark, røtter og plantemateriale med avlangt lyst hode. V2 retter et for rundt skallepreg.','Rotgrep, fremkomst og nedsynking følger hver originalrute. Ingen menneskeføtter.'),
'troll':('Hårløs blåfiolett kropp, lange bein, røde øyne og grov treklubbe.','Klubbe, hender, torso og bein må møte hverandre riktig gjennom hele slaget.'),
'ratman':('Liten sammenkrøket pelsklump, lang snute, små bare lemmer og lang hale.','Samme hode under hopp og rulling. Bladskjulet er et separat element.'),
'guardian':('Cyan demon med klør, tendriler og blåhvit energivirvel. Foreslått overgangstilstand.','Ren virvel og formet kropp må kartlegges separat. Konseptet beviser ingen bestemt rute.'),
'dragon':('Røde skjell, gult øye, lange bakoverrettede lyse horn og matte vingemembraner.','Total anatomi er delvis forslag. Original kropp og vinger må sammensettes før spritesheets.'),
'black-knight':('Lukket stålhjelm, grå rustning, mørk lilla drakt og rett sverd.','Bevar den originale ridderkroppen og palettomleggingen. Ingen ny bossanatomi.'),
'trogg-axe':('Oransjebrun hud, lang krokete nese, grå hjelm, mørkt hår og blå drakt.','Lys kompakt øks. Kropp og våpen bindes til originale separate ruter.'),
'trogg-hammer':('Samme Trogg som øksen, med enkel rektangulær metallhammer.','Hammeren ligger faktisk i TroggAxe2. Gjenbruk kropp bare ved identiske originalruter.'),
'trogg-spear':('Samme Trogg, med langt mørkt skaft og liten lys spydspiss.','Bevar spydlengde, håndkontakt, treffpunkt og klipping. Ikke krymp cellen rundt våpenet.'),
}
prov=json.loads((P/'provenance.json').read_text());rows=[]
for e in prov:
 slug=e['slug'];one,two=cards[slug];refs=' '.join(f'<a href="{html.escape(r)}" target="_blank">Original {i+1}</a>' for i,r in enumerate(e['source_references']))
 rows.append(f'''<article id="{slug}"><a class="art" href="{e['selected']}" target="_blank"><img src="{e['selected']}" alt="Konsept: {html.escape(e['name'])}"></a><div class="copy"><p class="eyebrow">KONSEPT · IKKE AKTIVERT</p><h2>{html.escape(e['name'])}</h2><p>{one}</p><p class="next"><strong>Før spritesheets:</strong> {two}</p><nav>{refs}</nav></div></article>''')
css='''*{box-sizing:border-box}body{margin:0;background:#111412;color:#e9e4d9;font:16px/1.55 system-ui,sans-serif}header,main,footer{max-width:1500px;margin:auto;padding:32px}header{padding-top:48px}h1{font:clamp(30px,4vw,52px)/1.1 Georgia,serif;margin:12px 0 20px;color:#e5c88d}h2{font:28px/1.2 Georgia,serif;margin:6px 0 14px}.eyebrow{font-size:11px;letter-spacing:.12em;color:#c4ab7a;margin:0}.intro{max-width:900px;color:#c9c9be}.links{display:flex;gap:12px;flex-wrap:wrap;margin:25px 0}a{color:#e6cc96;text-decoration:none}a:hover{text-decoration:underline}.links a,nav a{border:1px solid #515748;border-radius:5px;padding:7px 12px}.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:24px}article{background:#1d221e;border:1px solid #373d34;border-radius:9px;overflow:hidden}.art{display:flex;height:330px;background:#dedbd3;align-items:center;justify-content:center}.art img{height:100%;width:100%;object-fit:contain}.copy{padding:24px}.copy p{font-size:15px}.next{color:#c9c9be;border-top:1px solid #3c4239;padding-top:16px}nav{display:flex;gap:8px;flex-wrap:wrap}nav a{font-size:12px}.notice{border-left:3px solid #bc9b64;padding:8px 20px;background:#22271f;color:#dad4c5;max-width:1050px}footer{color:#a8b0a1;font-size:13px}@media(max-width:1000px){.grid{grid-template-columns:repeat(2,minmax(0,1fr))}}@media(max-width:650px){.grid{grid-template-columns:1fr}header,main,footer{padding:22px}.art{height:360px}}'''
page=f'''<!doctype html><html lang="nb"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Moonstone · Monsterkonsepter</title><style>{css}</style><header><p class="eyebrow">MOONSTONE HD · VISUELT FORARBEID · 12. OKTOBER 2026</p><h1>Elleve monsterkonsepter.<br>Originalen setter rammene.</h1><p class="intro">Ett bilde per monster og våpenvariant, sammenlignet med originalgrafikken. Klikk på et konsept for full størrelse eller åpne originalarkene under hvert bilde. Bildene er tegnet med den innebygde bildegeneratoren og er ikke spritesheets.</p><div class="links"><a href="ANALYSE.md">Full analyse og produksjonskrav</a><a href="BRIEF.md">Bestilling og avgrensning</a><a href="overview.png" target="_blank">Samlet bildeoversikt</a><a href="source/inventory.json">Kildemål og SHA-er</a></div><p class="notice">Dragens samlede anatomi og Guardians tilstandsdeling må avklares før full spriteproduksjon. Konseptene er holdt utenfor spillets aktive HD-pakke. dg1.cel er ritualdansere i sluttsekvensen, ikke en ekstra monsterart.</p></header><main class="grid">{''.join(rows)}</main><footer>25 originalbanker · 1 302 ruter inklusive fragmenter og effekter · 11 valgte konsepter · 2 avviste førsteutkast bevart separat. Konseptenes plass og størrelse på siden angir ikke figurstørrelse i spillet.</footer></html>'''
(P/'index.html').write_text(page)
# Ren visningsmontasje, ikke nye eller endrede kunstmastere.
w=1536;cw=w//3;ch=460;out=Image.new('RGB',(w,4*ch+110),'#111412');d=ImageDraw.Draw(out)
fontfile='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';font=ImageFont.truetype(fontfile,25);small=ImageFont.truetype(fontfile,16)
d.text((25,20),'MOONSTONE HD | MONSTERKONSEPTER',font=font,fill='#e5c88d');d.text((25,60),'Forarbeid. Ikke spritesheets. Størrelse på arket er ikke spillstørrelse.',font=small,fill='#c9c9be')
for i,e in enumerate(prov):
 x=i%3*cw;y=110+i//3*ch;im=Image.open(P/e['selected']).convert('RGB');im.thumbnail((cw-24,ch-68));d.rectangle((x+8,y,x+cw-8,y+ch-20),fill='#dedbd3');out.paste(im,(x+(cw-im.width)//2,y+12+(ch-74-im.height)//2));d.rectangle((x+8,y+ch-58,x+cw-8,y+ch-20),fill='#23291f');d.text((x+20,y+ch-54),e['name'],font=font,fill='#e5c88d')
(P/'overview.png').parent.mkdir(exist_ok=True);out.save(P/'overview.png')
print('Galleri og oversiktsark bygget:',len(prov),'konsepter')
