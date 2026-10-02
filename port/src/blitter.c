/*
 * blitter.c - Blitteren: kopiering med skift, masker, minterm, fylling og linjer.
 *
 * Hele blittingen gjores med en gang BLTSIZE skrives, med registrene slik de er
 * da. Blitteren regnes likevel som opptatt (BBUSY) i like lang tid som paa en
 * ekte maskin, og avbruddet (BLIT) kommer forst naar den er ferdig. Programmer
 * som venter paa Blitteren paa riktig maate merker ingen forskjell.
 */
#include "amiga.h"
#include "m68k.h"
#include <string.h>
#include <stdio.h>

Blitter  B;
unsigned blit_w = 1, blit_h = 1;

/* --blit-log: hvor Blitteren startes fra (PC), for aa finne tegnerutinene */
bool blit_log;
static struct { uint32_t pc; uint32_t n; uint16_t con0, con1; unsigned w, h; } blit_pcs[64];
static int n_blit_pcs;

static void note_blit(void)
{
    uint32_t pc = m68k_get_reg(NULL, M68K_REG_PPC);
    for (int i = 0; i < n_blit_pcs; i++)
        if (blit_pcs[i].pc == pc) { blit_pcs[i].n++; return; }
    if (n_blit_pcs < 64) {
        blit_pcs[n_blit_pcs].pc = pc; blit_pcs[n_blit_pcs].n = 1;
        blit_pcs[n_blit_pcs].con0 = B.con0; blit_pcs[n_blit_pcs].con1 = B.con1;
        blit_pcs[n_blit_pcs].w = blit_w; blit_pcs[n_blit_pcs].h = blit_h;
        n_blit_pcs++;
    }
}

/* --blit-trace F:N: hver blit i bilde F til F+N-1, med pekere og storrelse */
int blit_trace_from = -1, blit_trace_n;

static void trace_blit(void)
{
    if (blit_trace_from < 0 || (int)M.frame < blit_trace_from || (int)M.frame >= blit_trace_from + blit_trace_n) return;
    printf("blit bilde %u pc %06x con %04x %04x A %06x B %06x C %06x D %06x mod %d %d %d %d %ux%u\n",
           M.frame, m68k_get_reg(NULL, M68K_REG_PPC), B.con0, B.con1, B.pt[0], B.pt[1], B.pt[2], B.pt[3],
           B.mod[0], B.mod[1], B.mod[2], B.mod[3], blit_w, blit_h);
}

void blit_report(void)
{
    for (int i = 0; i < n_blit_pcs; i++)
        printf("blit fra PC %06x: %u ganger (forste: BLTCON0 %04x BLTCON1 %04x, %u x %u ord)\n",
               blit_pcs[i].pc, blit_pcs[i].n, blit_pcs[i].con0, blit_pcs[i].con1, blit_pcs[i].w, blit_pcs[i].h);
}

void blitter_reset(void)
{
    memset(&B, 0, sizeof B);
    blit_w = blit_h = 1;
}

static inline uint16_t minterm(uint8_t lf, uint16_t a, uint16_t b, uint16_t c)
{
    uint16_t d = 0;
    if (lf & 0x80) d |=  a &  b &  c;
    if (lf & 0x40) d |=  a &  b & ~c;
    if (lf & 0x20) d |=  a & ~b &  c;
    if (lf & 0x10) d |=  a & ~b & ~c;
    if (lf & 0x08) d |= ~a &  b &  c;
    if (lf & 0x04) d |= ~a &  b & ~c;
    if (lf & 0x02) d |= ~a & ~b &  c;
    if (lf & 0x01) d |= ~a & ~b & ~c;
    return d;
}

static void blit_area(void)
{
    bool usea = B.con0 & 0x0800, useb = B.con0 & 0x0400, usec = B.con0 & 0x0200, used = B.con0 & 0x0100;
    uint8_t lf = (uint8_t)B.con0;
    int ash = B.con0 >> 12, bsh = B.con1 >> 12;
    bool desc = B.con1 & 0x0002;
    bool ife = B.con1 & 0x0008, efe = B.con1 & 0x0010, fill = ife || efe;
    int inc = desc ? -2 : 2;
    uint32_t apt = B.pt[0], bpt = B.pt[1], cpt = B.pt[2], dpt = B.pt[3];
    uint16_t aold = 0, bold = 0;
    uint16_t adat = B.dat[0], bdat = B.dat[1], cdat = B.dat[2];
    bool zero = true;

    for (unsigned y = 0; y < blit_h; y++) {
        int carry = (B.con1 & 0x0004) ? 1 : 0;   /* FCI */
        for (unsigned x = 0; x < blit_w; x++) {
            if (usea) { adat = chip_r16(apt); apt += inc; }
            if (useb) { bdat = chip_r16(bpt); bpt += inc; }
            if (usec) { cdat = chip_r16(cpt); cpt += inc; }
            uint16_t a = adat;
            if (x == 0) a &= B.afwm;
            if (x == blit_w - 1) a &= B.alwm;
            uint16_t as, bs;
            if (!desc) {
                as = (uint16_t)((((uint32_t)aold << 16) | a) >> ash);
                bs = (uint16_t)((((uint32_t)bold << 16) | bdat) >> bsh);
            } else {
                as = (uint16_t)(((((uint32_t)a << 16) | aold) << ash) >> 16);
                bs = (uint16_t)(((((uint32_t)bdat << 16) | bold) << bsh) >> 16);
            }
            aold = a;
            bold = bdat;
            uint16_t d = minterm(lf, as, bs, cdat);
            if (fill) {
                uint16_t out = 0;
                for (int i = 0; i < 16; i++) {
                    int bit = (d >> i) & 1;
                    if (ife) {
                        if (carry | bit) out |= (uint16_t)(1 << i);
                        if (bit) carry ^= 1;
                    } else {
                        if (bit) carry ^= 1;
                        if (carry) out |= (uint16_t)(1 << i);
                    }
                }
                d = out;
            }
            if (d) zero = false;
            if (used) { chip_w16(dpt, d); dpt += inc; }
        }
        if (desc) {
            if (usea) apt -= B.mod[0];
            if (useb) bpt -= B.mod[1];
            if (usec) cpt -= B.mod[2];
            if (used) dpt -= B.mod[3];
        } else {
            if (usea) apt += B.mod[0];
            if (useb) bpt += B.mod[1];
            if (usec) cpt += B.mod[2];
            if (used) dpt += B.mod[3];
        }
    }
    B.pt[0] = apt & 0x1ffffe; B.pt[1] = bpt & 0x1ffffe;
    B.pt[2] = cpt & 0x1ffffe; B.pt[3] = dpt & 0x1ffffe;
    B.dat[0] = adat; B.dat[1] = bdat; B.dat[2] = cdat;
    B.zero = zero;
}

/* Linjemodus. Oktanten er gitt av SUD, SUL og AUL i BLTCON1: med SUD satt er
 * x hovedaksen (y endres bare noen ganger), ellers er y hovedaksen. AUL velger
 * retningen paa hovedaksen (opp/venstre), SUL retningen paa den andre. */
static void blit_line(void)
{
    uint8_t lf = (uint8_t)B.con0;
    bool sud = B.con1 & 0x10, sul = B.con1 & 0x08, aul = B.con1 & 0x04, sing = B.con1 & 0x02;
    bool usec = B.con0 & 0x0200, used = B.con0 & 0x0100;
    int ash = B.con0 >> 12, bsh = B.con1 >> 12;
    int32_t err = (int16_t)(B.pt[0] & 0xffff);
    bool sign = (B.con1 & 0x40) != 0;
    uint32_t cpt = B.pt[2];
    int16_t bmod = B.mod[1], amod = B.mod[0], cmod = B.mod[2];
    uint16_t adat = B.dat[0], bdat = B.dat[1];
    bool zero = true, dot_on_row = false;

    for (unsigned n = 0; n < blit_h; n++) {
        uint16_t c = usec ? chip_r16(cpt) : B.dat[2];
        uint16_t a = (uint16_t)(adat >> ash);
        uint16_t rot = (uint16_t)((bdat << bsh) | (bdat >> ((16 - bsh) & 15)));
        uint16_t b = (bsh == 0 ? bdat : rot) & 0x8000 ? 0xffff : 0;
        uint16_t d = minterm(lf, a, b, c);
        if (d) zero = false;
        if (used && !(sing && dot_on_row)) chip_w16(cpt, d);
        dot_on_row = true;
        bsh = (bsh - 1) & 15;

        bool step_y = false;
        /* den sjeldne aksen */
        if (!sign) {
            if (sud) {                    /* y er den sjeldne aksen */
                cpt += sul ? -cmod : cmod;
                step_y = true;
            } else {                      /* x er den sjeldne aksen */
                if (sul) { if (--ash < 0) { ash = 15; cpt -= 2; } }
                else     { if (++ash > 15) { ash = 0; cpt += 2; } }
            }
            err += amod;
        } else {
            err += bmod;
        }
        /* hovedaksen */
        if (sud) {
            if (aul) { if (--ash < 0) { ash = 15; cpt -= 2; } }
            else     { if (++ash > 15) { ash = 0; cpt += 2; } }
        } else {
            cpt += aul ? -cmod : cmod;
            step_y = true;
        }
        if (step_y) dot_on_row = false;
        sign = (int16_t)err < 0;
        err = (int16_t)err;
    }
    B.pt[0] = (B.pt[0] & 0xffff0000) | (uint16_t)err;
    B.pt[2] = B.pt[3] = cpt & 0x1ffffe;
    B.con0 = (uint16_t)((B.con0 & 0x0fff) | (ash << 12));
    B.con1 = (uint16_t)((B.con1 & 0x0fbf) | (bsh << 12) | (sign ? 0x40 : 0));
    B.zero = zero;
}

void blitter_start(void)
{
    if (blit_log) note_blit();
    trace_blit();
    if (B.busy) blitter_finish();          /* forrige var ikke ferdig: avslutt den forst */
    unsigned words;
    int cyc_per_word;
    if (B.con1 & 1) {
        blit_line();
        words = blit_h;
        cyc_per_word = 4;
    } else {
        blit_area();
        words = blit_w * blit_h;
        int n = ((B.con0 >> 11) & 1) + ((B.con0 >> 10) & 1) + ((B.con0 >> 9) & 1);
        cyc_per_word = n + 1 < 2 ? 2 : n + 1;
    }
    B.blits++;
    B.busy = true;
    /* tiden i CPU-sykluser: fargeklokker * 2 */
    B.done_time = amiga_now() + (uint64_t)words * (uint64_t)cyc_per_word * 2 + 8;
    amiga_end_slice();
}

void blitter_finish(void)
{
    if (!B.busy) return;
    B.busy = false;
    C.intreq |= 0x0040;
    amiga_update_irq();
}
