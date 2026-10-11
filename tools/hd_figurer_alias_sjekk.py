#!/usr/bin/env python3
"""Originale HE-indeksaliaser og allerede aktiv masterkontekst i aktiveringsporten."""
import copy
import hashlib
import json
from pathlib import Path
import hd_figurer_aktiver as gate
import moonfiles as mf
import hd_bestilling as order

root = gate.ROOT
game = mf.Spill(str(root / 'Moonstonecd32-AMIGA.zip'))
checks = []

def pixels(bank, frame):
    r = mf.cel_les(game.les('data/' + bank))[0][frame]
    return order.utvid_indekser(mf.plan_til_indeks(r['data'], r['plan'], r['bredde'], r['hoyde']), r['maske'])

for frame in range(64):
    source = pixels('KN3.ob', frame)
    he = pixels('HE3.ob', frame)
    entry = dict(bank='HE3.ob', frame=frame,
                 index_remap={str(i): i + 3 if 6 <= i <= 8 else i for i in set(source)})
    gate.alias_indices(dict(bank='KN3.ob', frame=frame), entry, source, he)
    checks.append(f'KN3/HE3/{frame:03}: original geometri og indeksflytting')

def rejects(name, fn, expected=None):
    try:
        fn()
    except AssertionError as error:
        if expected is not None:
            assert expected in str(error), (name, str(error))
        checks.append(name)
    else:
        raise AssertionError('Ulovlig alias ble godkjent: ' + name)

source = pixels('KN3.ob', 0)
he = pixels('HE3.ob', 0)
master = dict(bank='KN3.ob', frame=0)
entry = dict(bank='HE3.ob', frame=0, index_remap={str(i): i+3 if 6<=i<=8 else i for i in set(source)})
bad = copy.deepcopy(entry);bad['index_remap']['6'] = 11
rejects('Feil originalindeks avvises', lambda: gate.alias_indices(master, bad, source, he))
bad = copy.deepcopy(entry);bad['bank'] = 'HE2.ob'
rejects('Feil HE-bank avvises', lambda: gate.alias_indices(master, bad, source, he))
rejects('Annen aliasgeometri avvises', lambda: gate.alias_indices(master, entry, source, bytes([31])+he[1:]))

delivery = json.loads((root / 'art/hd-completion-figures-2026-10-11/production/activation-set-troll-003-with-alias.json').read_text())
context = next(e for e in delivery['entries'] if e.get('existing_master'))
png = root / context['png']
gate.checked_active(context['key'], png)
checks.append('Allerede aktiv master er eksakt bevist kontekst')
rejects('Uaktiv kontekstmaster avvises', lambda: gate.checked_active('TROLL1.CEL/999.png', png))
other = root / 'web/hd/KN3.ob/000.png'
rejects('Annet aktivt kontekstbilde avvises', lambda: gate.checked_active(context['key'], other))
extra_path = root / 'art/hd-completion-figures-2026-10-11/production/activation-set-troll-004.json'
old_extra = json.loads(extra_path.read_text())
# Nye negative proever starter med en gyldig leveranse paa gjeldende renderer.
# Ellers kunne en urelatert gammel kodehash gi falskt bestaaende avvisning.
current = json.loads((root/'art/hd-completion-figures-2026-10-11/production/activation-set-balok-008-attack-seven-ankle-v5.json').read_text())
current_count = len(gate.validate(current))
extra_delivery = copy.deepcopy(current)
extra_delivery['entries'][0]['additional_generated_material'] = next(e['additional_generated_material'] for e in old_extra['entries'] if e.get('additional_generated_material'))
assert len(gate.validate(extra_delivery)) == current_count
checks.append('Tilleggsmaterialproeve er gyldig foer negativ mutasjon')
bad = copy.deepcopy(extra_delivery)
next(e for e in bad['entries'] if e.get('additional_generated_material'))['additional_generated_material']['raw_sha256'] = '0'*64
rejects('Annet generert tilleggsraabilde avvises', lambda: gate.validate(bad), 'Endret fil')
bad = copy.deepcopy(extra_delivery)
bad['entries'][0]['art_record_sha256'] = '0'*64
rejects('Endret materialproveniens avvises', lambda: gate.validate(bad), 'Endret fil')
old_many = json.loads((root / 'art/hd-completion-figures-2026-10-11/production/activation-set-troll-005-join-v1.json').read_text())
many_delivery = copy.deepcopy(current)
many_delivery['entries'][0]['additional_generated_materials'] = next(e['additional_generated_materials'] for e in old_many['entries'] if e.get('additional_generated_materials'))
assert len(gate.validate(many_delivery)) == current_count
checks.append('Materiallisteproeve er gyldig foer negativ mutasjon')
bad = copy.deepcopy(many_delivery)
next(e for e in bad['entries'] if e.get('additional_generated_materials'))['additional_generated_materials'][-1]['raw_sha256'] = '0'*64
rejects('Endret ekstra raabilde i materialliste avvises', lambda: gate.validate(bad), 'Endret fil')
bad = copy.deepcopy(many_delivery)
next(e for e in bad['entries'] if e.get('additional_generated_materials'))['additional_generated_materials'][-1]['prompt_sha256'] = '0'*64
rejects('Endret ekstra prompt i materialliste avvises', lambda: gate.validate(bad), 'Endret fil')
report = dict(status='passed', count=len(checks), checks=checks,
              source_zip_sha256=hashlib.sha256((root/'Moonstonecd32-AMIGA.zip').read_bytes()).hexdigest())
out = root / 'art/hd-completion-figures-2026-10-11/verification/activation-alias-gates.json'
out.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
print(f'{len(checks)} alias- og kontekstporter bestaar.')
