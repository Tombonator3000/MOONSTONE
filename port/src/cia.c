/*
 * cia.c - de to CIA 8520-brikkene: tidtakere, klokke (TOD), porter og tastatur.
 *
 * CIA-A ($BFE001, oddetallsadresser) har fireknappene paa joystickene,
 * LED/lydfilteret og tastaturet (serieporten). Avbruddet gaar til INT2 (PORTS).
 * CIA-B ($BFD000, partallsadresser) styrer diskstasjonen, og avbruddet gaar
 * til INT6 (EXTER). Tidtakerne teller E-klokken (CPU/10).
 *
 * Tidtakerne oppdateres naar de leses eller skrives (cia_sync) og ved hendelser
 * fra amiga.c. cia_next_event() sier naar neste avbrudd fra en tidtaker kommer.
 */
#include "amiga.h"
#include <string.h>

Cia CIAA, CIAB;

void cia_reset(void)
{
    memset(&CIAA, 0, sizeof CIAA);
    memset(&CIAB, 0, sizeof CIAB);
    CIAA.ta = CIAA.tb = CIAA.ta_latch = CIAA.tb_latch = 0xffff;
    CIAB.ta = CIAB.tb = CIAB.ta_latch = CIAB.tb_latch = 0xffff;
    CIAA.ddra = 0x03;
    CIAA.pra = 0x03;
}

void cia_update_irq(void)
{
    if (CIAA.icr & CIAA.imask & 0x1f) C.intreq |= 0x0008;
    if (CIAB.icr & CIAB.imask & 0x1f) C.intreq |= 0x2000;
}

static void signal(Cia *c, uint8_t bit)
{
    c->icr |= bit;
    if (c->imask & bit) {
        cia_update_irq();
        amiga_update_irq();
    }
}

/* Teller ned en tidtaker n tikk. Returnerer antall underflyt. */
static uint32_t count(uint16_t *t, uint16_t latch, uint8_t *cr, uint32_t n)
{
    uint32_t under = 0;
    while (n > 0 && (*cr & 1)) {
        uint32_t left = (uint32_t)*t + 1;
        if (n < left) { *t = (uint16_t)(*t - n); break; }
        n -= left;
        *t = latch;
        under++;
        if (*cr & 0x08) { *cr &= (uint8_t)~1; break; }      /* en gang */
    }
    return under;
}

static void tick_one(Cia *c, uint32_t n)
{
    uint32_t ua = 0, ub = 0;
    if (!(c->cra & 0x20)) ua = count(&c->ta, c->ta_latch, &c->cra, n);
    if (ua) signal(c, 1);
    int inb = (c->crb >> 5) & 3;
    if (inb == 0) ub = count(&c->tb, c->tb_latch, &c->crb, n);
    else if (inb >= 2 && ua) ub = count(&c->tb, c->tb_latch, &c->crb, ua);
    if (ub) signal(c, 2);
}

void cia_tick(uint32_t eticks)
{
    tick_one(&CIAA, eticks);
    tick_one(&CIAB, eticks);
}

void cia_sync(void)
{
    uint64_t e = amiga_now() / ECLOCK_DIV;
    if (e > M.eclk_done) {
        uint64_t n = e - M.eclk_done;
        M.eclk_done = e;
        while (n > 0) {
            uint32_t step = n > 0x10000000 ? 0x10000000 : (uint32_t)n;
            cia_tick(step);
            n -= step;
        }
    }
}

static uint32_t next_one(const Cia *c)
{
    uint32_t best = 0xffffffff;
    if ((c->cra & 1) && !(c->cra & 0x20) && (c->imask & 1)) {
        uint32_t t = (uint32_t)c->ta + 1;
        if (t < best) best = t;
    }
    if ((c->crb & 1) && !(c->crb & 0x60) && (c->imask & 2)) {
        uint32_t t = (uint32_t)c->tb + 1;
        if (t < best) best = t;
    }
    if ((c->crb & 1) && ((c->crb >> 5) & 3) >= 2 && (c->imask & 2) && (c->cra & 1) && !(c->cra & 0x20)) {
        /* B teller underflyt fra A: neste A-underflyt er nok som hendelse */
        uint32_t t = (uint32_t)c->ta + 1;
        if (t < best) best = t;
    }
    return best;
}

uint32_t cia_next_event(void)
{
    uint32_t a = next_one(&CIAA), b = next_one(&CIAB);
    return a < b ? a : b;
}

/* ------------------------------------------------------------ TOD */
static void tod_inc(Cia *c)
{
    if (c->tod_halt) return;
    c->tod = (c->tod + 1) & 0xffffff;
    if (c->tod == c->alarm) signal(c, 4);
}

void cia_tod_vsync(void) { tod_inc(&CIAA); }
void cia_tod_hsync(void) { tod_inc(&CIAB); }

void cia_serial_in(uint8_t byte)
{
    CIAA.sdr = byte;
    signal(&CIAA, 8);
}

/* ------------------------------------------------------------ lesing og skriving */
static uint8_t port_a_inputs(const Cia *c)
{
    if (c == &CIAA) {
        uint8_t v = 0xfc;                 /* disk inaktiv, ingen knapper */
        if (IN.joy[0] & JOY_FIRE) v &= (uint8_t)~0x40;
        if (IN.joy[1] & JOY_FIRE) v &= (uint8_t)~0x80;
        return v;
    }
    return 0xff;
}

uint8_t cia_read(Cia *c, int reg)
{
    cia_sync();
    switch (reg) {
    case 0: return (uint8_t)((c->pra & c->ddra) | (port_a_inputs(c) & ~c->ddra));
    case 1: return (uint8_t)((c->prb & c->ddrb) | (0xff & ~c->ddrb));
    case 2: return c->ddra;
    case 3: return c->ddrb;
    case 4: return (uint8_t)c->ta;
    case 5: return (uint8_t)(c->ta >> 8);
    case 6: return (uint8_t)c->tb;
    case 7: return (uint8_t)(c->tb >> 8);
    case 8: {
        uint32_t t = c->tod_latched ? c->tod_latch : c->tod;
        c->tod_latched = false;
        return (uint8_t)t;
    }
    case 9:  return (uint8_t)((c->tod_latched ? c->tod_latch : c->tod) >> 8);
    case 10:
        if (!c->tod_latched) { c->tod_latch = c->tod; c->tod_latched = true; }
        return (uint8_t)(c->tod_latch >> 16);
    case 12: return c->sdr;
    case 13: {
        uint8_t v = c->icr;
        if (v & c->imask & 0x1f) v |= 0x80;
        c->icr = 0;
        return v;
    }
    case 14: return c->cra & (uint8_t)~0x10;
    case 15: return c->crb & (uint8_t)~0x10;
    }
    return 0xff;
}

static void filter_from_pra(void)
{
    /* LED paa (bit 1 lav) betyr at lydfilteret er paa */
    paula_filter_led = (CIAA.ddra & 2) && !(CIAA.pra & 2);
}

void cia_write(Cia *c, int reg, uint8_t v)
{
    cia_sync();
    switch (reg) {
    case 0: c->pra = v; if (c == &CIAA) filter_from_pra(); break;
    case 1: c->prb = v; break;
    case 2: c->ddra = v; if (c == &CIAA) filter_from_pra(); break;
    case 3: c->ddrb = v; break;
    case 4: c->ta_latch = (c->ta_latch & 0xff00) | v; break;
    case 5:
        c->ta_latch = (uint16_t)((c->ta_latch & 0x00ff) | v << 8);
        if (!(c->cra & 1)) c->ta = c->ta_latch;
        if (c->cra & 0x08) { c->ta = c->ta_latch; c->cra |= 1; }  /* 8520: en gang-modus starter */
        amiga_end_slice();
        break;
    case 6: c->tb_latch = (c->tb_latch & 0xff00) | v; break;
    case 7:
        c->tb_latch = (uint16_t)((c->tb_latch & 0x00ff) | v << 8);
        if (!(c->crb & 1)) c->tb = c->tb_latch;
        if (c->crb & 0x08) { c->tb = c->tb_latch; c->crb |= 1; }
        amiga_end_slice();
        break;
    case 8:
        if (c->crb & 0x80) c->alarm = (c->alarm & 0xffff00) | v;
        else { c->tod = (c->tod & 0xffff00) | v; c->tod_halt = false; }
        break;
    case 9:
        if (c->crb & 0x80) c->alarm = (c->alarm & 0xff00ff) | (uint32_t)v << 8;
        else c->tod = (c->tod & 0xff00ff) | (uint32_t)v << 8;
        break;
    case 10:
        if (c->crb & 0x80) c->alarm = (c->alarm & 0x00ffff) | (uint32_t)v << 16;
        else { c->tod = (c->tod & 0x00ffff) | (uint32_t)v << 16; c->tod_halt = true; }
        break;
    case 12: c->sdr = v; break;
    case 13:
        if (v & 0x80) c->imask |= v & 0x1f;
        else c->imask &= (uint8_t)~(v & 0x1f);
        cia_update_irq();
        amiga_update_irq();
        break;
    case 14:
        if (c == &CIAA && (c->cra & 0x40) && !(v & 0x40)) M.kbd_handshake = true;
        if (v & 0x10) c->ta = c->ta_latch;
        c->cra = v & (uint8_t)~0x10;
        amiga_end_slice();
        break;
    case 15:
        if (v & 0x10) c->tb = c->tb_latch;
        c->crb = v & (uint8_t)~0x10;
        amiga_end_slice();
        break;
    }
}
