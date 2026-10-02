/*
 * whdload.c - starter spillet slik WHDLoad gjor, og etterligner resload-funksjonene.
 *
 * Moonstone.Slave (skrevet av Wepl) er et lite 68000-program som laster
 * spillfilene, lapper dem og hopper inn i spillet. Det bruker WHDLoad sine
 * funksjoner gjennom en hoppetabell (resload). Her ligger tabellen i
 * fast-minnet paa RESLOAD_BASE, og hver plass inneholder bare RTS. Naar
 * CPU-en kommer dit, kaller hooks.c whd_call() med forskyvningen, og vi gjor
 * jobben i C for RTS-en kjores.
 *
 * Minnet er som WHDLoad setter det opp: BaseMem (chip) fra adresse 0, ExpMem
 * i fast-minnet paa EXPMEM_BASE, og slaven paa SLAVE_BASE.
 */
#include "amiga.h"
#include "m68k.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>

int  whd_buttonwait = 0;
bool whd_mog_loaded;                       /* hovedspillet er lastet (ikke introen) */
int  whd_keyexit = -1;                     /* ws_keyexit: tasten som avslutter (F10) */
void (*whd_log)(const char *msg);

#define DELAY_STUB  (RESLOAD_BASE + 0x100)
#define DELAY_FLAG  (RESLOAD_BASE + 0x1f0)
#define EXIT_STUB   (RESLOAD_BASE + 0x1f8)

static char     current_dir[64] = "data";
static uint32_t slave_version, slave_flags, slave_basemem, slave_expmem;

static uint32_t reg(int r) { return m68k_get_reg(NULL, (m68k_register_t)r); }
static void set_reg(int r, uint32_t v) { m68k_set_reg((m68k_register_t)r, v); }

static void wlog(const char *fmt, ...)
{
    char buf[256];
    va_list ap;
    va_start(ap, fmt);
    vsnprintf(buf, sizeof buf, fmt, ap);
    va_end(ap);
    if (whd_log) whd_log(buf);
    LOG2("whdload: %s\n", buf);
}

static void abort_game(const char *fmt, ...)
{
    va_list ap;
    va_start(ap, fmt);
    vsnprintf(M.abort_msg, sizeof M.abort_msg, fmt, ap);
    va_end(ap);
    M.aborted = true;
    amiga_end_slice();
    LOG("whdload: stopp: %s\n", M.abort_msg);
}

static void read_name(uint32_t a, char *out, size_t n)
{
    size_t i = 0;
    for (; i + 1 < n; i++) {
        uint8_t c = (uint8_t)mem_read8(a + (uint32_t)i);
        if (!c) break;
        out[i] = (char)c;
    }
    out[i] = 0;
}

/* sti relativt til spillmappen: "data/navn" */
static void game_path(uint32_t name_addr, char *out, size_t n)
{
    char name[200];
    read_name(name_addr, name, sizeof name);
    const char *p = strchr(name, ':');
    p = p ? p + 1 : name;
    if (current_dir[0]) snprintf(out, n, "%s/%s", current_dir, p);
    else snprintf(out, n, "%s", p);
}

static bool copy_in(uint32_t a, const uint8_t *src, size_t len)
{
    uint8_t *d = mem_ptr(a, (uint32_t)len);
    if (d) { memcpy(d, src, len); return true; }
    for (size_t i = 0; i < len; i++) mem_write8(a + (uint32_t)i, src[i]);
    return true;
}

/* ------------------------------------------------------------ hunk-filer */
#define HUNK_HEADER  0x3f3
#define HUNK_CODE    0x3e9
#define HUNK_DATA    0x3ea
#define HUNK_BSS     0x3eb
#define HUNK_RELOC32 0x3ec
#define HUNK_SYMBOL  0x3f0
#define HUNK_DEBUG   0x3f1
#define HUNK_END     0x3f2
#define HUNK_RELOC32SHORT 0x3fc

static uint32_t rd32(const uint8_t *p) { return (uint32_t)p[0] << 24 | p[1] << 16 | p[2] << 8 | p[3]; }

/* adressene til langordene siste resload_Relocate rettet (patch.c bruker dem
 * for aa flytte tekster i mog) */
uint32_t *whd_relocs;
int       whd_n_relocs;
static int relocs_cap;

static void note_reloc(uint32_t a)
{
    if (whd_n_relocs == relocs_cap) {
        int cap = relocs_cap ? relocs_cap * 2 : 4096;
        uint32_t *n = realloc(whd_relocs, (size_t)cap * sizeof *n);
        if (!n) return;
        whd_relocs = n;
        relocs_cap = cap;
    }
    whd_relocs[whd_n_relocs++] = a;
}

/* Legger en hunk-fil (som i AmigaDOS LoadSeg) ut paa adresse base, med hunkene
 * rett etter hverandre slik resload_Relocate gjor. Returnerer storrelsen.
 * Med record lagres adressene som relokeres i whd_relocs. */
static long hunk_relocate(const uint8_t *f, size_t len, uint32_t base, bool record)
{
    size_t p = 0;
#define NEED(n) do { if (p + (n) > len) return -1; } while (0)
    NEED(4);
    if (rd32(f) != HUNK_HEADER) return -1;
    p = 4;
    for (;;) { NEED(4); uint32_t n = rd32(f + p); p += 4; if (!n) break; p += (size_t)n * 4; }
    NEED(12);
    uint32_t first = rd32(f + p + 4), last = rd32(f + p + 8);
    p += 12;
    uint32_t nh = last - first + 1;
    if (nh > 256) return -1;
    uint32_t addr[256], alloc[256];
    uint32_t a = base;
    for (uint32_t i = 0; i < nh; i++) {
        NEED(4);
        uint32_t s = rd32(f + p) & 0x3fffffff;
        if (rd32(f + p) >> 30 == 3) p += 4;   /* egne minneflagg */
        p += 4;
        addr[i] = a;
        alloc[i] = s * 4;
        a += s * 4;
    }
    uint32_t total = a - base;
    /* hele omraadet nullstilles forst (BSS og resten av hver hunk) */
    uint8_t *out = calloc(total ? total : 1, 1);
    if (!out) return -1;
    int h = -1;
    while (p + 4 <= len) {
        uint32_t t = rd32(f + p) & 0x3fffffff;
        p += 4;
        if (t == HUNK_CODE || t == HUNK_DATA) {
            NEED(4);
            uint32_t n = rd32(f + p) * 4;
            p += 4;
            if (++h >= (int)nh) break;
            NEED(n);
            uint32_t c = n < alloc[h] ? n : alloc[h];
            memcpy(out + (addr[h] - base), f + p, c);
            p += n;
        } else if (t == HUNK_BSS) {
            NEED(4);
            p += 4;
            if (++h >= (int)nh) break;
        } else if (t == HUNK_RELOC32) {
            for (;;) {
                NEED(4);
                uint32_t n = rd32(f + p); p += 4;
                if (!n) break;
                NEED(4 + (size_t)n * 4);
                uint32_t th = rd32(f + p); p += 4;
                for (uint32_t i = 0; i < n; i++, p += 4) {
                    uint32_t off = rd32(f + p);
                    if (h < 0 || th >= nh || off + 4 > alloc[h]) continue;
                    uint8_t *q = out + (addr[h] - base) + off;
                    uint32_t v = rd32(q) + addr[th];
                    q[0] = (uint8_t)(v >> 24); q[1] = (uint8_t)(v >> 16); q[2] = (uint8_t)(v >> 8); q[3] = (uint8_t)v;
                    if (record) note_reloc(addr[h] + off);
                }
            }
        } else if (t == HUNK_RELOC32SHORT) {
            size_t start = p;
            for (;;) {
                NEED(2);
                uint32_t n = (uint32_t)f[p] << 8 | f[p + 1]; p += 2;
                if (!n) break;
                uint32_t th = (uint32_t)f[p] << 8 | f[p + 1]; p += 2;
                for (uint32_t i = 0; i < n; i++, p += 2) {
                    uint32_t off = (uint32_t)f[p] << 8 | f[p + 1];
                    if (h < 0 || th >= nh || off + 4 > alloc[h]) continue;
                    uint8_t *q = out + (addr[h] - base) + off;
                    uint32_t v = rd32(q) + addr[th];
                    q[0] = (uint8_t)(v >> 24); q[1] = (uint8_t)(v >> 16); q[2] = (uint8_t)(v >> 8); q[3] = (uint8_t)v;
                    if (record) note_reloc(addr[h] + off);
                }
            }
            if ((p - start) & 2) p += 2;
        } else if (t == HUNK_SYMBOL) {
            for (;;) { NEED(4); uint32_t n = rd32(f + p); p += 4; if (!n) break; p += (size_t)n * 4 + 4; }
        } else if (t == HUNK_DEBUG) {
            NEED(4);
            p += 4 + (size_t)rd32(f + p) * 4;
        } else if (t == HUNK_END) {
            if (h == (int)nh - 1) break;
        } else {
            free(out);
            return -1;
        }
    }
#undef NEED
    copy_in(base, out, total);
    free(out);
    return (long)total;
}

/* ------------------------------------------------------------ patchlister */
static bool apply_patchlist(uint32_t pl, uint32_t base)
{
    uint32_t p = pl;
    for (int guard = 0; guard < 100000; guard++) {
        uint16_t cmd = (uint16_t)mem_read16(p); p += 2;
        bool word = cmd & 0x8000;
        cmd &= 0x3fff;
        if (cmd == 0) return true;                       /* PL_END */
        if (cmd == 17) {                                 /* PL_NEXT */
            uint32_t next = pl + (uint16_t)mem_read16(p);
            pl = p = next;
            continue;
        }
        uint32_t off;
        if (word) { off = (uint16_t)mem_read16(p); p += 2; }
        else { off = mem_read32(p); p += 4; }
        uint32_t a = base + off;
        switch (cmd) {
        case 1: mem_write16(a, 0x4e75); break;                                       /* R */
        case 2: mem_write16(a, 0x4ef9); mem_write32(a + 2, pl + (uint16_t)mem_read16(p)); p += 2; break; /* P */
        case 3: mem_write16(a, 0x4eb9); mem_write32(a + 2, pl + (uint16_t)mem_read16(p)); p += 2; break; /* PS */
        case 4: mem_write16(a, 0x6000); mem_write16(a + 2, (uint16_t)(mem_read16(p) - 2)); p += 2; break; /* S */
        case 5: mem_write16(a, 0x4afc); break;                                       /* I */
        case 6: mem_write8(a, mem_read16(p) & 0xff); p += 2; break;                  /* B */
        case 7: mem_write16(a, mem_read16(p)); p += 2; break;                        /* W */
        case 8: mem_write32(a, mem_read32(p)); p += 4; break;                        /* L */
        case 9: mem_write32(a, base + mem_read32(p)); p += 4; break;                 /* A */
        case 10: mem_write32(a, pl + (uint16_t)mem_read16(p)); p += 2; break;        /* PA */
        case 11: { uint32_t n = mem_read16(p); p += 2;                               /* NOP */
            for (uint32_t i = 0; i + 1 < n + 1; i += 2) mem_write16(a + i, 0x4e71); break; }
        case 12: { uint32_t n = mem_read16(p); p += 2;                               /* C */
            for (uint32_t i = 0; i < n; i++) mem_write8(a + i, 0); break; }
        case 13: mem_write8(a, 0); break;                                            /* CB */
        case 14: mem_write16(a, 0); break;                                           /* CW */
        case 15: mem_write32(a, 0); break;                                           /* CL */
        case 16: { uint32_t s = pl + (uint16_t)mem_read16(p); uint32_t n = mem_read16(p + 2); p += 4; /* PSS */
            mem_write16(a, 0x4eb9); mem_write32(a + 2, s);
            for (uint32_t i = 0; i < n; i += 2) mem_write16(a + 6 + i, 0x4e71); break; }
        case 18: mem_write8(a, mem_read8(a) + (mem_read16(p) & 0xff)); p += 2; break;    /* AB */
        case 19: mem_write16(a, mem_read16(a) + mem_read16(p)); p += 2; break;            /* AW */
        case 20: mem_write32(a, mem_read32(a) + mem_read32(p)); p += 4; break;            /* AL */
        case 21: { uint32_t n = mem_read16(p); p += 2;                                    /* DATA */
            for (uint32_t i = 0; i < n; i++) mem_write8(a + i, mem_read8(p + i));
            p += (n + 1) & ~1u; break; }
        case 22: mem_write8(a, mem_read8(a) | (mem_read16(p) & 0xff)); p += 2; break;     /* ORB */
        case 23: mem_write16(a, mem_read16(a) | mem_read16(p)); p += 2; break;            /* ORW */
        case 24: mem_write32(a, mem_read32(a) | mem_read32(p)); p += 4; break;            /* ORL */
        case 25: mem_write32(pl + (uint16_t)mem_read16(p), a); p += 2; break;             /* GA */
        default:
            abort_game("Ukjent kommando %d i patchlisten paa %06x", cmd, p);
            return false;
        }
    }
    return false;
}

/* ------------------------------------------------------------ resload */
static void load_file(bool decrunch)
{
    char path[256];
    game_path(reg(M68K_REG_A0), path, sizeof path);
    uint32_t dest = reg(M68K_REG_A1);
    size_t size;
    uint8_t *data = files_read(path, &size);
    if (!data) {
        abort_game("Fant ikke filen %s", path);
        set_reg(M68K_REG_D0, 0);
        set_reg(M68K_REG_D1, 205);         /* ERROR_OBJECT_NOT_FOUND */
        return;
    }
    if (decrunch) {
        long ul = rnc_unpacked_size(data, size);
        if (ul > 0) {
            uint8_t *u = malloc((size_t)ul);
            long r = u ? rnc_unpack(data, size, u, (size_t)ul) : -1;
            /* Gaar det ikke (feil sjekksum eller hode), lastes filen som den er, slik
             * WHDLoad gjor. music.cmp har et eldre RNC-hode paa 12 byte, og
             * introen pakker den ut selv. */
            if (r > 0) { free(data); data = u; size = (size_t)r; }
            else free(u);
        }
    }
    copy_in(dest, data, size);
    {
        size_t pl = strlen(path);
        if (pl >= 4 && !strcmp(path + pl - 4, "/mog")) whd_mog_loaded = true;
        if (pl >= 8 && !strcmp(path + pl - 8, "/program")) whd_mog_loaded = false;
    }
    wlog("LoadFile%s %s -> %06x (%u byte)", decrunch ? "Decrunch" : "", path, dest, (unsigned)size);
    free(data);
    set_reg(M68K_REG_D0, (uint32_t)size);
    set_reg(M68K_REG_D1, 0);
}

static void control(uint32_t tl)
{
    for (int guard = 0; guard < 1000; guard++) {
        uint32_t tag = mem_read32(tl), data_addr = tl + 4;
        tl += 8;
        switch (tag) {
        case 0: return;                                   /* TAG_DONE */
        case 1: continue;                                 /* TAG_IGNORE */
        case 2: tl = mem_read32(data_addr); continue;     /* TAG_MORE */
        case 3: tl += 8 * mem_read32(data_addr); continue;/* TAG_SKIP */
        case 0x88000001: mem_write32(data_addr, 0); break;            /* ATTNFLAGS: 68000 */
        case 0x88000002: mem_write32(data_addr, CPU_HZ / 10); break;  /* E-klokken */
        case 0x88000003: mem_write32(data_addr, 0x00021000); break;   /* PAL_MONITOR_ID */
        case 0x88000005: mem_write32(data_addr, 1); break;            /* registrert WHDLoad */
        case 0x88000006: mem_write32(data_addr, (uint32_t)whd_buttonwait); break; /* ButtonWait */
        default:
            if ((tag & 0xff000000) == 0x88000000) {
                wlog("Control: ukjent tag %08x", tag);
                mem_write32(data_addr, 0);
            }
            break;
        }
    }
}

void whd_call(unsigned off)
{
    uint32_t a0 = reg(M68K_REG_A0), a1 = reg(M68K_REG_A1);
    uint32_t d0 = reg(M68K_REG_D0), d1 = reg(M68K_REG_D1);
    switch (off) {
    case 0x04: {                                          /* Abort */
        uint32_t sp = reg(M68K_REG_SP);
        int32_t reason = (int32_t)mem_read32(sp);
        if (reason == -1) abort_game("Spillet er avsluttet.");
        else if (reason == 15) abort_game("Slaven krever registrert WHDLoad.");
        else if (reason == 9) abort_game("Feil versjon av spillfilene.");
        else abort_game("Slaven stoppet (aarsak %d, %08x %08x)", reason, mem_read32(sp + 4), mem_read32(sp + 8));
        break;
    }
    case 0x08: load_file(false); break;                   /* LoadFile */
    case 0x1c: load_file(true); break;                    /* LoadFileDecrunch */
    case 0x0c: case 0x38: {                               /* SaveFile, SaveFileOffset */
        char path[256];
        game_path(a0, path, sizeof path);
        uint32_t size = d0, offset = off == 0x38 ? d1 : 0;
        uint8_t *buf = malloc(size ? size : 1);
        for (uint32_t i = 0; i < size; i++) buf[i] = (uint8_t)mem_read8(a1 + i);
        files_save(path, buf, size, offset);
        free(buf);
        wlog("SaveFile %s (%u byte)", path, size);
        set_reg(M68K_REG_D0, 1);
        break;
    }
    case 0x10: set_reg(M68K_REG_D0, 0); break;            /* SetCACR */
    case 0x14: set_reg(M68K_REG_D0, 0); set_reg(M68K_REG_D1, 0); break;  /* ListFiles */
    case 0x18: {                                          /* Decrunch */
        uint8_t hdr[18];
        for (int i = 0; i < 18; i++) hdr[i] = (uint8_t)mem_read8(a0 + (uint32_t)i);
        long ul = rnc_unpacked_size(hdr, 18);
        if (ul <= 0) { set_reg(M68K_REG_D0, 0); break; }
        uint32_t pl = (uint32_t)hdr[8] << 24 | hdr[9] << 16 | hdr[10] << 8 | hdr[11];
        uint8_t *src = malloc(pl + 18), *dst = malloc((size_t)ul);
        for (uint32_t i = 0; i < pl + 18; i++) src[i] = (uint8_t)mem_read8(a0 + i);
        long r = rnc_unpack(src, pl + 18, dst, (size_t)ul);
        if (r > 0) copy_in(a1, dst, (size_t)r);
        set_reg(M68K_REG_D0, r > 0 ? (uint32_t)r : 0);
        free(src); free(dst);
        break;
    }
    case 0x20: break;                                     /* FlushCache */
    case 0x24: case 0x70: {                               /* GetFileSize, GetFileSizeDec */
        char path[256];
        game_path(a0, path, sizeof path);
        size_t size = 0;
        if (!files_exists(path, &size)) size = 0;
        else if (off == 0x70) {
            uint8_t *d = files_read(path, &size);
            long ul = d ? rnc_unpacked_size(d, size) : 0;
            if (ul > 0) size = (size_t)ul;
            free(d);
        }
        set_reg(M68K_REG_D0, (uint32_t)size);
        break;
    }
    case 0x30: {                                          /* CRC16 */
        uint16_t c = 0;
        for (uint32_t i = 0; i < d0; i++) {
            c ^= (uint8_t)mem_read8(a0 + i);
            for (int k = 0; k < 8; k++) c = (c & 1) ? (uint16_t)((c >> 1) ^ 0xa001) : (uint16_t)(c >> 1);
        }
        set_reg(M68K_REG_D0, c);
        break;
    }
    case 0x34: control(a0); set_reg(M68K_REG_D0, 1); break;  /* Control */
    case 0x3c: case 0x40: case 0x44: case 0x48: case 0x5c: break; /* Protect* */
    case 0x4c: {                                          /* LoadFileOffset */
        char path[256];
        game_path(a0, path, sizeof path);
        size_t size;
        uint8_t *data = files_read(path, &size);
        if (!data) { abort_game("Fant ikke filen %s", path); break; }
        uint32_t n = d0, o = d1;
        if (o > size) o = (uint32_t)size;
        if (o + n > size) n = (uint32_t)(size - o);
        copy_in(a1, data + o, n);
        free(data);
        set_reg(M68K_REG_D0, 1);
        set_reg(M68K_REG_D1, 0);
        break;
    }
    case 0x50: {                                          /* Relocate */
        /* filen ligger i minnet paa a0; vi vet ikke lengden, saa vi tar med alt til slutten av minnet */
        uint32_t max = a0 < CHIP_SIZE ? CHIP_SIZE - a0 : (FAST_BASE + FAST_SIZE) - a0;
        uint8_t *copy = malloc(max);
        for (uint32_t i = 0; i < max; i++) copy[i] = (uint8_t)mem_read8(a0 + i);
        whd_n_relocs = 0;
        long size = hunk_relocate(copy, max, a0, true);
        free(copy);
        if (size < 0) { abort_game("Kunne ikke relokere filen paa %06x", a0); break; }
        wlog("Relocate %06x: %ld byte", a0, size);
        set_reg(M68K_REG_D0, (uint32_t)size);
        break;
    }
    case 0x54: {                                          /* Delay: 68000 venter i en lokke, avbrudd gaar */
        M.stall_until = amiga_now() + (uint64_t)d0 * (CPU_HZ / 10);
        M.stall_button = true;
        mem_write8(DELAY_FLAG, 1);
        set_reg(M68K_REG_PC, DELAY_STUB);
        break;
    }
    case 0x58: break;                                     /* DeleteFile */
    case 0x60: set_reg(M68K_REG_D0, 0); break;            /* SetCPU */
    case 0x64:                                            /* Patch */
        wlog("Patch %06x -> %06x", a0, a1);
        apply_patchlist(a0, a1);
        if (whd_mog_loaded) game_mog_ready();   /* mog er lastet, relokert og lappet */
        break;
    case 0x6c:
        abort_game("Denne versjonen av spillfilene trenger resload_Delta, som ikke er med.");
        break;
    default:
        if (off == EXIT_STUB - RESLOAD_BASE) abort_game("Slaven returnerte.");
        else abort_game("Ukjent resload-funksjon %02x", off);
        break;
    }
}

/* ------------------------------------------------------------ oppstart */
bool whd_boot(void)
{
    size_t size;
    uint8_t *f = files_read("Moonstone.Slave", &size);
    if (!f) { snprintf(files_error, sizeof files_error, "Fant ikke Moonstone.Slave."); return false; }
    long n = hunk_relocate(f, size, SLAVE_BASE, false);
    free(f);
    if (n < 64) { snprintf(files_error, sizeof files_error, "Moonstone.Slave kan ikke leses."); return false; }
    uint8_t *s = fast + (SLAVE_BASE - FAST_BASE);
    if (memcmp(s + 4, "WHDLOADS", 8) != 0) { snprintf(files_error, sizeof files_error, "Moonstone.Slave er ikke en WHDLoad-slave."); return false; }
    slave_version = (uint32_t)(s[12] << 8 | s[13]);
    slave_flags = (uint32_t)(s[14] << 8 | s[15]);
    slave_basemem = rd32(s + 16);
    uint32_t loader = (uint32_t)(s[24] << 8 | s[25]);
    uint32_t cdir = (uint32_t)(s[26] << 8 | s[27]);
    whd_keyexit = s[31] ? s[31] : -1;
    if (cdir) snprintf(current_dir, sizeof current_dir, "%s", (const char *)s + cdir);
    else current_dir[0] = 0;
    if (slave_version >= 8) {
        slave_expmem = rd32(s + 32);
        s[32] = (uint8_t)(EXPMEM_BASE >> 24); s[33] = (uint8_t)(EXPMEM_BASE >> 16);
        s[34] = (uint8_t)(EXPMEM_BASE >> 8);  s[35] = (uint8_t)EXPMEM_BASE;
    }
    LOG2("slave: versjon %u, flagg %04x, BaseMem %06x, ExpMem %06x, mappe '%s'\n",
         slave_version, slave_flags, slave_basemem, slave_expmem, current_dir);

    /* resload-tabellen: bare RTS */
    for (uint32_t i = 0; i < RESLOAD_SIZE; i += 2) mem_write16(RESLOAD_BASE + i, 0x4e75);
    /* Delay-lokka: tst.b DELAY_FLAG.l / bne.s lokka / rts */
    mem_write16(DELAY_STUB, 0x4a39); mem_write32(DELAY_STUB + 2, DELAY_FLAG);
    mem_write16(DELAY_STUB + 6, 0x66f8); mem_write16(DELAY_STUB + 8, 0x4e75);
    mem_write8(DELAY_FLAG, 0);

    /* CPU: supervisor, stakk i fast-minnet, PC paa GameLoader */
    set_reg(M68K_REG_SR, 0x2000);         /* som WHDLoad: supervisor, CPU-en tar avbrudd (INTENA er av) */
    set_reg(M68K_REG_ISP, SSP_INIT);
    set_reg(M68K_REG_USP, SSP_INIT - 0x1000);
    set_reg(M68K_REG_SP, SSP_INIT);
    uint32_t sp = SSP_INIT - 4;
    mem_write32(sp, EXIT_STUB);           /* hvis slaven returnerer */
    set_reg(M68K_REG_SP, sp);
    set_reg(M68K_REG_A0, RESLOAD_BASE);
    set_reg(M68K_REG_PC, SLAVE_BASE + loader);
    return true;
}

void whd_delay_check(void)
{
    if (!M.stall_until) return;
    bool button = M.stall_button && ((IN.joy[0] | IN.joy[1]) & (JOY_FIRE | JOY_FIRE2));
    if (M.clk >= M.stall_until || button) {
        M.stall_until = 0;
        mem_write8(DELAY_FLAG, 0);
    }
}

void whd_state(StateIO *s)
{
    STATE_VAR(s, current_dir);
    STATE_VAR(s, whd_mog_loaded);
}
