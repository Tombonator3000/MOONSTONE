/*
 * hver.c - flerspiller "Hver for seg": hver spiller har sitt eget spill.
 * Se docs/flerspiller.md.
 *
 * Hver maskin spiller et vanlig enspillerspill (ridder 1). Plassene 2-4, som
 * datamaskinen ellers styrer, brukes av de andre spillerne i rommet: de merkes
 * som fjerne, turen deres hoppes over, og posisjonen, livet, hvilken ridder det
 * er og navnet skrives inn fra nettet ved starten av hvert bilde. Spillet tegner
 * dem selv paa kartet ($0AAB0A), og de kan utfordres der de staar ($080F56).
 *
 * Turen til en fjern ridder hoppes over i starten ($0AAC14): trekktelleren
 * ($8E7A0) settes til maks ($8E7C2), som naar tasten E trykkes, og vi hopper
 * rett til slutten av turen ($0AAE62). Tilstanden er med i lagringen.
 *
 * Kartet: de andre ridderne tegnes inn i bakgrunnen ($8CDE8) naar en tur
 * starter ($0AAC54), og skjermen bygges paa nytt fra bakgrunnen hvert bilde
 * ($0AAF38). Saa de fjerne ridderne flytter seg mens du har turen, tar vi en
 * kopi av bakgrunnen rett foer de tegnes, og naar en av dem har flyttet seg,
 * legges kopien tilbake og ridderne tegnes paa nytt (en liten rutine i ledig
 * chip-minne, kalt fra toppen av lokka paa kartet, $0AAC8C).
 *
 * Kamp ($080AB8, a1 = den som blir angrepet): til duellene over nettet er paa
 * plass, styres en fjern ridder av datamaskinen her i kampen (+$36 = 4), og
 * den skrives ikke over fra nettet foer kampen er slutt ($080BD8). Etterpaa er
 * den som i sitt eget spill igjen.
 */
#include "amiga.h"
#include "m68k.h"
#include <stdio.h>
#include <string.h>

#define RIDDERE    0x8d5b4
#define RSTR       0x84
#define AKTIV      0x8d9ac
#define TELLER     0x8e7a0
#define MAKS       0x8e7c2
#define NAVN_BASE  0xfc000                 /* navnene til de fjerne ridderne (ledig chip) */
#define RUTINE     0xfc080                 /* tegner de andre ridderne i bakgrunnen paa nytt */
#define BAK_PEKER  0x8cde8                 /* long: bakgrunnen */
#define PLAN       0x1f40
#define LOKKE      0x0aac8c                /* toppen av lokka paa kartet */

static struct {
    uint8_t  fjern;                         /* bit k: plass k spilles paa en annen maskin */
    uint8_t  har[4];                        /* posisjonen er kjent */
    int16_t  x[4], y[4];
    int8_t   liv[4];
    uint8_t  figur[4];                      /* +$36: hvilken av de fire ridderne (0-3) */
    char     navn[4][16];
    uint8_t  kart;                          /* spillet er paa kartet (en tur har startet) */
    uint8_t  tatt;                          /* bit k: plassen er tatt over, originalen er lagret */
    uint32_t o36[4], o6c[4];                /* datamaskinens ridder, til plassen gis tilbake */
    uint8_t  o0b[4], o49[4];
    int16_t  tx[4], ty[4];                  /* slik de fjerne ridderne er tegnet i bakgrunnen */
    int8_t   tliv[4];
    uint8_t  tfigur[4], tvist;              /* tvist: bit k, plass k er tegnet */
    uint32_t sist_tegnet;                   /* bildet de sist ble tegnet paa nytt */
    uint8_t  kamp;                          /* bit k: plass k er i kamp her (datamaskinen styrer) */
} H;

/* bakgrunnen uten de andre ridderne, fra turen startet (ikke i lagringen: etter
 * lasting tegnes de foerst paa nytt neste tur) */
static uint8_t  kopi[5 * PLAN];
static uint32_t kopi_adr;
static bool     kopi_ok;

static uint32_t rd32(uint32_t a) { return mem_read32(a); }
static void gi_tilbake(void);

void hver_reset(void) { memset(&H, 0, sizeof H); kopi_ok = false; }
void hver_state(StateIO *s)
{
    STATE_VAR(s, H);
    if (!s->saving) kopi_ok = false;
}
bool hver_paa(void) { return H.fjern != 0; }
bool hver_kart(void) { return H.kart != 0; }

/* kommandoer fra frontenden, ved starten av et bilde:
 *   HVER_FJERN  arg = bitmaske med fjerne plasser (0 = av)
 *   HVER_RIDDER text = "plass x y liv figur NAVN" */
void hver_kommando(int k, int arg, const char *text)
{
    switch (k) {
    case HVER_FJERN:
        H.fjern = (uint8_t)(arg & 0x0e);    /* plass 0 er alltid den som spiller her */
        gi_tilbake();
        break;
    case HVER_RIDDER: {
        int p, x, y, liv, figur;
        char navn[16] = "";
        if (sscanf(text, "%d %d %d %d %d %15s", &p, &x, &y, &liv, &figur, navn) < 5) return;
        if (p < 1 || p > 3) return;
        H.har[p] = 1;
        H.x[p] = (int16_t)x;
        H.y[p] = (int16_t)y;
        H.liv[p] = (int8_t)liv;
        H.figur[p] = (uint8_t)(figur & 3);
        for (char *c = navn; *c; c++) if (*c == '_') *c = ' ';
        snprintf(H.navn[p], sizeof H.navn[p], "%s", navn[0] ? navn : "KNIGHT");
        break;
    }
    }
}

/* plasser som ikke lenger er fjerne, faar datamaskinens ridder tilbake (ellers
 * venter spillet paa en spiller som ikke finnes, siden +$36 ikke er 4) */
static void gi_tilbake(void)
{
    for (int k = 1; k < 4; k++) {
        if (!(H.tatt & (1 << k)) || (H.fjern & (1 << k))) continue;
        uint32_t r = RIDDERE + (uint32_t)k * RSTR;
        if (whd_mog_loaded) {
            mem_write32(r + 0x36, H.o36[k]);
            mem_write32(r + 0x6c, H.o6c[k]);
            mem_write8(r + 0x0b, H.o0b[k]);
            mem_write8(r + 0x49, H.o49[k]);
        }
        H.tatt &= (uint8_t)~(1 << k);
        H.kamp &= (uint8_t)~(1 << k);
        H.har[k] = 0;
    }
}

/* skriver de fjerne ridderne inn i spillet; kalles foer hvert bilde, men bare
 * paa kartet (paa tittelskjermen og under valg av ridder settes ridderne opp) */
void hver_frame(void)
{
    if (!H.fjern || !whd_mog_loaded || !H.kart) return;
    for (int k = 1; k < 4; k++) {
        if (!(H.fjern & (1 << k)) || !H.har[k] || (H.kamp & (1 << k))) continue;
        uint32_t r = RIDDERE + (uint32_t)k * RSTR;
        if (!(H.tatt & (1 << k))) {
            if (mem_read32(r + 0x36) != 4) continue;   /* bare datamaskinens plasser (to kan spille paa en maskin) */
            H.o36[k] = mem_read32(r + 0x36);
            H.o6c[k] = mem_read32(r + 0x6c);
            H.o0b[k] = (uint8_t)mem_read8(r + 0x0b);
            H.o49[k] = (uint8_t)mem_read8(r + 0x49);
            H.tatt |= (uint8_t)(1 << k);
        }
        mem_write16(r + 0x7e, (uint16_t)H.x[k]);
        mem_write16(r + 0x80, (uint16_t)H.y[k]);
        mem_write8(r + 0x49, (uint8_t)H.liv[k]);
        mem_write32(r + 0x36, H.figur[k]);  /* ikke 4: da ville datamaskinen styrt den */
        mem_write8(r + 0x0b, 2);
        /* +$52 > 0: turen hoppes over ($0AAEEC). En doed ridder som ikke er datamaskinens,
         * teller ellers som en doed spiller, og spillet slutter ($0AAF08) */
        mem_write8(r + 0x52, H.liv[k] > 0 ? 0 : 1);
        uint32_t n = NAVN_BASE + (uint32_t)k * 16;
        for (int i = 0; i < 16; i++) mem_write8(n + (uint32_t)i, (uint8_t)H.navn[k][i]);
        mem_write32(r + 0x6c, n);
    }
}

/* ridder k slik den er i spillet her: x, y, liv, figur (til nettet) */
void hver_ridder(int k, int ut[4])
{
    uint32_t r = RIDDERE + (uint32_t)(k & 3) * RSTR;
    ut[0] = (int16_t)mem_read16(r + 0x7e);
    ut[1] = (int16_t)mem_read16(r + 0x80);
    ut[2] = (int8_t)mem_read8(r + 0x49);
    ut[3] = (int)rd32(r + 0x36);
}

/* tittelmenyen: et nytt spill begynner, ingen plasser er tatt over */
static bool hook_tittel(void)
{
    H.kart = 0;
    H.tatt = 0;
    H.kamp = 0;
    kopi_ok = false;
    return false;
}

/* plass k er tegnet slik den er naa */
static void merk_tegnet(int k)
{
    H.tx[k] = H.x[k];
    H.ty[k] = H.y[k];
    H.tliv[k] = H.liv[k];
    H.tfigur[k] = H.figur[k];
}

/* turen starter, bakgrunnen har kartet og stedene, men ikke ridderne ennaa */
static bool hook_foer_riddere(void)
{
    uint32_t bak = mem_read32(BAK_PEKER);
    kopi_ok = false;
    H.tvist = 0;
    if (!H.fjern || bak < 0x100 || bak + sizeof kopi > CHIP_SIZE) return false;
    memcpy(kopi, chip + bak, sizeof kopi);
    kopi_adr = bak;
    kopi_ok = true;
    for (int k = 1; k < 4; k++)
        if (H.tatt & (1 << k)) { merk_tegnet(k); H.tvist |= (uint8_t)(1 << k); }
    H.sist_tegnet = M.frame;
    return false;
}

/* rutinen i chip-minnet: ridderne inn i bakgrunnen, tegnemaalet som foer */
static const uint16_t rutine[] = {
    0x48e7, 0xfffe,                         /* movem.l d0-d7/a0-a6,-(a7) */
    0x2f39, 0x0009, 0xe202,                 /* move.l $9e202,-(a7) ... tegnemaalet (fem plan) */
    0x2f39, 0x0009, 0xe206,
    0x2f39, 0x0009, 0xe20a,
    0x2f39, 0x0009, 0xe20e,
    0x2f39, 0x0009, 0xe212,
    0x2039, 0x0008, 0xcde8,                 /* move.l $8cde8,d0 */
    0x4eb9, 0x0008, 0x8f42,                 /* jsr $88f42: tegn i bakgrunnen */
    0x4eb9, 0x000a, 0xab0a,                 /* jsr $aab0a: de andre ridderne */
    0x23df, 0x0009, 0xe212,                 /* move.l (a7)+,$9e212 ... */
    0x23df, 0x0009, 0xe20e,
    0x23df, 0x0009, 0xe20a,
    0x23df, 0x0009, 0xe206,
    0x23df, 0x0009, 0xe202,
    0x4cdf, 0x7fff,                         /* movem.l (a7)+,d0-d7/a0-a6 */
    0x4e75,                                 /* rts */
};

/* toppen av lokka paa kartet: har en fjern ridder flyttet seg, tegnes de paa nytt */
static bool hook_lokke(void)
{
    if ((!H.fjern && !H.tvist) || !kopi_ok || M.frame - H.sist_tegnet < 4) return false;   /* tvist: de som gikk, viskes ut */
    if (mem_read32(BAK_PEKER) != kopi_adr) { kopi_ok = false; return false; }
    bool endret = false;
    for (int k = 1; k < 4; k++) {
        bool vis = (H.tatt >> k) & 1;
        bool var = (H.tvist >> k) & 1;
        if (vis != var || (vis && (H.tx[k] != H.x[k] || H.ty[k] != H.y[k] || H.tliv[k] != H.liv[k] || H.tfigur[k] != H.figur[k])))
            endret = true;
    }
    if (!endret) return false;
    H.tvist = 0;
    for (int k = 1; k < 4; k++)
        if (H.tatt & (1 << k)) { merk_tegnet(k); H.tvist |= (uint8_t)(1 << k); }
    H.sist_tegnet = M.frame;
    memcpy(chip + kopi_adr, kopi, sizeof kopi);
    for (size_t i = 0; i < sizeof rutine / sizeof rutine[0]; i++) mem_write16(RUTINE + (uint32_t)i * 2, rutine[i]);
    uint32_t sp = m68k_get_reg(NULL, M68K_REG_SP) - 4;
    mem_write32(sp, LOKKE);                 /* rts i rutinen kommer tilbake hit, og da er ingenting endret */
    m68k_set_reg(M68K_REG_SP, sp);
    m68k_set_reg(M68K_REG_PC, RUTINE);
    return true;
}

/* turen til en fjern ridder: hopp over den */
static bool hook_turstart(void)
{
    H.kart = 1;
    if (!H.fjern) return false;
    uint32_t a = rd32(AKTIV);
    if (a < RIDDERE || a >= RIDDERE + 4 * RSTR || (a - RIDDERE) % RSTR) return false;
    int k = (int)((a - RIDDERE) / RSTR);
    if (!(H.tatt & (1 << k))) return false;
    mem_write16(TELLER, mem_read16(MAKS));
    m68k_set_reg(M68K_REG_PC, 0x0aae62);
    return true;
}

/* en ridder blir angrepet (a1): er det en fjern ridder, styrer datamaskinen den i kampen */
static bool hook_kamp(void)
{
    if (!H.fjern) return false;
    uint32_t a = m68k_get_reg(NULL, M68K_REG_A1);
    if (a < RIDDERE || a >= RIDDERE + 4 * RSTR || (a - RIDDERE) % RSTR) return false;
    int k = (int)((a - RIDDERE) / RSTR);
    if (!(H.tatt & (1 << k))) return false;
    H.kamp |= (uint8_t)(1 << k);
    mem_write32(a + 0x36, 4);
    return false;
}

/* kampen er over (eller ble ikke noe av) */
static bool hook_kamp_slutt(void)
{
    H.kamp = 0;
    return false;
}

void hver_register_hooks(void)
{
    hooks_register_patch(0x0aac14, hook_turstart, "turstart (hver for seg)");
    hooks_register_patch(0x08188c, hook_tittel, "tittelmeny (hver for seg)");
    hooks_register_patch(0x0aac54, hook_foer_riddere, "kartet foer ridderne (hver for seg)");
    hooks_register_patch(LOKKE, hook_lokke, "lokka paa kartet (hver for seg)");
    hooks_register_patch(0x080ab8, hook_kamp, "ridder mot ridder (hver for seg)");
    hooks_register_patch(0x080bd8, hook_kamp_slutt, "ridder mot ridder slutt (hver for seg)");
}
