/*
 * decrunch.c - utpakking av RNC ProPack (metode 1) og Moonstone sin egen LZ-pakking.
 *
 * RNC brukes paa musikken (music.cmp, vmusic.cmp). WHDLoad pakker slike filer
 * ut av seg selv i resload_LoadFileDecrunch, og det gjor vi ogsaa. Koden for
 * metode 1 folger den kjente beskrivelsen av formatet (dernc): et hode paa 18
 * byte, og data i blokker med tre Huffman-tabeller (bokstaver, avstand, lengde).
 *
 * Spillets egen pakking (PIV, CEL, .t, .c, .p, .ob) er en enkel LZ77: en
 * kontrollbyte med 8 flagg, hoyeste bit forst. Flagg 0 = en byte som den er.
 * Flagg 1 = to byte: 5 bit gir lengden (34 - n, altsaa 3 til 34) og 11 bit
 * avstanden bakover. Slik er utpakkeren i slaven (adresse $50e i Moonstone.Slave).
 */
#include "amiga.h"
#include <stdlib.h>
#include <string.h>

/* ------------------------------------------------------------ RNC metode 1 */
typedef struct { uint64_t buf; int count; const uint8_t *p; } Bits;
typedef struct { int num; struct { uint32_t code; int len; int value; } t[32]; } Huf;

static uint32_t lword(const uint8_t *p) { return p[0] | p[1] << 8 | p[2] << 16 | (uint32_t)p[3] << 24; }
static uint32_t be32(const uint8_t *p) { return (uint32_t)p[0] << 24 | p[1] << 16 | p[2] << 8 | p[3]; }

static void bits_init(Bits *b, const uint8_t *p) { b->p = p; b->buf = lword(p); b->count = 16; }

static void bits_fix(Bits *b)
{
    b->count -= 16;
    b->buf &= ((uint64_t)1 << b->count) - 1;
    b->buf |= (uint64_t)lword(b->p) << b->count;
    b->count += 16;
}

static void bits_advance(Bits *b, int n)
{
    b->buf >>= n;
    b->count -= n;
    if (b->count < 16) {
        b->p += 2;
        b->buf |= (uint64_t)lword(b->p) << b->count;
        b->count += 16;
    }
}

static uint32_t bits_read(Bits *b, uint32_t mask, int n)
{
    uint32_t v = (uint32_t)(b->buf & mask);
    bits_advance(b, n);
    return v;
}

static uint32_t mirror(uint32_t x, int n)
{
    uint32_t top = 1u << (n - 1), bottom = 1;
    while (top > bottom) {
        uint32_t m = top | bottom, v = x & m;
        if (v != 0 && v != m) x ^= m;
        top >>= 1; bottom <<= 1;
    }
    return x;
}

static void read_huf(Huf *h, Bits *b)
{
    int len[32], num = (int)bits_read(b, 0x1f, 5), maxlen = 1;
    h->num = 0;
    if (!num) return;
    for (int i = 0; i < num; i++) {
        len[i] = (int)bits_read(b, 0x0f, 4);
        if (len[i] > maxlen) maxlen = len[i];
    }
    uint32_t code = 0;
    int k = 0;
    for (int l = 1; l <= maxlen; l++) {
        for (int j = 0; j < num; j++)
            if (len[j] == l) {
                h->t[k].code = mirror(code, l);
                h->t[k].len = l;
                h->t[k].value = j;
                code++;
                k++;
            }
        code <<= 1;
    }
    h->num = k;
}

static long huf_read(const Huf *h, Bits *b)
{
    int i;
    for (i = 0; i < h->num; i++) {
        uint32_t mask = (1u << h->t[i].len) - 1;
        if ((b->buf & mask) == h->t[i].code) break;
    }
    if (i == h->num) return -1;
    bits_advance(b, h->t[i].len);
    long v = h->t[i].value;
    if (v >= 2) {
        long top = 1L << (v - 1);
        v = top | (long)bits_read(b, (uint32_t)top - 1, h->t[i].value - 1);
    }
    return v;
}

static uint16_t crc16(const uint8_t *p, size_t n)
{
    uint16_t c = 0;
    while (n--) {
        c ^= *p++;
        for (int i = 0; i < 8; i++) c = (c & 1) ? (uint16_t)((c >> 1) ^ 0xa001) : (uint16_t)(c >> 1);
    }
    return c;
}

long rnc_unpacked_size(const uint8_t *src, size_t len)
{
    if (len < 18 || src[0] != 'R' || src[1] != 'N' || src[2] != 'C') return 0;
    return (long)be32(src + 4);
}

long rnc_unpack(const uint8_t *src, size_t len, uint8_t *dst, size_t dstlen)
{
    if (len < 18 || src[0] != 'R' || src[1] != 'N' || src[2] != 'C') return 0;
    if (src[3] != 1) return -1;           /* bare metode 1 trengs for Moonstone */
    uint32_t ulen = be32(src + 4), plen = be32(src + 8);
    if (ulen > dstlen || 18 + (size_t)plen > len) return -1;
    if (crc16(src + 18, plen) != (uint16_t)(src[14] << 8 | src[15])) return -1;
    /* kopi med litt luft bak, fordi bitlesingen ser noen byte forbi slutten */
    uint8_t *in = calloc(plen + 16, 1);
    if (!in) return -1;
    memcpy(in, src + 18, plen);
    Bits b;
    bits_init(&b, in);
    bits_advance(&b, 2);
    uint8_t *out = dst, *end = dst + ulen;
    Huf raw, dist, ln;
    long result = (long)ulen;
    while (out < end) {
        read_huf(&raw, &b);
        read_huf(&dist, &b);
        read_huf(&ln, &b);
        long count = (long)bits_read(&b, 0xffff, 16);
        for (;;) {
            long n = huf_read(&raw, &b);
            if (n < 0) { result = -1; goto done; }
            if (n) {
                if (out + n > end || b.p + n > in + plen + 8) { result = -1; goto done; }
                while (n--) *out++ = *b.p++;
                bits_fix(&b);
            }
            if (--count <= 0) break;
            long pos = huf_read(&dist, &b);
            long l = huf_read(&ln, &b);
            if (pos < 0 || l < 0) { result = -1; goto done; }
            pos += 1;
            l += 2;
            if (out - pos < dst || out + l > end) { result = -1; goto done; }
            while (l--) { *out = out[-pos]; out++; }
        }
    }
    if (crc16(dst, ulen) != (uint16_t)(src[12] << 8 | src[13])) result = -1;
done:
    free(in);
    return result;
}

/* ------------------------------------------------------------ Moonstone-LZ */
size_t ms_unpack(const uint8_t *src, size_t srclen, uint8_t *dst, size_t dstmax)
{
    const uint8_t *s = src, *se = src + srclen;
    size_t o = 0;
    while (s < se) {
        uint8_t ctl = *s++;
        for (int bit = 0; bit < 8 && s < se; bit++, ctl <<= 1) {
            if (ctl & 0x80) {
                if (s + 2 > se) return o;
                unsigned w = (unsigned)s[0] << 8 | s[1];
                s += 2;
                unsigned dist = w & 0x7ff, len = 34 - (w >> 11);
                for (unsigned i = 0; i < len; i++) {
                    uint8_t v = (o >= dist && o - dist < dstmax) ? dst[o - dist] : 0;
                    if (o < dstmax) dst[o] = v;
                    o++;
                }
            } else {
                if (o < dstmax) dst[o] = *s;
                o++;
                s++;
            }
        }
    }
    return o;
}
