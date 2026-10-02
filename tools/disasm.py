#!/usr/bin/env python3
"""
disasm.py - disassembly av program (introen) og mog (hovedspillet).

    python3 tools/disasm.py Moonstonecd32-AMIGA.zip disasm
    python3 tools/disasm.py Moonstonecd32-AMIGA.zip disasm --coverage disasm/coverage.bin

Filene legges ut slik slaven gjør det: relokert til $80000 med hunkene rett etter
hverandre. Da stemmer adressene med det du ser i emulatoren (PC, minnedump,
patchlistene i slaven og port/src/game.c).

Hva som er kode, finnes slik:
  - starten av hver kodehunk, og alle mål for bsr/jsr/jmp/bra/bcc/dbcc
  - adresser i kodehunkene som lastes med lea/pea/move.l #, f.eks. avbruddsrutiner
  - kodedekning fra emulatoren (port/moonstone --coverage FIL), som viser hva
    som faktisk er kjørt
Resten skrives som data (dc.b/dc.l). Relokerte langord vises som etiketter.

Navn og kommentarer leses fra disasm/symbols.txt:
    81f92 les_joystick      leser JOY0DAT og JOY1DAT til $8D9A0 og $8D9A2
Ut kommer disasm/mog.s, disasm/program.s og disasm/functions.txt.
mog.s og program.s inneholder hele spillkoden og sjekkes ikke inn.

Krever capstone (pip install capstone).
"""
import os
import re
import struct
import sys

import capstone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import moonfiles as mf  # noqa: E402

BASE = 0x80000
GREN = re.compile(r'^(bsr|jsr|jmp|bra|b[a-z][a-z]|db[a-z]+)(\.[bwls])?$')
ADR = re.compile(r'\$([0-9a-f]+)')


def legg_ut(d, base=BASE):
    """Relokerer hunk-filen. Returnerer (minne, hunker) der hunker er (start, slutt, type)."""
    p = 0

    def L():
        nonlocal p
        v = struct.unpack('>I', d[p:p + 4])[0]
        p += 4
        return v
    assert L() == 0x3f3
    while L():
        p += 4 * struct.unpack('>I', d[p - 4:p])[0]
    L()
    forste, siste = L(), L()
    storrelser = [L() & 0x3fffffff for _ in range(siste - forste + 1)]
    adr, a = [], base
    for s in storrelser:
        adr.append(a)
        a += s * 4
    minne = bytearray(a - base)
    hunker, rel = [], []
    h = -1
    while p + 4 <= len(d):
        t = L() & 0x3fffffff
        if t in (0x3e9, 0x3ea, 0x3eb):
            h += 1
            n = L() * 4
            typ = {0x3e9: 'kode', 0x3ea: 'data', 0x3eb: 'bss'}[t]
            if t != 0x3eb:
                minne[adr[h] - base:adr[h] - base + n] = d[p:p + n]
                p += n
            hunker.append((adr[h], adr[h] + storrelser[h] * 4, typ))
        elif t == 0x3ec:
            while True:
                n = L()
                if not n:
                    break
                th = L()
                for _ in range(n):
                    off = L()
                    q = adr[h] - base + off
                    v = struct.unpack('>I', minne[q:q + 4])[0] + adr[th]
                    minne[q:q + 4] = struct.pack('>I', v)
                    rel.append(adr[h] + off)
        elif t == 0x3f2:
            pass
        else:
            break
    return bytes(minne), hunker, set(rel)


def les_symboler(sti):
    navn, kommentar = {}, {}
    if not os.path.exists(sti):
        return navn, kommentar
    with open(sti, encoding='utf-8') as f:
        for linje in f:
            linje = linje.strip()
            if not linje or linje.startswith('#'):
                continue
            deler = linje.split(None, 2)
            try:
                a = int(deler[0].replace('$', ''), 16)
            except ValueError:
                continue
            if len(deler) > 1:
                navn[a] = deler[1]
            if len(deler) > 2:
                kommentar[a] = deler[2]
    return navn, kommentar


class Disasm:
    def __init__(self, minne, hunker, rel, navn, kommentar, dekning=None):
        self.m = minne
        self.hunker = hunker
        self.rel = rel
        self.navn = dict(navn)
        self.kommentar = kommentar
        self.cs = capstone.Cs(capstone.CS_ARCH_M68K, capstone.CS_MODE_BIG_ENDIAN | capstone.CS_MODE_M68K_000)
        self.kode = {}            # adresse -> (lengde, mnemonic, operander)
        self.kall = {}            # mål -> antall kall
        self.mal = set()          # alle hoppmål
        self.data_ref = set()
        self.dekning = dekning or set()

    def i_kode(self, a):
        return any(s <= a < e and t == 'kode' for s, e, t in self.hunker)

    def i_minne(self, a):
        return BASE <= a < BASE + len(self.m)

    def dekod(self, a):
        o = a - BASE
        ins = list(self.cs.disasm(self.m[o:o + 12], a, 1))
        return ins[0] if ins else None

    def folg(self, starter):
        ko = list(starter)
        while ko:
            a = ko.pop()
            while self.i_kode(a) and a not in self.kode and a & 1 == 0:
                i = self.dekod(a)
                if not i or i.mnemonic in ('dc.w',) or i.mnemonic.startswith('invalid'):
                    break
                self.kode[a] = (i.size, i.mnemonic, i.op_str)
                mn = i.mnemonic.split('.')[0]
                mal = [int(x, 16) for x in ADR.findall(i.op_str)]
                if GREN.match(i.mnemonic):
                    for t in mal:
                        if self.i_kode(t) and ('(' not in i.op_str or '(pc)' in i.op_str or i.op_str.endswith('.l')):
                            self.mal.add(t)
                            ko.append(t)
                            if mn in ('bsr', 'jsr'):
                                self.kall[t] = self.kall.get(t, 0) + 1
                else:
                    for t in mal:
                        if self.i_minne(t) and t >= BASE + 0x100:
                            if mn in ('lea', 'pea') and self.i_kode(t):
                                self.mal.add(t)
                                ko.append(t)
                            elif mn == 'move' and i.op_str.startswith('#') and self.i_kode(t) and t in self.dekning:
                                self.mal.add(t)
                                ko.append(t)
                            else:
                                self.data_ref.add(t)
                if mn in ('rts', 'rte', 'jmp', 'bra', 'rtr', 'illegal'):
                    break
                a += i.size

    def etikett(self, a):
        if a in self.navn:
            return self.navn[a]
        if a in self.kall:
            return 'sub_%06x' % a
        if a in self.mal:
            return 'loc_%06x' % a
        if a in self.data_ref:
            return 'dat_%06x' % a
        return None

    def skriv(self, ut, tittel):
        linjer = ['; %s - disassembly laget av tools/disasm.py, lastet til $%06x' % (tittel, BASE),
                  '; Navn og kommentarer: disasm/symbols.txt. Adressene stemmer med emulatoren.', '']
        for (s, e, t) in self.hunker:
            linjer.append('')
            linjer.append('; ---------------------------------------------------------------- hunk %s $%06x-$%06x' % (t, s, e))
            a = s
            while a < e:
                et = self.etikett(a)
                if et:
                    if a in self.kall:
                        linjer.append('')
                    linjer.append('%s:%s' % (et, ('\t\t; ' + self.kommentar[a]) if a in self.kommentar else ''))
                if a in self.kode:
                    n, mn, ops = self.kode[a]

                    def bytt(m):
                        v = int(m.group(1), 16)
                        e2 = self.etikett(v)
                        return e2 if e2 and self.i_minne(v) else m.group(0)
                    ops2 = ADR.sub(bytt, ops)
                    rå = self.m[a - BASE:a - BASE + n].hex()
                    k = ''
                    if a in self.dekning:
                        k = ''
                    linjer.append('%06x  %-20s  %-8s %s%s' % (a, rå, mn, ops2, k))
                    a += n
                    continue
                if t == 'bss':
                    slutt = e
                    nxt = [x for x in list(self.navn) + list(self.data_ref) if a < x < e]
                    if nxt:
                        slutt = min(nxt)
                    linjer.append('%06x  %-20s  ds.b     %d' % (a, '', slutt - a))
                    a = slutt
                    continue
                if a in self.rel or (a + 4 <= e and a in self.rel):
                    v = struct.unpack('>I', self.m[a - BASE:a - BASE + 4])[0]
                    linjer.append('%06x  %-20s  dc.l     %s' % (a, self.m[a - BASE:a - BASE + 4].hex(), self.etikett(v) or '$%06x' % v))
                    a += 4
                    continue
                # data: til neste etikett, kode eller reloc, maks 16 byte per linje
                slutt = a + 1
                while slutt < e and slutt - a < 16 and slutt not in self.kode and not self.etikett(slutt) and slutt not in self.rel:
                    slutt += 1
                bit = self.m[a - BASE:slutt - BASE]
                tekst = ''.join(chr(c) if 32 <= c < 127 else '.' for c in bit)
                linjer.append('%06x  %-20s  dc.b     %s  ; %s' % (a, '', ','.join('$%02x' % c for c in bit), tekst))
                a = slutt
        with open(ut, 'w', encoding='utf-8') as f:
            f.write('\n'.join(linjer) + '\n')

    def tekst_paa(self, a):
        """Teksten som starter paa a, hvis det ser ut som en tekst."""
        if not self.i_minne(a) or self.i_kode(a) and a in self.kode:
            return None
        o = a - BASE
        s = bytearray()
        while o < len(self.m) and 32 <= self.m[o] < 127 and len(s) < 40:
            s.append(self.m[o])
            o += 1
        if len(s) >= 4 and (o >= len(self.m) or self.m[o] == 0):
            return s.decode('latin-1').strip()
        return None

    def funksjoner(self):
        ut = []
        alle = sorted(set(self.kall) | set(a for a in self.navn if self.i_kode(a)))
        kode = sorted(self.kode)
        import bisect
        for n, a in enumerate(alle):
            kjort = 'ja' if a in self.dekning else 'nei'
            # tekster funksjonen bruker: adresser i instruksjonene fram til neste funksjon
            slutt = alle[n + 1] if n + 1 < len(alle) else a + 0x400
            tekster = []
            i = bisect.bisect_left(kode, a)
            while i < len(kode) and kode[i] < slutt:
                _, _, ops = self.kode[kode[i]]
                for t in ADR.findall(ops):
                    tk = self.tekst_paa(int(t, 16))
                    if tk and tk not in tekster:
                        tekster.append(tk)
                i += 1
            t = '; '.join('"%s"' % x for x in tekster[:4])
            ut.append('%06x  %-28s kall %-4d kjort %-4s %s%s' % (a, self.etikett(a), self.kall.get(a, 0), kjort,
                                                                   self.kommentar.get(a, ''),
                                                                   ('  tekster: ' + t) if t else ''))
        return ut


def les_dekning(sti):
    if not sti or not os.path.exists(sti):
        return set()
    d = open(sti, 'rb').read()
    ut = set()
    for i, b in enumerate(d):
        if b:
            for k in range(8):
                if b >> k & 1:
                    ut.add(i * 16 + k * 2)
    return ut


def main():
    a = sys.argv[1:]
    if len(a) < 2:
        print(__doc__)
        sys.exit(1)
    spill = mf.Spill(a[0])
    ut = a[1]
    dekning_sti = a[a.index('--coverage') + 1] if '--coverage' in a else os.path.join(ut, 'coverage.bin')
    os.makedirs(ut, exist_ok=True)
    navn, kommentar = les_symboler(os.path.join(ut, 'symbols.txt'))
    dekning = les_dekning(dekning_sti)
    funk = []
    for fil in ('mog', 'program'):
        minne, hunker, rel = legg_ut(spill.les('data/' + fil))
        dek = dekning if fil == 'mog' else set()
        d = Disasm(minne, hunker, rel, navn if fil == 'mog' else {}, kommentar if fil == 'mog' else {}, dek)
        starter = [s for s, e, t in hunker if t == 'kode'] + [x for x in dek if d.i_kode(x)]
        starter += [x for x in d.navn if d.i_kode(x)]
        d.folg(starter)
        d.skriv(os.path.join(ut, fil + '.s'), fil)
        kodebyte = sum(n for n, _, _ in d.kode.values())
        totalt = sum(e - s for s, e, t in hunker if t == 'kode')
        print('%-8s %d instruksjoner, %d av %d byte kode funnet, %d funksjoner' %
              (fil, len(d.kode), kodebyte, totalt, len(d.kall)))
        if fil == 'mog':
            funk = d.funksjoner()
    with open(os.path.join(ut, 'functions.txt'), 'w', encoding='utf-8') as f:
        f.write('# Funksjoner i mog: adresse, navn, antall kall i koden, kjort i emulatoren, kommentar og tekster den bruker\n')
        f.write('\n'.join(funk) + '\n')


if __name__ == '__main__':
    main()
