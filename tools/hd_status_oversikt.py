#!/usr/bin/env python3
"""Lag en kilde-/manifestbundet HD-oversikt. Endrer bare valgt utmappe.

python3 tools/hd_status_oversikt.py --out docs/hd-status-2026-10-12 \
    --candidate-root /sti/til/separat/artcheckout

Kandidatrepoet leses uten aa kjore dets verktøy eller endre dets filer.
Dette er fildekning, ikke en paastand om naturlig animasjons-/runtimedekning.
"""
import argparse
import collections
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

from PIL import Image
import moonfiles as mf
import hd_bestilling as hb

ROOT = Path(__file__).resolve().parents[1]
sha = lambda data: hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--candidate-root', type=Path)
    args = parser.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    game = mf.Spill(str(ROOT/'Moonstonecd32-AMIGA.zip'))
    raw_manifest = (ROOT/'web/hd/manifest.json').read_bytes()
    manifest = json.loads(raw_manifest)
    active = {e['path'].lower():e for e in manifest['files']}
    assert len(active)==len(manifest['files'])
    for e in manifest['files']:
        data=(ROOT/'web/hd'/e['path']).read_bytes()
        assert sha(data)==e['sha256'] and len(data)==e['bytes'],e['path']
    with tempfile.TemporaryDirectory() as temporary:
        regenerated=Path(temporary)/'bestilling.csv'
        subprocess.run([sys.executable,str(ROOT/'tools/hd_bestilling.py'),str(ROOT/'Moonstonecd32-AMIGA.zip'),str(regenerated)],check=True,stdout=subprocess.DEVNULL)
        order_identical=regenerated.read_bytes()==(ROOT/'docs/hd-bestilling-liste.csv').read_bytes()
        regenerated_sha=sha(regenerated.read_bytes())
        orders=list(csv.DictReader(regenerated.open(),delimiter=';'))
    missing_orders=[e for e in orders if e['hd_fil'].lower() not in active]
    active_revisions=[e['hd_fil'] for e in orders if e['hd_fil'].lower() in active]
    program,mog=game.les('data/program').lower(),game.les('data/mog').lower()
    def intro(f):
        return f.lower().encode() in program and f.lower().encode() not in mog
    def rank(b):
        f=b[0]
        if intro(f):return 4,2,f.lower(),b[1]
        if f.lower() in ('po.cel','small.font'):return 1,1,f.lower(),b[1]
        return hb.figur_info(f,b[1])[0],0 if f.startswith('KN') else 1,f.lower(),b[1]
    images,empty,bank_sha=[],[],{}
    for path in sorted(game.data_filer(),key=str.lower):
        bank=path.split('/',1)[1]
        data=game.filer[path]
        if not(bank.lower().endswith(hb.FIGURER) and mf.er_cel(data)):continue
        bank_sha[bank]=sha(data)
        for n,b in enumerate(mf.cel_les(data)[0]):
            if not b['plan']:
                empty.append((bank,n,b['bredde'],b['hoyde']))
                continue
            indices=hb.utvid_indekser(mf.plan_til_indeks(b['data'],b['plan'],b['bredde'],b['hoyde']),b['maske'])
            images.append((bank,n,b['bredde'],b['hoyde'],indices))
    images.sort(key=rank)
    first,master,bybank={}, {},collections.defaultdict(list)
    for b in images:
        key=b[2],b[3],b[4]
        first.setdefault(key,b)
        master[b[:2]]=first[key][:2]
        bybank[b[0],b[2],b[3]].append(b)
    def remap_match(kn,he):
        pairs={}
        for p,q in zip(kn,he):
            if pairs.setdefault(p,q)!=q or (p!=q and hb.HE_BYTTE.get(p)!=q):return False
        return not(set(pairs)&set(hb.HE_BYTTE.values()))
    for f,n,w,h,indices in images:
        if f not in hb.HE_TIL_KN or master[f,n]!=(f,n):continue
        for kn in sorted(bybank[hb.HE_TIL_KN[f],w,h],key=lambda b:(b[1]!=n,b[1])):
            if remap_match(kn[4],indices):
                old,target=master[f,n],master[kn[:2]]
                master.update({k:target for k,v in master.items() if v==old})
                break
    def route(k):return '%s/%03d.png'%k
    active_masters={master[b[:2]] for b in images if route(b[:2]).lower() in active}
    missing_masters=set(master.values())-active_masters
    assert missing_masters=={(e['fil'],int(e['bilde'])) for e in missing_orders if not e['hd_fil'].startswith('bg/')}
    candidate_routes,candidate_info={},None
    if args.candidate_root:
        candidate=args.candidate_root.resolve()
        contract_path=candidate/'art/hd-completion-figures-2026-10-11/delivery-progress-009-activation-v1.json'
        contract=json.loads(contract_path.read_bytes())
        for name,digest in contract['expected_new_files'].items():
            data=(candidate/'web/hd'/name).read_bytes()
            assert sha(data)==digest,name
            if name.endswith('.png') and not name.endswith('.mask.png'):candidate_routes[name.lower()]=digest
        candidate_info={'checkout':str(candidate),'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=candidate,text=True).strip(),
            'contract_status':contract['status'],'contract_sha256':sha(contract_path.read_bytes()),
            'manifest_sha256':sha((candidate/'web/hd/manifest.json').read_bytes()),
            'new_routes':len(candidate_routes),'new_files':len(contract['expected_new_files']),
            'new_masks':sum(k.endswith('.mask.png') for k in contract['expected_new_files']),
            'photographic_masters':contract['photographic_masters'],'preserved_original_routes':contract['preserved_original_routes']}
    legacy=json.loads((ROOT/'art/photoreal/catalog.json').read_bytes())
    legacy_by_key={}
    for e in legacy['rows']:
        if not e['id'].startswith('sprite:'):continue
        _,bank,n=e['id'].split(':')
        assert sha((ROOT/e['photo']).read_bytes())==e['photo_sha256'],e['photo']
        legacy_by_key[route((bank,int(n))).lower()]=e['status']
    rows=[]
    for bank,n,w,h,indices in images:
        key=route((bank,n));entry=active.get(key.lower())
        black_shadow=False
        exact_shadow=False
        if entry and set(indices)<={0,5} and bank.lower()!='mys.cel':
            black_shadow=True
            im=Image.open(ROOT/'web/hd'/entry['path']).convert('RGBA')
            original=Image.frombytes('RGBA',(w,h),bytes(v for c in indices for v in (0,0,0,255 if c else 0)))
            exact_shadow=im.tobytes()==original.resize(im.size,Image.Resampling.NEAREST).tobytes()
        needed=bool(hb.maskefarger(bank,n)&set(indices))
        mask=key[:-4]+'.mask.png'
        if entry and needed:assert mask.lower() in active,mask
        status=('missing_hd' if not entry else 'preserved_original_black_shadow' if exact_shadow else
                'active_black_shadow_redraw' if black_shadow else 'active_hd')
        rows.append({'bank':bank,'frame':n,'source_width':w,'source_height':h,'route':key,
            'source_bank_sha256':bank_sha[bank],'source_indices_sha256':sha(indices),
            'master':route(master[bank,n]),'master_group':('Intro og slutt' if intro(master[bank,n][0]) else
                'Skrift og peker' if master[bank,n][0].lower() in ('po.cel','small.font') else hb.figur_info(*master[bank,n])[1]),
            'is_master':int(master[bank,n]==(bank,n)),'status':status,'palette_mask_needed':int(needed),
            'palette_mask_active':int(mask.lower() in active),'active_sha256':entry['sha256'] if entry else '',
            'local_candidate_009_sha256':candidate_routes.get(key.lower(),''),'legacy_candidate_status':legacy_by_key.get(key.lower(),'')})
    for bank,n,w,h in empty:
        rows.append(dict.fromkeys(rows[0],''))
        rows[-1].update(bank=bank,frame=n,source_width=w,source_height=h,route=route((bank,n)),source_bank_sha256=bank_sha[bank],status='empty_source',is_master=0,palette_mask_needed=0,palette_mask_active=0)
    rows.sort(key=lambda e:(e['bank'].lower(),e['frame']))
    banks=[]
    for bank in sorted(bank_sha,key=str.lower):
        selected=[e for e in rows if e['bank']==bank]
        banks.append({'bank':bank,'source_routes':len(selected),'empty_source_routes':sum(e['status']=='empty_source' for e in selected),
            'active_routes':sum(e['status'].startswith(('active','preserved')) for e in selected),
            'preserved_original_black_shadow_routes':sum(e['status']=='preserved_original_black_shadow' for e in selected),
            'active_black_shadow_redraw_routes':sum(e['status']=='active_black_shadow_redraw' for e in selected),
            'active_masters':sum(e['is_master'] and e['status'].startswith(('active','preserved')) for e in selected),
            'remaining_routes':sum(e['status']=='missing_hd' for e in selected),
            'remaining_masters':sum(e['status']=='missing_hd' and e['is_master'] for e in selected),
            'remaining_master_masks':sum(e['status']=='missing_hd' and e['is_master'] and e['palette_mask_needed'] for e in selected),
            'remaining_concrete_masks':sum(e['status']=='missing_hd' and e['palette_mask_needed'] for e in selected),
            'active_masks':sum(e['palette_mask_active'] for e in selected),
            'local_candidate_009_routes':sum(bool(e['local_candidate_009_sha256']) for e in selected)})
    for name,data in [('ruter.csv',rows),('banker.csv',banks)]:
        with (args.out/name).open('w',newline='',encoding='utf-8') as file:
            writer=csv.DictWriter(file,fieldnames=list(data[0]),delimiter=';',lineterminator='\n')
            writer.writeheader();writer.writerows(data)
    summary={'schema':1,'checked_utc':datetime.now(timezone.utc).isoformat(),
        'status':'passed' if order_identical else 'needs_order_refresh',
        'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'manifest_sha256':sha(raw_manifest),'source_zip_sha256':sha((ROOT/'Moonstonecd32-AMIGA.zip').read_bytes()),
        'order_sha256':sha((ROOT/'docs/hd-bestilling-liste.csv').read_bytes()),'order_regenerated_sha256':regenerated_sha,
        'order_regenerated_identical':order_identical,'active_assets_flagged_for_revision':active_revisions,
        'manifest_files_verified':len(manifest['files']),'active_pngs':manifest['images'],
        'active_backgrounds':sum(e['kind']=='background' for e in manifest['files']),
        'active_palette_mask_pngs':sum(e['path'].endswith('.mask.png') for e in manifest['files']),
        'original_figure_routes':len(rows),'empty_original_routes':len(empty),'original_independent_masters':len(set(master.values())),
        'active_original_bank_routes':sum(e['active_routes'] for e in banks),'active_original_masters':len(active_masters),
        'preserved_original_black_shadow_routes':sum(e['status']=='preserved_original_black_shadow' for e in rows),
        'preserved_original_black_shadow_masters':len({e['master'] for e in rows if e['status']=='preserved_original_black_shadow'}),
        'active_black_shadow_redraw_routes':sum(e['status']=='active_black_shadow_redraw' for e in rows),
        'remaining_masters':len(missing_masters),'remaining_routes':sum(e['status']=='missing_hd' for e in rows),
        'remaining_master_masks':sum(e['trenger_maske']=='ja' for e in missing_orders),'remaining_concrete_masks':sum(e['status']=='missing_hd' and e['palette_mask_needed'] for e in rows),
        'remaining_by_group':dict(collections.Counter(e['gruppe'] for e in missing_orders)),
        'legacy_catalog_entries':len(legacy['rows']),'legacy_sprite_candidates':len(legacy_by_key),
        'legacy_sprite_candidates_without_active_route':sum(k not in active for k in legacy_by_key),
        'local_unmerged_candidates':candidate_info,'runtime_scope':'Fildekning. Aktive bilder kan fortsatt ha tegneregresjoner; naturlig full animasjonsdekning er ikke bevist.'}
    (args.out/'audit.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(summary,ensure_ascii=False))
    if not order_identical:
        raise SystemExit('Bestillingslisten er utdatert; auditdata er skrevet med status needs_order_refresh.')


if __name__=='__main__':
    main()
