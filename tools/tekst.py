#!/usr/bin/env python3
"""
tekst.py - tekstene i Moonstone ut til en fil som kan redigeres.

    python3 tools/tekst.py extract Moonstonecd32-AMIGA.zip tekster.txt
    python3 tools/tekst.py check Moonstonecd32-AMIGA.zip tekster.txt

extract skriver alle tekstene i hovedspillet (mog) til en fil, en per linje:

    8f123 "Players"

Tallet er adressen der teksten ligger når spillet kjører. Endre teksten i
anførselstegnene og legg filen som tekster.txt i mod-mappen (port/moonstone
--mod MAPPE) eller velg den under «Egne filer» på nettsiden. Linjer du ikke
har endret, brukes ikke, så du kan også slette dem.

Porten bruker filen når mog er lastet (port/src/patch.c), så selve spillfilen
endres ikke:
  - en tekst som er like lang eller kortere, skrives der den ligger
  - en lengre tekst legges i ledig minne, og alle pekere til den rettes
  - en lengre tekst uten pekere (ingen kode peker rett på den) kan ikke
    flyttes, og blir kuttet. check sier fra om det.

check sammenligner en redigert fil med spillet og viser hva som endres, og
om noe blir kuttet eller har tegn som fonten ikke har.

Tegn: vanlig ASCII. \\" og \\\\ for anførselstegn og skråstrek, \\xNN for andre
byte. Fonten har store og små bokstaver, tall og vanlige skilletegn, ikke æøå.
Filnavn (som "He1.ob") og tabeller tas ikke med; endres de, finner ikke spillet
filene sine.
"""
import os
import re
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import moonfiles as mf  # noqa: E402
from moonfiles import legg_ut  # noqa: E402

BASE = 0x80000                # mog legges hit, som i spillet

TEGNTABELL = 0x96210          # tegn - 32 -> bilde i fonten (96 byte), se disasm/symbols.txt
TOMT_TEGN = 69                # bildet ubrukte tegn peker paa
# tabeller som ser ut som tekst, men ikke er det
IKKE_TEKST = {
    TEGNTABELL: 'tegntabellen til fonten',
}
IKKE_TEKST_INNHOLD = {'0123456789', '-./010/.'}
IKKE_TEKST_OMRAADER = [
    (0xaaa1b, 0xaaa90),       # tastaturtabellen ("1234567890-=", "QWERTYUIOP[]" ...)
]
FILNAVN = re.compile(r'^[A-Za-z0-9_]+\.[A-Za-z]{1,5}$')
LINJE = re.compile(r'^\s*([0-9a-fA-F]{5,6})\s+"((?:[^"\\]|\\.)*)"\s*(#.*)?$')


def u32(m, a):
    return struct.unpack('>I', m[a - BASE:a - BASE + 4])[0]


def les_mog(spill):
    """minne, hunker og pekere: {maal: antall} for relokerte langord, uten jsr/jmp-maal"""
    minne, hunker, rel = legg_ut(spill.les('data/mog'))
    pekere, kodemaal = {}, set()
    for r in rel:
        v = u32(minne, r)
        if struct.unpack('>H', minne[r - 2 - BASE:r - BASE])[0] in (0x4eb9, 0x4ef9):   # jsr/jmp
            kodemaal.add(v)
        pekere[v] = pekere.get(v, 0) + 1
    for v in kodemaal:
        pekere.pop(v, None)
    return minne, hunker, pekere


def ligner_tekst(t, kort):
    """minst to bokstaver, og mest bokstaver og mellomrom"""
    bokstaver = sum(c.isalpha() for c in t)
    if len(t) < (2 if kort else 3) or bokstaver < min(2, len(t)):
        return False
    return (bokstaver + t.count(' ')) / len(t) >= 0.6


def finn_avsnitt(minne, hunker, pekere):
    """Avsnitt: en peker til en byte med antall linjer (1-31), saa linjene med 0 etter hver.
    Gir {linjeadresse: avsnittets start}."""
    ut = {}
    for p in pekere:
        h = next(((s, e) for s, e, t in hunker if s <= p < e and t == 'data'), None)
        if not h or not 1 <= minne[p - BASE] <= 31:   # 32 og over er vanlige tegn
            continue
        a, linjer = p + 1, []
        for _ in range(minne[p - BASE]):
            s = a
            while a < h[1] and 32 <= minne[a - BASE] <= 126:
                a += 1
            if a >= h[1] or minne[a - BASE] != 0 or a - s > 60:
                linjer = None
                break
            linjer.append(s)
            a += 1
        if linjer and any(ligner_tekst(bytes(minne[x - BASE:x - BASE + 60]).split(b'\0')[0].decode('latin-1'), False)
                          for x in linjer):
            for x in linjer:
                ut[x] = p
    return ut


def finn_tekster(minne, hunker, pekere, filnavn):
    """(adresse, bytes, hvordan) for tekstene i mog, sortert etter adresse.
    hvordan: 'peker' (kan flyttes), 'avsnitt' (hele avsnittet flyttes) eller 'fast'."""
    avsnitt = finn_avsnitt(minne, hunker, pekere)
    ut = []
    for start, slutt, typ in hunker:
        if typ == 'bss':
            continue
        a = start
        while a < slutt:
            if not 32 <= minne[a - BASE] <= 126:
                a += 1
                continue
            s = a
            while a < slutt and 32 <= minne[a - BASE] <= 126:
                a += 1
            if a >= slutt or minne[a - BASE] != 0:
                continue                       # ikke avsluttet med 0
            # en tekst kan ha pekere til flere steder inni seg; hver blir en linje
            starter = sorted({s} | {p for p in pekere if s < p < a})
            for p in starter:
                b = bytes(minne[p - BASE:a - BASE])
                t = b.decode('latin-1')
                n = pekere.get(p, 0)
                if p in IKKE_TEKST or t in IKKE_TEKST_INNHOLD or any(x <= p < y for x, y in IKKE_TEKST_OMRAADER):
                    continue
                if FILNAVN.match(t) or t.lower() in filnavn:
                    continue
                if p in avsnitt:
                    ut.append((p, b, 'avsnitt'))
                    continue
                if n == 0:
                    # uten peker: bare i datahunkene, rett etter en 0, og bare noe som ligner tekst
                    if typ != 'data' or p != s or (s > start and minne[s - 1 - BASE] != 0):
                        continue
                    if not ligner_tekst(t, False) or sum(c.isalpha() for c in t) < 3:
                        continue
                    if not any(c in 'aeiouyAEIOUY' for c in t):    # tabeller som "fff~fff" og "lkj"
                        continue
                elif not ligner_tekst(t, typ == 'data'):
                    continue
                ut.append((p, b, 'peker' if n else 'fast'))
    return ut, avsnitt


def kod(b):
    s = ''
    for c in b:
        if c == 0x22:
            s += '\\"'
        elif c == 0x5c:
            s += '\\\\'
        elif 32 <= c <= 126:
            s += chr(c)
        else:
            s += '\\x%02x' % c
    return s


def dekod(s):
    ut = bytearray()
    i = 0
    while i < len(s):
        c = s[i]
        if c == '\\' and i + 1 < len(s):
            n = s[i + 1]
            if n == 'x' and i + 3 < len(s) + 1:
                ut.append(int(s[i + 2:i + 4], 16))
                i += 4
                continue
            ut.append(ord(n))
            i += 2
            continue
        o = ord(c)
        ut.append(o if o < 128 else ord('?'))      # som porten: fonten har bare ASCII
        i += 1
    return bytes(ut)


def les_fil(sti):
    """{adresse: bytes} fra en tekstfil, og feil med linjenummer"""
    tekster, feil = {}, []
    with open(sti, encoding='utf-8') as f:
        for nr, linje in enumerate(f, 1):
            t = linje.strip()
            if not t or t.startswith('#'):
                continue
            m = LINJE.match(linje.rstrip('\n'))
            if not m:
                feil.append('linje %d: forstår ikke "%s"' % (nr, t[:50]))
                continue
            tekster[int(m.group(1), 16)] = (dekod(m.group(2)), nr, sorted({c for c in m.group(2) if ord(c) > 127}))
    return tekster, feil


def extract(spill, sti):
    minne, hunker, pekere = les_mog(spill)
    filnavn = {os.path.basename(n).lower() for n in spill.filer}
    tekster, avsnitt = finn_tekster(minne, hunker, pekere, filnavn)
    with open(sti, 'w', encoding='utf-8') as f:
        f.write('# Tekstene i Moonstone (mog). Endre teksten i anførselstegnene og legg filen\n'
                '# som tekster.txt i mod-mappen eller under «Egne filer» på nettsiden.\n'
                '# Adressen foran er der teksten ligger når spillet kjører. Linjer som ikke er\n'
                '# endret, brukes ikke. Se tools/tekst.py for detaljer.\n'
                '#\n'
                '# Merket "kan ikke bli lengre": ingen kode peker rett på teksten, så den kan\n'
                '# bare byttes med en like lang eller kortere tekst. Linjene i et avsnitt kan\n'
                '# endres fritt; da flyttes hele avsnittet.\n\n')
        forrige = None
        for a, b, hvordan in tekster:
            if hvordan == 'avsnitt' and avsnitt[a] != forrige:
                n = sum(1 for x in avsnitt.values() if x == avsnitt[a])
                f.write('# avsnitt, %d linje%s\n' % (n, 'r' if n > 1 else ''))
            forrige = avsnitt.get(a)
            f.write('%05x "%s"%s\n' % (a, kod(b), '    # kan ikke bli lengre' if hvordan == 'fast' else ''))
    print('%d tekster skrevet til %s' % (len(tekster), sti))


def bredder(spill, fil):
    """bredden paa hvert bilde i en font (bold.f er den store, Small.font den lille)"""
    d = spill.les('data/' + fil)
    n = struct.unpack('>H', d[:2])[0]
    return [struct.unpack('>H', d[10 + 10 * i + 4:10 + 10 * i + 6])[0] for i in range(n)]


def check(spill, sti):
    minne, hunker, pekere = les_mog(spill)
    tabell = minne[TEGNTABELL - BASE:TEGNTABELL - BASE + 96]
    stor, liten = bredder(spill, 'bold.f'), bredder(spill, 'Small.font')

    def bredde(t, font):
        return sum(font[tabell[c - 32]] for c in t if 32 <= c <= 127 and tabell[c - 32] < len(font))
    tekster, feil = les_fil(sti)
    filnavn = {os.path.basename(n).lower() for n in spill.filer}
    _, avsnitt = finn_tekster(minne, hunker, pekere, filnavn)
    endret = 0
    for a, (ny, nr, ikke_ascii) in sorted(tekster.items()):
        if not any(s <= a < e and t != 'bss' for s, e, t in hunker):
            feil.append('linje %d: %05x er ikke i mog' % (nr, a))
            continue
        e = a
        while e - BASE < len(minne) and minne[e - BASE]:
            e += 1
        gml = bytes(minne[a - BASE:e - BASE])
        if ny == gml:
            continue
        endret += 1
        mangler = sorted({chr(c) for c in ny if not 32 <= c <= 127 or (tabell[c - 32] == TOMT_TEGN and c != 32)})
        if a in avsnitt:
            hvor = 'på samme sted' if len(ny) == len(gml) else 'hele avsnittet flyttes'
        elif len(ny) <= len(gml):
            hvor = 'på samme sted'
        elif pekere.get(a):
            hvor = 'flyttes (%d peker%s)' % (pekere[a], 'e' if pekere[a] > 1 else '')
        else:
            hvor = 'KUTTES til %d tegn (ingen peker, kan ikke flyttes)' % len(gml)
        print('%05x "%s" -> "%s": %s' % (a, kod(gml), kod(ny), hvor))
        # avsnittene vises med den lille fonten, menyer og overskrifter ofte med den store
        if bredde(ny, liten) > 320:
            print('      %d piksler: bredere enn skjermen (320), resten kommer på neste linje' % bredde(ny, liten))
        elif a not in avsnitt and bredde(ny, stor) > 320 >= bredde(gml, stor):
            print('      %d piksler med den store fonten: for bred hvis teksten vises med den (menyer, '
                  'overskrifter), da kommer resten på neste linje' % bredde(ny, stor))
        if ikke_ascii:
            print('      tegn utenfor ASCII blir til ?: %s' % ' '.join(ikke_ascii))
        if mangler:
            print('      tegn som fonten ikke har (vises som tomrom): %s' % ' '.join(mangler))
    for f in feil:
        print('feil: ' + f)
    print('%d tekster endret' % endret)
    return 1 if feil else 0


def main():
    a = sys.argv[1:]
    if len(a) != 3 or a[0] not in ('extract', 'check'):
        print(__doc__)
        sys.exit(1)
    spill = mf.Spill(a[1])
    if a[0] == 'extract':
        extract(spill, a[2])
    else:
        sys.exit(check(spill, a[2]))


if __name__ == '__main__':
    main()
