#!/usr/bin/env python3
"""Lag en avgrenset loot-fixtur med faktisk original CPU og tegneliste.

Bygg foerst med `make -C port headless`, og kjor for eksempel:
    python3 tools/lag_loot_fixture.py --out /tmp/moonstone-loot-proof

Fixturen gaar inn i en eksisterende kartlokasjon og avslutter en kontrollert
kamp. Den er ikke en naturlig full gjennomspilling. Bakgrunn, palett, tekst og
tegnebuffere skrives bare av originalkoden. Sluttlagringen ber originalen tegne
loot-skjermen paa nytt, saa en nettlesertest kan samle engangstegningene.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess


BOOT = ['--press', '100:esc:4', '--press', '700:down:10',
        '--press', '760:down:10', '--press', '820:down:10',
        '--press', '880:fire:10', '--press', '1300:fire:10',
        '--press', '1500:return:6']


def chunks(raw):
    if raw[:8] != b'MOONSAV2':
        raise ValueError('Fixturen krever lagringsformatet MOONSAV2')
    at = 20
    for _ in range(struct.unpack_from('<I', raw, 16)[0]):
        tag, version, size = struct.unpack_from('<4sII', raw, at)
        yield tag, version, at + 12, size
        at += 12 + size


def memory(save):
    raw = save.read_bytes()
    for tag, version, at, size in chunks(raw):
        if tag == b'MEM ':
            if version != 1 or size != 0x300000:
                raise ValueError('Uventet minneformat i lagringen')
            return raw[at:at + size]
    raise ValueError('Lagringen mangler MEM-delen')


def read(mem, address, size):
    if 0 <= address and address + size <= 0x100000:
        offset = address
    elif 0x200000 <= address and address + size <= 0x400000:
        offset = address - 0x100000
    else:
        raise ValueError(f'Adresse utenfor kildehukommelsen: {address:x}')
    return mem[offset:offset + size]


def word(mem, address):
    return int.from_bytes(read(mem, address, 2), 'big')


def longword(mem, address):
    return int.from_bytes(read(mem, address, 4), 'big')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root, out = args.root.resolve(), args.out.resolve()
    binary = root / 'port/moonstone-headless'
    if not binary.is_file():
        parser.error(f'Bygg foerst: make -C {root / "port"} headless')
    out.mkdir(parents=True, exist_ok=True)
    commands = []

    def run(name, options):
        command = [str(binary), '--headless', '--online-meny', '--log', '0'] + list(map(str, options))
        result = subprocess.run(command, cwd=root, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        (out / (name + '.log')).write_text(result.stdout)
        commands.append({'stage': name, 'argv': command})
        if result.returncode or 'Stoppet i bilde' in result.stdout:
            raise RuntimeError(f'Native-fixturen stoppet; se {out / (name + ".log")}')
        return result.stdout

    seed = out / 'map.sav'
    run('map', BOOT + ['--frames', 2001, '--save-state', f'2000:{seed}'])
    mem = memory(seed)
    knight = longword(mem, 0x8d9ac)
    assert (word(mem, knight + 0x7e), word(mem, knight + 0x80)) == (10, 10), 'Uventet startposisjon'
    chest = longword(mem, 0x8cd6e + 0x44) + 18 * 22
    assert (word(mem, chest + 10), word(mem, chest + 12)) == (24, 24), 'Originalens lokasjon18 er endret'
    assert word(mem, chest + 4) == 32, 'Originalens monstervalg i lokasjon18 er endret'

    # Posisjonsfixturen settes utenfor loekka. Ett ekte bevegelsessteg lar
    # originalen bygge sin egen interaksjonstabell foer fire og kartvalg2.
    choices = out / 'choices.sav'
    run('choices', ['--load-state', seed,
        '--skriv', f'2019:{knight + 0x7e:x}:23:2',
        '--skriv', f'2019:{knight + 0x80:x}:24:2',
        '--skriv', f'2019:{chest + 6:x}:0:2',
        '--press', '2020:right:4', '--press', '2040:fire:4',
        '--frames', 600, '--save-state', f'600:{choices}'])
    mem = memory(choices)
    assert longword(mem, 0x8eeec + 8) == chest and longword(mem, 0x8eeec + 12) == 2, 'Manglende originalt kartvalg2'

    battle = out / 'battle.sav'
    run('battle', ['--load-state', choices, '--press', '2610:2:4',
        '--frames', 700, '--save-state', f'700:{battle}'])
    mem = memory(battle)
    assert longword(mem, 0x95f28) == chest, 'Kampen kom ikke fra den valgte lokasjonen'
    actors = longword(mem, 0x8cdf4)
    alive = [actors + i * 0x84 for i in range(20) if longword(mem, actors + i * 0x84)]
    assert alive, 'Kampen mangler originaltegnet monster'
    writes = [(address, 0, 4) for address in alive] + [(address + 0x50, 0, 2) for address in alive]
    writes += [(knight + 0x50, 20, 2), (0x8ce9c, 0, 1), (0x8cea4, 1, 1)]
    loot = out / 'loot.sav'
    options = ['--load-state', battle]
    for address, value, size in writes:
        options += ['--skriv', f'3301:{address:x}:{value}:{size}']
    run('loot', options + ['--frames', 300, '--save-state', f'300:{loot}',
        '--dump', f'3600:{out / "loot.bin"}', '--lag', f'3599:{out / "loot"}'])
    mem = memory(loot)
    assert longword(mem, 0x8e8ca) == 2 and word(mem, 0x98088) == 1, 'Originalen tegnet ikke loot-skjermen'
    assert read(mem, 0x8ce3e, 1) == b'\x02', 'Originalens kampresultat er ikke seier'

    # Be om original redraw og flytt pekeren uten fire. MENY_CMD_PEKER ville
    # ogsaa klikke, og et klikk paa denne soeylen avslutter loot-skjermen.
    cursor = out / 'loot-cursor.sav'
    log = run('loot-cursor', ['--load-state', loot,
        '--skriv', '3601:8e8b4:1:2', '--skriv', '3750:98092:155:2', '--skriv', '3750:98094:150:2',
        '--frames', 250, '--save-state', f'250:{cursor}', '--dump', f'3850:{out / "loot-cursor.bin"}',
        '--lag', f'3849:{out / "loot-cursor"}', '--tegneliste', '3601:100',
        '--shot-every', 250, '--shot-dir', out])
    mem = memory(cursor)
    assert longword(mem, 0x8e8ca) == 2 and word(mem, 0x98088) == 1
    assert (word(mem, 0x98092), word(mem, 0x98094)) == (155, 150)
    assert longword(mem, 0x95f28) == chest
    match = re.search(r'lag bilde 3849: gyldig, bakgrunn ([0-9a-f]{8}), forgrunn (\d+) piksler, lys (\d+)', log)
    assert match and match[1] == 'e868fda9' and int(match[3]) > 0, 'Loot-bakgrunnen eller paletten stemmer ikke'
    assert all(f'ki.cel bilde {frame} ' in log for frame in (26, 31, 32, 33, 34, 35, 36)), 'Originalens kiste/dekor mangler i trace'

    # Ingen geometrifiks i minnet: bare originalens dokumenterte redraw-flag.
    # Den foerste CPU-loekka etter browser-load gjenutsteder engangstegningene.
    raw = bytearray(cursor.read_bytes())
    for tag, _, at, _ in chunks(raw):
        if tag == b'MEM ':
            raw[at + 0x8e8b4:at + 0x8e8b4 + 2] = b'\x00\x01'
    ready = out / 'loot-redraw-ready.sav'
    ready.write_bytes(raw)
    replay_dir = out / 'ready-replay'
    replay_dir.mkdir(exist_ok=True)
    replay = replay_dir / 'replay.sav'
    replay_log = run('ready-replay', ['--load-state', ready, '--frames', 200,
        '--save-state', f'200:{replay}', '--lag', f'4049:{replay_dir / "replay"}',
        '--tegneliste', '3851:100', '--shot-every', 200, '--shot-dir', replay_dir])
    replay_mem = memory(replay)
    assert longword(replay_mem, 0x8e8ca) == 2 and word(replay_mem, 0x98088) == 1
    assert (word(replay_mem, 0x98092), word(replay_mem, 0x98094)) == (155, 150)
    assert 'bakgrunn e868fda9' in replay_log
    assert all(f'ki.cel bilde {frame} ' in replay_log for frame in (26, 31, 32, 33, 34, 35, 36))
    original_image = replay_dir / 'shot_00200.png'
    report = {
        'scope': 'Kontrollert original CPU-kamp/loot-fixtur, ikke naturlig full gjennomspilling. Ingen bakgrunns-, palett- eller tegnebufferpatcher.',
        'ready_sav': str(ready), 'ready_sha256': sha(ready), 'native_sav': str(cursor),
        'frame': 3850, 'original_background_hash': match[1], 'foreground_pixels': int(match[2]), 'light': int(match[3]),
        'pointer': [155, 150], 'source_chest': f'{chest:x}', 'source_monsters': [f'{a:x}' for a in alive],
        'browser_recipe': 'Last ready_sav, nullstill frontendens scene/tegneliste, kjor original CPU minst200bilder med nyttBilde(tegneliste()) hvert bilde, og vent paa HD-bakgrunnen.',
        'ready_replay_original_image': str(original_image), 'ready_replay_original_sha256': sha(original_image),
        'controlled_endcombat_writes': [[f'{a:x}', value, size] for a, value, size in writes],
        'ready_save_change': {'address': '8e8b4', 'value': 1, 'size': 2, 'purpose': 'Original redraw request etter loading'},
        'commands': commands,
        'hashes': {p.name: sha(p) for p in (cursor, ready, out / 'loot-cursor.bin', out / 'loot-cursor_bak.png', out / 'loot-cursor_for.png', out / 'shot_00250.png')},
    }
    report_path = out / 'fixture.json'
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'ready_sav': str(ready), 'ready_sha256': sha(ready), 'hash': match[1], 'report': str(report_path)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
