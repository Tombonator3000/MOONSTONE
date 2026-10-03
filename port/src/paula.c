/*
 * paula.c - lyden: fire 8-bits kanaler med DMA, periode og volum.
 *
 * Kanal 0 og 3 gaar til venstre, 1 og 2 til hoyre. Hver kanal er en trappekurve
 * som byttes hver periode (i fargeklokker). Utgangen lages ved aa ta
 * gjennomsnittet av kurven over hver utgangssample (48 kHz), og deretter et
 * lavpassfilter som paa en A500 (ca. 4,5 kHz), pluss LED-filteret naar
 * spillet slaar det paa.
 *
 * Avbruddet for en kanal (AUD0-3) kommer naar en ny buffer starter, slik at
 * spillet kan legge inn neste adresse og lengde.
 */
#include "amiga.h"
#include <string.h>
#include <math.h>

AudChan AUD[4];
float   paula_volume = 1.0f;
bool    paula_filter_led;

static int16_t ring[AUDIO_RING * 2];
static int     ring_w, ring_r;

/* tid maales i 1/256 fargeklokke */
static const int64_t sample_num = (int64_t)CCK_HZ * 256;
static int32_t to_next;                   /* igjen til neste utgangssample */
static int64_t frac;                      /* rest i Bresenham-delingen */
static int64_t acc_l, acc_r;
static int32_t acc_t;
static float   f1l, f1r, f2l, f2r, f3l, f3r;

static void next_sample_period(void)
{
    int64_t p = sample_num / AUDIO_RATE;
    frac += sample_num % AUDIO_RATE;
    if (frac >= AUDIO_RATE) { frac -= AUDIO_RATE; p++; }
    to_next = (int32_t)p;
}

void paula_reset(void)
{
    memset(AUD, 0, sizeof AUD);
    ring_w = ring_r = 0;
    frac = 0;
    acc_l = acc_r = 0;
    acc_t = 0;
    f1l = f1r = f2l = f2r = f3l = f3r = 0;
    next_sample_period();
}

static void irq(int ch)
{
    C.intreq |= (uint16_t)(0x0080 << ch);
    amiga_update_irq();
}

static int period(const AudChan *a)
{
    int p = a->per;
    if (p < 124) p = 124;
    return p;
}

static void fetch_word(int ch)
{
    AudChan *a = &AUD[ch];
    a->buf = chip_r16(a->pt);
    a->pt += 2;
    if (a->lencnt <= 1) {
        a->pt = a->lc;
        a->lencnt = a->len ? a->len : 0x10000;
        irq(ch);
    } else {
        a->lencnt--;
    }
}

static void dma_start(int ch)
{
    AudChan *a = &AUD[ch];
    a->state = 1;
    a->pt = a->lc;
    a->lencnt = a->len ? a->len : 0x10000;
    irq(ch);
    fetch_word(ch);
    a->bytepos = 0;
    a->sample = (int8_t)(a->buf >> 8);
    a->percnt = period(a) * 256;
}

void paula_dma_change(uint16_t old, uint16_t now)
{
    for (int ch = 0; ch < 4; ch++) {
        bool was = (old & 0x0200) && (old & (1 << ch));
        bool is = (now & 0x0200) && (now & (1 << ch));
        if (!was && is) dma_start(ch);
        else if (was && !is) { AUD[ch].state = 0; AUD[ch].sample = 0; }
    }
}

void paula_write(unsigned reg, uint16_t v)
{
    int ch = (reg - 0x0a0) >> 4;
    AudChan *a = &AUD[ch];
    switch (reg & 0x0e) {
    case 0x0: a->lc = (a->lc & 0xffff) | (uint32_t)(v & 0x1f) << 16; break;
    case 0x2: a->lc = (a->lc & 0xffff0000) | (v & 0xfffe); break;
    case 0x4: a->len = v; break;
    case 0x6: a->per = v; break;
    case 0x8: a->vol = v & 0x7f; if (a->vol > 64) a->vol = 64; break;
    case 0xa:
        a->dat = v;
        if (a->state != 1) {
            /* manuell modus: CPU-en mater kanalen selv */
            a->state = 2;
            a->buf = v;
            a->bytepos = 0;
            a->sample = (int8_t)(v >> 8);
            a->percnt = period(a) * 256;
        }
        break;
    }
}

static void advance(int ch)
{
    AudChan *a = &AUD[ch];
    if (a->bytepos == 0) {
        a->bytepos = 1;
        a->sample = (int8_t)(a->buf & 0xff);
    } else if (a->state == 1) {
        fetch_word(ch);
        a->bytepos = 0;
        a->sample = (int8_t)(a->buf >> 8);
    } else {
        /* manuell: ordet er spilt, be om et nytt og hold siste verdi */
        a->state = 0;
        irq(ch);
    }
    a->percnt += period(a) * 256;
}

static void emit(void)
{
    float l = (float)acc_l / (float)acc_t;
    float r = (float)acc_r / (float)acc_t;
    acc_l = acc_r = 0;
    acc_t = 0;
    /* fast lavpass som A500 (ca. 4,5 kHz) */
    const float k1 = 0.45f;
    f1l += k1 * (l - f1l); f1r += k1 * (r - f1r);
    l = f1l; r = f1r;
    if (paula_filter_led) {
        const float k2 = 0.35f;
        f2l += k2 * (l - f2l); f2r += k2 * (r - f2r);
        f3l += k2 * (f2l - f3l); f3r += k2 * (f2r - f3r);
        l = f3l; r = f3r;
    }
    float g = 1.9f * paula_volume;
    int il = (int)lrintf(l * g), ir = (int)lrintf(r * g);
    if (il > 32767) il = 32767; if (il < -32768) il = -32768;
    if (ir > 32767) ir = 32767; if (ir < -32768) ir = -32768;
    int next = (ring_w + 1) % AUDIO_RING;
    if (next == ring_r) ring_r = (ring_r + 1) % AUDIO_RING;   /* fullt: kast det eldste */
    ring[ring_w * 2] = (int16_t)il;
    ring[ring_w * 2 + 1] = (int16_t)ir;
    ring_w = next;
}

void paula_run(int cck)
{
    int32_t remaining = cck * 256;
    while (remaining > 0) {
        int32_t step = remaining < to_next ? remaining : to_next;
        for (int ch = 0; ch < 4; ch++)
            if (AUD[ch].state && AUD[ch].percnt < step) step = AUD[ch].percnt > 0 ? AUD[ch].percnt : 1;
        int32_t vl = AUD[0].sample * AUD[0].vol + AUD[3].sample * AUD[3].vol;
        int32_t vr = AUD[1].sample * AUD[1].vol + AUD[2].sample * AUD[2].vol;
        acc_l += (int64_t)vl * step;
        acc_r += (int64_t)vr * step;
        acc_t += step;
        remaining -= step;
        to_next -= step;
        for (int ch = 0; ch < 4; ch++) {
            if (!AUD[ch].state) continue;
            AUD[ch].percnt -= step;
            while (AUD[ch].state && AUD[ch].percnt <= 0) advance(ch);
        }
        if (to_next <= 0) {
            emit();
            next_sample_period();
        }
    }
}

int paula_take(int16_t *out, int max_frames)
{
    int n = 0;
    while (n < max_frames && ring_r != ring_w) {
        out[n * 2] = ring[ring_r * 2];
        out[n * 2 + 1] = ring[ring_r * 2 + 1];
        ring_r = (ring_r + 1) % AUDIO_RING;
        n++;
    }
    musikk_bland(out, n);                 /* bakgrunnsmusikken (musikk.c), ikke en del av emuleringen */
    return n;
}

void paula_state(StateIO *s)
{
    STATE_VAR(s, AUD);
    STATE_VAR(s, to_next);
    STATE_VAR(s, frac);
    STATE_VAR(s, acc_l);
    STATE_VAR(s, acc_r);
    STATE_VAR(s, acc_t);
    STATE_VAR(s, paula_filter_led);
}
