#!/usr/bin/env python3
"""
lyd.py - pakker ut lydene og musikken i Moonstone.

    python3 tools/lyd.py extract Moonstonecd32-AMIGA.zip assets/lyd

  .a-filene     hunk-filer med 8SVX-lyder (kn.a = ridderen, ba.a = Balok osv.).
                Hver lyd blir en WAV-fil (8 bit mono, med samplefrekvensen fra filen).
  music.cmp     musikken (introen) og vmusic.cmp (seiersmusikken), pakket med en
                egen metode (se cmp_ut). Innholdet er ProTracker-moduler med 31
                instrumenter der bare merket "M.K." mangler. Lagres som .mod (spilles
                i OpenMPT, VLC, XMP) og som .bin (akkurat slik spillet har dem).

Lydene er 8-bits PCM med fortegn, som Paula spiller dem.
"""
import os
import struct
import sys
import wave

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import moonfiles as mf  # noqa: E402


# ---------------------------------------------------------------- musikkpakkingen

def cmp_ut(d):
    """Pakker ut music.cmp og vmusic.cmp.

    Hodet sier RNC\\x01, men dataene er pakket med en annen metode enn vanlig RNC:
    bitene leses bakfra, og utdataene skrives bakfra. Dette er en direkte
    oversettelse av utpakkeren i introen (program, $85968-$85AA2).
    Hode: 'RNC\\x01', long utpakket lengde, long pakket lengde, pakkede data.
    """
    if d[:4] != b'RNC\x01':
        raise ValueError('ikke en .cmp-fil')
    ulen, plen = struct.unpack('>II', d[4:12])
    src = d[12:12 + plen]
    ut = bytearray(ulen + 1024)
    a3 = len(ut)                      # skrivepeker, gaar bakover
    a2 = a3
    a6 = len(src)                     # lesepeker, gaar bakover
    st = {'d3': 0}

    a6 -= 1
    st['d3'] = src[a6]

    def bit():
        nonlocal a6
        d3 = st['d3']
        c = d3 >> 7 & 1
        d3 = (d3 << 1) & 0xff
        if d3:
            st['d3'] = d3
            return c
        a6 -= 1
        d3 = src[a6]
        c = d3 >> 7 & 1
        st['d3'] = ((d3 << 1) | 1) & 0xff      # roxl med X = 1 (markoren)
        return c

    def bits(n):
        v = 0
        for _ in range(n):
            v = (v << 1) | bit()
        return v

    while True:
        # en rekke bytes som de er
        if bit():
            if bit():
                for d1, (bredde, pluss) in enumerate(((2, 1), (2, 4), (3, 7), (10, 14))):
                    d5 = bits(bredde)
                    if d1 == 3 or d5 != (1 << bredde) - 1:
                        break
                n = d5 + pluss + 1
            else:
                n = 1
            for _ in range(n):
                a6 -= 1
                a3 -= 1
                ut[a3] = src[a6]
        if a6 <= 0:
            break
        # lengde
        k = 0
        while k < 4 and bit():
            k += 1
        lengde = (2, 3, 4, 6, 10)[k] + bits((0, 0, 1, 2, 10)[k])
        # avstand
        if lengde == 2:
            avstand = bits(9) + 0x40 if bit() else bits(6)
        else:
            k = 0
            while k < 2 and bit():
                k += 1
            if k == 0:
                avstand = bits(8) + 32
            elif k == 1:
                avstand = bits(5)
            else:
                avstand = bits(12) + 288
        kilde = a3 + avstand + lengde - 1 if avstand else a3 + 1
        for _ in range(lengde):
            kilde -= 1
            a3 -= 1
            ut[a3] = ut[kilde]
    return bytes(ut[a3:a2])


def lagre_wav(sti, data, rate):
    with wave.open(sti, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(1)
        w.setframerate(rate)
        w.writeframes(bytes((b + 128) & 0xff for b in data))   # WAV 8 bit er uten fortegn


def extract(spill_sti, ut):
    spill = mf.Spill(spill_sti)
    os.makedirs(ut, exist_ok=True)
    antall = 0
    for sti in spill.data_filer():
        navn = sti.split('/', 1)[1]
        data = spill.filer[sti]
        if navn.lower().endswith('.a'):
            lyder = mf.svx_alle(data)
            mappe = os.path.join(ut, navn)
            os.makedirs(mappe, exist_ok=True)
            for i, s in enumerate(lyder):
                fil = '%02d%s.wav' % (i, ('_' + s['navn']) if s['navn'] else '')
                lagre_wav(os.path.join(mappe, fil), s['data'], s['rate'])
                antall += 1
            print('%-12s %d lyder' % (navn, len(lyder)))
        elif navn.lower().endswith('.cmp'):
            u = cmp_ut(data)
            with open(os.path.join(ut, navn + '.bin'), 'wb') as f:
                f.write(u)
            # ProTracker-modul med 31 instrumenter, men uten "M.K." paa 1080
            mod = bytearray(u)
            mod[1080:1084] = b'M.K.'
            with open(os.path.join(ut, navn.rsplit('.', 1)[0] + '.mod'), 'wb') as f:
                f.write(mod)
            ulen = struct.unpack('>I', data[4:8])[0]
            print('%-12s %d -> %d byte (%s)' % (navn, len(data), len(u), 'ok' if len(u) == ulen else 'FEIL LENGDE'))
    print('Ferdig: %d lyder i %s' % (antall, ut))


def main():
    a = sys.argv[1:]
    if len(a) >= 3 and a[0] == 'extract':
        extract(a[1], a[2])
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == '__main__':
    main()
