/* unzip.h - lesing av zip-filer (stored og deflate) og CRC32. */
#ifndef UNZIP_H
#define UNZIP_H

#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

typedef struct {
    char     name[256];
    unsigned method;        /* 0 = stored, 8 = deflate */
    uint32_t crc, csize, usize, offset;
} ZipEntry;

typedef struct {
    uint8_t  *data;         /* hele zip-filen i minnet */
    size_t    size;
    ZipEntry *entries;
    int       count;
} Zip;

uint32_t crc32_calc(const uint8_t *p, size_t n);
bool zip_open(Zip *z, const char *path);
/* Som zip_open, men fra minnet. Zip tar over data (frigjores av zip_close, ogsaa ved feil). */
bool zip_open_mem(Zip *z, uint8_t *data, size_t size);
void zip_close(Zip *z);
/* Finner en fil paa navn (uten mappe, store/smaa bokstaver likegyldig), eller paa CRC hvis crc != 0. */
const ZipEntry *zip_find(const Zip *z, const char *name, uint32_t crc);
/* Pakker ut filen og sjekker CRC. Returnerer NULL ved feil. Frigjor med free(). */
uint8_t *zip_read(const Zip *z, const ZipEntry *e);

#endif
