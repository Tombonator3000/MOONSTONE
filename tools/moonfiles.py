"""
moonfiles.py - felles kode for verktøyene: spillfilene og formatene til Moonstone.

    from moonfiles import Spill
    spill = Spill('Moonstonecd32-AMIGA.zip')     # zip, ISO eller mappe
    data = spill.les('data/bg1a.PIV')

Formatene (se også memory.md):

  LZ        Spillets egen pakking. En kontrollbyte med 8 flagg, høyeste bit først.
            0 = en byte som den er. 1 = to byte: 5 bit lengde (34 - n, altså 3-34)
            og 11 bit avstand bakover (1-2047).
  PIV / .p  Bilde: ord plan, long pakket lengde, (1 << plan) palettord, LZ-data.
            Utpakket: plan for plan, 320 x 200 (40 byte per linje).
            Filen "Test" er ni slike bilder etter hverandre.
  CEL       Figurer (.cel .c .ob .f .font): ord antall, long pakket lengde,
            long minnebehov (8 x utpakket), 10 byte per bilde (long offset,
            ord bredde, ord høyde, byte flagg, byte planmaske), LZ-data.
            Hvert bilde ligger plan for plan, bredden rundet opp til hele ord.
  .a        AmigaDOS hunk-fil med 8SVX-lyder (FORM....8SVX) etter hverandre.
"""
import io
import os
import struct
import zipfile

# ---------------------------------------------------------------- spillfilene


class Spill:
    """Filene i Moonstone-mappen (Moonstone.Slave og data/), med stier som 'data/bg1a.PIV'."""

    def __init__(self, sti):
        self.filer = {}
        if os.path.isdir(sti):
            self._mappe(sti)
        else:
            with open(sti, 'rb') as f:
                self._blob(f.read())
        self._finn_rot()

    def _mappe(self, sti):
        for rot, _, navn in os.walk(sti):
            for n in navn:
                full = os.path.join(rot, n)
                rel = os.path.relpath(full, sti).replace(os.sep, '/')
                with open(full, 'rb') as f:
                    data = f.read()
                if n.lower().endswith(('.zip', '.iso')) and 'moonstone.slave' not in [x.lower() for x in navn]:
                    try:
                        self._blob(data)
                        continue
                    except ValueError:
                        pass
                self.filer[rel] = data

    def _blob(self, data):
        if data[:2] == b'PK':
            z = zipfile.ZipFile(io.BytesIO(data))
            for info in z.infolist():
                if info.filename.lower().endswith('.iso'):
                    self._iso(z.read(info))
                    return
            for info in z.infolist():
                if not info.is_dir():
                    self.filer[info.filename] = z.read(info)
            return
        if data[0x8001:0x8006] == b'CD001':
            self._iso(data)
            return
        raise ValueError('verken zip eller ISO')

    def _iso(self, iso):
        def le32(p):
            return struct.unpack('<I', iso[p:p + 4])[0]

        def mappe(lba, lengde, prefiks, dybde):
            pos, slutt = lba * 2048, lba * 2048 + lengde
            while pos < slutt:
                rl = iso[pos]
                if rl == 0:
                    pos = (pos // 2048 + 1) * 2048
                    continue
                elba, elen, flagg, nl = le32(pos + 2), le32(pos + 10), iso[pos + 25], iso[pos + 32]
                navn = iso[pos + 33:pos + 33 + nl]
                pos += rl
                if navn in (b'\0', b'\1'):
                    continue
                navn = navn.decode('latin-1').split(';')[0].rstrip('.')
                sti = prefiks + '/' + navn if prefiks else navn
                if flagg & 2:
                    if dybde < 8:
                        mappe(elba, elen, sti, dybde + 1)
                else:
                    self.filer[sti] = iso[elba * 2048:elba * 2048 + elen]

        rot = 0x8000 + 156
        mappe(le32(rot + 2), le32(rot + 10), '', 0)

    def _finn_rot(self):
        slave = [p for p in self.filer if p.split('/')[-1].lower() == 'moonstone.slave']
        if not slave:
            raise ValueError('fant ikke Moonstone.Slave')
        rot = slave[0][:-len('Moonstone.Slave')]
        self.filer = {p[len(rot):]: d for p, d in self.filer.items() if p.startswith(rot)}

    def finn(self, navn):
        """Riktig sti for et navn, store og små bokstaver likegyldig."""
        n = navn.lower()
        for p in self.filer:
            if p.lower() == n or p.lower() == 'data/' + n:
                return p
        return None

    def les(self, navn):
        p = self.finn(navn)
        if p is None:
            raise KeyError(navn)
        return self.filer[p]

    def data_filer(self):
        return sorted(p for p in self.filer if p.lower().startswith('data/'))


# ---------------------------------------------------------------- LZ


def lz_ut(src, maks=None):
    """Pakker ut spillets LZ-format. Som utpakkeren i slaven ($50E)."""
    src = bytes(src) + b'\0\0'
    slutt = len(src) - 2
    ut = bytearray()
    s = 0
    while s < slutt:
        ctl = src[s]
        s += 1
        for _ in range(8):
            if s >= slutt:
                break
            if ctl & 0x80:
                w = src[s] << 8 | src[s + 1]
                s += 2
                avstand, lengde = w & 0x7ff, 34 - (w >> 11)
                for _ in range(lengde):
                    ut.append(ut[-avstand] if 0 < avstand <= len(ut) else 0)
            else:
                ut.append(src[s])
                s += 1
            ctl = (ctl << 1) & 0xff
            if maks is not None and len(ut) >= maks:
                return bytes(ut[:maks])
    return bytes(ut)


def lz_inn(data):
    """Pakker data i spillets LZ-format (grådig, med hasjkjeder)."""
    data = bytes(data)
    n = len(data)
    ut = bytearray()
    hode = {}
    kjede = [-1] * n
    i = 0
    while i < n:
        ctl_pos = len(ut)
        ut.append(0)
        ctl = 0
        for bit in range(8):
            if i >= n:
                break
            beste_l, beste_a = 0, 0
            if i + 3 <= n:
                k = data[i:i + 3]
                j = hode.get(k, -1)
                forsok = 0
                while j >= 0 and i - j <= 2047 and forsok < 64:
                    l = 0
                    while l < 34 and i + l < n and data[j + l] == data[i + l]:
                        l += 1
                    if l > beste_l:
                        beste_l, beste_a = l, i - j
                        if l == 34:
                            break
                    j = kjede[j]
                    forsok += 1
            steg = beste_l if beste_l >= 3 else 1
            for p in range(i, min(i + steg, n - 2)):
                k = data[p:p + 3]
                kjede[p] = hode.get(k, -1)
                hode[k] = p
            if beste_l >= 3:
                ctl |= 0x80 >> bit
                w = (34 - beste_l) << 11 | beste_a
                ut += bytes([w >> 8, w & 0xff])
                i += beste_l
            else:
                ut.append(data[i])
                i += 1
        ut[ctl_pos] = ctl
    return bytes(ut)


# ---------------------------------------------------------------- PIV


def piv_les(d, pos=0):
    """Returnerer (plan, palett, bitplan, slutt). bitplan er utpakket, plan for plan."""
    plan, plen = struct.unpack('>HI', d[pos:pos + 6])
    nc = 1 << plan
    palett = list(struct.unpack('>%dH' % nc, d[pos + 6:pos + 6 + nc * 2]))
    start = pos + 6 + nc * 2
    bitplan = lz_ut(d[start:start + plen], plan * 8000)
    return plan, palett, bitplan, start + plen


def piv_lag(plan, palett, bitplan):
    pakket = lz_inn(bitplan)
    return struct.pack('>HI', plan, len(pakket)) + struct.pack('>%dH' % len(palett), *palett) + pakket


def er_piv(d):
    if len(d) < 6:
        return False
    plan, plen = struct.unpack('>HI', d[:6])
    return plan in (1, 2, 3, 4, 5) and 6 + (2 << plan) + plen <= len(d) and plen > 100


def piv_alle(d):
    """Alle bildene i en fil (Test har ni)."""
    ut, pos = [], 0
    while pos + 6 <= len(d) and er_piv(d[pos:]):
        plan, palett, bitplan, pos = piv_les(d, pos)
        ut.append((plan, palett, bitplan))
    return ut, pos


def plan_til_indeks(bitplan, plan, bredde=320, hoyde=200):
    """Bitplan (plan for plan) til en liste med fargeindekser, linje for linje."""
    bpr = (bredde + 15) // 16 * 2
    psize = bpr * hoyde
    ut = bytearray(bredde * hoyde)
    for y in range(hoyde):
        for p in range(plan):
            rad = bitplan[p * psize + y * bpr:p * psize + y * bpr + bpr]
            bit = 1 << p
            for x in range(bredde):
                if rad[x >> 3] >> (7 - (x & 7)) & 1:
                    ut[y * bredde + x] |= bit
    return bytes(ut)


def indeks_til_plan(indekser, plan, bredde=320, hoyde=200):
    bpr = (bredde + 15) // 16 * 2
    psize = bpr * hoyde
    ut = bytearray(psize * plan)
    for y in range(hoyde):
        for x in range(bredde):
            v = indekser[y * bredde + x]
            for p in range(plan):
                if v >> p & 1:
                    ut[p * psize + y * bpr + (x >> 3)] |= 0x80 >> (x & 7)
    return bytes(ut)


def amiga_rgb(c):
    return ((c >> 8) & 15) * 17, ((c >> 4) & 15) * 17, (c & 15) * 17


# ---------------------------------------------------------------- CEL


def cel_les(d):
    """Returnerer (bilder, minne). bilder: liste med dict (bredde, hoyde, flagg, maske, plan, data)."""
    n, plen, minne = struct.unpack('>HII', d[:10])
    tabell = [struct.unpack('>IHHBB', d[10 + i * 10:20 + i * 10]) for i in range(n)]
    total = sum(((w + 15) // 16) * 2 * h * bin(m).count('1') for (_, w, h, _, m) in tabell)
    raw = lz_ut(d[10 + n * 10:10 + n * 10 + plen], total)
    bilder = []
    for (off, w, h, flagg, maske) in tabell:
        plan = bin(maske).count('1')
        storrelse = ((w + 15) // 16) * 2 * h * plan
        bilder.append(dict(bredde=w, hoyde=h, flagg=flagg, maske=maske, plan=plan, offset=off,
                           data=raw[off:off + storrelse]))
    return bilder, minne


def cel_lag(bilder):
    raw = bytearray()
    tabell = b''
    for b in bilder:
        tabell += struct.pack('>IHHBB', len(raw), b['bredde'], b['hoyde'], b['flagg'], b['maske'])
        raw += b['data']
    pakket = lz_inn(raw)
    return struct.pack('>HII', len(bilder), len(pakket), len(raw) * 8) + tabell + pakket


def er_cel(d):
    if len(d) < 20:
        return False
    n, plen, minne = struct.unpack('>HII', d[:10])
    if n == 0 or n > 500 or 10 + n * 10 + plen > len(d) + 2:
        return False
    off, w, h, flagg, maske = struct.unpack('>IHHBB', d[10:20])
    return off == 0 and 0 < w <= 640 and 0 < h <= 400 and maske != 0


# ---------------------------------------------------------------- hunk og 8SVX


def hunker(d):
    """Liste med (type, data) fra en AmigaDOS hunk-fil."""
    p = 0

    def L():
        nonlocal p
        v = struct.unpack('>I', d[p:p + 4])[0]
        p += 4
        return v
    if L() != 0x3f3:
        raise ValueError('ikke en hunk-fil')
    while L():
        p += 4 * struct.unpack('>I', d[p - 4:p])[0]
    L()
    forste, siste = L(), L()
    for _ in range(siste - forste + 1):
        L()
    ut = []
    while p + 4 <= len(d):
        t = L() & 0x3fffffff
        if t in (0x3e9, 0x3ea):
            n = L() * 4
            ut.append(('kode' if t == 0x3e9 else 'data', d[p:p + n]))
            p += n
        elif t == 0x3eb:
            L()
            ut.append(('bss', b''))
        elif t == 0x3ec:
            while True:
                n = L()
                if not n:
                    break
                p += 4 + n * 4
        elif t == 0x3f0:
            while True:
                n = L()
                if not n:
                    break
                p += n * 4 + 4
        elif t == 0x3f1:
            p += L() * 4
        elif t == 0x3f2:
            pass
        else:
            break
    return ut


def svx_alle(d):
    """Finner alle FORM 8SVX i data. Returnerer liste med dict (rate, data, navn)."""
    ut = []
    i = d.find(b'FORM')
    while i >= 0:
        lengde = struct.unpack('>I', d[i + 4:i + 8])[0]
        if d[i + 8:i + 12] == b'8SVX':
            stk = d[i + 12:i + 8 + lengde]
            p, rate, data, navn = 0, 8363, b'', ''
            while p + 8 <= len(stk):
                cid, ln = stk[p:p + 4], struct.unpack('>I', stk[p + 4:p + 8])[0]
                c = stk[p + 8:p + 8 + ln]
                if cid == b'VHDR':
                    rate = struct.unpack('>H', c[12:14])[0]
                elif cid == b'BODY':
                    data = c
                elif cid == b'NAME':
                    navn = c.split(b'\0')[0].decode('latin-1')
                p += 8 + ln + (ln & 1)
            ut.append(dict(rate=rate or 8363, data=data, navn=navn, offset=i))
        i = d.find(b'FORM', i + 4)
    return ut
