/*
 * custom.c - registrene i custom-brikkene ($DFF000) og Copper.
 *
 * Lesing og skriving fra CPU-en og Copper gaar hit og fordeles videre til
 * Blitter (blitter.c), lyd (paula.c) og bildet (video.c). Copper kjores fra
 * amiga.c i takt med CPU-en: copper_next_time() sier naar den skal gjore noe,
 * og copper_run() utforer det som er forfalt.
 */
#include "amiga.h"
#include <string.h>

Custom C;
int custom_write_hpos = -1;               /* hpos for skriving fra Copper, -1 = CPU */

void custom_reset(void)
{
    memset(&C, 0, sizeof C);
    C.cop_state = COP_STOP;
    C.potgo = 0;
}

/* ------------------------------------------------------------ inndata */
static uint16_t joy_dat(int port)
{
    uint8_t j = IN.joy[port];
    int right = (j & JOY_RIGHT) != 0, left = (j & JOY_LEFT) != 0;
    int down = (j & JOY_DOWN) != 0, up = (j & JOY_UP) != 0;
    int x1 = right, y1 = left;
    int x0 = x1 ^ down, y0 = y1 ^ up;
    return (uint16_t)(y1 << 9 | y0 << 8 | x1 << 1 | x0);
}

static uint16_t potgor(void)
{
    uint16_t v = 0x5500;                  /* DATRY, DATRX, DATLY, DATLX hoy = ikke trykket */
    if (IN.joy[0] & JOY_FIRE2) v &= ~0x0400;
    if (IN.joy[1] & JOY_FIRE2) v &= ~0x4000;
    /* bitene som er satt som utganger leses tilbake */
    if (C.potgo & 0x8000) v = (v & ~0x4000) | (C.potgo & 0x4000);
    if (C.potgo & 0x2000) v = (v & ~0x1000) | (C.potgo & 0x1000);
    if (C.potgo & 0x0800) v = (v & ~0x0400) | (C.potgo & 0x0400);
    if (C.potgo & 0x0200) v = (v & ~0x0100) | (C.potgo & 0x0100);
    return v;
}

/* ------------------------------------------------------------ lesing */
uint16_t custom_read(uint32_t reg)
{
    switch (reg & 0x1fe) {
    case 0x002: {                          /* DMACONR */
        uint16_t v = C.dmacon & 0x07ff;
        if (B.busy) v |= 0x4000;
        if (B.zero) v |= 0x2000;
        return v;
    }
    case 0x004: {                          /* VPOSR: LOF, Agnus-ID (8372 PAL = $20), V8 */
        return (uint16_t)((M.lof ? 0x8000 : 0) | 0x2000 | ((M.vpos >> 8) & 1));
    }
    case 0x006: {                          /* VHPOSR */
        int h = amiga_hpos();
        return (uint16_t)((M.vpos & 0xff) << 8 | (h & 0xff));
    }
    case 0x00a: return joy_dat(0);
    case 0x00c: return joy_dat(1);
    case 0x00e: { uint16_t v = C.clxdat | 0x8000; C.clxdat = 0; return v; }
    case 0x010: return C.adkcon;
    case 0x012: case 0x014: return 0;
    case 0x016: return potgor();
    case 0x018: return 0x3000;             /* SERDATR: sendebuffer tom */
    case 0x01a: return 0;
    case 0x01c: return C.intena;
    case 0x01e: return C.intreq;
    case 0x07c: return 0xffff;             /* DENISEID: OCS har ingen */
    }
    return 0;
}

/* ------------------------------------------------------------ Copper */
static uint64_t cop_wait_time(void);

void copper_vblank(void)
{
    C.coppc = C.cop1lc;
    C.cop_state = COP_FETCH;
    C.cop_time = M.clk + 4;
}

static void copper_jump(uint32_t lc)
{
    C.coppc = lc;
    C.cop_state = COP_FETCH;
    if (custom_write_hpos >= 0) C.cop_time += 8;      /* Copper hopper selv */
    else { C.cop_time = amiga_now() + 4; amiga_end_slice(); }
}

static bool copper_on(void)
{
    return (C.dmacon & 0x0280) == 0x0280;
}

uint64_t copper_next_time(void)
{
    if (!copper_on() || C.cop_state == COP_STOP) return UINT64_MAX;
    return C.cop_time;
}

/* Er stralen forbi (vp,hp) med maskene ve og he? */
static bool beam_ge(int v, int h, int vp, int hp, int ve, int he)
{
    int vv = v & 0xff & ve, vw = vp & ve;
    if (vv > vw) return true;
    if (vv < vw) return false;
    return (h & he) >= (hp & he);
}

/* Foerste tidspunkt fra naa der WAIT-betingelsen holder, innen bildet. */
static uint64_t cop_wait_time(void)
{
    int vp = (C.cop_ir1 >> 8) & 0xff, hp = C.cop_ir1 & 0xfe;
    int ve = 0x80 | ((C.cop_ir2 >> 8) & 0x7f), he = C.cop_ir2 & 0xfe;
    uint64_t t0 = C.cop_time;
    if (t0 < M.line_clk) t0 = M.line_clk;
    int line = M.vpos;
    int h0 = (int)((t0 - M.line_clk) / 2);
    uint64_t lclk = M.line_clk;
    while (h0 >= LINE_CCK) { h0 -= LINE_CCK; line++; lclk += LINE_CYC; }
    for (; line < FRAME_LINES; line++, lclk += LINE_CYC, h0 = 0) {
        int vv = line & 0xff & ve, vw = vp & ve;
        if (vv < vw) continue;
        if (vv > vw) {
            uint64_t t = lclk + (uint64_t)h0 * 2;
            return t < t0 ? t0 : t;
        }
        for (int h = h0; h < LINE_CCK; h++) {
            if (beam_ge(line, h, vp, hp, ve, he)) {
                uint64_t t = lclk + (uint64_t)h * 2;
                return t < t0 ? t0 : t;
            }
        }
    }
    return UINT64_MAX;                     /* venter til neste bilde */
}

void copper_run(uint64_t until)
{
    int guard = 0;
    while (copper_on() && C.cop_state != COP_STOP && C.cop_time <= until && guard++ < 2000) {
        if (C.cop_state == COP_WAIT) {
            /* ventingen er over; vent ogsaa paa Blitteren hvis BFD er 0 */
            if (!(C.cop_ir2 & 0x8000) && B.busy) {
                C.cop_time = B.done_time;
                continue;
            }
            C.cop_state = COP_FETCH;
            C.cop_time += 4;
            continue;
        }
        uint32_t pc = C.coppc & (CHIP_SIZE - 2);
        C.cop_ir1 = chip_r16(pc);
        C.cop_ir2 = chip_r16(pc + 2);
        C.coppc = pc + 4;
        if (!(C.cop_ir1 & 1)) {
            /* MOVE */
            unsigned reg = C.cop_ir1 & 0x1fe;
            if (reg < 0x40 || (reg < 0x80 && !(C.copcon & 2))) {
                C.cop_state = COP_STOP;
                break;
            }
            int h = (int)((C.cop_time - M.line_clk) / 2);
            custom_write_hpos = h < 0 ? 0 : h > LINE_CCK - 1 ? LINE_CCK - 1 : h;
            custom_write(reg, C.cop_ir2);
            custom_write_hpos = -1;
            if (reg == 0x088 || reg == 0x08a) continue;   /* hopp: tiden er satt */
            C.cop_time += 8;
        } else if (!(C.cop_ir2 & 1)) {
            /* WAIT */
            C.cop_state = COP_WAIT;
            C.cop_time += 4;
            C.cop_time = cop_wait_time();
        } else {
            /* SKIP */
            int vp = (C.cop_ir1 >> 8) & 0xff, hp = C.cop_ir1 & 0xfe;
            int ve = 0x80 | ((C.cop_ir2 >> 8) & 0x7f), he = C.cop_ir2 & 0xfe;
            int h = (int)((C.cop_time - M.line_clk) / 2);
            if (beam_ge(M.vpos, h, vp, hp, ve, he)) C.coppc += 4;
            C.cop_time += 8;
        }
    }
}

void custom_line_start(void)
{
}

/* ------------------------------------------------------------ skriving */
static void set_clr(uint16_t *r, uint16_t v, uint16_t mask)
{
    if (v & 0x8000) *r |= v & mask;
    else *r &= ~(v & mask);
}

static void ptr_hi(uint32_t *p, uint16_t v) { *p = (*p & 0x0000ffff) | ((uint32_t)(v & 0x001f) << 16); }
static void ptr_lo(uint32_t *p, uint16_t v) { *p = (*p & 0xffff0000) | (v & 0xfffe); }

void custom_write(uint32_t reg, uint16_t v)
{
    reg &= 0x1fe;
    if (reg >= 0x0a0 && reg < 0x0e0) { paula_write(reg, v); return; }
    if (reg >= 0x180 && reg < 0x1c0) {
        video_reg_change(reg, v);
        C.color[(reg - 0x180) >> 1] = v & 0x0fff;
        return;
    }
    if (reg >= 0x0e0 && reg < 0x0f8) {
        int n = (reg - 0x0e0) >> 2;
        if (reg & 2) ptr_lo(&C.bplpt[n], v); else ptr_hi(&C.bplpt[n], v);
        return;
    }
    if (reg >= 0x120 && reg < 0x140) {
        int n = (reg - 0x120) >> 2;
        if (reg & 2) ptr_lo(&C.sprpt[n], v); else ptr_hi(&C.sprpt[n], v);
        return;
    }
    if (reg >= 0x140 && reg < 0x180) {
        int n = (reg - 0x140) >> 3;
        video_reg_change(reg, v);
        switch (reg & 6) {
        case 0: C.sprpos[n] = v; break;
        case 2: C.sprctl[n] = v; C.spr_armed[n] = 0; break;
        case 4: C.sprdata[n] = v; C.spr_armed[n] = 1; break;
        case 6: C.sprdatb[n] = v; break;
        }
        return;
    }
    switch (reg) {
    case 0x020: case 0x022: case 0x024: case 0x026: break;          /* disk: brukes ikke */
    case 0x02a: case 0x02c: break;                                   /* VPOSW/VHPOSW */
    case 0x02e: C.copcon = v; break;
    case 0x030: C.serdat = v; break;
    case 0x032: C.serper = v; break;
    case 0x034: C.potgo = v; break;
    case 0x036: break;                                               /* JOYTEST */
    case 0x040: B.con0 = v; break;
    case 0x042: B.con1 = v; break;
    case 0x044: B.afwm = v; break;
    case 0x046: B.alwm = v; break;
    case 0x048: ptr_hi(&B.pt[2], v); break;
    case 0x04a: ptr_lo(&B.pt[2], v); break;
    case 0x04c: ptr_hi(&B.pt[1], v); break;
    case 0x04e: ptr_lo(&B.pt[1], v); break;
    case 0x050: ptr_hi(&B.pt[0], v); break;
    case 0x052: ptr_lo(&B.pt[0], v); break;
    case 0x054: ptr_hi(&B.pt[3], v); break;
    case 0x056: ptr_lo(&B.pt[3], v); break;
    case 0x058: {                                                    /* BLTSIZE */
        extern unsigned blit_w, blit_h;
        blit_h = (v >> 6) & 0x3ff; if (!blit_h) blit_h = 1024;
        blit_w = v & 0x3f;         if (!blit_w) blit_w = 64;
        blitter_start();
        break;
    }
    case 0x05a: B.con0 = (B.con0 & 0xff00) | (v & 0xff); break;      /* BLTCON0L (ECS) */
    case 0x05c: { extern unsigned blit_h; blit_h = v & 0x7fff; if (!blit_h) blit_h = 0x8000; break; }
    case 0x05e: { extern unsigned blit_w; blit_w = v & 0x7ff; if (!blit_w) blit_w = 0x800; blitter_start(); break; }
    case 0x060: B.mod[2] = (int16_t)(v & 0xfffe); break;
    case 0x062: B.mod[1] = (int16_t)(v & 0xfffe); break;
    case 0x064: B.mod[0] = (int16_t)(v & 0xfffe); break;
    case 0x066: B.mod[3] = (int16_t)(v & 0xfffe); break;
    case 0x070: B.dat[2] = v; break;
    case 0x072: B.dat[1] = v; break;
    case 0x074: B.dat[0] = v; break;
    case 0x07e: C.dsksync = v; break;
    case 0x080: ptr_hi(&C.cop1lc, v); break;
    case 0x082: ptr_lo(&C.cop1lc, v); break;
    case 0x084: ptr_hi(&C.cop2lc, v); break;
    case 0x086: ptr_lo(&C.cop2lc, v); break;
    case 0x088: copper_jump(C.cop1lc); break;
    case 0x08a: copper_jump(C.cop2lc); break;
    case 0x08c: break;
    case 0x08e: C.diwstrt = v; break;
    case 0x090: C.diwstop = v; break;
    case 0x092: C.ddfstrt = v & 0xfc; break;
    case 0x094: C.ddfstop = v & 0xfc; break;
    case 0x096: {                                                    /* DMACON */
        uint16_t old = C.dmacon;
        set_clr(&C.dmacon, v, 0x07ff);
        paula_dma_change(old, C.dmacon);
        if ((old ^ C.dmacon) & 0x0280) {
            if (copper_on() && C.cop_state == COP_FETCH && C.cop_time < amiga_now())
                C.cop_time = amiga_now();
            amiga_end_slice();
        }
        break;
    }
    case 0x098: C.clxcon = v; break;
    case 0x09a: set_clr(&C.intena, v, 0x7fff); amiga_update_irq(); break;
    case 0x09c:
        set_clr(&C.intreq, v, 0x7fff);
        cia_update_irq();                 /* CIA-linjene setter bit 3 og 13 igjen hvis de fortsatt er aktive */
        amiga_update_irq();
        break;
    case 0x09e: set_clr(&C.adkcon, v, 0x7fff); break;
    case 0x100: video_reg_change(reg, v); C.bplcon0 = v; break;
    case 0x102: video_reg_change(reg, v); C.bplcon1 = v; break;
    case 0x104: video_reg_change(reg, v); C.bplcon2 = v; break;
    case 0x106: C.bplcon3 = v; break;
    case 0x108: C.bpl1mod = (int16_t)(v & 0xfffe); break;
    case 0x10a: C.bpl2mod = (int16_t)(v & 0xfffe); break;
    case 0x110: case 0x112: case 0x114: case 0x116: case 0x118: case 0x11a: break;
    case 0x1dc: C.beamcon0 = v; break;
    default:
        LOG2("skriving til ukjent custom-register %03x = %04x\n", reg, v);
        break;
    }
}

const char *custom_reg_name(unsigned reg)
{
    static const struct { unsigned r; const char *n; } names[] = {
        {0x002,"DMACONR"},{0x004,"VPOSR"},{0x006,"VHPOSR"},{0x00a,"JOY0DAT"},{0x00c,"JOY1DAT"},
        {0x00e,"CLXDAT"},{0x010,"ADKCONR"},{0x016,"POTGOR"},{0x01c,"INTENAR"},{0x01e,"INTREQR"},
        {0x02e,"COPCON"},{0x034,"POTGO"},{0x040,"BLTCON0"},{0x042,"BLTCON1"},{0x044,"BLTAFWM"},
        {0x046,"BLTALWM"},{0x048,"BLTCPTH"},{0x04c,"BLTBPTH"},{0x050,"BLTAPTH"},{0x054,"BLTDPTH"},
        {0x058,"BLTSIZE"},{0x060,"BLTCMOD"},{0x062,"BLTBMOD"},{0x064,"BLTAMOD"},{0x066,"BLTDMOD"},
        {0x070,"BLTCDAT"},{0x072,"BLTBDAT"},{0x074,"BLTADAT"},{0x080,"COP1LCH"},{0x082,"COP1LCL"},
        {0x084,"COP2LCH"},{0x086,"COP2LCL"},{0x088,"COPJMP1"},{0x08a,"COPJMP2"},{0x08e,"DIWSTRT"},
        {0x090,"DIWSTOP"},{0x092,"DDFSTRT"},{0x094,"DDFSTOP"},{0x096,"DMACON"},{0x098,"CLXCON"},
        {0x09a,"INTENA"},{0x09c,"INTREQ"},{0x09e,"ADKCON"},{0x100,"BPLCON0"},{0x102,"BPLCON1"},
        {0x104,"BPLCON2"},{0x108,"BPL1MOD"},{0x10a,"BPL2MOD"},
    };
    for (size_t i = 0; i < sizeof names / sizeof names[0]; i++) if (names[i].r == reg) return names[i].n;
    return NULL;
}
