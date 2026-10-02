/*
 * video.c - Denise: bitplan, sprites, prioritet og farger, tegnet linje for linje.
 *
 * Bitplan-DMA (video_fetch) skjer naar stralen naar DDFSTRT, med pekerne slik
 * de er da, og modulo legges til etterpaa. Paa slutten av linjen
 * (video_line_end) settes pikslene sammen. Fargeskift og BPLCON-skift midt paa
 * linjen (typisk fra Copper) logges med tidspunkt og tas med der de skjedde.
 *
 * Rammebufferet er i hires-oppløsning (720 x 288), en lowres-piksel blir to.
 */
#include "amiga.h"
#include <string.h>

uint32_t video_fb[FB_W * FB_H];
int      video_diw[4];
uint32_t video_bpl_first[6];              /* bitplanpekerne paa forste linje i bildet (analyse, lag.c) */
uint32_t video_line_pal[FB_H][32];        /* paletten (RGBA) ved starten av hver linje (lag.c) */
int      video_bpl_planes;
static uint32_t bpl_frame = 0xffffffffu;

/* logg over endringer paa linjen */
typedef struct { int16_t x; uint16_t reg, val; } Change;
static Change   changes[1024];
static int      n_changes;
static uint16_t line_color[32];           /* fargene ved starten av linjen */
static uint16_t line_bplcon2;

/* data hentet av bitplan-DMA paa denne linjen */
static uint16_t fetch_data[6][128];
static int      fetch_words;              /* ord per plan */
static int      fetch_planes;
static bool     fetch_hires, fetch_done;
static int      fetch_x0;                 /* lowres-x (DIW-koordinat) for forste piksel */
static uint16_t fetch_bplcon0, fetch_bplcon1;

static uint8_t  pf[FB_W];                 /* fargeindeks fra bitplanene (0-63) */
static uint8_t  spr[FB_W];                /* sprite: 0 = ingen, ellers 16-31 */
static uint8_t  spr_num[FB_W];            /* hvilket spritepar (0-3) */

void video_reset(void)
{
    memset(video_fb, 0, sizeof video_fb);
    n_changes = 0;
    fetch_done = false;
    video_diw[0] = (0x81 - FB_X0) * 2; video_diw[1] = 0x2c - FB_Y0;
    video_diw[2] = video_diw[0] + 640;  video_diw[3] = video_diw[1] + 256;
}

static inline uint32_t rgb12(uint16_t c)
{
    uint32_t r = (c >> 8) & 15, g = (c >> 4) & 15, b = c & 15;
    return 0xff000000u | (b * 17) << 16 | (g * 17) << 8 | (r * 17);
}

void video_reg_change(unsigned reg, uint16_t v)
{
    extern int custom_write_hpos;
    if (n_changes >= (int)(sizeof changes / sizeof changes[0])) return;
    int h = custom_write_hpos >= 0 ? custom_write_hpos : amiga_hpos();
    /* lowres-x der endringen synes */
    changes[n_changes].x = (int16_t)(h * 2 + 1);
    changes[n_changes].reg = (uint16_t)reg;
    changes[n_changes].val = v;
    n_changes++;
}

/* ------------------------------------------------------------ sprite-DMA */
static void sprite_dma(int vpos)
{
    if ((C.dmacon & 0x0220) != 0x0220) return;
    for (int n = 0; n < 8; n++) {
        uint32_t pt = C.sprpt[n];
        if (vpos == 25) {
            /* forste linje etter vertikal blanking: hent kontrollordene */
            C.sprpos[n] = chip_r16(pt); C.sprctl[n] = chip_r16(pt + 2);
            pt += 4;
            C.spr_dma[n] = 1;
            C.spr_armed[n] = 0;
        }
        if (vpos < 25) { C.spr_armed[n] = 0; continue; }
        int vstart = (C.sprpos[n] >> 8) | ((C.sprctl[n] & 4) << 6);
        int vstop  = (C.sprctl[n] >> 8) | ((C.sprctl[n] & 2) << 7);
        if (C.spr_dma[n] == 1 && vpos == vstart) C.spr_dma[n] = 2;
        if (C.spr_dma[n] == 2) {
            if (vpos == vstop) {
                C.sprpos[n] = chip_r16(pt); C.sprctl[n] = chip_r16(pt + 2);
                pt += 4;
                C.spr_armed[n] = 0;
                C.spr_dma[n] = 1;
                int ns = (C.sprpos[n] >> 8) | ((C.sprctl[n] & 4) << 6);
                (void)ns;
            } else {
                C.sprdata[n] = chip_r16(pt); C.sprdatb[n] = chip_r16(pt + 2);
                pt += 4;
                C.spr_armed[n] = 1;
            }
        }
        C.sprpt[n] = pt & 0x1ffffe;
    }
}

void video_line_start(int vpos)
{
    memcpy(line_color, C.color, sizeof line_color);
    line_bplcon2 = C.bplcon2;
    n_changes = 0;
    fetch_done = false;
    sprite_dma(vpos);
}

/* ------------------------------------------------------------ bitplan-DMA */
static bool line_in_vdiw(int vpos)
{
    int vstart = C.diwstrt >> 8;
    int vstop = C.diwstop >> 8;
    if (!(vstop & 0x80)) vstop |= 0x100;
    return vpos >= vstart && vpos < vstop;
}

int video_fetch_hpos(void)
{
    if (fetch_done || (C.dmacon & 0x0300) != 0x0300) return -1;
    if (!line_in_vdiw(M.vpos)) return -1;
    int start = C.ddfstrt;
    if (start < 0x18) start = 0x18;
    return start;
}

void video_fetch(int vpos)
{
    if (fetch_done) return;
    fetch_done = true;
    fetch_planes = 0;
    if ((C.dmacon & 0x0300) != 0x0300 || !line_in_vdiw(vpos)) return;
    int planes = (C.bplcon0 >> 12) & 7;
    if (planes > 6) planes = 6;
    bool hires = C.bplcon0 & 0x8000;
    if (hires && planes > 4) planes = 4;
    int start = C.ddfstrt, stop = C.ddfstop;
    if (start < 0x18) start = 0x18;
    if (stop > 0xd8) stop = 0xd8;
    if (!hires) { start &= ~7; }
    if (stop < start) { return; }
    int units = ((stop - start) >> 3) + 1;
    int words = hires ? units * 2 : units;
    if (words > 128) words = 128;
    fetch_words = words;
    fetch_planes = planes;
    fetch_hires = hires;
    fetch_x0 = hires ? start * 2 + 9 : start * 2 + 17;
    fetch_bplcon0 = C.bplcon0;
    fetch_bplcon1 = C.bplcon1;
    if (bpl_frame != M.frame) {
        bpl_frame = M.frame;
        video_bpl_planes = planes;
        for (int p = 0; p < planes; p++) video_bpl_first[p] = C.bplpt[p];
    }
    for (int p = 0; p < planes; p++) {
        uint32_t pt = C.bplpt[p];
        for (int w = 0; w < words; w++) { fetch_data[p][w] = chip_r16(pt); pt += 2; }
        pt += (p & 1) ? C.bpl2mod : C.bpl1mod;
        C.bplpt[p] = pt & 0x1ffffe;
    }
}

/* ------------------------------------------------------------ tegning */
static void draw_sprites(void)
{
    memset(spr, 0, sizeof spr);
    int hstart_diw = C.diwstrt & 0xff, hstop_diw = (C.diwstop & 0xff) | 0x100;
    for (int n = 7; n >= 0; n--) {
        if (!C.spr_armed[n]) continue;
        bool attached = (n & 1) && (C.sprctl[n] & 0x80);
        if (!(n & 1) && n + 1 < 8 && (C.sprctl[n + 1] & 0x80) && C.spr_armed[n + 1]) {
            /* tegnes sammen med den odde spriten som er festet til denne */
            int x = ((C.sprpos[n] & 0xff) << 1 | (C.sprctl[n] & 1)) + 1;
            for (int i = 0; i < 16; i++) {
                int bit = 15 - i;
                int v = ((C.sprdata[n] >> bit) & 1) | ((C.sprdatb[n] >> bit) & 1) << 1
                      | ((C.sprdata[n + 1] >> bit) & 1) << 2 | ((C.sprdatb[n + 1] >> bit) & 1) << 3;
                if (!v) continue;
                int lx = x + i;
                if (lx < hstart_diw || lx >= hstop_diw) continue;
                int hx = (lx - FB_X0) * 2;
                if (hx < 0 || hx + 1 >= FB_W) continue;
                spr[hx] = spr[hx + 1] = (uint8_t)(16 + v);
                spr_num[hx] = spr_num[hx + 1] = (uint8_t)(n >> 1);
            }
            continue;
        }
        if (attached) continue;
        int x = ((C.sprpos[n] & 0xff) << 1 | (C.sprctl[n] & 1)) + 1;
        int base = 16 + (n >> 1) * 4;
        for (int i = 0; i < 16; i++) {
            int bit = 15 - i;
            int v = ((C.sprdata[n] >> bit) & 1) | ((C.sprdatb[n] >> bit) & 1) << 1;
            if (!v) continue;
            int lx = x + i;
            if (lx < hstart_diw || lx >= hstop_diw) continue;
            int hx = (lx - FB_X0) * 2;
            if (hx < 0 || hx + 1 >= FB_W) continue;
            spr[hx] = spr[hx + 1] = (uint8_t)(base + v);
            spr_num[hx] = spr_num[hx + 1] = (uint8_t)(n >> 1);
        }
    }
}

void video_line_end(int vpos)
{
    int y = vpos - FB_Y0;
    if (y < 0 || y >= FB_H) return;
    uint32_t *out = video_fb + (size_t)y * FB_W;
    memset(pf, 0, sizeof pf);

    bool vdiw = line_in_vdiw(vpos);
    int hstart = C.diwstrt & 0xff, hstop = (C.diwstop & 0xff) | 0x100;

    if (fetch_done && fetch_planes > 0) {
        int pf1h = fetch_bplcon1 & 15, pf2h = (fetch_bplcon1 >> 4) & 15;
        int npix = fetch_words * 16;
        for (int p = 0; p < fetch_planes; p++) {
            int delay = (p & 1) ? pf2h : pf1h;
            uint8_t bitv = (uint8_t)(1 << p);
            if (fetch_hires) {
                int hx0 = (fetch_x0 - FB_X0) * 2 + delay * 2;
                for (int i = 0; i < npix; i++) {
                    if (!((fetch_data[p][i >> 4] >> (15 - (i & 15))) & 1)) continue;
                    int hx = hx0 + i;
                    if (hx >= 0 && hx < FB_W) pf[hx] |= bitv;
                }
            } else {
                int hx0 = (fetch_x0 + delay - FB_X0) * 2;
                for (int i = 0; i < npix; i++) {
                    if (!((fetch_data[p][i >> 4] >> (15 - (i & 15))) & 1)) continue;
                    int hx = hx0 + i * 2;
                    if (hx >= 0 && hx + 1 < FB_W) { pf[hx] |= bitv; pf[hx + 1] |= bitv; }
                }
            }
        }
        /* utenfor vinduet (DIW) vises bare bakgrunnsfargen */
        int a = (hstart - FB_X0) * 2, b = (hstop - FB_X0) * 2;
        if (a > 0) memset(pf, 0, (size_t)(a < FB_W ? a : FB_W));
        if (b < FB_W) memset(pf + (b > 0 ? b : 0), 0, (size_t)(FB_W - (b > 0 ? b : 0)));
    }
    if (vdiw) draw_sprites(); else memset(spr, 0, sizeof spr);

    uint16_t con0 = fetch_done ? fetch_bplcon0 : C.bplcon0;
    bool dpf = con0 & 0x0400, ham = (con0 & 0x0800) && fetch_planes >= 5;
    bool ehb = !dpf && !ham && fetch_planes == 6;
    uint16_t col[32];
    memcpy(col, line_color, sizeof col);
    uint16_t con2 = line_bplcon2;
    int ci = 0;
    uint16_t hamc = col[0];
    uint32_t pal[32];
    for (int i = 0; i < 32; i++) pal[i] = rgb12(col[i]);
    memcpy(video_line_pal[y], pal, sizeof pal);

    for (int hx = 0; hx < FB_W; hx++) {
        int lx = FB_X0 + (hx >> 1);
        while (ci < n_changes && changes[ci].x <= lx) {
            unsigned reg = changes[ci].reg;
            if (reg >= 0x180 && reg < 0x1c0) {
                int k = (reg - 0x180) >> 1;
                col[k] = changes[ci].val & 0x0fff;
                pal[k] = rgb12(col[k]);
            } else if (reg == 0x104) {
                con2 = changes[ci].val;
            }
            ci++;
        }
        int p1 = con2 & 7, p2 = (con2 >> 3) & 7;
        uint8_t v = pf[hx];
        uint8_t s = spr[hx];
        uint32_t c;
        if (ham) {
            int ctl = (v >> 4) & 3, d = v & 15;
            switch (ctl) {
            case 0: hamc = col[d]; break;
            case 1: hamc = (hamc & 0xff0) | d; break;
            case 2: hamc = (uint16_t)((hamc & 0x0ff) | d << 8); break;
            case 3: hamc = (uint16_t)((hamc & 0xf0f) | d << 4); break;
            }
            c = rgb12(hamc);
            if (s && (int)spr_num[hx] < p2) c = pal[s];
        } else if (dpf) {
            int v1 = (v & 1) | ((v >> 1) & 2) | ((v >> 2) & 4);
            int v2 = ((v >> 1) & 1) | ((v >> 2) & 2) | ((v >> 3) & 4);
            bool pf2pri = con2 & 0x40;
            int k1 = v1 ? 4 * p1 + (pf2pri ? 1 : 0) : 99;
            int k2 = v2 ? 4 * p2 + (pf2pri ? 0 : 1) : 99;
            int ks = s ? 4 * spr_num[hx] + 2 : 99;
            if (ks < k1 && ks < k2) c = pal[s];
            else if (k1 < k2) c = pal[v1];
            else if (k2 < 99) c = pal[8 + v2];
            else c = pal[0];
        } else {
            int ks = s ? 4 * spr_num[hx] + 2 : 99;
            int kp = v ? 4 * p2 : 99;
            if (ks < kp) c = pal[s];
            else if (v >= 32 && ehb) {
                uint16_t h = (col[v - 32] >> 1) & 0x777;
                c = rgb12(h);
            } else c = pal[v & 31];
        }
        out[hx] = c;
    }
    if (vdiw) {
        int vstart = C.diwstrt >> 8, vstop = C.diwstop >> 8;
        if (!(vstop & 0x80)) vstop |= 0x100;
        video_diw[0] = (hstart - FB_X0) * 2; video_diw[2] = (hstop - FB_X0) * 2;
        video_diw[1] = vstart - FB_Y0;       video_diw[3] = vstop - FB_Y0;
    }
}

void video_frame_done(void)
{
}

void video_state(StateIO *s)
{
    (void)s;
}
