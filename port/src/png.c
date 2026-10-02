/*
 * png.c - skriver skjermbilder som PNG uten eksterne bibliotek.
 *
 * Bildet lagres med "stored" deflate-blokker (ingen pakking). Filene blir store,
 * men koden er kort og trenger ingen zlib.
 */
#include "amiga.h"
#include "unzip.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void be32w(uint8_t *p, uint32_t v) { p[0] = (uint8_t)(v >> 24); p[1] = (uint8_t)(v >> 16); p[2] = (uint8_t)(v >> 8); p[3] = (uint8_t)v; }

static void chunk(FILE *f, const char *type, const uint8_t *data, uint32_t len)
{
    uint8_t hdr[8];
    be32w(hdr, len);
    memcpy(hdr + 4, type, 4);
    fwrite(hdr, 1, 8, f);
    uint8_t *tmp = malloc(len + 4);
    memcpy(tmp, type, 4);
    if (len) memcpy(tmp + 4, data, len);
    uint32_t crc = crc32_calc(tmp, len + 4);
    free(tmp);
    if (len) fwrite(data, 1, len, f);
    uint8_t c[4];
    be32w(c, crc);
    fwrite(c, 1, 4, f);
}

/* rgba: byte R, G, B, A per piksel. Lagres som RGB. */
bool png_write(const char *path, const uint32_t *rgba, int w, int h, int stride)
{
    FILE *f = fopen(path, "wb");
    if (!f) return false;
    static const uint8_t sig[8] = { 0x89, 'P', 'N', 'G', 13, 10, 26, 10 };
    fwrite(sig, 1, 8, f);
    uint8_t ihdr[13];
    be32w(ihdr, (uint32_t)w);
    be32w(ihdr + 4, (uint32_t)h);
    ihdr[8] = 8; ihdr[9] = 2; ihdr[10] = 0; ihdr[11] = 0; ihdr[12] = 0;
    chunk(f, "IHDR", ihdr, 13);

    size_t raw_len = (size_t)h * (size_t)(w * 3 + 1);
    uint8_t *raw = malloc(raw_len);
    size_t o = 0;
    for (int y = 0; y < h; y++) {
        raw[o++] = 0;
        const uint8_t *src = (const uint8_t *)(rgba + (size_t)y * stride);
        for (int x = 0; x < w; x++) { raw[o++] = src[x * 4]; raw[o++] = src[x * 4 + 1]; raw[o++] = src[x * 4 + 2]; }
    }
    size_t nblocks = (raw_len + 65534) / 65535;
    size_t zlen = 2 + raw_len + nblocks * 5 + 4;
    uint8_t *z = malloc(zlen);
    size_t zp = 0;
    z[zp++] = 0x78; z[zp++] = 0x01;
    uint32_t a = 1, b = 0;
    for (size_t i = 0; i < raw_len; i++) { a = (a + raw[i]) % 65521; b = (b + a) % 65521; }
    for (size_t pos = 0; pos < raw_len;) {
        size_t n = raw_len - pos > 65535 ? 65535 : raw_len - pos;
        z[zp++] = pos + n == raw_len ? 1 : 0;
        z[zp++] = (uint8_t)n; z[zp++] = (uint8_t)(n >> 8);
        z[zp++] = (uint8_t)~n; z[zp++] = (uint8_t)(~n >> 8);
        memcpy(z + zp, raw + pos, n);
        zp += n;
        pos += n;
    }
    be32w(z + zp, b << 16 | a);
    zp += 4;
    chunk(f, "IDAT", z, (uint32_t)zp);
    chunk(f, "IEND", NULL, 0);
    free(raw);
    free(z);
    fclose(f);
    return true;
}
