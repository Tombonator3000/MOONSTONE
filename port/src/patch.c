/*
 * patch.c - endringer porten gjor i mog etter at den er lastet.
 *
 * game_mog_ready() kalles fra resload_Patch naar slaven har lastet, relokert
 * og lappet mog (whdload.c), for spillet starter. Her brukes:
 *   - tekstene i data/tekster.txt (lages med tools/tekst.py)
 *   - menyvalget for nettspill (meny.c), naar frontenden har slaatt det paa
 *
 * Nye data legges i chip-minnet over $B1000. Slaven ber WHDLoad om BaseMem
 * $B1000, og spillet bruker aldri minnet over (sjekket med minnedumper fra
 * intro, meny, kart og kamp). Tekstfilen leses gjennom fillaget, saa i
 * nettspill faar gjestene den fra verten som alle andre filer.
 *
 * Tekstene: en linje er adresse og tekst, f.eks. 8f123 "Players".
 *   - like lang eller kortere: skrives der den ligger. Har noen kode en peker
 *     til teksten, fylles resten med 0, ellers med mellomrom (teksten kan
 *     leses i rekkefolge med andre tekster).
 *   - lengre, og kode peker paa den: legges i ledig minne, pekerne rettes.
 *   - en linje i et avsnitt (en byte med antall linjer og saa linjene, bare
 *     starten har peker) som faar ny lengde: hele avsnittet legges paa nytt.
 *   - ellers kuttes teksten.
 */
#include "amiga.h"
#include "m68k.h"
#include <string.h>
#include <stdio.h>
#include <stdlib.h>

#define MOG_START   0x80000
#define MOG_END     0xb1000                 /* BaseMem */
#define RESTORE_A   0xe0000                 /* listene over det som er tegnet (se widen_restore_lists) */
#define RESTORE_B   0xe0800
#define RESTORE_N   255                     /* plasser i hver liste, 8 byte hver, pluss en til slutt */
#define TEXT_BASE   0xf0000                 /* flyttede tekster */
#define TEXT_END    0xf8000                 /* $F8000-$FFFFF: menyen (meny.c) */
#define MAX_TEXT    255

static uint32_t text_next;
static uint8_t  texts_patched;              /* i tilstanden: tekstene er endret */

static uint32_t rd32c(uint32_t a) { return (uint32_t)chip[a] << 24 | chip[a + 1] << 16 | chip[a + 2] << 8 | chip[a + 3]; }
static void wr32c(uint32_t a, uint32_t v) { chip[a] = (uint8_t)(v >> 24); chip[a + 1] = (uint8_t)(v >> 16); chip[a + 2] = (uint8_t)(v >> 8); chip[a + 3] = (uint8_t)v; }

static size_t mem_len(uint32_t a)
{
    size_t n = 0;
    while (a + n < CHIP_SIZE && chip[a + n]) n++;
    return n;
}

/* antall relokerte langord som peker paa a */
static int refs_to(uint32_t a)
{
    int n = 0;
    for (int i = 0; i < whd_n_relocs; i++)
        if (whd_relocs[i] + 4 <= CHIP_SIZE && rd32c(whd_relocs[i]) == a) n++;
    return n;
}

static void repoint(uint32_t from, uint32_t to)
{
    for (int i = 0; i < whd_n_relocs; i++)
        if (whd_relocs[i] + 4 <= CHIP_SIZE && rd32c(whd_relocs[i]) == from) wr32c(whd_relocs[i], to);
}

/* plass i det ledige minnet, eller 0 */
static uint32_t text_alloc(size_t n)
{
    if (text_next + n > TEXT_END) return 0;
    uint32_t a = text_next;
    text_next += (uint32_t)((n + 1) & ~(size_t)1);
    return a;
}

/* Avsnittet linjen paa a hoerer til (adressen til antall-byten), eller 0. */
static uint32_t find_block(uint32_t a)
{
    for (int i = 0; i < whd_n_relocs; i++) {
        if (whd_relocs[i] + 4 > CHIP_SIZE) continue;
        uint32_t v = rd32c(whd_relocs[i]);
        if (v >= a || a - v > 4096 || chip[v] < 1 || chip[v] > 31) continue;   /* 32 og over er vanlige tegn */
        uint32_t p = v + 1;
        for (int l = 0; l < chip[v] && p < MOG_END; l++) {
            if (p == a) return v;
            p += (uint32_t)mem_len(p) + 1;
        }
    }
    return 0;
}

typedef struct { uint32_t addr; uint8_t text[MAX_TEXT + 1]; int len; } TextEdit;

/* "8f123 "Players"  # kommentar" -> adresse og tekst. false for kommentarer og tomme linjer. */
static bool parse_line(const char *s, TextEdit *e)
{
    while (*s == ' ' || *s == '\t') s++;
    if (!*s || *s == '#' || *s == '\r' || *s == '\n') return false;
    char *end;
    unsigned long a = strtoul(s, &end, 16);
    if (end == s) return false;
    s = end;
    while (*s == ' ' || *s == '\t') s++;
    if (*s++ != '"') return false;
    int n = 0;
    while (*s && *s != '"' && *s != '\n') {
        int c = (unsigned char)*s++;
        if (c == '\\' && *s) {
            c = (unsigned char)*s++;
            if (c == 'x' && s[0] && s[1]) {
                char hex[3] = { s[0], s[1], 0 };
                c = (int)strtoul(hex, NULL, 16);
                s += 2;
            }
        } else if (c >= 0x80) {
            c = '?';                       /* UTF-8: fonten har bare ASCII */
            while (((unsigned char)*s & 0xc0) == 0x80) s++;
        }
        if (n < MAX_TEXT) e->text[n++] = (uint8_t)c;
    }
    if (*s != '"') return false;
    e->text[n] = 0;
    e->len = n;
    e->addr = (uint32_t)a;
    return true;
}

static const TextEdit *edit_at(const TextEdit *ed, int n, uint32_t a)
{
    for (int i = 0; i < n; i++) if (ed[i].addr == a) return &ed[i];
    return NULL;
}

/* Spillet husker alt det tegner paa skjermen i en av to lister ($8DE4A og
 * $8DFB2, 45 plasser a 8 byte: x, y, bredde, hoyde), saa bakgrunnen kan
 * settes tilbake. Figurene ($87B46) stopper paa 45, men tekst ($8930C) har
 * ingen grense, og lengre tekster enn originalen skriver da over det som
 * ligger etter (bl.a. verdiene til ridderne). Listene flyttes derfor til
 * ledig minne med plass til 255, og grensene heves. */
static void widen_restore_lists(void)
{
    repoint(0x8de4a, RESTORE_A);                     /* $87672, $8828A */
    repoint(0x8dfb2, RESTORE_B);                     /* $8767C */
    wr32c(0x88290, (RESTORE_B - RESTORE_A) * 2 - 1); /* sub_088288 fyller begge med $FF */
    wr32c(0x882b8, RESTORE_N);                       /* cmpi.l #$2d i sub_08829e */
    chip[0x87b56] = 0; chip[0x87b57] = RESTORE_N;    /* cmpi.w #$2d for figurene */
    memset(chip + RESTORE_A, 0xff, (RESTORE_B - RESTORE_A) * 2);
}

static int apply_texts(void)
{
    size_t size;
    uint8_t *f = files_read("data/tekster.txt", &size);
    if (!f) return 0;
    char *src = malloc(size + 1);
    memcpy(src, f, size);
    src[size] = 0;
    free(f);

    int cap = 64, n = 0;
    TextEdit *ed = malloc(sizeof *ed * (size_t)cap);
    for (char *line = src; line && *line; ) {
        char *nl = strchr(line, '\n');
        if (nl) *nl = 0;
        TextEdit e;
        if (parse_line(line, &e) && e.addr >= MOG_START && e.addr < MOG_END) {
            size_t ol = mem_len(e.addr);
            if ((size_t)e.len != ol || memcmp(chip + e.addr, e.text, ol)) {
                if (n == cap) { cap *= 2; ed = realloc(ed, sizeof *ed * (size_t)cap); }
                ed[n++] = e;
            }
        }
        line = nl ? nl + 1 : NULL;
    }
    free(src);

    int in_place = 0, moved = 0, cut = 0, blocks = 0;
    uint32_t block_list[64];
    int n_blocks = 0;
    for (int i = 0; i < n; i++) {
        TextEdit *e = &ed[i];
        size_t ol = mem_len(e->addr);
        uint32_t b = find_block(e->addr);
        if (b && (size_t)e->len != ol) {
            int k;
            for (k = 0; k < n_blocks; k++) if (block_list[k] == b) break;
            if (k == n_blocks && n_blocks < 64) block_list[n_blocks++] = b;
            continue;
        }
        int refs = b ? 0 : refs_to(e->addr);
        if ((size_t)e->len <= ol) {
            memcpy(chip + e->addr, e->text, (size_t)e->len);
            memset(chip + e->addr + e->len, refs ? 0 : ' ', ol - (size_t)e->len);
            in_place++;
        } else if (refs) {
            uint32_t a = text_alloc((size_t)e->len + 1);
            if (!a) { LOG("tekster: ikke plass til %05x\n", e->addr); continue; }
            memcpy(chip + a, e->text, (size_t)e->len + 1);
            repoint(e->addr, a);
            moved++;
        } else {
            memcpy(chip + e->addr, e->text, ol);
            LOG("tekster: %05x kan ikke bli lengre (ingen peker), kuttet til %u tegn\n", e->addr, (unsigned)ol);
            cut++;
        }
    }
    /* avsnitt der en linje har faatt ny lengde: legges paa nytt */
    for (int k = 0; k < n_blocks; k++) {
        uint32_t b = block_list[k];
        int lines = chip[b];
        uint8_t buf[4096];
        size_t bl = 0;
        buf[bl++] = (uint8_t)lines;
        uint32_t p = b + 1;
        for (int l = 0; l < lines; l++) {
            const TextEdit *e = edit_at(ed, n, p);
            size_t ol = mem_len(p);
            const uint8_t *t = e ? e->text : chip + p;
            size_t tl = e ? (size_t)e->len : ol;
            if (bl + tl + 1 > sizeof buf) break;
            memcpy(buf + bl, t, tl);
            bl += tl;
            buf[bl++] = 0;
            p += (uint32_t)ol + 1;
        }
        uint32_t a = text_alloc(bl);
        if (!a) { LOG("tekster: ikke plass til avsnittet paa %05x\n", b); continue; }
        memcpy(chip + a, buf, bl);
        repoint(b, a);
        blocks++;
    }
    free(ed);
    LOG("tekster.txt: %d endret paa samme sted, %d flyttet, %d avsnitt lagt paa nytt, %d kuttet\n",
        in_place, moved, blocks, cut);
    return n;
}

/* skriv_tekst sentrerer med x = (320 - bredde) / 2, og hoyrejusterer med
 * 320 - bredde. Er teksten bredere enn skjermen, blir x et stort tall, og naar
 * bakgrunnen settes tilbake, skrives det utenfor skjermen. Originalen har ingen
 * saa brede tekster, men en endret tekst kan ha det. Da starter vi paa x = 0,
 * og teksten brytes paa neste linje slik skriv_tekst gjor ved hoyre kant. */
static bool clamp_text_x(void)
{
    if (!texts_patched) return false;
    uint32_t d1 = m68k_get_reg(NULL, M68K_REG_D1);
    if ((d1 & 0xffff) >= 320) m68k_set_reg(M68K_REG_D1, d1 & 0xffff0000);
    return false;                          /* move.w d1,... kjores som vanlig */
}

/* skriv_tekst gir bredden paa siste sentrerte tekst tilbake i D0 ($89284).
 * Utstyrsskjermen leser STR, CON og END med move.b (a0,d1.w),d0 paa $8B132
 * uten aa toemme D0 forst. I originalen er alle tekster smalere enn 256
 * piksler, saa den ovre byten er 0. En bredere tekst (f.eks. en lengre
 * overskrift) gjor at 1 vises som 257. Vi toemmer D0 foer instruksjonen. */
static bool clear_d0_stats(void)
{
    if (texts_patched) m68k_set_reg(M68K_REG_D0, 0);
    return false;
}

void patch_register_hooks(void)
{
    hooks_register_patch(0x890bc, clamp_text_x, "skriv_tekst x (sentrert)");
    hooks_register_patch(0x890ea, clamp_text_x, "skriv_tekst x (hoyre)");
    hooks_register_patch(0x8b132, clear_d0_stats, "utstyr: STR/CON/END");
    meny_register_hooks();
}

void patch_state(StateIO *s)
{
    STATE_VAR(s, texts_patched);
}

/* ny maskin: ingen lapper foer mog er lastet */
void patch_reset(void)
{
    texts_patched = 0;
    meny_reset();
}

void game_mog_ready(void)
{
    text_next = TEXT_BASE;
    int changed = apply_texts();
    bool menu = meny_mog_ready();
    texts_patched = changed > 0;
    if (changed || menu) widen_restore_lists();
}
