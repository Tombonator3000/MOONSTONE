/*
 * decomp.c - funksjoner fra Moonstone (mog) som er skrevet om til C.
 *
 * Hver funksjon registreres i decomp_register_all() med adressen den har naar
 * mog er lastet til $80000 (samme adresser som i disasm/mog.s). Naar CPU-en
 * kommer dit, kjores C-funksjonen i stedet (hooks.c). Den skal gi samme
 * resultat som originalen: registre, flagg, minne (ogsaa det originalen skriver
 * paa stakken) og antall sykluser (hook_cycles, maal med --hook-cycles).
 *
 * Arbeidsflyt:
 *   1. Finn funksjonen i disasm/mog.s og gi den et navn i disasm/symbols.txt.
 *   2. Skriv den her med originalkoden som kommentar, og registrer den nederst.
 *   3. ./moonstone --headless --hook-cycles ... viser syklusene til originalen.
 *   4. python3 tools/check_hooks.py kjorer spillet med og uten C-versjonene og
 *      sammenligner minnet og bildet. Alt skal vaere likt.
 */
#include "amiga.h"
#include "m68k.h"

/* ------------------------------------------------------------ hjelpere */
enum { CCR_C = 1, CCR_V = 2, CCR_Z = 4, CCR_N = 8, CCR_X = 16 };

static uint32_t D(int n) { return m68k_get_reg(NULL, (m68k_register_t)(M68K_REG_D0 + n)); }
static uint32_t A(int n) { return m68k_get_reg(NULL, (m68k_register_t)(M68K_REG_A0 + n)); }
static void setD(int n, uint32_t v) { m68k_set_reg((m68k_register_t)(M68K_REG_D0 + n), v); }
static uint16_t ccr(void) { return (uint16_t)(m68k_get_reg(NULL, M68K_REG_SR) & 0x1f); }
static void set_ccr(uint16_t c)
{
    uint32_t sr = m68k_get_reg(NULL, M68K_REG_SR);
    m68k_set_reg(M68K_REG_SR, (sr & ~0x1fu) | (c & 0x1f));
}
/* flagg etter en flytt/logisk operasjon paa et ord: N og Z fra verdien, V = C = 0, X uendret */
static uint16_t flags_w(uint16_t c, uint16_t v)
{
    c &= CCR_X;
    if (v & 0x8000) c |= CCR_N;
    if (!v) c |= CCR_Z;
    return c;
}

/* ------------------------------------------------------------ joystick */

/* $82008 joydat_til_bits
 *   btst #1,d0 / beq / ori.w #1,d1       hoyre
 *   btst #9,d0 / beq / ori.w #2,d1       venstre
 *   move.w d0,d2 / lsl.w #1,d2 / eor.w d0,d2
 *   btst #1,d2 / beq / ori.w #4,d1       ned  (X1 ^ X0)
 *   btst #9,d2 / beq / ori.w #8,d1       opp  (Y1 ^ Y0)
 *   rts
 * D0 = JOYxDAT, D1 faar bitene. D2 blir brukt. */
static uint16_t joydat_bits(uint32_t d0, uint32_t *d1io, uint32_t *d2out, uint16_t c)
{
    uint16_t w0 = (uint16_t)d0, d1 = (uint16_t)*d1io;
    if (w0 & 0x0002) { d1 |= 1; c = flags_w(c, d1); } else c |= CCR_Z;
    if (w0 & 0x0200) { d1 |= 2; c = flags_w(c, d1); } else c |= CCR_Z;
    uint16_t d2 = (uint16_t)(w0 << 1);
    c = (uint16_t)((c & ~(CCR_X | CCR_C)) | ((w0 & 0x8000) ? (CCR_X | CCR_C) : 0));   /* lsl: X = C = bit 15 */
    d2 ^= w0;
    c = flags_w(c, d2);                                                                  /* eor */
    if (d2 & 0x0002) { d1 |= 4; c = flags_w(c, d1); } else c |= CCR_Z;
    if (d2 & 0x0200) { d1 |= 8; c = flags_w(c, d1); } else c |= CCR_Z;
    *d1io = (*d1io & 0xffff0000u) | d1;
    *d2out = (*d2out & 0xffff0000u) | d2;
    return c;
}

/* Sykluser (maalt med --hook-cycles): 112, pluss 6 for hver av de fire testene som
 * slaar til (btst + beq tatt = 20, btst + beq ikke tatt + ori = 26). */
static int bits_satt(uint16_t d0)
{
    uint16_t d2 = (uint16_t)((d0 << 1) ^ d0);
    return ((d0 >> 1) & 1) + ((d0 >> 9) & 1) + ((d2 >> 1) & 1) + ((d2 >> 9) & 1);
}

static bool joydat_til_bits(void)
{
    uint32_t d0 = D(0), d1 = D(1), d2 = D(2);
    uint16_t c = joydat_bits(d0, &d1, &d2, ccr());
    setD(1, d1);
    setD(2, d2);
    set_ccr(c);
    hook_return();
    hook_cycles(112 + 6 * bits_satt((uint16_t)d0));
    return true;
}

/* $81F92 les_joysticker
 * Leser joystick i port 2 (JOY1DAT, fire = CIA-A PRA bit 7) til $8D9A2 og port 1
 * (JOY0DAT, fire = bit 6) til $8D9A0. For port 1 nulles retningen hvis venstre og
 * hoyre (eller opp og ned) er nede samtidig. Returnerer D0 = port 1, D1 = port 2.
 *   movem.l d0-d2,-(a7)
 *   move.w $dff00c,d0 / moveq #0,d1 / jsr joydat_til_bits
 *   btst #7,$bfe001 / bne / ori.w #$10,d1 / move.w d1,$8d9a2
 *   moveq #0,d1 / move.w $dff00a,d0 / jsr joydat_til_bits
 *   (venstre+hoyre eller opp+ned: moveq #0,d1)
 *   btst #6,$bfe001 / bne / ori.w #$10,d1 / move.w d1,$8d9a0
 *   movem.l (a7)+,d0-d2
 *   move.w $8d9a0,d0 / move.w $8d9a2,d1 / rts */
static bool les_joysticker(void)
{
    uint32_t sp = A(7);
    uint32_t d0 = D(0), d1 = D(1), d2 = D(2);
    /* det originalen skriver paa stakken: d0-d2 og returadressen til det siste jsr */
    mem_write32(sp - 12, d0);
    mem_write32(sp - 8, d1);
    mem_write32(sp - 4, d2);
    mem_write32(sp - 16, 0x00081fc6);

    uint16_t c = ccr();
    int cyc = 572;
    uint32_t r0 = (d0 & 0xffff0000u) | mem_read16(0xdff00c);
    uint32_t r1 = 0, r2 = d2;
    cyc += 6 * bits_satt((uint16_t)r0);
    c = joydat_bits(r0, &r1, &r2, c);
    if (!(mem_read8(0xbfe001) & 0x80)) { r1 |= 0x10; cyc += 6; }
    uint16_t port2 = (uint16_t)r1;
    mem_write16(0x8d9a2, port2);

    r1 = 0;
    r0 = (r0 & 0xffff0000u) | mem_read16(0xdff00a);
    cyc += 6 * bits_satt((uint16_t)r0);
    c = joydat_bits(r0, &r1, &r2, c);
    if ((r1 & 3) == 3) { r1 = 0; cyc += 2; }
    if ((r1 & 0xc) == 0xc) { r1 = 0; cyc += 2; }
    if (!(mem_read8(0xbfe001) & 0x40)) { r1 |= 0x10; cyc += 6; }
    uint16_t port1 = (uint16_t)r1;
    mem_write16(0x8d9a0, port1);

    setD(0, (d0 & 0xffff0000u) | port1);
    setD(1, (d1 & 0xffff0000u) | port2);
    setD(2, d2);
    set_ccr(flags_w(c, port2));
    hook_return();
    hook_cycles(cyc);
    return true;
}

void decomp_register_all(void)
{
    hooks_clear();
    hooks_register(0x82008, joydat_til_bits, "joydat_til_bits");
    hooks_register(0x81f92, les_joysticker, "les_joysticker");
    game_register_hooks();                 /* observatorer (tegnelisten), endrer ingenting */
}
