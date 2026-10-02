#!/usr/bin/env python3
"""
bin2c.py UT [FIL] - bygger spillfila inn i programmet.

Lager C-fila UT med innholdet i FIL (Moonstonecd32-AMIGA.zip) som
spill_innebygd og lengden som spill_innebygd_storrelse. Uten FIL blir
tabellen tom, og programmet ser etter spillfila paa disk som foer.

Dataene skrives som strengkonstanter med \\xNN, som kompilatorene leser mye
raskere enn en tallliste med to millioner tall. Fila skrives bare naar
innholdet er endret, saa make ikke bygger paa nytt uten grunn.
"""
import os
import sys


def main():
    if len(sys.argv) not in (2, 3):
        sys.exit(__doc__)
    ut = sys.argv[1]
    inn = sys.argv[2] if len(sys.argv) == 3 else None
    data = b''
    if inn:
        with open(inn, 'rb') as f:
            data = f.read()
    linjer = ['/* Laget av port/bin2c.py fra %s. Ikke rediger, og ikke sjekk inn. */'
              % (os.path.basename(inn) if inn else 'ingen fil'),
              '#include <stddef.h>', '']
    if data:
        linjer.append('const unsigned char spill_innebygd[] =')
        for i in range(0, len(data), 48):
            linjer.append('    "' + ''.join('\\x%02x' % b for b in data[i:i + 48]) + '"')
        linjer[-1] += ';'
    else:
        linjer.append('const unsigned char spill_innebygd[1] = { 0 };')
    linjer.append('const size_t spill_innebygd_storrelse = %d;' % len(data))
    tekst = '\n'.join(linjer) + '\n'
    if os.path.exists(ut):
        with open(ut, encoding='ascii') as f:
            if f.read() == tekst:
                return
    with open(ut, 'w', encoding='ascii') as f:
        f.write(tekst)


if __name__ == '__main__':
    main()
