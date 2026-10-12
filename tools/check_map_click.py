#!/usr/bin/env python3
"""Kontroller klikkreise med virkelig originalkode, lagring og C-kroker."""
import argparse
from pathlib import Path
import struct
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent.parent
PROG = ROOT / 'port/moonstone-headless'
BOOT = ['--press', '100:esc:4', '--press', '700:down:10', '--press', '760:down:10',
        '--press', '820:down:10', '--press', '880:fire:10', '--press', '1300:fire:10', '--press', '1500:return:6']


def run(args):
    subprocess.run([str(PROG), '--headless', '--online-meny', '--log', '0'] + list(map(str, args)),
                   cwd=ROOT, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def pos(data):
    knight = struct.unpack_from('>I', data, 0x8d9ac)[0]
    return struct.unpack_from('>HH', data, knight + 0x7e)


def parts(data):
    at = 20
    for _ in range(struct.unpack_from('<I', data, 16)[0]):
        tag, ver, size = struct.unpack_from('<4sII', data, at)
        yield tag, ver, data[at + 12:at + 12 + size]
        at += 12 + size


def pointer(save):
    return next(body for tag, _, body in parts(save.read_bytes()) if tag == b'PEKR')


def target(x, y):
    # Den opprinnelige MI-ruten er 9x10: fotpunkt x+4,y+10.
    return str((x + 4) | (y + 10) << 16)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ut', type=Path)
    args = parser.parse_args()
    temporary = tempfile.TemporaryDirectory(prefix='moonstone-map-') if not args.ut else None
    out = args.ut or Path(temporary.name)
    out.mkdir(parents=True, exist_ok=True)
    checks = 0

    def check(ok, text):
        nonlocal checks
        if not ok:
            raise AssertionError(text)
        checks += 1
        print('OK   ' + text, flush=True)

    seed = out / 'kart.sav'
    run(BOOT + ['--frames', '2001', '--save-state', f'2000:{seed}', '--dump', f'2000:{out}/kart.bin'])
    initial = (out / 'kart.bin').read_bytes()
    check(pos(initial) == (10, 10), 'ekte enspillerspill begynner ved 10,10')

    def route(name, extra=(), until=350, command=None, nohooks=False):
        dump, save = out / (name + '.bin'), out / (name + '.sav')
        command = command or target(20, 30)
        options = ['--load-state', seed, '--meny', f'2020:15:{command}', '--frames', str(until),
                   '--dump', f'{2000 + until}:{dump}', '--save-state', f'{until}:{save}']
        run(options + list(extra) + (['--nohooks'] if nohooks else []))
        return dump.read_bytes(), save

    data, _ = route('foerste', until=21)
    check(pos(data) == (11, 11), 'foerste reisesteg bruker originalfart, uten teleport')
    data, save = route('ankomst')
    check(pos(data) == (20, 30), 'rett klikkreise stopper paa eksakt fotpunkt')
    check(struct.unpack_from('>H', data, 0x8e7a0)[0] == 20, 'originalens trekkbudsjett belastes for 20 steg')
    check(pointer(save)[3] == 255, 'maalet slettes etter ankomst')
    original, _ = route('original', nohooks=True)
    check(data == original, 'hele chip-minnet er likt med og uten C-kroker')
    manual = out / 'joystick-timing.bin'
    run(['--load-state', seed, '--frames', '60', '--press', '2020:right:40', '--dump', f'2060:{manual}'])
    data, _ = route('klikk-timing', command=target(300, 10), until=60)
    joy = manual.read_bytes()
    check(pos(data) == pos(joy) and data[0x8e7a0:0x8e7a2] == joy[0x8e7a0:0x8e7a2] and pos(data) == (30, 10),
          '40 bilder gir samme 20 steg og budsjett som holdt joystick i originalterrenget')
    data, save = route('lang-reise', command=target(300, 180), until=900)
    check(pointer(save)[3] == 255 and pos(data) != (300, 180), 'lang reise avsluttes ved originalens turbudsjett')
    data, save = route('teleport', ['--skriv', '2025:8d632:100:2'])
    check(pointer(save)[3] == 255 and pos(data)[0] == 100, 'uventet posisjonsbytte avbryter gammel rute uten divisjon med null')
    data, save = route('kartkant', ['--skriv', '2019:8d632:309:2', '--skriv', '2019:8d634:189:2'],
                       command=str(319 | 199 << 16))
    check(pos(data) == (310, 189) and pointer(save)[3] == 255, 'klikk ved kartkanten beholder originalens grenser og synlig fotpunkt')

    data, save = route('samme', command=target(10, 10))
    check(pos(data) == (10, 10) and struct.unpack_from('>H', data, 0x8e7a0)[0] == 0,
          'klikk paa eget fotpunkt koster ingen steg og gir ingen divisjon med null')
    data, save = route('ugyldig-cel', ['--skriv', '2019:8e7be:0xfffffff0:4'], until=21)
    check(pos(data) == (10, 10) and pointer(save)[3] == 255,
          'ugyldig CEL-peker avvises uten heltallsoverloep eller lesing utenfor chip-minnet')
    data, _ = route('nytt-maal', ['--meny', '2025:15:' + target(35, 12)])
    check(pos(data) == (35, 12), 'nytt klikk erstatter en paabegynt reise')
    data, save = route('manuell', ['--press', '2025:left:4'])
    check(pointer(save)[3] == 255 and pos(data)[0] < 15 and pos(data)[1] < 30,
          'fysisk joystick avbryter reisen og faar original kontroll')
    data, save = route('avbryt', ['--meny', '2025:15:-1'])
    check(pointer(save)[3] == 255 and pos(data) != (20, 30), 'hoyreklikkkommando avbryter maalreisen')
    data, save = route('inventar', ['--press', '2025:space:4'])
    check(pointer(save)[2:4] == bytes([0, 255]), 'inventaret avslutter kartreise og kartinput')
    data, save = route('tur', ['--press', '2025:e:4'], until=900)
    check(pointer(save)[3] == 255, 'slutt paa turen sletter maal foer neste ridder')
    for name, command in [('utenfor-x', str(320 | 20 << 16)), ('utenfor-y', str(14 | 200 << 16))]:
        data, save = route(name, command=command)
        check(pos(data) == (10, 10) and pointer(save)[3] == 255, name + ' avvises av kjernen')

    _, mid = route('midt', until=24)
    check(pointer(mid)[3] == 0, 'en paabegynt klikkreise finnes i lagringen')
    resumed = out / 'gjenopptatt.bin'
    run(['--load-state', mid, '--frames', '326', '--dump', f'2350:{resumed}'])
    continuous, _ = route('sammenhengende')
    check(resumed.read_bytes() == continuous, 'lasting midt i reisen gir samme hele chip-minne som sammenhengende spilling')
    for length in [1, 2]:
        old = out / f'eldre-pekr-{length}.sav'
        raw = seed.read_bytes()
        modified = bytearray(raw[:20])
        for tag, ver, body in parts(raw):
            if tag == b'PEKR':
                body = body[:length]
            modified += struct.pack('<4sII', tag, ver, len(body)) + body
        old.write_bytes(modified)
        dump = out / f'eldre-pekr-{length}.bin'
        run(['--load-state', old, '--frames', '350', '--meny', f'2020:15:{target(20, 30)}', '--dump', f'2350:{dump}'])
        check(pos(dump.read_bytes()) == (20, 30), f'eldre PEKR-lengde {length} faar standard og kartklikk virker igjen')
    print(f'Ferdig: {checks} OK, 0 FEIL', flush=True)


if __name__ == '__main__':
    main()
