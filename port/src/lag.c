/*
 * lag.c - bildet delt i to lag: bakgrunn og forgrunn (HD-grafikk og effekter).
 *
 * Spillet holder en ren kopi av bakgrunnen: fem bitplan paa 320 x 200, med en
 * peker paa $8CDE8. Figurene tegnes i et av to skjermbuffere (pekeren til det
 * det tegnes i ligger paa $AA948), og naar en figur flyttes, kopieres bakgrunnen
 * tilbake fra kopien ($882E2 med $9E252, ett plan om gangen). Det gir lagene:
 *
 *   bakgrunn  kopien, gjort om til farger med paletten paa hver linje
 *   forgrunn  det skjermen viser, der det er annerledes enn bakgrunnen
 *
 * Forgrunnen tas fra rammebufferet (video_fb), saa sprites, fargeskift midt paa
 * en linje og alt annet kommer med. Lagt oppaa hverandre gir lagene derfor
 * noyaktig det spillet viser. Modulen leser bare minnet og endrer ingenting, saa
 * nettspill og check_hooks er uberort.
 *
 * Lagene finnes bare naar skjermen er slik spillet vanligvis har den: fem plan i
 * lowres, 320 x 200, 40 byte per linje uten modulo. Ellers er lag_gyldig usann,
 * og frontenden viser rammebufferet som foer.
 */
#include "amiga.h"
#include <string.h>

#define BAK_PEKER   0x8cde8                /* long: den rene bakgrunnen */
#define PLAN        0x1f40                 /* 40 * 200 byte per plan */

extern uint32_t video_bpl_first[6];
extern int      video_bpl_planes;
extern uint32_t video_line_pal[FB_H][32];

bool     lag_paa;                          /* frontenden vil ha lagene */
bool     lag_gyldig;                       /* lagene under passer til siste bilde */
uint32_t lag_bak[LAG_H * LAG_W];           /* RGBA */
uint32_t lag_for[LAG_H * LAG_W];           /* RGBA, 0 = gjennomsiktig */
uint8_t  lag_for_idx[LAG_H * LAG_W];       /* fargeindeksen i forgrunnen, $FF = ingen, $FE = bare fargen er annerledes */
uint32_t lag_bak_hash;                     /* innholdet i bakgrunnen (bitplanene) */
uint32_t lag_bak_lys;                      /* summen av fargene bakgrunnen bruker (fading) */
int      lag_for_antall;                   /* piksler i forgrunnen */

/* fargeindeksene for 16 piksler fra fem plan */
static inline void indekser(const uint8_t *p, uint32_t off, uint8_t ut[8])
{
    uint8_t b[5];
    for (int k = 0; k < 5; k++) b[k] = p[off + (uint32_t)k * PLAN];
    for (int i = 0; i < 8; i++) {
        int s = 7 - i;
        ut[i] = (uint8_t)(((b[0] >> s) & 1) | ((b[1] >> s) & 1) << 1 | ((b[2] >> s) & 1) << 2 |
                          ((b[3] >> s) & 1) << 3 | ((b[4] >> s) & 1) << 4);
    }
}

static bool skjermen_passer(uint32_t bak)
{
    if (!whd_mog_loaded || video_bpl_planes != 5) return false;
    if (C.bplcon0 & 0x8c00) return false;                       /* hires, HAM eller to spillefelt */
    if (C.bpl1mod != 0 || C.bpl2mod != 0) return false;
    if (video_diw[2] - video_diw[0] != LAG_W * 2 || video_diw[3] - video_diw[1] != LAG_H) return false;
    if (bak < 0x100 || bak + 5 * PLAN > CHIP_SIZE || (bak & 1)) return false;
    for (int p = 0; p < 5; p++) {
        uint32_t a = video_bpl_first[p];
        if (a + PLAN > CHIP_SIZE || a != video_bpl_first[0] + (uint32_t)p * PLAN) return false;
    }
    return true;
}

/* Kalles etter hvert bilde naar lag_paa er sann. */
void lag_bygg(void)
{
    uint32_t bak = mem_read32(BAK_PEKER);
    lag_gyldig = lag_paa && skjermen_passer(bak);
    if (!lag_gyldig) return;
    const uint8_t *mem = chip;
    uint32_t skjerm = video_bpl_first[0];

    /* hash av bakgrunnens bitplan (FNV-1a), for aa kjenne igjen bakgrunnen */
    uint32_t h = 2166136261u;
    for (uint32_t i = 0; i < 5 * PLAN; i++) { h ^= mem[bak + i]; h *= 16777619u; }
    lag_bak_hash = h;

    uint32_t brukt = 0;                     /* fargene bakgrunnen bruker, bit per farge */
    int n = 0;
    for (int y = 0; y < LAG_H; y++) {
        const uint32_t *pal = video_line_pal[video_diw[1] + y];
        const uint32_t *fb = video_fb + (size_t)(video_diw[1] + y) * FB_W + video_diw[0];
        uint32_t *ob = lag_bak + (size_t)y * LAG_W, *of = lag_for + (size_t)y * LAG_W;
        uint8_t *oi = lag_for_idx + (size_t)y * LAG_W;
        for (int bx = 0; bx < LAG_W / 8; bx++) {
            uint32_t off = (uint32_t)(y * (LAG_W / 8) + bx);
            uint8_t ib[8], is[8];
            indekser(mem + bak, off, ib);
            indekser(mem + skjerm, off, is);
            for (int i = 0; i < 8; i++) {
                int x = bx * 8 + i;
                uint32_t cb = pal[ib[i]];
                uint32_t vist = fb[x * 2];
                ob[x] = cb;
                brukt |= 1u << ib[i];
                if (is[i] != ib[i]) { of[x] = vist; oi[x] = is[i]; n++; }
                else if (vist != cb) { of[x] = vist; oi[x] = 0xfe; n++; }
                else { of[x] = 0; oi[x] = 0xff; }
            }
        }
    }
    lag_for_antall = n;

    /* lysstyrken til fargene bakgrunnen bruker, midt paa skjermen: synker naar spillet fader ut */
    const uint32_t *pal = video_line_pal[video_diw[1] + LAG_H / 2];
    uint32_t lys = 0;
    for (int i = 0; i < 32; i++)
        if (brukt & (1u << i)) lys += (pal[i] & 0xff) + ((pal[i] >> 8) & 0xff) + ((pal[i] >> 16) & 0xff);
    lag_bak_lys = lys;
}
