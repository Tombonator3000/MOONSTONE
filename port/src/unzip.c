/*
 * unzip.c - leser filer fra en zip-fil (f.eks. Moonstonecd32-AMIGA.zip).
 *
 * Stotter "stored" og "deflate", som er det zip-programmer bruker. Inflate-delen
 * er en enkel kanonisk Huffman-dekoder etter samme oppskrift som puff.c av
 * Mark Adler (zlib-lisens) og RFC 1951. Den er laget for aa vaere lett aa lese,
 * ikke rask; spillfilene pakkes ut paa et brokdels sekund likevel.
 */
#include "unzip.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* ------------------------------------------------------------------ CRC32 */
uint32_t crc32_calc(const uint8_t *p, size_t n)
{
    static uint32_t table[256];
    if (!table[1]) {
        for (uint32_t i = 0; i < 256; i++) {
            uint32_t c = i;
            for (int k = 0; k < 8; k++) c = (c & 1) ? 0xedb88320u ^ (c >> 1) : c >> 1;
            table[i] = c;
        }
    }
    uint32_t crc = 0xffffffffu;
    while (n--) crc = table[(crc ^ *p++) & 0xff] ^ (crc >> 8);
    return crc ^ 0xffffffffu;
}

/* ------------------------------------------------------------------ inflate */
typedef struct {
    const uint8_t *in;
    size_t inlen, inpos;
    uint8_t *out;
    size_t outlen, outpos;
    uint32_t bitbuf;
    int bitcnt;
    int err;
} Inflate;

typedef struct {
    short count[16];     /* antall koder med hver lengde */
    short symbol[288];   /* symbolene sortert etter kode */
} Huffman;

static int getbits(Inflate *s, int need)
{
    uint32_t val = s->bitbuf;
    while (s->bitcnt < need) {
        if (s->inpos >= s->inlen) { s->err = 1; return 0; }
        val |= (uint32_t)s->in[s->inpos++] << s->bitcnt;
        s->bitcnt += 8;
    }
    s->bitbuf = val >> need;
    s->bitcnt -= need;
    return (int)(val & ((1u << need) - 1));
}

/* Lager dekodetabellen fra kodelengdene. Returnerer < 0 hvis lengdene er ugyldige. */
static int construct(Huffman *h, const short *length, int n)
{
    short offs[16];
    for (int len = 0; len < 16; len++) h->count[len] = 0;
    for (int sym = 0; sym < n; sym++) h->count[length[sym]]++;
    if (h->count[0] == n) return 0;
    int left = 1;
    for (int len = 1; len < 16; len++) {
        left <<= 1;
        left -= h->count[len];
        if (left < 0) return left;
    }
    offs[1] = 0;
    for (int len = 1; len < 15; len++) offs[len + 1] = offs[len] + h->count[len];
    for (int sym = 0; sym < n; sym++)
        if (length[sym]) h->symbol[offs[length[sym]]++] = (short)sym;
    return left;
}

static int decode(Inflate *s, const Huffman *h)
{
    int code = 0, first = 0, index = 0;
    for (int len = 1; len < 16; len++) {
        code |= getbits(s, 1);
        int count = h->count[len];
        if (code - count < first) return h->symbol[index + (code - first)];
        index += count;
        first += count;
        first <<= 1;
        code <<= 1;
    }
    return -1;
}

static int codes(Inflate *s, const Huffman *lencode, const Huffman *distcode)
{
    static const short lbase[29] = { 3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 15, 17, 19, 23, 27, 31,
                                     35, 43, 51, 59, 67, 83, 99, 115, 131, 163, 195, 227, 258 };
    static const short lext[29] = { 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2,
                                    3, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5, 5, 0 };
    static const short dbase[30] = { 1, 2, 3, 4, 5, 7, 9, 13, 17, 25, 33, 49, 65, 97, 129, 193,
                                     257, 385, 513, 769, 1025, 1537, 2049, 3073, 4097, 6145,
                                     8193, 12289, 16385, 24577 };
    static const short dext[30] = { 0, 0, 0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6,
                                    7, 7, 8, 8, 9, 9, 10, 10, 11, 11, 12, 12, 13, 13 };
    int sym;
    do {
        sym = decode(s, lencode);
        if (sym < 0 || s->err) return -1;
        if (sym < 256) {
            if (s->outpos >= s->outlen) return -1;
            s->out[s->outpos++] = (uint8_t)sym;
        } else if (sym > 256) {
            sym -= 257;
            if (sym >= 29) return -1;
            int len = lbase[sym] + getbits(s, lext[sym]);
            int dsym = decode(s, distcode);
            if (dsym < 0 || dsym >= 30) return -1;
            size_t dist = (size_t)(dbase[dsym] + getbits(s, dext[dsym]));
            if (s->err || dist > s->outpos || s->outpos + (size_t)len > s->outlen) return -1;
            while (len--) {
                s->out[s->outpos] = s->out[s->outpos - dist];
                s->outpos++;
            }
        }
    } while (sym != 256);
    return 0;
}

static int stored(Inflate *s)
{
    s->bitbuf = 0;
    s->bitcnt = 0;
    if (s->inpos + 4 > s->inlen) return -1;
    unsigned len = s->in[s->inpos] | (s->in[s->inpos + 1] << 8);
    unsigned nlen = s->in[s->inpos + 2] | (s->in[s->inpos + 3] << 8);
    s->inpos += 4;
    if (len != (~nlen & 0xffff)) return -1;
    if (s->inpos + len > s->inlen || s->outpos + len > s->outlen) return -1;
    memcpy(s->out + s->outpos, s->in + s->inpos, len);
    s->inpos += len;
    s->outpos += len;
    return 0;
}

static int fixed(Inflate *s)
{
    static Huffman lencode, distcode;
    static int ready;
    if (!ready) {
        short lengths[288];
        int sym = 0;
        for (; sym < 144; sym++) lengths[sym] = 8;
        for (; sym < 256; sym++) lengths[sym] = 9;
        for (; sym < 280; sym++) lengths[sym] = 7;
        for (; sym < 288; sym++) lengths[sym] = 8;
        construct(&lencode, lengths, 288);
        for (sym = 0; sym < 30; sym++) lengths[sym] = 5;
        construct(&distcode, lengths, 30);
        ready = 1;
    }
    return codes(s, &lencode, &distcode);
}

static int dynamic(Inflate *s)
{
    static const short order[19] = { 16, 17, 18, 0, 8, 7, 9, 6, 10, 5, 11, 4, 12, 3, 13, 2, 14, 1, 15 };
    short lengths[320];
    Huffman lencode, distcode;
    int nlen = getbits(s, 5) + 257;
    int ndist = getbits(s, 5) + 1;
    int ncode = getbits(s, 4) + 4;
    if (s->err || nlen > 286 || ndist > 30) return -1;
    int index;
    for (index = 0; index < ncode; index++) lengths[order[index]] = (short)getbits(s, 3);
    for (; index < 19; index++) lengths[order[index]] = 0;
    if (construct(&lencode, lengths, 19) != 0) return -1;

    index = 0;
    while (index < nlen + ndist) {
        int sym = decode(s, &lencode);
        if (sym < 0 || s->err) return -1;
        if (sym < 16) {
            lengths[index++] = (short)sym;
        } else {
            short len = 0;
            int rep;
            if (sym == 16) {
                if (index == 0) return -1;
                len = lengths[index - 1];
                rep = 3 + getbits(s, 2);
            } else if (sym == 17) {
                rep = 3 + getbits(s, 3);
            } else {
                rep = 11 + getbits(s, 7);
            }
            if (index + rep > nlen + ndist) return -1;
            while (rep--) lengths[index++] = len;
        }
    }
    if (lengths[256] == 0) return -1;     /* maa ha en sluttkode */
    int err = construct(&lencode, lengths, nlen);
    if (err < 0 || (err > 0 && nlen - lencode.count[0] != 1)) return -1;
    err = construct(&distcode, lengths + nlen, ndist);
    if (err < 0 || (err > 0 && ndist - distcode.count[0] != 1)) return -1;
    return codes(s, &lencode, &distcode);
}

static int inflate_raw(const uint8_t *in, size_t inlen, uint8_t *out, size_t outlen)
{
    Inflate s = { in, inlen, 0, out, outlen, 0, 0, 0, 0 };
    int last;
    do {
        last = getbits(&s, 1);
        int type = getbits(&s, 2);
        if (s.err) return -1;
        int r = type == 0 ? stored(&s) : type == 1 ? fixed(&s) : type == 2 ? dynamic(&s) : -1;
        if (r != 0) return -1;
    } while (!last);
    return s.outpos == outlen ? 0 : -1;
}

/* ------------------------------------------------------------------ zip */
static unsigned rd16(const uint8_t *p) { return p[0] | (p[1] << 8); }
static uint32_t rd32(const uint8_t *p) { return p[0] | (p[1] << 8) | (p[2] << 16) | ((uint32_t)p[3] << 24); }

bool zip_open(Zip *z, const char *path)
{
    memset(z, 0, sizeof *z);
    FILE *f = fopen(path, "rb");
    if (!f) return false;
    fseek(f, 0, SEEK_END);
    long size = ftell(f);
    fseek(f, 0, SEEK_SET);
    if (size < 22) { fclose(f); return false; }
    uint8_t *data = malloc((size_t)size);
    if (!data || fread(data, 1, (size_t)size, f) != (size_t)size) { fclose(f); free(data); return false; }
    fclose(f);
    return zip_open_mem(z, data, (size_t)size);
}

bool zip_open_mem(Zip *z, uint8_t *data, size_t size)
{
    memset(z, 0, sizeof *z);
    z->data = data;
    z->size = size;
    if (size < 22) { zip_close(z); return false; }

    /* finn "end of central directory" bakfra (kommentaren kan vaere opptil 64 kB) */
    const uint8_t *eocd = NULL;
    for (size_t i = z->size - 22; ; i--) {
        if (rd32(z->data + i) == 0x06054b50) { eocd = z->data + i; break; }
        if (i == 0 || z->size - i > 0x10000 + 22) break;
    }
    if (!eocd) { zip_close(z); return false; }
    unsigned count = rd16(eocd + 10);
    size_t pos = rd32(eocd + 16);
    z->entries = calloc(count ? count : 1, sizeof *z->entries);
    for (unsigned n = 0; n < count; n++) {
        if (pos + 46 > z->size || rd32(z->data + pos) != 0x02014b50) break;
        const uint8_t *c = z->data + pos;
        ZipEntry *e = &z->entries[z->count];
        unsigned namelen = rd16(c + 28), extralen = rd16(c + 30), commentlen = rd16(c + 32);
        e->method = rd16(c + 10);
        e->crc = rd32(c + 16);
        e->csize = rd32(c + 20);
        e->usize = rd32(c + 24);
        e->offset = rd32(c + 42);
        size_t nl = namelen < sizeof e->name - 1 ? namelen : sizeof e->name - 1;
        memcpy(e->name, c + 46, nl);
        e->name[nl] = 0;
        pos += 46 + namelen + extralen + commentlen;
        z->count++;
    }
    return true;
}

void zip_close(Zip *z)
{
    free(z->data);
    free(z->entries);
    memset(z, 0, sizeof *z);
}

static const char *basename_of(const char *p)
{
    const char *b = p;
    for (; *p; p++) if (*p == '/' || *p == '\\') b = p + 1;
    return b;
}

static bool same_name(const char *a, const char *b)
{
    for (; *a && *b; a++, b++) {
        char x = *a, y = *b;
        if (x >= 'A' && x <= 'Z') x += 32;
        if (y >= 'A' && y <= 'Z') y += 32;
        if (x != y) return false;
    }
    return *a == *b;
}

const ZipEntry *zip_find(const Zip *z, const char *name, uint32_t crc)
{
    for (int i = 0; i < z->count; i++)
        if (same_name(basename_of(z->entries[i].name), name)) return &z->entries[i];
    if (crc)
        for (int i = 0; i < z->count; i++)
            if (z->entries[i].crc == crc) return &z->entries[i];
    return NULL;
}

uint8_t *zip_read(const Zip *z, const ZipEntry *e)
{
    if (e->offset + 30 > z->size || rd32(z->data + e->offset) != 0x04034b50) return NULL;
    const uint8_t *lh = z->data + e->offset;
    size_t start = e->offset + 30 + rd16(lh + 26) + rd16(lh + 28);
    if (start + e->csize > z->size) return NULL;
    uint8_t *out = malloc(e->usize ? e->usize : 1);
    if (!out) return NULL;
    int ok;
    if (e->method == 0) ok = e->csize == e->usize && (memcpy(out, z->data + start, e->usize), 1);
    else if (e->method == 8) ok = inflate_raw(z->data + start, e->csize, out, e->usize) == 0;
    else ok = 0;
    if (!ok || crc32_calc(out, e->usize) != e->crc) { free(out); return NULL; }
    return out;
}
