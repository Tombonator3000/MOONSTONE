/*
 * musikk.c - bakgrunnsmusikk i resten av spillet.
 *
 * Originalen har musikk bare i introen (music.cmp, «introx5») og i sluttscenen
 * (vmusic.cmp, «vict0ry6yy»), spilt av program. Hovedspillet (mog: tittelmenyen,
 * kartet, byene og kampene) har bare lydeffekter. Paa nettsiden hopper de fleste
 * over introen for musikken begynner (den starter foerst etter ca. 32 sekunder),
 * og da hoerer man aldri musikk.
 *
 * Her spilles music.cmp av en liten ProTracker-spiller naar mog kjorer, og blandes
 * inn i lyden ut (paula_take). Introen og sluttscenen beholder sin egen musikk:
 * spilleren tones ut naar program kjorer. Musikken er ikke en del av emuleringen
 * (ingen minneadresser, ikke i lagringen), saa nettspill, lagring og check_hooks
 * er urort. Den kan slaas av (musikk_sett).
 *
 * Filen pakkes ut som introen gjor (samme metode som tools/lyd.py, cmp_ut), og
 * modulen er ProTracker med 31 instrumenter uten merket «M.K.».
 */
#include "amiga.h"
#include <stdlib.h>
#include <string.h>
#include <math.h>

/* ---------------------------------------------------------------- utpakking */
/* music.cmp: 'RNC\1', long utpakket lengde, long pakket lengde, pakkede data.
 * Bitene og utdataene gaar bakfra (introen, program $85968-$85AA2). */
typedef struct { const uint8_t *src; long a6; unsigned d3; bool feil; } Bits;

static int bit(Bits *b)
{
    unsigned d3 = b->d3;
    int c = (int)(d3 >> 7 & 1);
    d3 = (d3 << 1) & 0xff;
    if (d3) { b->d3 = d3; return c; }
    if (--b->a6 < 0) { b->feil = true; b->a6 = 0; return 0; }
    d3 = b->src[b->a6];
    c = (int)(d3 >> 7 & 1);
    b->d3 = ((d3 << 1) | 1) & 0xff;        /* roxl med X = 1 (markoren) */
    return c;
}

static int bits(Bits *b, int n)
{
    int v = 0;
    while (n--) v = (v << 1) | bit(b);
    return v;
}

static uint8_t *cmp_ut(const uint8_t *d, size_t n, size_t *ut_len)
{
    if (n < 12 || memcmp(d, "RNC\x01", 4)) return NULL;
    uint32_t ulen = (uint32_t)d[4] << 24 | d[5] << 16 | d[6] << 8 | d[7];
    uint32_t plen = (uint32_t)d[8] << 24 | d[9] << 16 | d[10] << 8 | d[11];
    if (plen > n - 12 || ulen > 4u << 20 || !plen) return NULL;
    long cap = (long)ulen + 1024, a3 = cap, a2 = cap;
    uint8_t *ut = calloc((size_t)cap, 1);
    if (!ut) return NULL;
    Bits b = { d + 12, (long)plen, 0, false };
    b.d3 = b.src[--b.a6];
    for (;;) {
        if (bit(&b)) {                     /* en rekke bytes som de er */
            int k = 1;
            if (bit(&b)) {
                static const int bredde[4] = { 2, 2, 3, 10 }, pluss[4] = { 1, 4, 7, 14 };
                int d5 = 0, d1;
                for (d1 = 0; d1 < 4; d1++) {
                    d5 = bits(&b, bredde[d1]);
                    if (d1 == 3 || d5 != (1 << bredde[d1]) - 1) break;
                }
                k = d5 + pluss[d1 < 4 ? d1 : 3] + 1;
            }
            while (k--) {
                if (--b.a6 < 0 || --a3 < 0) { free(ut); return NULL; }
                ut[a3] = b.src[b.a6];
            }
        }
        if (b.a6 <= 0) break;
        int k = 0;                         /* lengde */
        while (k < 4 && bit(&b)) k++;
        static const int grunn[5] = { 2, 3, 4, 6, 10 }, ekstra[5] = { 0, 0, 1, 2, 10 };
        int lengde = grunn[k] + bits(&b, ekstra[k]);
        int avstand;                       /* avstand */
        if (lengde == 2) avstand = bit(&b) ? bits(&b, 9) + 0x40 : bits(&b, 6);
        else {
            k = 0;
            while (k < 2 && bit(&b)) k++;
            avstand = k == 0 ? bits(&b, 8) + 32 : k == 1 ? bits(&b, 5) : bits(&b, 12) + 288;
        }
        long kilde = avstand ? a3 + avstand + lengde - 1 : a3 + 1;
        while (lengde--) {
            if (--kilde >= cap || kilde < 0 || --a3 < 0) { free(ut); return NULL; }
            ut[a3] = ut[kilde];
        }
        if (b.feil) { free(ut); return NULL; }
    }
    *ut_len = (size_t)(a2 - a3);
    memmove(ut, ut + a3, *ut_len);
    return ut;
}

/* ---------------------------------------------------------------- modulen */
typedef struct { const int8_t *data; uint32_t len, rep, replen; int fine, vol; } Instr;
typedef struct {
    const Instr *in;                       /* instrumentet (volum og finjustering) */
    const int8_t *data;                    /* lyden som spilles; byttes bare ved en ny note */
    uint64_t pos;                          /* 48.16 i sample (lyder kan vaere over 64 KB) */
    uint32_t slutt, lstart, llen;          /* bytes; llen 0 = ingen sloyfe */
    bool aktiv;
    int periode, base, maal, porta, vol, fine;
    int eff, par, vib_pos, vib_fart, vib_dybde, trem_pos, trem_fart, trem_dybde, vib_form, trem_form;
    int offset_mem, loop_rad, loop_ant, vol_ut, per_ut, kutt, forsink;
    uint8_t ny_note[4];                    /* raden som venter paa ED (notedelay) */
} Kanal;

static uint8_t *mod;
static size_t mod_len;
static Instr ins[32];
static int sang_len, sang_start, ant_monstre;
static const uint8_t *orden, *monstre;
static Kanal kan[4];
static int fart, tempo, tikk, rad, pos, neste_rad, neste_pos, monster_pause;
static bool hopp;
static int32_t igjen;                     /* samples til neste tikk */
static float f_l, f_r;                    /* lavpass som Paula */
static float styrke;                      /* 0-1, tones inn og ut */

bool  musikk_paa = true;
float musikk_volum = 0.5f;

static const int16_t per0[36] = {
    856, 808, 762, 720, 678, 640, 604, 570, 538, 508, 480, 453,
    428, 404, 381, 360, 339, 320, 302, 285, 269, 254, 240, 226,
    214, 202, 190, 180, 170, 160, 151, 143, 135, 127, 120, 113,
};
static int16_t per_tab[16][36];           /* finjustering 0-15 (8-15 er -8 til -1) */
static const uint8_t sinus[32] = {
    0, 24, 49, 74, 97, 120, 141, 161, 180, 197, 212, 224, 235, 244, 250, 253,
    255, 253, 250, 244, 235, 224, 212, 197, 180, 161, 141, 120, 97, 74, 49, 24,
};

static int note_for(int periode)
{
    int best = 0, avst = 1 << 30;
    for (int i = 0; i < 36; i++) {
        int a = abs(per0[i] - periode);
        if (a < avst) { avst = a; best = i; }
    }
    return best;
}

/* Sangen (19 posisjoner, ca. 105 s) aapner med 12 s nesten stille og slag fram til
 * 23 s; hovedtemaet begynner paa posisjon 4. Som bakgrunnsmusikk starter den der,
 * og der begynner den ogsaa paa nytt, saa man slipper den stille aapningen. */
#define BAKGRUNN_START 4

static void start_sang(void)
{
    memset(kan, 0, sizeof kan);
    fart = 6; tempo = 125; tikk = 0; rad = 0;
    pos = sang_len > BAKGRUNN_START ? BAKGRUNN_START : 0;
    neste_rad = 0; neste_pos = 0; hopp = false; monster_pause = 0;
    igjen = 0;
}

/* Kalles fra amiga_init. Nettsiden starter kjernen paa nytt uten aa laste den paa
 * nytt (en annen spillfil eller egne filer), saa modulen lastes hver gang fra filene
 * som gjelder naa. Finnes ingen music.cmp som kan spilles, blir det ingen musikk. */
void musikk_last(void)
{
    free(mod);
    mod = NULL;
    mod_len = 0;
    orden = monstre = NULL;
    memset(ins, 0, sizeof ins);
    memset(kan, 0, sizeof kan);
    styrke = 0.0f;                         /* maskinen starter paa nytt: ingen utoning av den gamle */
    f_l = f_r = 0.0f;
    for (int f = 0; f < 16; f++) {
        int ft = f < 8 ? f : f - 16;
        for (int i = 0; i < 36; i++) per_tab[f][i] = (int16_t)lrint(per0[i] * pow(2.0, -ft / 96.0));
    }
    size_t n = 0;
    const uint8_t *d = files_peek("data/music.cmp", &n);
    if (!d) return;
    size_t len = 0;
    uint8_t *u = cmp_ut(d, n, &len);
    if (!u || len < 1084) { free(u); return; }
    sang_len = u[950];
    sang_start = u[951] < 128 ? u[951] : 0;
    if (sang_len < 1 || sang_len > 128) { free(u); return; }
    orden = u + 952;
    ant_monstre = 0;
    for (int i = 0; i < 128; i++) if (orden[i] + 1 > ant_monstre) ant_monstre = orden[i] + 1;
    monstre = u + 1084;
    size_t s = 1084 + (size_t)ant_monstre * 1024;
    if (s > len) { free(u); return; }
    for (int i = 1; i <= 31; i++) {
        const uint8_t *h = u + 20 + (i - 1) * 30;
        Instr *in = &ins[i];
        in->len = (uint32_t)(h[22] << 8 | h[23]) * 2;
        in->fine = h[24] & 15;
        in->vol = h[25] > 64 ? 64 : h[25];
        in->rep = (uint32_t)(h[26] << 8 | h[27]) * 2;
        in->replen = (uint32_t)(h[28] << 8 | h[29]) * 2;
        if (s + in->len > len) in->len = (uint32_t)(len - s);
        in->data = (const int8_t *)(u + s);
        s += in->len;
        if (in->rep > in->len) in->rep = in->len;
        if (in->rep + in->replen > in->len) in->replen = in->len - in->rep;
    }
    mod = u;
    mod_len = len;
    start_sang();
}

/* ---------------------------------------------------------------- avspilling */
static void spill_note(Kanal *k)
{
    const Instr *in = k->in;
    if (!in || !in->data || !in->len) { k->aktiv = false; return; }
    uint32_t start = 0;
    if (k->eff == 9) {
        if (k->par) k->offset_mem = k->par;
        start = (uint32_t)k->offset_mem * 256;
    }
    /* som ProTracker: med en sloyfe spilles fra starten til slutten av sloyfen */
    uint32_t slutt = in->len;
    if (in->rep) slutt = in->rep + in->replen;
    if (start >= slutt) { k->aktiv = false; return; }
    k->data = in->data;
    k->pos = (uint64_t)start << 16;
    k->slutt = slutt;
    k->lstart = in->rep;
    k->llen = in->replen > 2 ? in->replen : 0;
    k->aktiv = true;
    if (!(k->vib_form & 4)) k->vib_pos = 0;
    if (!(k->trem_form & 4)) k->trem_pos = 0;
}

static int bolge(int form, int p)
{
    switch (form & 3) {
    case 1: return (p & 32) ? 255 - (p & 31) * 8 : (p & 31) * 8;      /* sagtann */
    case 2: return 255;                                              /* firkant */
    default: return sinus[p & 31];
    }
}

static void vol_skli(Kanal *k, int p)
{
    int opp = p >> 4, ned = p & 15;
    if (opp) k->vol += opp; else k->vol -= ned;
    if (k->vol < 0) k->vol = 0;
    if (k->vol > 64) k->vol = 64;
}

static void tone_porta(Kanal *k)
{
    if (!k->maal || !k->porta) return;
    if (k->periode < k->maal) { k->periode += k->porta; if (k->periode > k->maal) k->periode = k->maal; }
    else if (k->periode > k->maal) { k->periode -= k->porta; if (k->periode < k->maal) k->periode = k->maal; }
}

static void ny_rad(void)
{
    const uint8_t *r = monstre + (size_t)orden[pos] * 1024 + (size_t)rad * 16;
    for (int c = 0; c < 4; c++) {
        Kanal *k = &kan[c];
        const uint8_t *n = r + c * 4;
        int instr = (n[0] & 0xf0) | (n[2] >> 4);
        int periode = (n[0] & 0x0f) << 8 | n[1];
        k->eff = n[2] & 0x0f;
        k->par = n[3];
        k->kutt = -1;
        k->forsink = 0;
        if (k->eff == 0x0e && (k->par >> 4) == 0x0d && (k->par & 15)) {   /* ED: noten kommer senere */
            memcpy(k->ny_note, n, 4);
            k->forsink = k->par & 15;
            continue;
        }
        if (instr && instr < 32) {
            k->in = &ins[instr];
            k->vol = ins[instr].vol;
            k->fine = ins[instr].fine;
        }
        if (periode) {
            int note = note_for(periode);
            int p = per_tab[k->fine][note];
            if (k->eff == 0x0e && (k->par >> 4) == 5) p = per_tab[k->par & 15][note];   /* E5: finjustering */
            if (k->eff == 3 || k->eff == 5) k->maal = p;
            else { k->base = k->periode = p; k->maal = 0; spill_note(k); }
        }
        int x = k->par >> 4, y = k->par & 15;
        switch (k->eff) {
        case 0x3: if (k->par) k->porta = k->par; break;
        case 0x4: if (x) k->vib_fart = x; if (y) k->vib_dybde = y; break;
        case 0x7: if (x) k->trem_fart = x; if (y) k->trem_dybde = y; break;
        case 0xb: neste_pos = k->par; neste_rad = 0; hopp = true; break;
        case 0xc: k->vol = k->par > 64 ? 64 : k->par; break;
        case 0xd:
            if (!hopp) neste_pos = pos + 1;
            neste_rad = x * 10 + y;
            if (neste_rad > 63) neste_rad = 0;
            hopp = true;
            break;
        case 0xe:
            switch (x) {
            case 0x1: k->periode -= y; if (k->periode < 113) k->periode = 113; k->base = k->periode; break;
            case 0x2: k->periode += y; if (k->periode > 856) k->periode = 856; k->base = k->periode; break;
            case 0x4: k->vib_form = y; break;
            case 0x6:
                if (!y) k->loop_rad = rad;
                else {
                    if (!k->loop_ant) k->loop_ant = y; else k->loop_ant--;
                    if (k->loop_ant) { neste_pos = pos; neste_rad = k->loop_rad; hopp = true; }
                }
                break;
            case 0x7: k->trem_form = y; break;
            case 0xa: k->vol += y; if (k->vol > 64) k->vol = 64; break;
            case 0xb: k->vol -= y; if (k->vol < 0) k->vol = 0; break;
            case 0xc: k->kutt = y; break;
            case 0xe: if (!monster_pause) monster_pause = y; break;
            }
            break;
        case 0xf:
            if (k->par && k->par < 32) fart = k->par;
            else if (k->par >= 32) tempo = k->par;
            break;
        }
    }
}

/* et tikk: effektene og neste rad */
static void tikk_steg(void)
{
    if (tikk == 0) ny_rad();
    for (int c = 0; c < 4; c++) {
        Kanal *k = &kan[c];
        int x = k->par >> 4, y = k->par & 15;
        k->per_ut = k->periode;
        k->vol_ut = k->vol;
        if (k->forsink && tikk == k->forsink) {                 /* ED: noten naa */
            int instr = (k->ny_note[0] & 0xf0) | (k->ny_note[2] >> 4);
            int periode = (k->ny_note[0] & 0x0f) << 8 | k->ny_note[1];
            if (instr && instr < 32) { k->in = &ins[instr]; k->vol = ins[instr].vol; k->fine = ins[instr].fine; }
            if (periode) { k->base = k->periode = per_tab[k->fine][note_for(periode)]; spill_note(k); }
            k->per_ut = k->periode;
            k->vol_ut = k->vol;
        }
        if (k->kutt >= 0 && tikk == k->kutt) { k->vol = 0; k->vol_ut = 0; }
        if (tikk) {
            switch (k->eff) {
            case 0x1: k->periode -= k->par; if (k->periode < 113) k->periode = 113; k->base = k->periode; break;
            case 0x2: k->periode += k->par; if (k->periode > 856) k->periode = 856; k->base = k->periode; break;
            case 0x3: tone_porta(k); k->base = k->periode; break;
            case 0x5: tone_porta(k); k->base = k->periode; vol_skli(k, k->par); break;
            case 0x6: vol_skli(k, k->par); /* falls through */
            case 0x4: k->vib_pos = (k->vib_pos + k->vib_fart) & 63; break;
            case 0x7: k->trem_pos = (k->trem_pos + k->trem_fart) & 63; break;
            case 0xa: vol_skli(k, k->par); break;
            case 0xe:
                if (x == 0x9 && y && tikk % y == 0) spill_note(k);
                break;
            }
        }
        k->per_ut = k->periode;
        k->vol_ut = k->vol;
        if (k->eff == 0x0 && k->par) {                       /* arpeggio */
            int n = note_for(k->base), t = tikk % 3;
            if (t) { n += t == 1 ? x : y; if (n > 35) n = 35; k->per_ut = per_tab[k->fine][n]; }
        }
        if (k->eff == 0x4 || k->eff == 0x6) {
            int d = bolge(k->vib_form, k->vib_pos) * k->vib_dybde / 128;
            k->per_ut = k->periode + ((k->vib_pos & 32) ? -d : d);
        }
        if (k->eff == 0x7) {
            int d = bolge(k->trem_form, k->trem_pos) * k->trem_dybde / 64;
            k->vol_ut = k->vol + ((k->trem_pos & 32) ? -d : d);
            if (k->vol_ut < 0) k->vol_ut = 0;
            if (k->vol_ut > 64) k->vol_ut = 64;
        }
    }
    if (++tikk >= fart) {
        tikk = 0;
        if (monster_pause) { monster_pause--; return; }     /* EE: samme rad en gang til */
        if (hopp) {
            hopp = false;
            pos = neste_pos;
            rad = neste_rad;
        } else if (++rad >= 64) {
            rad = 0;
            pos++;
        }
        if (pos >= sang_len) pos = sang_len > BAKGRUNN_START ? BAKGRUNN_START : sang_start;
        neste_rad = 0;
    }
}

static int mikse(Kanal *k)
{
    if (!k->aktiv || k->per_ut < 113 || !k->vol_ut) return 0;
    uint32_t i = (uint32_t)(k->pos >> 16);
    if (i >= k->slutt) {
        if (!k->llen) { k->aktiv = false; return 0; }
        k->slutt = k->lstart + k->llen;
        i = k->lstart + (i - k->lstart) % k->llen;
        k->pos = (uint64_t)i << 16 | (k->pos & 0xffff);
    }
    int s = k->data[i] * k->vol_ut;
    /* PAL: 3546895 / periode Hz, i 16.16 per sample paa 48 kHz */
    k->pos += ((uint64_t)3546895 << 16) / ((uint64_t)k->per_ut * AUDIO_RATE);
    return s;
}

/* Blander musikken inn i lyden ut (n rammer, venstre/hoyre). Tones inn naar mog
 * kjorer og ut i introen og sluttscenen (program har sin egen musikk). */
void musikk_bland(int16_t *ut, int n)
{
    if (!mod) return;
    float maal = (musikk_paa && whd_mog_loaded) ? 1.0f : 0.0f;
    if (styrke <= 0.0f && maal <= 0.0f) return;
    if (styrke <= 0.0f) start_sang();                 /* fra begynnelsen hver gang den kommer tilbake */
    const float steg = 1.0f / (AUDIO_RATE * 1.5f);   /* 1,5 s inn eller ut */
    float g = 1.9f * paula_volume * musikk_volum;
    for (int i = 0; i < n; i++) {
        if (igjen <= 0) {
            tikk_steg();
            igjen += AUDIO_RATE * 5 / (tempo * 2);   /* 125 BPM = 50 tikk i sekundet */
        }
        igjen--;
        int l = mikse(&kan[0]) + mikse(&kan[3]);
        int r = mikse(&kan[1]) + mikse(&kan[2]);
        f_l += 0.45f * ((float)l - f_l);              /* lavpass som A500 (paula.c) */
        f_r += 0.45f * ((float)r - f_r);
        if (styrke < maal) { styrke += steg; if (styrke > maal) styrke = maal; }
        else if (styrke > maal) { styrke -= steg; if (styrke < 0.0f) styrke = 0.0f; }
        float k = g * styrke;
        int vl = ut[i * 2] + (int)lrintf(f_l * k), vr = ut[i * 2 + 1] + (int)lrintf(f_r * k);
        ut[i * 2] = (int16_t)(vl > 32767 ? 32767 : vl < -32768 ? -32768 : vl);
        ut[i * 2 + 1] = (int16_t)(vr > 32767 ? 32767 : vr < -32768 ? -32768 : vr);
    }
}

void musikk_sett(bool paa, float volum)
{
    musikk_paa = paa;
    if (volum >= 0.0f) musikk_volum = volum > 1.0f ? 1.0f : volum;
}

bool musikk_lastet(void) { return mod != NULL; }
