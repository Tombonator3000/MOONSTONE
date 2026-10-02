/*
 * files.c - spillfilene: slaven og datamappen til Moonstone.
 *
 * Filene kan komme fra:
 *   - Moonstonecd32-AMIGA.zip (zip med CD32-ISO-en inni)
 *   - ISO-filen selv ("Moonstone CD32.iso")
 *   - en zip med Moonstone-mappen (Moonstone.Slave og data/)
 *   - en vanlig mappe med de samme filene
 *
 * Alt leses inn i minnet. Mappen med Moonstone.Slave er roten; spillet ber om
 * filer relativt til data/ (ws_CurrentDir i slaven). Store og smaa bokstaver
 * er likegyldige, slik som paa Amiga.
 *
 * Filer spillet skriver (resload_SaveFile) legges i en egen liste i minnet og
 * gaar foran originalene naar de leses igjen.
 */
#include "amiga.h"
#include "unzip.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#ifndef _WIN32
#include <dirent.h>
#include <sys/stat.h>
#else
#include <windows.h>
#endif

typedef struct {
    char     path[160];                   /* relativt til spillmappen, med / */
    uint8_t *data;                        /* peker inn i blob, eller egen kopi */
    size_t   size;
    bool     owned;
} FileEntry;

static FileEntry *ents;
static int        n_ents, cap_ents;
static uint8_t   *blob;                   /* ISO-en eller zip-filen, holdes i minnet */
char files_error[256];

static FileEntry *saved;
static int        n_saved;

/* Filer spillet har sett paa (lest eller spurt etter storrelsen til). Verten i
 * nettspill sender dem til gjestene, som ikke har spillfilene selv. */
static char accessed[32][160];
static int  n_accessed;

static void note_access(const char *path)
{
    for (int i = 0; i < n_accessed; i++) if (!strcmp(accessed[i], path)) return;
    if (n_accessed < 32) snprintf(accessed[n_accessed++], sizeof accessed[0], "%s", path);
}

int files_accessed_count(void) { return n_accessed; }
const char *files_accessed_name(int i) { return i >= 0 && i < n_accessed ? accessed[i] : NULL; }
void files_accessed_clear(void) { n_accessed = 0; }

static bool same_ci(const char *a, const char *b)
{
    for (; *a && *b; a++, b++)
        if (tolower((unsigned char)*a) != tolower((unsigned char)*b)) return false;
    return *a == *b;
}

static void add_entry(const char *path, uint8_t *data, size_t size, bool owned)
{
    if (n_ents == cap_ents) {
        cap_ents = cap_ents ? cap_ents * 2 : 256;
        ents = realloc(ents, sizeof *ents * (size_t)cap_ents);
    }
    FileEntry *e = &ents[n_ents++];
    snprintf(e->path, sizeof e->path, "%s", path);
    for (char *p = e->path; *p; p++) if (*p == '\\') *p = '/';
    e->data = data;
    e->size = size;
    e->owned = owned;
}

void files_close(void)
{
    for (int i = 0; i < n_ents; i++) if (ents[i].owned) free(ents[i].data);
    free(ents);
    ents = NULL;
    n_ents = cap_ents = 0;
    free(blob);
    blob = NULL;
}

/* ------------------------------------------------------------ ISO 9660 */
static uint32_t le32(const uint8_t *p) { return p[0] | p[1] << 8 | p[2] << 16 | (uint32_t)p[3] << 24; }

static void iso_dir(uint8_t *iso, size_t size, uint32_t lba, uint32_t len, const char *prefix, int depth)
{
    if (depth > 8) return;
    size_t pos = (size_t)lba * 2048, end = pos + len;
    if (end > size) return;
    while (pos < end) {
        uint8_t rl = iso[pos];
        if (rl == 0) { pos = (pos / 2048 + 1) * 2048; continue; }
        const uint8_t *r = iso + pos;
        uint32_t elba = le32(r + 2), elen = le32(r + 10);
        uint8_t flags = r[25], nl = r[32];
        char name[128];
        if (nl == 1 && (r[33] == 0 || r[33] == 1)) { pos += rl; continue; }
        if (nl >= sizeof name) nl = sizeof name - 1;
        memcpy(name, r + 33, nl);
        name[nl] = 0;
        char *semi = strchr(name, ';');
        if (semi) *semi = 0;
        size_t n = strlen(name);
        if (n && name[n - 1] == '.') name[n - 1] = 0;
        char path[256];
        snprintf(path, sizeof path, "%s%s%s", prefix, *prefix ? "/" : "", name);
        if (flags & 2) iso_dir(iso, size, elba, elen, path, depth + 1);
        else if ((size_t)elba * 2048 + elen <= size) add_entry(path, iso + (size_t)elba * 2048, elen, false);
        pos += rl;
    }
}

static bool iso_parse(uint8_t *iso, size_t size)
{
    if (size < 0x8000 + 2048 || memcmp(iso + 0x8001, "CD001", 5) != 0) return false;
    const uint8_t *root = iso + 0x8000 + 156;
    iso_dir(iso, size, le32(root + 2), le32(root + 10), "", 0);
    return true;
}

/* ------------------------------------------------------------ roten */
/* Finner mappen med Moonstone.Slave og gjor stiene relative til den. */
static bool find_root(void)
{
    const char *slave = NULL;
    for (int i = 0; i < n_ents; i++) {
        const char *b = strrchr(ents[i].path, '/');
        b = b ? b + 1 : ents[i].path;
        if (same_ci(b, "Moonstone.Slave")) { slave = ents[i].path; break; }
    }
    if (!slave) {
        snprintf(files_error, sizeof files_error, "Fant ikke Moonstone.Slave i filene.");
        return false;
    }
    char root[160];
    snprintf(root, sizeof root, "%s", slave);
    char *b = strrchr(root, '/');
    if (b) b[1] = 0; else root[0] = 0;
    size_t rl = strlen(root);
    int j = 0;
    for (int i = 0; i < n_ents; i++) {
        if (rl && strncmp(ents[i].path, root, rl) != 0) {
            if (ents[i].owned) free(ents[i].data);
            continue;
        }
        FileEntry e = ents[i];
        memmove(e.path, e.path + rl, strlen(e.path + rl) + 1);
        ents[j++] = e;
    }
    n_ents = j;
    size_t sz;
    if (!files_exists("data/program", &sz) || !files_exists("data/mog", &sz)) {
        snprintf(files_error, sizeof files_error, "Mappen data med program og mog mangler.");
        return false;
    }
    return true;
}

/* ------------------------------------------------------------ zip */
static bool from_zip(uint8_t *data, size_t size)
{
    Zip z;
    if (!zip_open_mem(&z, data, size)) return false;   /* zip tar over data */
    /* ISO inni zip-filen? */
    for (int i = 0; i < z.count; i++) {
        const char *n = z.entries[i].name;
        size_t l = strlen(n);
        if (l > 4 && same_ci(n + l - 4, ".iso")) {
            uint8_t *iso = zip_read(&z, &z.entries[i]);
            size_t isz = z.entries[i].usize;
            zip_close(&z);
            if (!iso) { snprintf(files_error, sizeof files_error, "Klarte ikke pakke ut ISO-filen fra zip-filen."); return false; }
            blob = iso;
            if (!iso_parse(iso, isz)) { snprintf(files_error, sizeof files_error, "ISO-filen i zip-filen kan ikke leses."); return false; }
            return true;
        }
    }
    /* zip i zip (f.eks. lastet ned paa nytt) */
    for (int i = 0; i < z.count; i++) {
        const char *n = z.entries[i].name;
        size_t l = strlen(n);
        if (l > 4 && same_ci(n + l - 4, ".zip")) {
            uint8_t *inner = zip_read(&z, &z.entries[i]);
            size_t isz = z.entries[i].usize;
            if (inner) {
                int before = n_ents;
                if (from_zip(inner, isz) && n_ents > before) { zip_close(&z); return true; }
            }
        }
    }
    for (int i = 0; i < z.count; i++) {
        const ZipEntry *e = &z.entries[i];
        size_t l = strlen(e->name);
        if (!l || e->name[l - 1] == '/') continue;
        uint8_t *d = zip_read(&z, e);
        if (d) add_entry(e->name, d, e->usize, true);
    }
    zip_close(&z);
    return true;
}

/* ------------------------------------------------------------ mappe */
static uint8_t *read_file(const char *path, size_t *size)
{
    FILE *f = fopen(path, "rb");
    if (!f) return NULL;
    fseek(f, 0, SEEK_END);
    long n = ftell(f);
    fseek(f, 0, SEEK_SET);
    if (n < 0) { fclose(f); return NULL; }
    uint8_t *d = malloc((size_t)n + 1);
    if (d && fread(d, 1, (size_t)n, f) != (size_t)n) { free(d); d = NULL; }
    fclose(f);
    if (d) *size = (size_t)n;
    return d;
}

static void from_dir(const char *dir, const char *prefix, int depth)
{
    if (depth > 4) return;
#ifndef _WIN32
    DIR *d = opendir(dir);
    if (!d) return;
    struct dirent *de;
    while ((de = readdir(d))) {
        if (de->d_name[0] == '.') continue;
        char full[1024], rel[512];
        snprintf(full, sizeof full, "%s/%s", dir, de->d_name);
        snprintf(rel, sizeof rel, "%s%s%s", prefix, *prefix ? "/" : "", de->d_name);
        struct stat st;
        if (stat(full, &st) != 0) continue;
        if (S_ISDIR(st.st_mode)) from_dir(full, rel, depth + 1);
        else if (st.st_size < 32 * 1024 * 1024) {
            size_t sz;
            uint8_t *data = read_file(full, &sz);
            if (data) add_entry(rel, data, sz, true);
        }
    }
    closedir(d);
#else
    char pattern[1024];
    snprintf(pattern, sizeof pattern, "%s\\*", dir);
    WIN32_FIND_DATAA fd;
    HANDLE h = FindFirstFileA(pattern, &fd);
    if (h == INVALID_HANDLE_VALUE) return;
    do {
        if (fd.cFileName[0] == '.') continue;
        char full[1024], rel[512];
        snprintf(full, sizeof full, "%s\\%s", dir, fd.cFileName);
        snprintf(rel, sizeof rel, "%s%s%s", prefix, *prefix ? "/" : "", fd.cFileName);
        if (fd.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY) from_dir(full, rel, depth + 1);
        else {
            size_t sz;
            uint8_t *data = read_file(full, &sz);
            if (data) add_entry(rel, data, sz, true);
        }
    } while (FindNextFileA(h, &fd));
    FindClose(h);
#endif
}

/* ------------------------------------------------------------ inngang */
bool files_open_mem(uint8_t *data, size_t size, const char *name)
{
    (void)name;
    files_close();
    files_error[0] = 0;
    bool ok;
    if (size >= 4 && data[0] == 'P' && data[1] == 'K') ok = from_zip(data, size);
    else if (size > 0x8006 && memcmp(data + 0x8001, "CD001", 5) == 0) { blob = data; ok = iso_parse(data, size); }
    else {
        free(data);
        snprintf(files_error, sizeof files_error, "Filen er verken zip eller ISO.");
        return false;
    }
    if (!ok) {
        if (!files_error[0]) snprintf(files_error, sizeof files_error, "Filen kunne ikke leses.");
        return false;
    }
    return find_root();
}

/* Spillfila som er bygget inn i programmet (port/bin2c.py), eller false. */
bool files_open_embedded(void)
{
    if (!spill_innebygd_storrelse) return false;
    uint8_t *d = malloc(spill_innebygd_storrelse);       /* files_open_mem tar over bufferet */
    if (!d) return false;
    memcpy(d, spill_innebygd, spill_innebygd_storrelse);
    return files_open_mem(d, spill_innebygd_storrelse, "innebygd");
}

bool files_open(const char *path)
{
    files_close();
    files_error[0] = 0;
#ifndef _WIN32
    struct stat st;
    if (stat(path, &st) == 0 && S_ISDIR(st.st_mode)) {
#else
    DWORD attr = GetFileAttributesA(path);
    if (attr != INVALID_FILE_ATTRIBUTES && (attr & FILE_ATTRIBUTE_DIRECTORY)) {
#endif
        from_dir(path, "", 0);
        /* en zip eller ISO i mappen (f.eks. mappen "spill" med zip-filen)? */
        bool has_slave = false;
        for (int i = 0; i < n_ents; i++) {
            const char *b = strrchr(ents[i].path, '/');
            b = b ? b + 1 : ents[i].path;
            if (same_ci(b, "Moonstone.Slave")) has_slave = true;
        }
        if (!has_slave) {
            for (int i = 0; i < n_ents; i++) {
                size_t l = strlen(ents[i].path);
                if (l > 4 && (same_ci(ents[i].path + l - 4, ".zip") || same_ci(ents[i].path + l - 4, ".iso"))) {
                    uint8_t *d = malloc(ents[i].size);
                    if (!d) break;
                    memcpy(d, ents[i].data, ents[i].size);
                    size_t sz = ents[i].size;
                    if (files_open_mem(d, sz, ents[i].path)) return true;
                    files_close();
                    from_dir(path, "", 0);
                }
            }
        }
        return find_root();
    }
    size_t size;
    uint8_t *data = read_file(path, &size);
    if (!data) {
        snprintf(files_error, sizeof files_error, "Fant ikke %s.", path);
        return false;
    }
    return files_open_mem(data, size, path);
}

static FileEntry *lookup(const char *name)
{
    /* Amiga-stier: "data/bg1a.piv", eventuelt med enhet foran ("df0:...") */
    const char *n = strchr(name, ':');
    n = n ? n + 1 : name;
    while (*n == '/') n++;
    for (int i = 0; i < n_saved; i++) if (same_ci(saved[i].path, n)) return &saved[i];
    for (int i = 0; i < n_ents; i++) if (same_ci(ents[i].path, n)) { note_access(ents[i].path); return &ents[i]; }
    return NULL;
}

/* Henter en fil uten aa logge tilgangen (for aa sende den til en gjest). */
const uint8_t *files_peek(const char *path, size_t *size)
{
    for (int i = 0; i < n_ents; i++)
        if (same_ci(ents[i].path, path)) { *size = ents[i].size; return ents[i].data; }
    return NULL;
}

/* Legger inn en fil vi har faatt fra verten (gjest i nettspill). */
void files_inject(const char *path, const uint8_t *data, size_t size)
{
    for (int i = 0; i < n_ents; i++)
        if (same_ci(ents[i].path, path)) {
            if (ents[i].owned) free(ents[i].data);
            ents[i].data = malloc(size ? size : 1);
            memcpy(ents[i].data, data, size);
            ents[i].size = size;
            ents[i].owned = true;
            return;
        }
    uint8_t *d = malloc(size ? size : 1);
    memcpy(d, data, size);
    add_entry(path, d, size, true);
}

/* fjerner en fil (en duell la inn en fil spillet her ikke hadde) */
void files_remove(const char *path)
{
    for (int i = 0; i < n_ents; i++)
        if (same_ci(ents[i].path, path)) {
            if (ents[i].owned) free(ents[i].data);
            memmove(&ents[i], &ents[i + 1], sizeof *ents * (size_t)(n_ents - i - 1));
            n_ents--;
            return;
        }
}

/* Gjest uten egne filer: tomt filsystem. */
void files_empty(void)
{
    files_close();
    files_error[0] = 0;
}

bool files_exists(const char *name, size_t *size)
{
    FileEntry *e = lookup(name);
    if (!e) return false;
    if (size) *size = e->size;
    return true;
}

uint8_t *files_read(const char *name, size_t *size)
{
    FileEntry *e = lookup(name);
    if (!e) return NULL;
    uint8_t *d = malloc(e->size ? e->size : 1);
    if (!d) return NULL;
    memcpy(d, e->data, e->size);
    *size = e->size;
    return d;
}

bool files_save(const char *name, const uint8_t *data, size_t size, size_t offset)
{
    const char *n = strchr(name, ':');
    n = n ? n + 1 : name;
    FileEntry *e = NULL;
    for (int i = 0; i < n_saved; i++) if (same_ci(saved[i].path, n)) e = &saved[i];
    if (!e) {
        saved = realloc(saved, sizeof *saved * (size_t)(n_saved + 1));
        e = &saved[n_saved++];
        memset(e, 0, sizeof *e);
        snprintf(e->path, sizeof e->path, "%s", n);
        e->owned = true;
        FileEntry *orig = NULL;
        for (int i = 0; i < n_ents; i++) if (same_ci(ents[i].path, n)) orig = &ents[i];
        if (orig && offset) {
            e->data = malloc(orig->size);
            memcpy(e->data, orig->data, orig->size);
            e->size = orig->size;
        }
    }
    if (offset + size > e->size) {
        e->data = realloc(e->data, offset + size);
        if (offset > e->size) memset(e->data + e->size, 0, offset - e->size);
        e->size = offset + size;
    } else if (!offset) {
        e->size = size;
    }
    memcpy(e->data + offset, data, size);
    return true;
}

int files_saved_count(void) { return n_saved; }

const char *files_saved_name(int i, const uint8_t **data, size_t *size)
{
    if (i < 0 || i >= n_saved) return NULL;
    if (data) *data = saved[i].data;
    if (size) *size = saved[i].size;
    return saved[i].path;
}

uint32_t files_game_crc(void)
{
    uint32_t crc = 0;
    const char *names[] = { "Moonstone.Slave", "data/program", "data/mog" };
    for (int i = 0; i < 3; i++) {
        FileEntry *e = NULL;
        for (int j = 0; j < n_ents; j++) if (same_ci(ents[j].path, names[i])) e = &ents[j];
        if (e) crc ^= crc32_calc(e->data, e->size) * (uint32_t)(i + 1);
    }
    return crc;
}

/* Filer i en mappe (f.eks. fra tools/gfx.py build) legges over spillfilene i
 * data/. Det er slik endret grafikk og lyd tas i bruk. Returnerer antall filer. */
int files_add_overlay(const char *dir)
{
    int n = 0;
#ifndef _WIN32
    DIR *d = opendir(dir);
    if (!d) return -1;
    struct dirent *de;
    while ((de = readdir(d))) {
        if (de->d_name[0] == '.') continue;
        char full[1024], rel[300];
        snprintf(full, sizeof full, "%s/%s", dir, de->d_name);
        snprintf(rel, sizeof rel, "data/%s", de->d_name);
        size_t sz;
        uint8_t *data = read_file(full, &sz);
        if (!data) continue;
        files_inject(rel, data, sz);
        free(data);
        n++;
    }
    closedir(d);
#else
    char pattern[1024];
    snprintf(pattern, sizeof pattern, "%s\\*", dir);
    WIN32_FIND_DATAA fd;
    HANDLE h = FindFirstFileA(pattern, &fd);
    if (h == INVALID_HANDLE_VALUE) return -1;
    do {
        if (fd.cFileName[0] == '.' || (fd.dwFileAttributes & FILE_ATTRIBUTE_DIRECTORY)) continue;
        char full[1024], rel[300];
        snprintf(full, sizeof full, "%s\\%s", dir, fd.cFileName);
        snprintf(rel, sizeof rel, "data/%s", fd.cFileName);
        size_t sz;
        uint8_t *data = read_file(full, &sz);
        if (!data) continue;
        files_inject(rel, data, sz);
        free(data);
        n++;
    } while (FindNextFileA(h, &fd));
    FindClose(h);
#endif
    return n;
}
