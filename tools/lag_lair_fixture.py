#!/usr/bin/env python3
"""Lag kildebaserte lair-fixturer: seier med gull, noekkel og helt tom loot.

    make -C port headless
    python3 tools/lag_lair_fixture.py --out /tmp/moonstone-lairs

Dette er kontrollerte kamper, ikke en naturlig full gjennomspilling. Originalen
velger kampen, registrerer seieren, tegner loot, behandler exit og rydder kartet.
Alle oppsettsinngrep og kommandoer lagres i fixture.json. Ingen spillkode,
bakgrunn, palett, loot, seiersflagg eller stedskoordinater endres av generatoren.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

from lag_loot_fixture import BOOT, memory, longword, word, read


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
    commands, cases = [], []

    def run(name, options):
        cmd = [str(binary), '--headless', '--online-meny', '--log', '0'] + list(map(str, options))
        r = subprocess.run(cmd, cwd=root, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        (out / (name + '.log')).write_text(r.stdout)
        commands.append({'stage': name, 'argv': cmd})
        if r.returncode or 'Stoppet i bilde' in r.stdout:
            raise RuntimeError(f'Native-fixturen stoppet: {out / (name + ".log")}')
        return r.stdout

    seed = out / 'map.sav'
    run('map', BOOT + ['--frames', 2001, '--save-state', f'2000:{seed}'])
    for idx in (19, 20, 18):
        name = f'lair{idx}'
        mem = memory(seed)
        knight, table = longword(mem, 0x8d9ac), longword(mem, 0x8cdb2)
        chest = table + idx * 22
        x, y = word(mem, chest + 10), word(mem, chest + 12)
        assert (x, y) == {19: (96, 16), 20: (136, 40), 18: (24, 24)}[idx]
        original_gold = word(mem, chest + 8)
        original_items = list(read(mem, longword(mem, chest), 24))
        assert word(mem, chest + 20) == 0
        if idx == 19:
            assert not original_gold and not any(original_items)
        elif idx == 20:
            assert original_gold and not any(original_items)
        else:
            assert not original_gold and original_items[20] == 1

        # Bare ridderens testposisjon og lairens ventetid settes. Ett originalt
        # hoeyresteg bygger interaksjonstabellen foer vanlig fire/kartvalg.
        battle = out / (name + '-battle.sav')
        setup = [(knight + 126, x - 1, 2), (knight + 128, y, 2), (chest + 6, 0, 2)]
        options = ['--load-state', seed]
        for a, v, s in setup:
            options += ['--skriv', f'2019:{a:x}:{v}:{s}']
        run(name + '-enter', options + ['--press', '2020:right:4', '--press', '2040:fire:4',
            '--frames', 600, '--save-state', f'600:{battle}'])
        mem, end = memory(battle), 2600
        if longword(mem, 0x8d9ac) == knight:
            choice = out / (name + '-battle2.sav')
            run(name + '-choice', ['--load-state', battle, '--press', '2610:2:4',
                '--frames', 700, '--save-state', f'700:{choice}'])
            battle, mem, end = choice, memory(choice), 3300
        assert longword(mem, 0x95f28) == chest
        actors = longword(mem, 0x8cdf4)
        alive = [actors + i * 0x84 for i in range(20) if longword(mem, actors + i * 0x84)]
        assert alive
        # Avgrenset sluttkampfixtur. Original $08040A avgjoer resultatet,
        # $080D1C registrerer foerste seier og $08AAC4 tegner loot.
        finish = [(a, 0, 4) for a in alive] + [(a + 80, 0, 2) for a in alive]
        finish += [(knight + 80, 20, 2), (0x8ce9c, 0, 1), (0x8cea4, 1, 1)]
        loot = out / (name + '-loot.sav')
        options = ['--load-state', battle]
        for a, v, s in finish:
            options += ['--skriv', f'{end + 1}:{a:x}:{v}:{s}']
        run(name + '-win', options + ['--frames', 300, '--save-state', f'300:{loot}',
            '--lag', f'{end + 299}:{out}/{name}-loot'])
        end += 300
        mem = memory(loot)
        assert word(mem, chest + 20) == 1 and longword(mem, 0x8e8ca) == 2
        assert read(mem, 0x8ce3e, 1) == b'\x02'
        case = {'location': idx, 'address': chest, 'position': [x, y], 'loot_sav': str(loot),
                'gold': original_gold, 'items': original_items,
                'setup_writes': setup, 'controlled_endcombat_writes': finish}
        for view in (False, True):
            suffix = '-view' if view else '-natural'
            target = out / (name + suffix + '.sav')
            options = ['--load-state', loot]
            # Separat visningsfixtur: ridderen flyttes16piksler foer originalens
            # kartredraw, saa den ikke dekker porten. Natural har ingen slik flytt.
            if view:
                options += ['--skriv', f'{end + 1}:{knight + 126:x}:{x + 16}:2']
            log = run(name + suffix, options + ['--meny', f'{end + 10}:14:{155 | 150 << 16}',
                '--frames', 300, '--save-state', f'300:{target}', '--lag', f'{end + 299}:{out}/{name}{suffix}',
                '--tegneliste', f'{end + 100}:200', '--vakt', f'{chest + 10:x}'])
            mem = memory(target)
            assert word(mem, chest + 20) == 1
            assert word(mem, chest + 8) == original_gold
            assert list(read(mem, longword(mem, chest), 24)) == original_items
            after = [word(mem, chest + 10), word(mem, chest + 12)]
            assert after == ([65535, 65535] if idx == 19 else [x, y])
            if idx == 19:
                assert 'pc 080d80:' in log and '= ffffffff' in log
            case[suffix[1:] + '_sav'] = str(target)
            case[suffix[1:] + '_position_after'] = after
        cases.append(case)
    report = {'scope': __doc__, 'seed_sav': str(seed), 'cases': cases, 'commands': commands,
              'sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in out.glob('*.sav')}}
    path = out / 'fixture.json'
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'report': str(path), 'cases': len(cases)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
